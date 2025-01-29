import os
import openai
import pdfplumber
import base64
from pdf2image import convert_from_path
from io import BytesIO
from dotenv import load_dotenv
from config import (
    VISION_MODEL as model,
    CLEANUP_MODEL as model2,
    TEMPERATURE as temperature,
    MAX_TOKENS,
    IMAGE_AREA_THRESHOLD
)
from src.prompts.prompt_templates import get_interpretation_prompt, get_cleanup_prompt

# Load environment variables from a .env file
load_dotenv()

# Create OpenAI client
client = openai.OpenAI()

def estimate_tokens_from_string(text):
    """
    Estimate the number of tokens in a text string.
    A rough estimate is 1 token = 4 characters for English text.
    """
    return len(text) // 4

def estimate_image_tokens(base64_string, detail="high"):
    """More accurate token estimation based on actual usage patterns"""
    if detail == "high":
        image_tokens = 525  # Increased from 300 to account for actual usage
    else:
        image_tokens = 150  # Increased from 85 to maintain ratio
    
    prompt_tokens = estimate_tokens_from_string(get_interpretation_prompt())
    # Add 75% to account for consistent underestimation of image processing
    return int((image_tokens + prompt_tokens) * 1.75)

def encode_image_to_base64(image):
    """Convert a PIL image to base64 string and estimate tokens"""
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    base64_string = base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    # Calculate token estimate
    token_estimate = estimate_image_tokens(base64_string)
    print(f"Estimated tokens for this image: {token_estimate:,}")
    
    return base64_string, token_estimate

def convert_pdf_to_images(pdf_path):
    # This uses the pdf2image library using the default options
    print("Converting PDF pages to images...")
    return convert_from_path(pdf_path)

def interpret_page(image, page_number, total_pages):
    # Interpret a single PDF page using GPT-4 Turbo
    print(f"\nProcessing page {page_number}/{total_pages}")
    
    # This encodes the image into a format GPT4 can use
    base64_image, image_tokens = encode_image_to_base64(image)
    
    # Estimate prompt tokens
    prompt_tokens = estimate_tokens_from_string(get_interpretation_prompt())
    print(f"Estimated prompt tokens: {prompt_tokens:,}")
    
    try:
        response = client.chat.completions.create(
            model=model,
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
            temperature=temperature
        )
        
        # Get actual token usage from API response
        actual_tokens = response.usage.total_tokens if hasattr(response, 'usage') else 0
        
        # Get completion tokens from response for estimation
        completion_tokens = len(response.choices[0].message.content) // 4
        print(f"Estimated completion tokens: {completion_tokens:,}")
        
        # Calculate total estimated tokens for this page
        total_page_tokens_estimate = prompt_tokens + image_tokens + completion_tokens
        print(f"Total estimated tokens for page {page_number}: {total_page_tokens_estimate:,}")
        print(f"Actual tokens used (from API): {actual_tokens:,}\n")
        
        return response.choices[0].message.content, total_page_tokens_estimate, actual_tokens
    except Exception as e:
        print(f"Error processing page {page_number}: {str(e)}")
        return f"Error processing page {page_number}: {str(e)}", 0, 0

def combine_page_content(all_pages_data):
    """Combine interpreted content of all pages"""
    # Extract just the content (not token counts) for joining
    content_only = [content for content, _, _ in all_pages_data]  # Unpack three values, ignore the last two
    return "\n".join(content_only)

