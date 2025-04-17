# Speech module documentation

**Table of contents**

- [Speech module documentation](#speech-module-documentation)
  - [1.  Description](#1--description)
  - [2.  Installation](#2--installation)
  - [3.  Docker](#3--docker)
  - [4.  Running examples](#4--running-examples)
    - [Configuration file](#configuration-file)
    - [Examples](#examples)

##  1. <a name='1.Description'></a> Description

This module performs speech related tasks. So far we have implemented wrappers to do:
- ASR
- MT (tbd)
- TTS (tbd)

##  2. <a name='2.Installation'></a> Installation

To install the speech extra dependencies in poetry you can execute:

```bash
poetry install --extras speech
```

##  3. <a name='3.Installation'></a> Docker

To enter the docker image interactively while mounting external folders run, for example:

```bash
IMAGE_NAME="innovation-utilities"
INPUT_FOLDER="data/speech/input"
OUTPUT_FOLDER="data/speech/output"
docker run -it -v $(realpath $INPUT_FOLDER):/$INPUT_FOLDER -v $(realpath $OUTPUT_FOLDER):/$OUTPUT_FOLDER --rm $IMAGE_NAME bash
```

##  4. <a name='4.Runningexamples'></a> Running examples

Running the examples should be as easy as using the scripts in the environment or in the docker image.

### Configuration file

Check the configuration files used by the examples in order to know how to edit them.

Example in [config/speech/transcribe_folder.yaml](config/speech/transcribe_folder.yaml)

```yaml
---
modules:
  collect_data:
    log_level: DEBUG
    data:
      input_folder: data/speech/input     # change this path to your convenience
      input_extensions:
        - .mp3                     # it works with wav files as well
  transcribe_audios:
    log_level: DEBUG
    params:
      model: faster-whisper
      model_size: large-v2        # the first execution in a container the model will be downloaded
      device: null                # null, cpu or cuda. if null it will check if cuda is available first, cpu otherwise
      compute_type: null          # can be left like this
      beam_size: 5
      language: es                # es for Spanish
    data:
      output_folder: data/speech/output  # change this path to your convenience
      output_extensions:
        - .json
```

### Examples

Here we'll list the examples we include in the utilities repo:
- [examples/speech/transcribe_folder_example.py](examples/speech/transcribe_folder_example.py): 
  - it transcribes the wav files in a folder into txt files within the output folder. 
  - Parameters are specified in the configration file config/speech/transcribe_folder.yaml. 
  - The current example should work as is with a folder containing wav files in Spanish. 
  - It can be run with script: bash [scripts/speech/run_transcribe_folder_example.sh](scripts/speech/run_transcribe_folder_example.sh). The first time you run it will download the model files.