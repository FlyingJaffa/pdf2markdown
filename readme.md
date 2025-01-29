# PDF to Text Converter

A simple tool that turns PDF files into formatted markdown documents. 

It breaks down a PDF into pages and runs an analysis of each:

1. If the page is 90% text (by area) we can simply extract the text from the pdf, assuming that the images on the page are not of key importance. The benefit of having step 1 means that for PDF documents that contain many pages of pure text, we're not wasting LLM tokens on image processing every page.

2. If mixed content or only images, then the whole page is sent as an image for interpretation by the LLM. This seems to yield better results than non-LLM based extraction, as it allow 'in-context' addition of diagrams, organisational charts etc.

3. The document is then sent back for a final pass through the LLM to clean up formatting and check for structure.

## What it does

- Converts the PDF into images
- Analyses each page to decide if it's text only or mixed
- Extracts text or requests LLM interpretation of content
- Reassembles all pages of text
- Sends completed document (according to size of document this may get chunked and reassmbled after) back to the LLM for a final format/content check

## Quick Start

1. Currently only set up to work from the IDE
2. Install the required dependencies: `pip install -r requirements.txt`
3. Create a .env with OPENAI_API_KEY=your_api_key
4. Place a PDF file in the data folder
5. Run the 'run.py' script

## How it works

The tool looks at each page of your PDF and figures out whether it's mostly text or images. For text pages, it extracts the text directly. For pages with lots of images, it uses GPT-4 Vision to understand what's in them. Everything gets combined into a nice markdown file at the end.

You can tweak how it works by changing settings in `config.py`, like which GPT model to use or how it handles different types of pages.

That's it... Drop your PDFs in the data folder and run the script - it'll handle the rest.

## Configuration

Key settings can be adjusted in `config.py`:
- `VISION_MODEL`: Model for processing images and text pages
- `CLEANUP_MODEL`: Model for final document cleanup
- `TEMPERATURE`: Temperature setting for API calls
- `MAX_TOKENS`: Maximum tokens for API responses
- `IMAGE_AREA_THRESHOLD`: Threshold for determining text-only pages

## Output

The tool provides:
- Converted markdown files
- Progress updates during processing

## Error Handling

- Automatically creates missing directories
- Handles duplicate filenames
- Provides clear error messages for common issues
- Gracefully handles API rate limits and errors






