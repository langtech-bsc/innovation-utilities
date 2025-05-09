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
    if config["modules"]["collect_data"]["do_step"]:
        data = collect_data_module.collect_data(config = config["modules"]["collect_data"])
        data()
    else:
        print("Skipping data collection step.")

    # Apply ASR to the listed files
    if config["modules"]["transcribe_audios"]["do_step"]:
        asr = transcribe_audios_module.asr_factory(config = config["modules"]["transcribe_audios"])
        asr(wav_files = data.files)
    else:
        print("Skipping audio transcription step.")

    # Evaluate the transcripts
    evaluate = transcripts_module.evaluate_transcriptions(config = config["modules"]["evaluate_transcriptions"])
    if config["modules"]["evaluate_transcriptions"]["do_step"]:
        if config["modules"]["transcribe_audios"]["do_step"]:
            evaluate(transcription_files = asr.all_output_files,
                     reference_folder = config["modules"]["evaluate_transcriptions"]["params"]["reference_folder"])
        else:
            evaluate(transcription_folder = config["modules"]["transcribe_audios"]["data"]["output_folder"],
                     transcription_extension = config["modules"]["transcribe_audios"]["data"]["output_extensions"][0],
                     reference_folder = config["modules"]["evaluate_transcriptions"]["params"]["reference_folder"])
    else:
        print("Skipping evaluation step.")

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Transcribe folder script")
    parser.add_argument('--yaml_config', type=str, required=True, help="Path to the YAML configuration file")
    args = parser.parse_args()

    main(args.yaml_config)