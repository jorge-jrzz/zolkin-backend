"""
Functionalities for Optical Character Recognition (OCR) and text extraction from PDF files.
"""
import subprocess
from pathlib import Path
from typing import List

from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.documents import Document


class LoadFile:
    @staticmethod
    def ocr_pdf(input_pdf: str, language: str = "eng+spa") -> None:
        """
        Adds an OCR text layer to scanned PDF files, allowing them to be searched using OCRmyPDF.

        Args:
            input_pdf (str): The path to the input and output PDF file.
            language (str): The language(s) to use for OCR. Default is 'eng+spa' (English and Spanish).

        Returns:
            None
        """
        try:
            # Construir el comando
            comando = [
                "ocrmypdf",
                "-l",
                language,
                "--force-ocr",
                "--jobs",
                "6",  # Número de trabajos en paralelo
                "--output-type",
                "pdf",
                input_pdf,
                input_pdf,  # Sobreescribir el archivo de entrada
            ]
            # Ejecutar el comando
            subprocess.run(comando, check=True)
            print(f"OCR aplicado exitosamente a {input_pdf}.")
        except subprocess.CalledProcessError as e:
            print(f"Error al aplicar OCR: {e}")

    @classmethod
    def load_file(cls, file_path: str, namespace: str) -> List[Document]:
        """
        Load a PDF file and extract its text content.

        Args:
            file_path (str): The path to the PDF file.
            namespace (str): The namespace to use for the extracted text.

        Returns:
            List[Document]: A list of Document objects, each representing a page of the PDF file.
        """
        loader = PyMuPDFLoader(file_path)
        source = Path(file_path).name
        file_content = []
        for doc in loader.lazy_load():
            doc.metadata = {
                "namespace": namespace,
                "source": source,
                "page": doc.metadata["page"],
                "author": doc.metadata["author"],
            }
            file_content.append(doc)

        return file_content
