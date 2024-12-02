"""
This module contains the Strategy pattern implementation for the file management system.
"""

import os
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
import requests
from requests.exceptions import RequestException
# from .utils import get_logger


# # logger = get_logger(__name__)

class Strategy(ABC):
    """
    Strategy interface.
    """

    @abstractmethod
    def execute(self, src_path: str, dst_path: Optional[str] = None, dst_dir: Optional[str] = None) -> Optional[str]:
        """
        Execute the strategy.
        Aceepts a dst_path or a dst_dir, but not both.

        Args:
            src_path (str): The path to the source file.
            dst_path (str | None): The path to the destination file.
            dst_dir (str | None): The path to the destination directory.

        Returns:
            Optional[str]: The path to the output file.
        """


class AcceptedFiles(Strategy):
    """ 
    AcceptedFiles strategy:
    ['pdf', 'txt', 'md', 'html', 'java', 'py', 'c', 'cpp', 'js']
    This strategy moves the file to the destination path or directory.
    """

    def execute(self, src_path: str, dst_path: Optional[str] = None, dst_dir: Optional[str] = None) -> Optional[str]:
        if dst_path and dst_dir:
            # logger.error("Error: dst_path and dir_name cannot be used at the same time")
            return
        output_path = None
        if dst_path:
            output_path = shutil.move(src_path, dst_path)
            # logger.info("file successfully moved to: %s", dst_path)
            output_path = Path(dst_path).absolute()
        elif dst_dir:
            try:
                # Crear el directorio destino si no existe
                os.makedirs(os.path.dirname(dst_dir), exist_ok=True)
                # Mover el archivo
                output_path = shutil.move(src_path, dst_dir)
                # logger.info("file successfully moved to: %s", output_path)
            except OSError as e:
                print(e)
                # logger.error("Error moving the file: %s", e)
        return str(output_path)


class Another(Strategy):
    """
    Another strategy:
    ['png', 'jpg', 'jpeg', 'ppt', 'pptx', 'doc', 'docx']
    This strategy converts the file to pdf using LibreOffice and saves it to the destination path or directory.
    """

    def execute(self, src_path: str, dst_path: Optional[str] = None, dst_dir: Optional[str] = None) -> Optional[str]:
        if dst_path and dst_dir:
            # logger.error("Error: dst_path and dir_name cannot be used at the same time")
            return
        libre_office_url = os.getenv('LIBRE_OFFICE_URL')
        with open(src_path, 'rb') as file:
            files = {'file': file}
            data = {'convert-to': 'pdf'}
            try:
                response = requests.post(
                    url=libre_office_url, 
                    files=files, data=data, 
                    timeout=20)
                response.raise_for_status()
                # logger.info("File successfully converted")
            except (RequestException) as e:
                # logger.error("Error converting the file: %s", e)
                return
        output_path = None
        if dst_path:
            with open(dst_path, 'wb') as output_file:
                output_file.write(response.content)
            # logger.info("file converted and successfully moved to: %s", dst_path)
            output_path = Path(dst_path).absolute()
        elif dst_dir:
            os.makedirs(os.path.dirname(dst_dir), exist_ok=True)
            output_path = Path(dst_dir) / (Path(src_path).stem + '.pdf')
            with open(output_path, 'wb') as output_file:
                output_file.write(response.content)
            # logger.info("file converted and successfully moved to: %s", output_path)
        return str(output_path)


class FileManager:
    """
    File manager class that uses the Strategy pattern.
    """

    def __init__(self):
        self._strategy = None

    def set_strategy(self, strategy: Strategy) -> None:
        """
        Set the strategy.

        Args:
            strategy (Strategy): The strategy to use.
        
        Returns:
            None
        """

        self._strategy = strategy

    def execute_strategy(self, src_path: str, dst_path: Optional[str] = None, dst_dir: Optional[str] = None) -> Optional[str]:
        """
        Execute the strategy.

        Args:
            src_path (str): The path to the source file.
            dst_path (str | None): The path to the destination file.
            dst_dir (str | None): The path to the destination directory.

        Returns:
            Optional[str]: The path to the output file.
        """

        path = self._strategy.execute(src_path, dst_path, dst_dir)
        return path
    

def manage_files(file_path: str, dst_path: str) -> None:
    file_manager = FileManager()
    acceyepted_files = AcceptedFiles()
    another = Another()
    if file_path.lower().endswith("pdf"):
        file_manager.set_strategy(acceyepted_files)
    else:
        file_manager.set_strategy(another)
    file_manager.execute_strategy(file_path, dst_path=dst_path)
