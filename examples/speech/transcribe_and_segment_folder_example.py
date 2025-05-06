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
    # asr = transcribe_audios_module.asr_factory(config = config["modules"]["transcribe_audios"])
    # asr(wav_files = data.files)

    # Segment the transcribed files
    segmenter = transcripts_module.group_transcript_segments(config = config["modules"]["segmenter"])
    # segmenter(transcript_files = asr.all_output_files)
    transcript_files = ["data/speech/renfe/output/asr/1cd8983e-f38b-4df6-9510-7b973e006a17_nointro.json",
                        "data/speech/renfe/output/asr/0ec9288e-028a-463c-bc2d-d1c267249fac_nointro.json",
                        "data/speech/renfe/output/asr/1aec7b96-965f-422f-aee7-754e5e1f57ef_nointro.json",
                        "data/speech/renfe/output/asr/1a74859d-9185-4c33-8792-e33e5e67d3f7_nointro.json"]
    segmenter(transcript_files = transcript_files)



if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Transcribe folder script")
    parser.add_argument('--yaml_config', type=str, required=True, help="Path to the YAML configuration file")
    args = parser.parse_args()

    main(args.yaml_config)