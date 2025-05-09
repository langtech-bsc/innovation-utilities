from innovation.speech.utils import io_utils
import logging
from pathlib import Path
import os
from tqdm import tqdm
from jiwer import wer, cer
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

class evaluate_transcriptions():

    def __init__(self, config: dict = None):

        self.config = config
        self.valid_metrics = ["wer", "cer"]
        self.validate_config()

    def __call__(self, transcription_files: list = [], transcription_folder: str = None, transcription_extension: str = None, reference_folder : str = None):

        self.validate_call(transcription_files = transcription_files,
                           transcription_folder = transcription_folder,
                           transcription_extension = transcription_extension,
                           reference_folder = reference_folder)
        
        if transcription_folder:
            transcription_files = io_utils.get_files_by_extension(transcription_folder, extensions = transcription_extension)
            assert len(transcription_files) > 0, f"No transcription files found in {transcription_folder} with extensions {self.config['params']['transcription_extensions']}"

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
                df.drop(columns = ["transcription_file", "reference_file"], inplace = True)
                df.sort_values(by = "wer", ascending = False, inplace = True)
                logging.info(f"Saving evaluation data to {extension} file: {output_csv_file}")
                cols_in_df = ["id", "duration", "language", "words_transcription", "words_reference", "words_ratio", "n_labels", "wer", "cer"]
                df.round(4).to_csv(output_csv_file, columns = cols_in_df, index = False)
                self.make_plots(df)

                # filter data
                threshold = 0.2
                filtered = df[(df['wer'] < threshold) & (df['words_ratio_deviation'] < threshold)].shape[0]
                logging.info(f"Number of transcripts with WER < {threshold} and words_ratio_deviation < {threshold}: {filtered}/{df.shape[0]} = {filtered/df.shape[0]*100:.2f}%")
                threshold = 0.5
                filtered = df[(df['wer'] < threshold) & (df['words_ratio_deviation'] < threshold)].shape[0]
                logging.info(f"Number of transcripts with WER < {threshold} and words_ratio_deviation < {threshold}: {filtered}/{df.shape[0]} = {filtered/df.shape[0]*100:.2f}%")

    def make_plots(self, df: pd.DataFrame):
        """
        Make plots from the evaluation data.
        """

        self.make_column_histogram(df, 
                                   column_name = "wer", 
                                   max_value = None,
                                   xlabel = "Word Error Rate", 
                                   ylabel = "Frequency", 
                                   title = "Word Error Rate Histogram", 
                                   output_fig_basename = "wer_histogram.png")

        self.make_column_histogram(df, 
                                   column_name = "wer", 
                                   max_value = 1,
                                   xlabel = "Word Error Rate", 
                                   ylabel = "Frequency", 
                                   title = "Word Error Rate Histogram (max WER < 1)", 
                                   output_fig_basename = "wer_histogram_max_wer_1.png")

        self.make_column_histogram(df, 
                                   column_name = "words_ratio_deviation", 
                                   max_value = 1,
                                   xlabel = "Word Ratio Deviation", 
                                   ylabel = "Frequency", 
                                   title = "Word ratio deviation Histogram (max WER < 1)", 
                                   output_fig_basename = "word_ratio_deviation_histogram_max_wer_1.png")

        self.make_scatter_plot(df,
                               max_wer = None,
                               x_column = "words_ratio", 
                               y_column = "wer", 
                               xlabel = "Words Ratio", 
                               ylabel = "Word Error Rate", 
                               title = "Word Error Rate vs Words Ratio", 
                               output_fig_basename = "wer_vs_words_ratio.png")

        self.make_scatter_plot(df,
                               max_wer = 1,
                               x_column = "words_ratio", 
                               y_column = "wer", 
                               xlabel = "Words Ratio", 
                               ylabel = "Word Error Rate", 
                               title = "Word Error Rate vs Words Ratio (max WER < 1)", 
                               output_fig_basename = "wer_vs_words_ratio_max_wer_1.png")
        

    def make_scatter_plot(self, df: pd.DataFrame, max_wer: float,
                          x_column: str, y_column: str,
                          xlabel: str, ylabel: str, 
                          title: str, output_fig_basename: str):
        """
        Make a scatter plot of two columns in the dataframe.
        """

        if max_wer:
            df = df[df["wer"] < max_wer]

        fig = plt.figure(figsize=(10, 4))
        ax = fig.add_subplot(1, 1, 1)
        sns.scatterplot(data=df, x=x_column, y=y_column, ax=ax)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(title)

        scatter_filename = os.path.join(self.config["data"]["output_folder"], output_fig_basename)
        logging.info(f"Saving scatter plot to {scatter_filename}")
        plt.savefig(scatter_filename)

    def make_column_histogram(self, df: pd.DataFrame, column_name: str, 
                              max_value: float,
                              xlabel: str, ylabel: str, 
                              title: str, output_fig_basename: str):
        """
        Make a histogram of a column in the dataframe.
        """

        if max_value:
            df = df[df[column_name] < max_value]
        # ax = df.hist(column=[column_name], bins=100, figsize=(10, 5), grid=False)
        # ax[0][0].set_xlabel(xlabel)
        # ax[0][0].set_ylabel(ylabel)
        # ax[0][0].set_title(title)
        # histogram_filename = os.path.join(self.config["data"]["output_folder"], output_fig_basename)
        # logging.info(f"Saving histogram to {histogram_filename}")
        # ax[0][0].figure.savefig(histogram_filename)

        samples = df[column_name].values

        # specifying figure size
        fig = plt.figure(figsize=(10, 4))
        
        # adding sub plots
        ax1 = fig.add_subplot(1, 2, 1)
        
        # adding sub plots
        ax2 = fig.add_subplot(1, 2, 2)
        
        # getting histogram using hist function
        ax1.hist(samples, bins=25,
                color="green")
        
        # setting up the labels and title
        ax1.set_xlabel(xlabel)
        ax1.set_ylabel(ylabel)
        ax1.set_title(title)
        
        # cumulative graph
        # ax2.bar(x, res.cumcount, width=4, color="blue")
        ax2.hist(samples, 100, density=True, histtype='step',
                                cumulative=True, label='Empirical')
        
        # setting up the title
        ax2.set_title('Cumulative histogram')
        
        ax2.set_xlim([samples.min(), samples.max()])

        histogram_filename = os.path.join(self.config["data"]["output_folder"], output_fig_basename)
        logging.info(f"Saving histogram to {histogram_filename}")
        plt.savefig(histogram_filename)


    def validate_call(self, transcription_files: list = [], transcription_folder: str = None, transcription_extension: str = None, reference_folder : str = None):
        """
        Validate the call to the evaluate_transcriptions module.
        """

        assert transcription_files or transcription_folder, "[evaluate_transcriptions] Either transcription_files or transcription_folder must be provided"
        assert not (transcription_files and transcription_folder), "[evaluate_transcriptions] Either transcription_files or transcription_folder must be provided, not both"
        if transcription_folder:
            assert transcription_extension, "[evaluate_transcriptions] transcription_extension must be provided if transcription_folder is provided"
        assert transcription_extension, "[evaluate_transcriptions] transcription_extension must be provided"
        assert reference_folder, "[evaluate_transcriptions] reference_folder must be provided"

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
        n_labels = reference_transcription.count("[")
        transcription_clean = io_utils.clean_text(transcription)
        reference_transcription_clean = io_utils.clean_text(reference_transcription)
        words_transcription = len(transcription_clean.split(" "))
        words_reference = len(reference_transcription_clean.split(" "))
        words_ratio = words_transcription / words_reference if words_reference > 0 else 0
        eval_data = {"transcription_file": transcript_file,
                     "reference_file": reference_file,
                     "duration": data["duration"],
                     "language": data["language"],
                     "words_transcription": words_transcription,
                     "words_reference": words_reference,
                     "words_ratio": words_ratio,
                     "words_ratio_deviation": abs(1 - words_ratio),
                     "n_labels": n_labels}
        for metric in self.config["params"]["metrics"]:
            if metric == "wer":
                eval_data[metric] = wer(reference_transcription_clean, transcription_clean)
            if metric == "cer":
                eval_data[metric] = cer(reference_transcription_clean, transcription_clean)
        
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
        current_group["start"] = transcription["segments"][0]["start"]
        current_group["end"] = transcription["segments"][0]["end"]
        current_group["text"] = [transcription["segments"][0]["text"]]

        for segment in transcription["segments"][1:]:

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

