"""
Functionalities for Optical Character Recognition (OCR) and text extraction from PDF files.
"""
import logging
from pathlib import Path
from typing import List, Optional

import ocrmypdf

from langchain_core.documents import Document
from langchain_community.document_loaders import PyMuPDFLoader


logger = logging.getLogger(__name__)


class OCRProcessor:
    """
    Class for processing PDF files with OCR and extracting text content.
    """
    
    @staticmethod
    def ocr_pdf(input_pdf: str, language: str = "eng+spa", output_pdf: Optional[str] = None) -> Optional[str]:
        """
        Adds an OCR text layer to scanned PDF files, allowing them to be searched using OCRmyPDF.
        
        Args:
            input_pdf (str): The path to the input PDF file.
            language (str): The language(s) to use for OCR. Default is 'eng+spa' (English and Spanish).
            output_pdf (Optional[str]): The path to the output PDF file. If None, overwrites the input file.
            
        Returns:
            Optional[str]: The path to the processed PDF file if successful, None otherwise.
        """
        try:
            input_path = Path(input_pdf)
            # Validate input file
            if not input_path.exists():
                logger.error(f"Input PDF file '{input_pdf}' does not exist")
                return None
                
            # If no output path is specified, use the input path
            if output_pdf is None:
                output_pdf = input_pdf
            
            # Ensure the output directory exists
            output_path = Path(output_pdf)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Use ocrmypdf as a Python module
            logger.info(f"Applying OCR to '{input_pdf}' with language '{language}'")
            ocrmypdf.ocr(
                input_file=str(input_path),
                output_file=str(output_path),
                language=language,
                force_ocr=True,
                output_type="pdf"
            )
            logger.info(f"OCR successfully applied to '{input_pdf}', saved to '{output_pdf}'")
            
            return str(output_path)
        except ocrmypdf.exceptions.PriorOcrFoundError as e:
            logger.warning(f"Prior OCR found in '{input_pdf}': {str(e)}")
            return str(output_path)  # Return the path anyway as the file is usable
        except Exception as e:
            logger.exception(f"Error applying OCR to '{input_pdf}': {e}")
            return None
    
    @staticmethod
    def load_pdf(file_path: str, namespace: str) -> List[Optional[Document]]:
        """
        Load a PDF file and extract its text content.
        
        Args:
            file_path (str): The path to the PDF file.
            namespace (str): The namespace to use for the extracted text.
            metadata (Optional[Dict[str, Any]]): Additional metadata to include.
            
        Returns:
            List[Document]: A list of Document objects, each representing a page of the PDF file.
        """
        try:
            # Validate input file
            input_path = Path(file_path)
            if not input_path.exists():
                logger.error(f"PDF file '{file_path}' does not exist")
                return []
            
            logger.info(f"Loading PDF file '{file_path}' with namespace '{namespace}'")
            
            # Load the PDF file
            loader = PyMuPDFLoader(file_path)
            source = input_path.name
            
            # Process each page
            file_content = []
            for doc in loader.lazy_load():
                # Merge default metadata with document metadata and additional metadata
                doc_metadata = {
                    "namespace": namespace,
                    "source": source,
                    "page": doc.metadata.get("page", 0),
                    "author": doc.metadata.get("author", ""),
                }
                # Update document metadata
                doc.metadata = doc_metadata
                file_content.append(doc)
            
            logger.info(f"Successfully loaded {len(file_content)} pages from '{file_path}'")
            return file_content
        except Exception as e:
            logger.exception(f"Error loading PDF file '{file_path}': {e}")
            return []
