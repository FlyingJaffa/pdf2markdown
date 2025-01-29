import os
from pathlib import Path
from src.main import process_pdf
from config import DATA_DIR

def get_unique_filename(base_path):
    
    # If the file does not exist, return the base path
    if not os.path.exists(base_path):
        return base_path
    
    # Split the path into directory, filename, and extension
    directory = os.path.dirname(base_path)
    filename = os.path.splitext(os.path.basename(base_path))[0]
    extension = os.path.splitext(base_path)[1]
    
    counter = 2
    while True:
        new_filename = os.path.join(directory, f"{filename} {counter}{extension}")
        if not os.path.exists(new_filename):
            return new_filename
        counter += 1

def find_pdf_files(directory):
    """
    Find all PDF files in the specified directory.
    
    Args:
        directory: Directory to search in
        
    Returns:
        List of PDF filenames found
        
    Raises:
        OSError: If directory cannot be accessed
    """
    try:
        return [f.name for f in Path(directory).iterdir() if f.suffix.lower() == '.pdf']
    except OSError as e:
        raise OSError(f"Error accessing directory {directory}: {str(e)}")

def setup_data_directory():
    # 
    try:
        data_dir = os.path.join(os.path.dirname(__file__), DATA_DIR)
        print(f"\nFinding files located in the local data directory: {data_dir}")
        
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            print(f"Created data directory at: {data_dir}")
            print("Please place your PDF files in this directory and run the script again.")
            return None
        
        return data_dir
    except OSError as e:
        print(f"Error with data directory: {str(e)}")
        return None

def process_files(pdf_files, data_dir):
    # This is the primary function that processes the pdf files.
    successful = 0
    failed = 0
    
    # For each PDF file, create a markdown file with the same name
    for pdf_file in pdf_files:
        pdf_path = os.path.join(data_dir, pdf_file)
        markdown_filename = os.path.splitext(pdf_file)[0] + '.md'
        markdown_path = os.path.join(data_dir, markdown_filename)
        
        # Get a unique filename if the file already exists
        if os.path.exists(markdown_path):
            # This calls the get_unique_filename function to get a unique filename if the file already exists
            markdown_path = get_unique_filename(markdown_path)
        
        print(f"\nProcessing: {pdf_file}")
        try:
            process_pdf(pdf_path, markdown_path)
            print(f"Successfully created: {os.path.basename(markdown_path)}")
            successful += 1
        except Exception as e:
            print(f"Error processing {pdf_file}: {str(e)}")
            failed += 1
    
    return successful, failed

def main():
    # Main entry point for the application.
    try:
        # Set up data directory
        data_dir = setup_data_directory()
        if not data_dir:
            return
        
        # Find PDF files
        pdf_files = find_pdf_files(data_dir)
        if not pdf_files:
            print("No PDF files found in the data directory.")
            print(f"Please place your PDF files in: {data_dir}")
            return
        
        # Process files using the process_files function, with the pdf file names and data directory as arguments
        successful, failed = process_files(pdf_files, data_dir)
        print("\nProcessing complete!")
        print(f"Successfully processed: {successful} files")
        # Prints the failed files if there are any
        if failed > 0:
            print(f"Failed to process: {failed} files")
    # If there is an error, print the error and exit the program
    except Exception as e:
        print(f"Critical error: {str(e)}")
        raise SystemExit(1)

if __name__ == "__main__":
    main() 