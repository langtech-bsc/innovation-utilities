import json
import os
import yaml

def load_json(input_data):
    if os.path.isfile(input_data):  # Check if it's a file path
        with open(input_data, "r", encoding="utf-8") as f:
            return json.load(f)
    else:  # Assume it's a JSON string
        return json.loads(input_data)
    

def read_yaml(file_path):
    """Reads a YAML file and returns a JSON object (Python dictionary)."""
    with open(file_path, 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)
    return data

def copy_yaml(input_path, output_path):
    # Open the input YAML file and read the content as plain text
    with open(input_path, 'r', encoding='utf-8') as input_file:
        content = input_file.read()

    # Open the output file and write the content to it
    with open(output_path, 'w', encoding='utf-8') as output_file:
        output_file.write(content)

def generate_tmp_paths(path, number):
    directory, filename = os.path.split(path)  # Separate path and filename
    name, _ = os.path.splitext(filename)  # Split filename and extension
    new_filename = f"._{name}_{number}.jsonl"  # Insert number before extension
    pattern = f"._{name}_*.jsonl"  # Insert number before extension
    return os.path.join(directory, pattern), os.path.join(directory, new_filename)  # Reconstruct full path