from innovation_utilities.modules import collect_data_module, transcribe_audios_module
from innovation_utilities.utils import io_utils
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

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Transcribe folder script")
    parser.add_argument('--yaml_config', type=str, required=True, help="Path to the YAML configuration file")
    args = parser.parse_args()

    main(args.yaml_config)