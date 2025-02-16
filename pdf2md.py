import os
import openai
import pdfplumber
import base64
from pdf2image import convert_from_path
from io import BytesIO
from dotenv import load_dotenv

# Configuration
VISION_MODEL = "gpt-4-vision-preview"  # Model for processing images and text pages
CLEANUP_MODEL = "gpt-4"  # Model for final document cleanup
TEMPERATURE = 0.0  # Temperature setting for all API calls
MAX_TOKENS = 4096  # Maximum tokens for API responses
IMAGE_AREA_THRESHOLD = 0.1  # Threshold for determining text-only pages (10% of page area)

# Load environment variables from a .env file
load_dotenv()

# Create OpenAI client
client = openai.OpenAI()

def get_interpretation_prompt():
    """Returns the prompt used for interpreting PDF pages."""
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
    """Returns the prompt used for final document cleanup."""
    return f"""
This document has been created by an LLM by scanning images of a PDF and forms part of a larger document.
Ensure the formatting is coherent and the structure is correct.
Remove any mention of "markdown" from the top and don't add anything new.
{document_content}
"""

def get_text_page_prompt(text: str, page_number: int, total_pages: int) -> str:
    """Returns the prompt used for processing text-only pages."""
    return f"""Please process this text from page {page_number} of {total_pages}.
{get_interpretation_prompt()}

TEXT CONTENT:
{text}"""

def encode_image_to_base64(image):
    """Convert a PIL image to base64 string"""
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def convert_pdf_to_images(pdf_path):
    """Convert PDF pages to images"""
    print("Converting PDF pages to images...")
    return convert_from_path(pdf_path)

def interpret_page(image, page_number, total_pages):
    """Interpret a single PDF page using GPT-4 Vision"""
    print(f"\nProcessing page {page_number}/{total_pages}")
    
    base64_image = encode_image_to_base64(image)
    
    try:
        response = client.chat.completions.create(
            model=VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": get_interpretation_prompt()},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                    ]
                }
            ],
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error processing page {page_number}: {str(e)}")
        return f"Error processing page {page_number}: {str(e)}"

def combine_page_content(all_pages_data):
    """Combine interpreted content of all pages"""
    return "\n".join(all_pages_data)

def text_tidy_up(full_document):
    """Clean up formatting and check for structure"""
    try:
        final_response = client.chat.completions.create(
            model=CLEANUP_MODEL,
            messages=[{"role": "user", "content": get_cleanup_prompt(full_document)}],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS
        )
        return final_response.choices[0].message.content
    except Exception as e:
        print(f"Error in tidy up: {str(e)}")
        return f"Error in tidy up: {str(e)}\n\nRaw document content:\n\n{full_document}"

def save_markdown(output_markdown_path, final_content):
    """Save the final formatted content to a markdown file"""
    with open(output_markdown_path, "w", encoding="utf-8") as md_file:
        md_file.write(final_content)

def is_page_text_only(pdf_path, page_number):
    """Check if a page is primarily text-based"""
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_number]
        text = page.extract_text()
        images = page.images
        
        if not text:
            return False, ""
        
        if not images:
            return True, text
        
        page_area = page.width * page.height
        image_area = sum(img['width'] * img['height'] for img in images)
        
        if image_area / page_area < IMAGE_AREA_THRESHOLD:
            return True, text
            
        return False, text

def process_text_page(text, page_number, total_pages):
    """Process a text-only page through the LLM"""
    print(f"\nProcessing text page {page_number}/{total_pages}")
    
    try:
        response = client.chat.completions.create(
            model=VISION_MODEL,
            messages=[{"role": "user", "content": get_text_page_prompt(text, page_number, total_pages)}],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error processing text page {page_number}: {str(e)}")
        return f"Error processing text page {page_number}: {str(e)}"

def process_pdf(pdf_path, output_markdown_path):
    """Main function to process a PDF file and convert it to markdown"""
    # Convert PDF to images
    images = convert_pdf_to_images(pdf_path)
    total_pages = len(images)
    
    # Process each page
    processed_pages = []
    
    for page_number, image in enumerate(images, 1):
        # Check if page is primarily text
        is_text, text_content = is_page_text_only(pdf_path, page_number - 1)
        
        if is_text:
            print(f"Page {page_number} is primarily text, processing as text...")
            page_content = process_text_page(text_content, page_number, total_pages)
        else:
            print(f"Page {page_number} contains images, processing with vision model...")
            page_content = interpret_page(image, page_number, total_pages)
        
        processed_pages.append(page_content)
    
    # Combine all pages
    combined_content = combine_page_content(processed_pages)
    
    # Clean up the final document
    final_content = text_tidy_up(combined_content)
    
    # Save to markdown file
    save_markdown(output_markdown_path, final_content)
    print(f"\nMarkdown file saved to: {output_markdown_path}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Convert PDF to Markdown")
    parser.add_argument("pdf_path", help="Path to the input PDF file")
    parser.add_argument("output_path", help="Path for the output markdown file")
    
    args = parser.parse_args()
    
    process_pdf(args.pdf_path, args.output_path) 