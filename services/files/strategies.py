"""
This module contains the Strategy pattern implementation for file processing.
"""
from __future__ import annotations

import logging
import shutil
import mimetypes
import subprocess
from pathlib import Path
from typing import Optional
from abc import ABC, abstractmethod


logger = logging.getLogger(__name__)


class Strategy(ABC):
    """Strategy interface for file processing."""
    
    @abstractmethod
    def execute(self, input_file: str, outdir: str) -> Optional[str]:
        """
        Execute the strategy.
        
        Args:
            input_file (str): The path to the input file.
            outdir (str): The path to the destination directory.
            
        Returns:
            Optional[str]: The path to the output file if successful, None otherwise.
        """


class AcceptedFiles(Strategy):
    """
    AcceptedFiles strategy.
    This strategy only moves the file to the destination directory.
    """
    
    def execute(self, input_file: str, outdir: str) -> Optional[str]:
        """
        Execute the strategy (AcceptedFiles).
        
        Args:
            input_file (str): The path to the input file.
            outdir (str): The path to the destination directory.
            
        Returns:
            Optional[str]: The path to the moved file if successful, None otherwise.
        """
        try:
            input_path = Path(input_file)
            destination = Path(outdir) / input_path.name
            
            # Check if destination already exists
            if destination.exists():
                logger.warning(f"File '{destination}' already exists. Adding suffix.")
                destination = Path(outdir) / f"{input_path.stem}_copy{input_path.suffix}"
            
            output_path = shutil.move(str(input_path), str(destination))
            logger.info(f"File '{input_file}' moved to '{output_path}'")
            return Path(output_path).as_posix()
        except (shutil.Error, OSError) as e:
            logger.error(f"Error moving file '{input_file}' to '{outdir}': {e}")
            return None


class ConversionStrategy(Strategy):
    """
    Conversion strategy.
    This strategy converts the file to PDF:
      - Using ImageMagick if the file is an image.
      - Using LibreOffice if the file is a document.
    And saves the converted file to the destination directory.
    """
    
    def execute(self, input_file: str, outdir: str) -> Optional[str]:
        """
        Execute the strategy (ConversionStrategy).
        
        Args:
            input_file (str): The path to the input file.
            outdir (str): The path to the destination directory.
            
        Returns:
            Optional[str]: The path to the converted PDF file if successful, None otherwise.
        """
        input_path = Path(input_file)
        destination_pdf = Path(outdir) / f"{input_path.stem}.pdf"
        
        # Check if destination already exists
        if destination_pdf.exists():
            logger.warning(f"File '{destination_pdf}' already exists. Adding suffix.")
            destination_pdf = Path(outdir) / f"{input_path.stem}_copy.pdf"
        
        mime_type, _ = mimetypes.guess_type(input_file)
        
        try:
            if mime_type and mime_type.startswith("image"):
                logger.info(f"Converting image '{input_file}' to PDF using ImageMagick")
                try:
                    # First try with 'magick' command (newer ImageMagick versions)
                    result = subprocess.run(
                        ["magick", str(input_path), str(destination_pdf)],
                        check=True,
                        capture_output=True,
                        text=True,
                    )
                except FileNotFoundError:
                    # Fall back to 'convert' command (older ImageMagick versions or Debian)
                    logger.info("'magick' command not found, trying 'convert' instead")
                    result = subprocess.run(
                        ["convert", str(input_path), str(destination_pdf)],
                        check=True,
                        capture_output=True,
                        text=True,
                    )
                logger.debug(f"ImageMagick output: {result.stdout}")
            else:
                logger.info(f"Converting document '{input_file}' to PDF using LibreOffice")
                result = subprocess.run(
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
                logger.debug(f"LibreOffice output: {result.stdout}")
            
            # Verify the file was created
            if not destination_pdf.exists():
                logger.error(f"Conversion completed but file '{destination_pdf}' not found")
                return None
                
            logger.info(f"File '{input_file}' converted to PDF: '{destination_pdf}'")

            return destination_pdf.as_posix()
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else str(e)
            logger.error(f"Error converting file '{input_file}' to PDF: {error_msg}")

            return None
        except Exception as e:
            logger.error(f"Unexpected error converting file '{input_file}' to PDF: {e}")

            return None
