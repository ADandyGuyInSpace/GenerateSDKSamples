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

def clean_filename(filename):
    """Clean the filename to handle special cases"""
    # Handle 'actions' in the path
    if 'actions' in filename:
        parts = filename.split('actions')
        filename = parts[0] + parts[1].split('_')[0]
    
    # Handle cases with words after brackets
    pattern = r'{[^}]+}(.*)'
    match = re.search(pattern, filename)
    if match:
        suffix = match.group(1)
        filename = filename.replace(suffix, '')
    
    return filename

def process_file(file_path, reference_content, counter):
    """Process a single sample file and generate SDK code"""
    try:
        if counter > MAX_FILES:
            return None

        # Extract the relative path
        relative_path = os.path.relpath(file_path, SAMPLES_DIR)
        
        # Clean the filename
        cleaned_filename = clean_filename(os.path.splitext(os.path.basename(relative_path))[0])
        
        # Define output directory and file
        output_dir = os.path.join(SDK_DIR, os.path.dirname(relative_path))
        output_file = os.path.join(output_dir, f"{cleaned_filename}.md")
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Read the sample file
        with open(file_path, 'r', encoding='utf-8') as f:
            sample_content = f.read()

        # Generate the SDK code
        sdk_code = generate_sdk_code(sample_content, reference_content)
        
        # Write the output file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"{STANDARD_HEADER}\n\n{sdk_code}")

        print(f"Processed {counter} examples so far... Generated: {output_file}")
        return output_file

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None

def parse_endpoint_path(path):
    """Parse the endpoint path to extract resource and action information"""
    parts = path.strip('/').split('/')
    resource_parts = []
    params = {}
    
    for part in parts:
        if '{' in part and '}' in part:
            param_name = part[1:-1]  # Remove { and }
            param_var = f"{param_name}"
            params[param_name] = param_var
            resource_parts.append(param_var)
        else:
            resource_parts.append(part)
    
    return resource_parts, params

def determine_sdk_method(http_method, endpoint_path, operation_id=None):
    """Determine the appropriate SDK method based on the HTTP method and path"""
    possible_methods = HTTP_TO_SDK.get(http_method.lower(), [])
    
    # Check if it's a list operation
    if http_method.lower() == 'get' and not any('{' in part for part in endpoint_path.split('/')):
        return 'list'
    
    # For other operations, prefer the first possible method
    return possible_methods[0] if possible_methods else 'create'

def generate_sdk_code(sample_content, reference_content):
    """Generate SDK code based on sample content and reference content."""
    try:
        sample_data = json.loads(sample_content)
        
        # Extract relevant information
        http_method = sample_data.get('method', '').lower()
        endpoint_path = sample_data.get('path', '')
        request_body = sample_data.get('request', {}).get('body', {})
        
        # Parse the endpoint path
        resource_parts, params = parse_endpoint_path(endpoint_path)
        
        # Determine the SDK method to use
        sdk_method = determine_sdk_method(http_method, endpoint_path)
        
        # Generate the resource path
        resource_path = '_'.join(part for part in resource_parts if not part.startswith('{'))
        
        # Build the SDK code
        code_lines = []
        
        # Add parameter definitions
        for param_name, param_var in params.items():
            code_lines.append(f"{param_name} = 'your_{param_name}'")
        
        # Add request body if present
        if request_body:
            body_params = []
            for key, value in request_body.items():
                if isinstance(value, str):
                    body_params.append(f"    {key}='{value}'")
                else:
                    body_params.append(f"    {key}={value}")
            
            if body_params:
                code_lines.append("params = {")
                code_lines.extend(body_params)
                code_lines.append("}")
        
        # Build the SDK call
        if resource_path:
            resource_var = resource_path.replace('-', '_')
            if params:
                param_str = ', '.join(f"{k}={v}" for k, v in params.items())
                if request_body:
                    code_lines.append(f"response = telnyx.{resource_var}.{sdk_method}({param_str}, **params)")
                else:
                    code_lines.append(f"response = telnyx.{resource_var}.{sdk_method}({param_str})")
            else:
                if request_body:
                    code_lines.append(f"response = telnyx.{resource_var}.{sdk_method}(**params)")
                else:
                    code_lines.append(f"response = telnyx.{resource_var}.{sdk_method}()")
        
        # Add print statement for response
        code_lines.append("print(response)")
        
        return '\n'.join(code_lines)
        
    except Exception as e:
        print(f"Error generating SDK code: {e}")
        return f"# Error generating SDK code: {str(e)}"

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