from innovation.speech.modules import collect_data_module, transcribe_audios_module, transcripts_module
from innovation.speech.utils import io_utils
import argparse

def main(yaml_config: str = None):
    """
    Main function to run the transcription workflow.
    
    Args:
        yaml_config (str): Path to the YAML configuration file.
    """
    # Load and show the configuration
    config = io_utils.load_yaml_config(yaml_config)
    io_utils.show_config(config)

    # List files to process
    data = collect_data_module.collect_data(config = config["modules"]["collect_data"])
    data()

    # Apply ASR to the listed files
    asr = transcribe_audios_module.asr_factory(config = config["modules"]["transcribe_audios"])
    asr(wav_files = data.files)

    # Evaluate the transcripts
    evaluate = transcripts_module.evaluate_transcriptions(config = config["modules"]["evaluate_transcriptions"])
    evaluate(transcription_files = asr.all_output_files,
             reference_folder = config["modules"]["evaluate_transcriptions"]["params"]["reference_folder"])
    # evaluate(transcription_files = ["data/speech/renfe380/transcriptions/199a60e8-159b-44ca-95a4-36f2825a1de6.json",
    #                                 "data/speech/renfe380/transcriptions/d629e7cc-1a18-4f51-971a-4d5b1bbf38c9.json"],
    #         reference_folder = config["modules"]["evaluate_transcriptions"]["params"]["reference_folder"])

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Transcribe folder script")
    parser.add_argument('--yaml_config', type=str, required=True, help="Path to the YAML configuration file")
    args = parser.parse_args()

    main(args.yaml_config)