def text_tidy_up(full_document):
    """Clean up formatting and check for structure, handling large documents appropriately"""
    
    # First estimate total tokens needed
    prompt_tokens = estimate_tokens_from_string(get_cleanup_prompt(full_document))
    print(f"\nTidy up prompt tokens: {prompt_tokens:,}")
    
    # GPT-4 has a context window of about 8k tokens, let's keep a safety margin
    MAX_CHUNK_SIZE = 6000  # tokens
    
    # If document is small enough, process it normally
    if prompt_tokens <= MAX_CHUNK_SIZE:
        try:
            final_response = client.chat.completions.create(
                model=model2,
                messages=[{"role": "user", "content": get_cleanup_prompt(full_document)}],
                temperature=temperature,
                max_tokens=MAX_TOKENS
            )
            
            actual_tokens = final_response.usage.total_tokens if hasattr(final_response, 'usage') else 0
            completion_tokens = len(final_response.choices[0].message.content) // 4
            print(f"Tidy up completion tokens: {completion_tokens:,}")
            print(f"Actual tidy up tokens (from API): {actual_tokens:,}")
            
            return final_response.choices[0].message.content, prompt_tokens, actual_tokens
            
        except Exception as e:
            print(f"Error in tidy up: {str(e)}")
            return f"Error in tidy up: {str(e)}\n\nRaw document content:\n\n{full_document}", 0, 0
    
    # If document is too large, split it into chunks and process each chunk
    print("\nDocument too large for single processing, splitting into chunks...")
    
    # Split document into paragraphs
    paragraphs = full_document.split('\n\n')
    chunks = []
    current_chunk = []
    current_chunk_tokens = 0
    
    # Build chunks that fit within token limit
    for paragraph in paragraphs:
        paragraph_tokens = estimate_tokens_from_string(paragraph)
        if current_chunk_tokens + paragraph_tokens > MAX_CHUNK_SIZE:
            # Process current chunk
            chunk_text = '\n\n'.join(current_chunk)
            chunks.append(chunk_text)
            current_chunk = [paragraph]
            current_chunk_tokens = paragraph_tokens
        else:
            current_chunk.append(paragraph)
            current_chunk_tokens += paragraph_tokens
    
    # Add the last chunk if it exists
    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))
    
    print(f"Split document into {len(chunks)} chunks")
    
    # Process each chunk
    processed_chunks = []
    total_prompt_tokens = 0
    total_actual_tokens = 0
    
    for i, chunk in enumerate(chunks, 1):
        print(f"\nProcessing chunk {i}/{len(chunks)}")
        try:
            chunk_response = client.chat.completions.create(
                model=model2,
                messages=[{
                    "role": "user", 
                    "content": get_cleanup_prompt(chunk) + "\nThis is part " + str(i) + " of " + str(len(chunks)) + "."
                }],
                temperature=temperature,
                max_tokens=MAX_TOKENS
            )
            
            chunk_actual_tokens = chunk_response.usage.total_tokens if hasattr(chunk_response, 'usage') else 0
            total_actual_tokens += chunk_actual_tokens
            total_prompt_tokens += estimate_tokens_from_string(chunk)
            
            processed_chunks.append(chunk_response.choices[0].message.content)
            
        except Exception as e:
            print(f"Error processing chunk {i}: {str(e)}")
            processed_chunks.append(chunk)  # Use original chunk if processing fails
    
    # Combine processed chunks
    final_content = '\n\n'.join(processed_chunks)
    
    return final_content, total_prompt_tokens, total_actual_tokens

def save_markdown(output_markdown_path, final_content):
    """Save the final formatted content to a markdown file"""
    with open(output_markdown_path, "w", encoding="utf-8") as md_file:
        md_file.write(final_content)

def is_page_text_only(pdf_path, page_number):
    """
    Check if a page is primarily text-based.
    Returns (is_text_only, extracted_text)
    """
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_number]
        
        # Get text content
        text = page.extract_text()
        
        # Get images
        images = page.images
        
        # If there's no text, it's definitely not text-only
        if not text:
            return False, ""
        
        # If there are no images, it's text-only
        if not images:
            return True, text
        
        # If there are images but they're small compared to page size
        page_area = page.width * page.height
        image_area = sum(img['width'] * img['height'] for img in images)
        
        # If images take up less than threshold of the page, consider it text-only
        if image_area / page_area < IMAGE_AREA_THRESHOLD:
            return True, text
            
        return False, text

def process_text_page(text, page_number, total_pages):
    """Process a text-only page through the LLM"""
    print(f"\nProcessing text page {page_number}/{total_pages}")
    
    try:
        # Estimate prompt tokens
        prompt_tokens = estimate_tokens_from_string(text)
        print(f"Estimated text tokens: {prompt_tokens:,}")
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": f"""Please process this text from page {page_number} of {total_pages}.
{get_interpretation_prompt()}

