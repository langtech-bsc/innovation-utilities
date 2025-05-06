import os
from typing import List, Set
import yaml
import logging
import json
import string

def clean_text(text: str) -> str:
    """
    Clean the input text by removing punctuation and converting to lowercase.

    Args:
        text (str): The input text to clean.

    Returns:
        str: The cleaned text.
    """
    translator = str.maketrans('', '', string.punctuation + "¿")
    text_without_punctuation = text.translate(translator)

    return text_without_punctuation.lower()

def load_text(file_path: str) -> List[str]:
    """
    Load a text file and return its lines as a list of strings.

    Args:
        file_path (str): The path to the text file.

    Returns:
        List[str]: A list of lines from the text file.
    """
    with open(file_path, 'r') as file:
        lines = [line.strip() for line in file.readlines()]
    return lines

def save_txt(lines: List[str], file_path: str) -> None:
    """
    Save a list of strings to a text file.

    Args:
        lines (List[str]): The list of strings to save.
        file_path (str): The path to the output text file.
    """
    with open(file_path, 'w') as file:
        for line in lines:
            file.write(f"{line}\n")

def save_json(lines: None, file_path: str) -> None:
    """
    Save a list of strings to a JSON file.
    Args:
        lines (List[str]): The list of strings to save.
        file_path (str): The path to the output JSON file.
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(lines, f, ensure_ascii=False, indent=4)

def load_json(file_path: str) -> dict:
    """
    Load a JSON file as a dictionary.

    Args:
        file_path (str): The path to the JSON file.

    Returns:
        dict: The loaded JSON data as a dictionary.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def show_config(config: dict) -> None:
    """
    Print the configuration dictionary in a readable format.

    Args:
        config (dict): The configuration dictionary to print.
    """
    setup_logging("INFO")
    logging.info("Configuration:")
    logging.info(yaml.dump(config, default_flow_style=False, indent=4))

def setup_logging(log_level: str) -> None:

    logging.basicConfig(
        level=log_level.upper(),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def get_files_by_extension(folder: str, extensions: Set[str]) -> List[str]:
    """
    Get absolute file paths with specific extensions from a folder and its subfolders.

    Args:
        folder (str): The input folder to search in.
        extensions (Set[str]): A set of file extensions to filter by (e.g., {'.txt', '.csv'}).

    Returns:
        List[str]: A list of absolute file paths matching the given extensions.
    """
    matching_files = []
    for root, _, files in os.walk(folder):
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                matching_files.append(os.path.abspath(os.path.join(root, file)))
    return matching_files

def load_yaml_config(file_path: str) -> dict:
    """
    Load a YAML file as a configuration dictionary.

    Args:
        file_path (str): The path to the YAML file.

    Returns:
        dict: The loaded configuration as a dictionary.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file '{file_path}' does not exist.")
        
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def check_folder_exists(folder: str) -> bool:
    """
    Check if a folder exists.

    Args:
        folder (str): The path to the folder.

    Returns:
        bool: True if the folder exists, False otherwise.
    """
    return os.path.exists(folder) and os.path.isdir(folder)

