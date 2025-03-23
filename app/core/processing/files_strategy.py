"""
This module contains the Strategy pattern implementation for the file management system.
"""
from __future__ import annotations
import logging
import shutil
import mimetypes
import subprocess
from pathlib import Path
from typing import Optional
from abc import ABC, abstractmethod


# Configuración del logger para este módulo
logger = logging.getLogger(__name__)


class Strategy(ABC):
    """Strategy interface."""
    @abstractmethod
    def execute(self, input_file: str, outdir: str) -> Optional[str]:
        """Execute the strategy."""


class AcceptedFiles(Strategy):
    """
    AcceptedFiles strategy.
    This strategy only moves the file to the destination directory.
    """
    def execute(self, input_file: str, outdir: str) -> Optional[str]:
        """Execute the strategy (AcceptedFiles)."""
        try:
            input_path = Path(input_file)
            destination = Path(outdir) / input_path.name
            output_path = shutil.move(str(input_path), str(destination))
            return Path(output_path).as_posix()
        except shutil.Error as e:
            logger.error(f"Error moving file '{input_file}' to '{outdir}': {e}")
            return None


class Another(Strategy):
    """
    Another strategy.
    This strategy converts the file to PDF:
      - Using ImageMagick if the file is an image (ImageMagick must be installed in the Docker container).
      - Using LibreOffice if the file is a document (LibreOffice must be installed in the Docker container).
    And saves the converted file to the destination directory.
    """
    def execute(self, input_file: str, outdir: str) -> Optional[str]:
        """Execute the strategy (Another)."""
        input_path = Path(input_file)
        destination_pdf = Path(outdir) / f"{input_path.stem}.pdf"
        mime_type, _ = mimetypes.guess_type(input_file)
        try:
            if mime_type and mime_type.startswith("image"):
                subprocess.run(
                    ["magick", str(input_path), str(destination_pdf)],
                    check=True,
                    capture_output=True,
                    text=True,
                )
            else:
                subprocess.run(
                    [
                        "soffice",
                        "--headless",
                        "--convert-to",
                        "pdf",
                        "--outdir",
                        str(outdir),
                        str(input_path),
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else str(e)
            logger.error(f"Error converting file '{input_file}' to PDF: {error_msg}")
            return None
        return destination_pdf.as_posix()


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
            outdir (str): The path to the destination directory.

        Returns:
            Optional[str]: The path to the output file.
        """
        if self._strategy is None:
            logger.error("No strategy set for FileManager")
            return None
        return self._strategy.execute(input_file, outdir)


def manage_files(input_file: str, outdir: str) -> Optional[str]:
    """
    Function to manage the files using the Strategy pattern.

    Args:
        input_file (str): The path to the source file.
        outdir (str): The path to the destination directory.

    Returns:
        Optional[str]: The path to the processed file.
    """
    context = FileManager()
    mime_type, _ = mimetypes.guess_type(input_file)
    if mime_type == "application/pdf":
        context.strategy = AcceptedFiles()
    else:
        context.strategy = Another()
    return context.execute_strategy(input_file, outdir=outdir)
