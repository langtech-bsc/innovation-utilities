from abc import ABC, abstractmethod
import os
from pprint import pformat
import sys
import importlib.util
import logging
from typing import Optional, Type, Union
import pandas as pd
import torch
import json
import glob
from innovation.gendata.utils import timer
from innovation.gendata.utils.logger import setup_logger
from innovation.gendata.utils.class_manager import ClassManager
from typing import List, Dict, Protocol, Union, Any
from types import SimpleNamespace
import numpy as np
import string

class MessagesType(Dict[str, str]):
    """Defines the message format with 'role' and 'content' keys."""
    role: str
    content: str


class GetLLMResponseType(Protocol):
    """A callable type for generating LLM responses.

    Args:
        messages (List[MessagesType]): A list of message dictionaries, each containing 'role' and 'content'.
        wait_for_connection (bool): Whether to wait until a connection is available.

    Returns:
        str: The generated AI response in text format.
    """
    def __call__(self, messages: List[MessagesType], wait_for_connection: bool) -> str:
        pass



logger = setup_logger(__name__)

class MethodManager(ClassManager):
    registered_classes: dict[str, Type] = {}


class BaseMethod(ABC):
    def __init__(self, input: str, output: str, global_rank:int, wait_for_model:bool, messages_list: List[MessagesType], unique_key, output_keys, output_types, random_extra_keys):
        self._default_unique_id = "_index"
        self.input = input
        self.output = output
        self.global_rank = global_rank
        self.wait_for_model = wait_for_model
        self.unique_key = unique_key if unique_key else self._default_unique_id
        self.output_keys = output_keys
        self.output_types = output_types
        self.random_extra_keys = random_extra_keys
        self.messages_list = messages_list
        self.replaceable_keys = [self._get_replaceable_keys(messages) for messages in self.messages_list]
        self._detect_file_type(self.output)
        self._data = self.load_data(self.input)
        if self._default_unique_id == self.unique_key:
            self._data[self.unique_key] = range(len(self._data))
        
        self._check_data(self._data, self.unique_key, self.output_keys, self.output_types, self.messages_list)
        self._output_path_pattern, self._output_rank_path = self._generate_temporal_path(self.output, self.global_rank)
        self._already_done = self.extract_unique_key_values(self._output_path_pattern, self.unique_key, self.global_rank)
    
    @staticmethod
    def _get_replaceable_keys(messages: MessagesType):
        keys = []
        for msg in messages:
            formatter = string.Formatter()
            keys.extend([field_name for _, field_name, _, _ in formatter.parse(msg["content"]) if field_name])
        return keys

    @staticmethod
    def _check_data(df, unique_key, output_keys, output_types, messages_list):
        existing_keys = [key for key in output_keys if key in df.columns]
        if existing_keys:
            raise KeyError(f"These keys '{str(existing_keys)}' already exists in dataset.")
        
        if unique_key not in df.columns:
            raise ValueError(f"The unique key '{unique_key}' does not exist in the dataset.")
        
        if not df[unique_key].is_unique:
            raise ValueError(f"The unique key '{unique_key}' exists but its values are not unique in the dataset.")
        
        not_permitted_types = set(output_types) - set(["json", "str"])
        if not_permitted_types:
            raise TypeError(f"Output types '{str(not_permitted_types)}' are not permitted")

        #TODO: Check messages format

    def load_data(self, path):
        return self._read_file(path)
    
    def get_unique_id(self, index):
        value = self._data.at[index, self.unique_key]
        return int(value) if isinstance(value, np.integer) else value
    
    def get_extra_keys(self, index):
        new_data = {}
        for key in self.random_extra_keys:
            idx = index % len(self.random_extra_keys[key])
            new_data[key] = self.random_extra_keys[key][idx]

        return new_data
    
    def print_args(self):
        attr = {"Data method": self.__class__.__name__}
        public_attrs = {k: v for k, v in self.__dict__.items() if not k.startswith("_")}
        attr.update(public_attrs)
        logger.info("Namespace:\n%s", pformat(vars(SimpleNamespace(**attr))))
    
    def generate_messages(self, json_data: Dict[str, Any], index: int = -1) -> List[MessagesType]:
        """Substitutes placeholders in messages with values from json_data.

        Args:
            json_data (Dict[str, Any]): Dictionary containing values to replace placeholders.
            index (int, optional): If -1, all messages are processed. Otherwise, only messages[index] is processed.

        Returns:
            List[Dict[str, str]]: The modified messages with placeholders replaced.
        
        Raises:
            KeyError: If a placeholder is found but not in json_data.
            IndexError: If index is out of range.
            ValueError: If no changes were made after substitution.
        """

        is_changed = False

        def substitute_placeholders(template: str) -> str:
            """Replaces placeholders using str.format(), raising an error if a key is missing."""
            try:
                text = template.format(**json_data)
                return (text, True) if text != template else (text, False)
            
            except KeyError as e:
                raise KeyError(f"Missing key in json_data: {e}. Please ensure that your input dataset contains all the required keys for the task.")

        if 0 <= index < len(self.messages_list):
            messages = self.messages_list[index]
            new_messages = []
            for msg in messages:
                content, changed = substitute_placeholders(msg["content"])
                new_messages.append({"role": msg["role"], "content": content})
                is_changed = is_changed or changed
        else:
            raise IndexError("Invalid index: out of range.")

        if not changed:
            raise ValueError("No substitutions made: The content is the same as before.")
        
        return new_messages

    @abstractmethod
    def generate_data(self, index, get_llm_response: GetLLMResponseType):
        """Function to be implemented by subclasses"""
        pass

    def is_done(self, index):
        return self._data.at[index, self.unique_key] in self._already_done

    @staticmethod
    def _generate_temporal_path(path: str, number: int) -> str:
        directory, filename = os.path.split(path)  # Separate path and filename
        name, _ = os.path.splitext(filename)  # Split filename and extension
        new_filename = f"._{name}_{number}.jsonl"  # Insert number before extension
        pattern = f"._{name}_*.jsonl"  # Insert number before extension
        return os.path.join(directory, pattern), os.path.join(directory, new_filename)  # Reconstruct full path


    @staticmethod
    def _detect_file_type(path):
        """Detect file format based on extension."""
        _, ext = os.path.splitext(path.lower())
        if ext == ".json":
            return "json"
        elif ext in (".jsonl", ".ndjson"):
            return "jsonl"
        elif ext == ".csv":
            return "csv"
        elif ext == ".parquet":
            return "parquet"
        else:
            raise ValueError(f"Unsupported file format: {ext}")
    
    @staticmethod
    def _read_file(path, file_type=None, cache=False, rank=0):
        if not file_type:
            file_type = BaseMethod._detect_file_type(path)
        
        """Reads a file and returns a Pandas DataFrame and its type."""
        if file_type == "json":
            df = pd.read_json(path)
        elif file_type == "jsonl":
            if cache and rank == 0:
                try:
                    df = pd.read_json(path, lines=True)
                except:
                    temp_path = path + ".tmp"
                    with open(path, 'r') as infile, open(temp_path, 'w') as outfile:
                        for i, line in enumerate(infile, start=1):
                            try:
                                json.loads(line)
                                outfile.write(line)
                            except json.JSONDecodeError as e:
                                print(f"Skipping bad line {i}: {e}")
                        os.replace(temp_path, path)
            
            torch.distributed.barrier()
            df = pd.read_json(path, lines=True)
        elif file_type == "csv":
            df = pd.read_csv(path)
        elif file_type == "parquet":
            df = pd.read_parquet(path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

        return df
    
    @staticmethod
    def _get_all_records(files_pattern):
        files = sorted(glob.glob(files_pattern))  # Find all matching JSONL files
        all_data = []

        for file in files:
            with open(file, "r", encoding="utf-8") as f:
                all_data.extend(json.loads(line) for line in f)  # Load line-by-line

        return pd.DataFrame(all_data)
    
    @staticmethod
    def extract_unique_key_values(file_pattern, key, rank):
        unique_values = set()  # To store unique values of the key

        # Get all file paths matching the pattern
        file_paths = glob.glob(file_pattern)

        for file_path in file_paths:
            df = BaseMethod._read_file(file_path, cache=True, rank=rank)  # Read JSONL file into a DataFrame

            # Add unique values from the current file to the set
            if not df.empty:
                unique_values.update(df[key].dropna().unique())

        return unique_values 

    def set_record(self, record, index):
        """Append JSON line by line"""
        logger.debug(f"Setting record for field {index} in {self._output_rank_path}.")
        with open(self._output_rank_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def save_all(self):
        file_type = BaseMethod._detect_file_type(self.output)
        df = BaseMethod._get_all_records(self._output_path_pattern)
    
        if file_type == "json":
            df.to_json(self.output, orient="records", indent=4)
        elif file_type == "jsonl":
            df.to_json(self.output, orient="records", lines=True)
        elif file_type == "csv":
            df.to_csv(self.output, index=False)
        elif file_type == "parquet":
            df.to_parquet(self.output, index=False)
        
        [os.remove(file) for file in sorted(glob.glob(self._output_path_pattern))]
        logging.info(f"Saved: {self.output}")

    def __len__(self):
        return len(self._data)

    def __getitem__(self, index):
        self._data[index]


