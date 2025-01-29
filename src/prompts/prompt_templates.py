"""
This module contains all prompt templates used in the PDF processing pipeline.
Each prompt is documented with its purpose and usage.
"""

def get_interpretation_prompt():
    """
    Returns the prompt used for interpreting PDF pages.
    This prompt is used for both image-based and text-based page processing.
    """
    return """
1. Convert the image to a markdown document, being aware that it forms part of a larger multipage document.
2. Preserve the original formatting of the document where possible.
3. Ensure tables are scanned and converted to markdown tables.
4. For organisational charts or diagrams, attempt to create a text based representation of the diagram that 
```
Manager 1
    ├── Sub manager 1
        ├── Sub manager 4
```
5. Don't add any text that is not in the original document.
6. Look for any page numbers and add them to the top of the page with the text "Page X"
7. Look for any headers or footers that indicate the title or effective date of the document. Only include the title at the top of the text.
    """
def get_cleanup_prompt(document_content: str) -> str:
    """
    Returns the prompt used for final document cleanup.
    
    Args:
        document_content (str): The combined content of all processed pages
        
    Returns:
        str: The formatted cleanup prompt
    """
    return f"""
This document has been created by an LLM by scanning images of a PDF and forms part of a larger document.
Ensure the formatting is coherent and the structure is correct.
Remove any mention of "markdown" from the top and don't add anything new.
{document_content}
"""

def get_text_page_prompt(text: str, page_number: int, total_pages: int) -> str:
    """
    Returns the prompt used for processing text-only pages.
    
    Args:
        text (str): The extracted text content from the page
        page_number (int): Current page number
        total_pages (int): Total number of pages
        
    Returns:
        str: The formatted text processing prompt
    """
    return f"""Please process this text from page {page_number} of {total_pages}.
{get_interpretation_prompt()}

TEXT CONTENT:
{text}""" 