import os
import glob
import json
import re
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from dotenv import load_dotenv

# Constants
SAMPLES_DIR = "Samples"  # Update this path to your Samples directory
REFERENCE_DIR = "reference/python"  # Update this path to your Reference directory
SDK_DIR = "SDK/python_v4"  # Directory to save the generated code samples
MAX_FILES = float('inf')  # Set to a number to limit processing

# SDK Method mappings
METHOD_MAPPINGS = {
    'delete': 'del',
    'retrieve': 'retrieve',
    'list': 'list',
    'create': 'create',
    'update': 'update'
}

# HTTP method to SDK method mapping
HTTP_TO_SDK = {
    'get': ['retrieve', 'list'],
    'post': ['create'],
    'patch': ['update'],
    'put': ['update'],
    'delete': ['del']
}

# Standard header for all files
STANDARD_HEADER = '''---
label: Python SDK
lang: Python
---
import telnyx
telnyx.api_key = "YOUR_API_KEY"
'''

def load_environment():
    """Load environment variables from .env file"""
    if os.path.exists('.env'):
        load_dotenv()

def create_reference_content():
    """Concatenate all reference files into a single string"""
    reference_content = []
    for filepath in Path(REFERENCE_DIR).rglob('*'):
        if filepath.is_file():
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    reference_content.append(f.read())
            except Exception as e:
                print(f"Error reading {filepath}: {e}")
    return '\n'.join(reference_content)

def process_file(file_path, reference_content, counter):
    """Process a single sample file and generate SDK code"""
    try:
        if counter > MAX_FILES:
            return None

        # Extract the relative path
        relative_path = os.path.relpath(file_path, SAMPLES_DIR)
        
        # Define output directory and file
        output_dir = os.path.join(SDK_DIR, os.path.dirname(relative_path))
        output_file = os.path.join(output_dir, 
                                 os.path.splitext(os.path.basename(relative_path))[0] + '.md')
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Read the sample file
        with open(file_path, 'r', encoding='utf-8') as f:
            sample_content = f.read()

        # Here you would implement the logic to generate the SDK code
        # This is where you'd use the sample_content and reference_content
        # to generate the appropriate SDK code
        # For now, we'll just create a placeholder
        sdk_code = generate_sdk_code(sample_content, reference_content)
        
        # Write the output file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"{STANDARD_HEADER}\n\n{sdk_code}")

        print(f"Processed {counter} examples so far...")
        return output_file

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None

def generate_sdk_code(sample_content, reference_content):
    """
    Generate SDK code based on sample content and reference content.
    This is where you would implement the actual code generation logic.
    """
    # This is a placeholder - you would need to implement the actual
    # code generation logic here based on your requirements
    return "# TODO: Implement actual SDK code generation\n"

def main():
    # Load environment variables
    load_environment()
    
    # Create concatenated reference content
    reference_content = create_reference_content()
    
    # Get all JSON files in the Samples directory
    sample_files = glob.glob(os.path.join(SAMPLES_DIR, "**/*.json"), recursive=True)
    
    # Process files in parallel
    counter = 0
    with ProcessPoolExecutor() as executor:
        futures = []
        for file_path in sample_files:
            counter += 1
            futures.append(
                executor.submit(process_file, file_path, reference_content, counter)
            )
        
        # Wait for all tasks to complete
        for future in futures:
            result = future.result()
            if result:
                print(f"Generated: {result}")

if __name__ == "__main__":
    main()
