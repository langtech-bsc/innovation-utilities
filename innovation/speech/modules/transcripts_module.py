from innovation.speech.utils import io_utils
import logging
from pathlib import Path
import os
from tqdm import tqdm
from jiwer import wer, cer
import pandas as pd

class evaluate_transcriptions():

    def __init__(self, config: dict = None):

        self.config = config
        self.valid_metrics = ["wer", "cer"]
        self.validate_config()

    def __call__(self, transcription_files: list = [], reference_folder : str = None):

        all_eval_data = []

        print(self.config['params']['reference_extensions'])
        reference_files = io_utils.get_files_by_extension(reference_folder, extensions = self.config['params']['reference_extensions'])

        for transcript_file in tqdm(transcription_files):
            reference_file = os.path.join(reference_folder, os.path.basename(transcript_file).replace(".json", "_anonymized.txt"))
            assert reference_file not in reference_files, f"Reference file {reference_file} not found in {reference_folder}"
            eval_data = self.process_transcripts_file(transcript_file, reference_file = reference_file)
            all_eval_data.append(eval_data)

        # Save output files
        for extension in self.config["data"]["output_extensions"]:
            if extension == ".json":
                output_json_file = os.path.join(self.config["data"]["output_folder"], "metrics" + extension)
                logging.info(f"Saving evaluation data to {extension} file {output_json_file}")
                io_utils.save_json(all_eval_data, output_json_file)
                self.output_json_file = output_json_file
            if extension == ".csv":
                output_csv_file = os.path.join(self.config["data"]["output_folder"], "metrics" + extension)
                for eval_data in all_eval_data:
                    eval_data["id"] = os.path.basename(eval_data["transcription_file"])
                df = pd.DataFrame.from_records(all_eval_data) 
                df.sort_values(by = "id", inplace = True)
                logging.info(f"Saving evaluation data to {extension} file: {output_csv_file}")
                df.round(4).to_csv(output_csv_file, columns=["id", "wer", "cer"], index = False)
        
    def validate_config(self):

        os.makedirs(self.config["data"]["output_folder"], exist_ok = True)
        if not set(self.config["params"]["metrics"]) <= set(self.valid_metrics):
            raise ValueError(f"Invalid metrics: {self.config['params']['metrics']}. Valid metrics are: {self.valid_metrics}")
        

    def process_transcripts_file(self, transcript_file: str, reference_file: str = "test.txt"):
        """
        Evaluate a single transcript file.
        """
        logging.debug(f"Evaluating transcript file: {transcript_file}")

        # Load the transcript file
        data = io_utils.load_json(transcript_file)
        transcription = " ".join([segment["text"] for segment in data["segments"]])
        reference_transcription = " ".join(io_utils.load_text(reference_file))
        eval_data = {"transcription_file": transcript_file,
                     "reference_file": reference_file}
        for metric in self.config["params"]["metrics"]:
            if metric == "wer":
                eval_data[metric] = wer(reference_transcription, transcription)
            if metric == "cer":
                eval_data[metric] = cer(reference_transcription, transcription)
        
        return eval_data

class group_transcript_segments():

    def __init__(self, config: dict = None):

        self.config = config
        self.validate_config()

    def __call__(self, transcript_files: list):

        all_output_files = []

        for transcript_file in transcript_files:
            json_file = self.process_transcripts_file(transcript_file)
            all_output_files.append(json_file)

    def validate_config(self):

        os.makedirs(self.config["data"]["output_folder"], exist_ok = True)
        try:
            self.config["params"]["min_pause_between_groups"] = int(self.config["params"]["min_pause_between_groups"])
        except:
            raise ValueError("min_pause_between_groups must be an integer")

    def process_transcripts_file(self, transcript_file: str):
        """
        Process a single transcript file.
        """
        logging.info(f"Processing transcript file: {transcript_file}")

        # Load the transcript file
        transcription = io_utils.load_json(transcript_file)

        # Perform segment grouping
        groups = self.group_segments(transcription)

        # Save output files
        for extension in self.config["data"]["output_extensions"]:
            if extension == ".json":
                json_file = os.path.join(self.config["data"]["output_folder"], Path(transcript_file).stem + extension) 
                print(json_file)
                io_utils.save_json(groups, json_file)
        
        return json_file

    def join_current_group_and_next_segment(self, segment, current_group):

        max_time_stamps_where_segment_can_start_to_join = current_group["end"] + self.config["params"]["min_pause_between_groups"]
        new_group_duration_if_segment_is_joined = segment["end"] - current_group["start"]
        last_sentence_character = current_group["text"][-1][-1]

        if segment["start"] < max_time_stamps_where_segment_can_start_to_join and \
           new_group_duration_if_segment_is_joined <= self.config["params"]["max_group_duration"]:
            return True
        elif last_sentence_character not in self.config["params"]["group_character_delimiters"]:
            return True
        else:
            return False

    def group_segments(self, transcription: dict = {}) -> list:
        """
        Group a transcript segments.
        """
        groups = []

        current_group = {}
        current_group["start"] = transcription[0]["start"]
        current_group["end"] = transcription[0]["end"]
        current_group["text"] = [transcription[0]["text"]]

        for segment in transcription[1:]:

            if self.join_current_group_and_next_segment(segment, current_group): 
                current_group["end"] = segment["end"]
                current_group["text"].append(segment["text"])
            else:
                groups.append(current_group)
                current_group = {}
                current_group["start"] = segment["start"]
                current_group["end"] = segment["end"]
                current_group["text"] = [segment["text"]]

        # Append the last group
        if current_group:
            groups.append(current_group)            

        return groups

