"""
This module contains the Strategy pattern implementation for the file management system.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
import subprocess
import mimetypes
import shutil


class Strategy(ABC):
    """Strategy interface."""
    @abstractmethod
    def execute(self, input_file: str, outdir: str) -> Optional[str]:
        """Execute the strategy. """


class AcceptedFiles(Strategy):
    """ 
    AcceptedFiles strategy.
    This strategy only moves the file to the destination path directory.
    """
    def execute(self, input_file: str, outdir: str) -> Optional[str]:
        """Execute the strategy (AcceptedFiles)."""
        try:
            output_path = shutil.move(input_file, f"{outdir}/{Path(input_file).name}")
        except shutil.Error as e:
            print(f"Error moving file: {e}")
            return None
        return Path(output_path).as_posix()


class Another(Strategy):
    """
    Another strategy.
    This strategy converts the file to PDF
    - Using LibreOffice if the file is a document (LibreOffice have to donwloaded in Docker container).
    - Using ImageMagick if the file is an image. (ImageMagick have to donwloaded in Docker container).
    And saves it to the destination directory.
    """
    def execute(self, input_file: str, outdir: str) -> Optional[str]:
        """Execute the strategy (Another)."""
        mime_type, _ = mimetypes.guess_type(input_file)
        try:
            if mime_type.startswith('image'):
                subprocess.run([
                    'convert',
                    input_file,
                    f'{outdir}/{Path(input_file).stem}.pdf'
                ], check=True)
            else:
                subprocess.run([
                    'soffice',
                    '--headless',
                    '--convert-to', 'pdf',
                    '--outdir', outdir,
                    input_file
                ], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error converting file: {e}")
            return None
        return Path(f'{outdir}/{Path(input_file).stem}.pdf').as_posix()


class FileManager:
    """File manager class that uses the Strategy pattern."""
    def __init__(self, strategy: Optional[Strategy] = None) -> None:
        self._strategy = strategy

    @property
    def strategy(self) -> Strategy:
        """Get the strategy."""
        return self._strategy
    
    @strategy.setter
    def strategy(self, strategy: Strategy) -> None:
        """Set the strategy."""
        self._strategy = strategy

    def execute_strategy(self, input_file: str, outdir: str) -> Optional[str]:
        """
        Execute the strategy.

        Args:
            input_file (str): The path to the input file.
            outdir str: The path to the destination directory.

        Returns:
            Optional[str]: The path to the output file.
        """
        return self._strategy.execute(input_file, outdir)
 

def manage_files(input_file: str, outdir: str) -> Optional[str]:
    """
    Function to manage the files using the Strategy pattern.

    Args:
        input_file (str): The path to the source file.
        outdir (str): The path to the destination directory.
    """
    context = FileManager()
    mime_type, _ = mimetypes.guess_type(input_file)
    if mime_type == 'application/pdf':
        context.strategy = AcceptedFiles()
    else:
        context.strategy = Another()
    return context.execute_strategy(input_file, outdir=outdir)
