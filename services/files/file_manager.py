"""
File manager module that implements the Strategy pattern for file processing.
"""
import logging
import mimetypes
from pathlib import Path
from typing import Optional, Dict, Type

from .strategies import Strategy, AcceptedFiles, ConversionStrategy


logger = logging.getLogger(__name__)


class FileManager:
    """
    File manager class that uses the Strategy pattern to process files.
    """
    
    def __init__(self, strategy: Optional[Strategy] = None) -> None:
        """
        Initialize the FileManager with an optional strategy.
        
        Args:
            strategy (Optional[Strategy]): The strategy to use for file processing.
        """
        self._strategy = strategy
    
    @property
    def strategy(self) -> Optional[Strategy]:
        """Get the current strategy."""
        return self._strategy
    
    @strategy.setter
    def strategy(self, strategy: Strategy) -> None:
        """
        Set the strategy.
        
        Args:
            strategy (Strategy): The strategy to use for file processing.
        """
        self._strategy = strategy
    
    def execute_strategy(self, input_file: str, outdir: str) -> Optional[str]:
        """
        Execute the current strategy.
        
        Args:
            input_file (str): The path to the input file.
            outdir (str): The path to the destination directory.
            
        Returns:
            Optional[str]: The path to the output file if successful, None otherwise.
        """
        if self._strategy is None:
            logger.error("No strategy set for FileManager")
            return None
        
        # Validate input file exists
        if not Path(input_file).exists():
            logger.error(f"Input file '{input_file}' does not exist")
            return None
        
        return self._strategy.execute(input_file, outdir)


# Strategy factory mapping file types to strategies
STRATEGY_MAP: Dict[str, Type[Strategy]] = {
    "application/pdf": AcceptedFiles,
    "default": ConversionStrategy
}


def manage_files(input_file: str, outdir: str) -> Optional[str]:
    """
    Function to manage files using the Strategy pattern.
    
    Args:
        input_file (str): The path to the source file.
        outdir (str): The path to the destination directory.
        
    Returns:
        Optional[str]: The path to the processed file if successful, None otherwise.
    """
    try:
        # Validate input
        input_path = Path(input_file)
        if not input_path.exists():
            logger.error(f"Input file '{input_file}' does not exist")
            return None
        
        # Determine file type and select appropriate strategy
        mime_type, _ = mimetypes.guess_type(input_file)
        
        # Get the appropriate strategy class
        strategy_class = STRATEGY_MAP.get(mime_type, STRATEGY_MAP["default"])
        
        # Create FileManager with the selected strategy
        context = FileManager(strategy=strategy_class())
        
        # Execute the strategy
        logger.info(f"Processing file '{input_file}' with strategy '{strategy_class.__name__}'")
        result = context.execute_strategy(input_file, outdir=outdir)
        
        if result:
            logger.info(f"File processing completed successfully: '{result}'")
        else:
            logger.error(f"File processing failed for '{input_file}'")

        return result
    
    except Exception as e:
        logger.exception(f"Unexpected error processing file '{input_file}': {e}")
        
        return None