TEXT CONTENT:
{text}"""
                }
            ],
            temperature=temperature
        )
        
        # Get actual token usage from API response
        actual_tokens = response.usage.total_tokens if hasattr(response, 'usage') else 0
        
        # Get completion tokens from response for estimation
        completion_tokens = len(response.choices[0].message.content) // 4
        print(f"Estimated completion tokens: {completion_tokens:,}")
        
        # Calculate total estimated tokens for this page
        total_page_tokens_estimate = prompt_tokens + completion_tokens
        print(f"Total estimated tokens for page {page_number}: {total_page_tokens_estimate:,}")
        print(f"Actual tokens used (from API): {actual_tokens:,}\n")
        
        return response.choices[0].message.content, total_page_tokens_estimate, actual_tokens
    except Exception as e:
        print(f"Error processing text page {page_number}: {str(e)}")
        return f"Error processing page {page_number}: {str(e)}", 0, 0

# This function is the primary one called by run.py
def process_pdf(pdf_path, output_markdown_path):

    total_estimated_tokens = 0
    total_actual_tokens = 0
    
    # Get total pages
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
    
    # Create a list for all pages data
    all_pages_data = []
    
    # Uses pdf2images to convert to images
    print("\nConverting PDF pages to images (for non-text pages)...")
    images = convert_from_path(pdf_path)
    
    for page_number in range(total_pages):
        # Using the is_page_text_only, it checks whether it's text content or mixed.
        # There are two variables, the bolean is_text and the actual text.
        is_text, extracted_text = is_page_text_only(pdf_path, page_number)
        
        #If it's text only, we call the process_text_page function and get our text and token counts.
        if is_text:
            print(f"\nPage {page_number + 1} is primarily text - processing directly")
            content, estimated_tokens, actual_tokens = process_text_page(
                extracted_text, 
                page_number + 1, 
                total_pages
            )
        # If it's a mixture, we call the interpret_page function so LLM provides data.
        # It also returns text and token content.
        else:
            print(f"\nPage {page_number + 1} contains significant images - processing via image analysis")
            content, estimated_tokens, actual_tokens = interpret_page(
                images[page_number], 
                page_number + 1, 
                total_pages
            )
        # This appends all content and token counts.
        all_pages_data.append((content, estimated_tokens, actual_tokens))
        total_estimated_tokens += estimated_tokens
        total_actual_tokens += actual_tokens
    
    # Combine pages and send it to the function text_tidy_up
    full_document = combine_page_content(all_pages_data)
    final_content, analysis_estimated_tokens, analysis_actual_tokens = text_tidy_up(full_document)
    
    # Appends analysis token count
    total_estimated_tokens += analysis_estimated_tokens
    total_actual_tokens += analysis_actual_tokens
    
    # Save the final content using the save_markdown function
    save_markdown(output_markdown_path, final_content)
    
    print("\nTidy up:")
    analysis_diff_percent = ((analysis_actual_tokens - analysis_estimated_tokens) / analysis_estimated_tokens * 100) if analysis_estimated_tokens > 0 else 0
    print(f"  Estimated: {analysis_estimated_tokens:,} tokens")
    print(f"  Actual: {analysis_actual_tokens:,} tokens")
    print(f"  Difference: {analysis_diff_percent:+.1f}% ({analysis_actual_tokens - analysis_estimated_tokens:+,} tokens)")
    
    print("\nTotal Usage:")
    print("-" * 60)
    total_diff_percent = ((total_actual_tokens - total_estimated_tokens) / total_estimated_tokens * 100) if total_estimated_tokens > 0 else 0
    print(f"Total Estimated Tokens: {total_estimated_tokens:,}")
    print(f"Total Actual Tokens: {total_actual_tokens:,}")
    print(f"Overall Difference: {total_diff_percent:+.1f}% ({total_actual_tokens - total_estimated_tokens:+,} tokens)")
    
    return total_estimated_tokens, total_actual_tokens 