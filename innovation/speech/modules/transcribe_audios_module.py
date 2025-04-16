from faster_whisper import WhisperModel
from innovation.speech.utils import io_utils
import logging
from tqdm import tqdm
import torch
import os
from pathlib import Path

VALID_ASR_CONFIGS = {
    "faster_whisper": {
        "model_size": ["small-v2", "medium-v2", "large-v2"],
        "device": ["cpu", "cuda", None],
        "compute_type": ["int8", "float16", "int8_float16", None]
    }
}

# function that loads the model in the configuration file
def asr_factory(config):
    """
    Creates and configures an ASR and ASR Online instance based on the specified backend and arguments.
    """

    if "faster-whisper" in config["params"]["model"]:
        asr_cls = FasterWhisperASR
    else:
        raise Exception (f"Unknown ASR model: {config['params']['model']}")

    asr = asr_cls(model_size = config["params"]["model_size"],
                  device = config["params"]["device"],
                  compute_type = config["params"]["compute_type"],
                  beam_size = config["params"]["beam_size"],
                  language = config["params"]["language"],
                  output_folder = config["data"]["output_folder"],
                  output_extensions = config["data"]["output_extensions"])
    
    return asr

class ASRBase:

    def __init__(self, model_size: str = "large-v2", 
                       device: str = "cpu", 
                       compute_type: str = "int8",
                       beam_size: int = 5, 
                       language: str = None, 
                       output_folder: str = None,
                       output_extensions: list = [".txt"]):
        raise NotImplemented("must be implemented in the child class")
    
    def __call__(self, wav_files: list):
        raise NotImplemented("must be implemented in the child class")

    def transcribe(self, wav_list: list, beam_size: int = 5, language: str = None):
        raise NotImplemented("must be implemented in the child class")

class FasterWhisperASR(ASRBase):
    def __init__(self, 
                 model_size: str = "large-v2", 
                 device: str = "cpu", 
                 compute_type: str = "int8",
                 beam_size: int = 5, 
                 language: str = None, 
                 output_folder: str = None,
                 output_extensions: list = [".txt"]):
        
        self._validate(VALID_ASR_CONFIGS["faster_whisper"], model_size, device, compute_type)

        if device in [None, "None"]:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            compute_type = "int8_float16" if torch.cuda.is_available() else "int8"

        logging.info(f"Loading Whisper {model_size} model for {device}...")
        self.model = WhisperModel(model_size, 
                                  device = device, 
                                  compute_type = compute_type)
        self.beam_size = beam_size
        self.device = device
        self.compute_type = compute_type
        self.language = language
        self.output_folder = output_folder
        self.output_extensions = output_extensions

        os.makedirs(self.output_folder, exist_ok = True)

    def __call__(self, wav_files: list):
        self.all_transcriptions, self.all_infos, self.all_output_files = self.transcribe_list(wav_files = wav_files)

    def transcribe_list(self, wav_files: list):

        all_transcriptions = []
        all_infos = []
        all_output_files = []

        for wav_file in tqdm(wav_files):
            logging.debug("Transcribing %s" % wav_file)
            if self.language:
                segments, info = self.model.transcribe(wav_file, beam_size = self.beam_size, language = self.language)
            else:
                segments, info = self.model.transcribe(wav_file, beam_size = self.beam_size)
                logging.debug("Detected language '%s' with probability %f" % (info.language, info.language_probability))

            total_duration = round(info.duration, 2)
            transcription = []
            with tqdm(total=total_duration, unit=" seconds") as pbar:
                for segment in tqdm(segments):
                    seg = {"start": segment.start, "end": segment.end, "text": segment.text.strip()}
                    transcription.append(seg)
                    logging.debug(seg)
                    segment_duration = segment.end - segment.start
                    pbar.update(segment_duration)

            all_transcriptions.append(transcription)
            all_infos.append(info)

            for extension in self.output_extensions:
                if extension == ".json":
                    json_file = os.path.join(self.output_folder, Path(wav_file).stem + extension) 
                    io_utils.save_json(transcription, json_file)
            all_output_files.append(json_file)

        return all_transcriptions, all_infos, all_output_files

    def _validate(self, valid_asr_configs, model_size, device, compute_type):

        if device not in valid_asr_configs['device']:
            raise ValueError(f"device {device} must be one of: {valid_asr_configs['device']}")
        if compute_type not in valid_asr_configs['compute_type']:
            raise ValueError(f"compute_type must be: {valid_asr_configs['compute_type']}")        
