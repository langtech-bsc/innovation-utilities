# Innovation utilities

**Table of contents**

- [Innovation utilities](#innovation-utilities)
  - [1. Description](#1-description)
  - [2. Installation](#2-installation)
    - [Poetry](#poetry)
    - [Other environments](#other-environments)
    - [Docker](#docker)
  - [3. Usage](#3-usage)
    - [Configuration file](#configuration-file)
    - [Script](#script)
  - [4. Examples](#4-examples)
  - [5. Folder structure](#5-folder-structure)


##  1. Description

This project aims to gather basic python classes to quickly run some basic tasks. We'll start with ASR and some examples.

Some recommendations:
- We recommend using the code by building the docker image.
- We've tested the configuration with device set to cpu, but the gpu device should be working as well.

##  2. Installation

### Poetry

To setup this project you can use poetry.

1. install poetry: https://python-poetry.org/docs/
2. should be as easy as running
```bash
git clone git@github.com:langtech-bsc/innovation-utilities.git
cd innovation-utilities
poetry install
```

### Other environments

The requirements.txt file has been exported from the poetry environment in case the user needs to work with other environments.

### Docker

A working dockerfile is already provided. To build the image run:

```bash
IMAGE_NAME="innovation-utilities"
docker build -t $IMAGE_NAME .
```

To enter the docker image interactively while mounting external folders run, for example:

```bash
IMAGE_NAME="innovation-utilities"
INPUT_FOLDER="data/input"
OUTPUT_FOLDER="data/output"
docker run -it -v $(realpath $INPUT_FOLDER):/$INPUT_FOLDER -v $(realpath $OUTPUT_FOLDER):/$OUTPUT_FOLDER --rm $IMAGE_NAME bash
```

##  3. Usage

Running the examples should be as easy as using the scripts in the environment or in the docker image.

### Configuration file

Check the configuration files used by the examples in order to know how to edit them.

Example in [config/transcribe_folder.yaml](config/transcribe_folder.yaml)

```yaml
---
modules:
  collect_data:
    log_level: DEBUG
    data:
      input_folder: data/input     # change this path to your convenience
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
      output_folder: data/output  # change this path to your convenience
      output_extensions:
        - .json
```

### Script

Either from within the Docker container or you local environment run:

```bash
bash scripts/run_transcribe_folder_example.sh
```


## 4. Examples

Here we'll list the examples we include in the utilities repo:
- [examples/transcribe_folder_example.py](examples/transcribe_folder_example.py): 
  - it transcribes the wav files in a folder into txt files within the output folder. 
  - Parameters are specified in the configration file config/transcribe_folder.yaml. 
  - The current example should work as is with a folder containing wav files in Spanish. 
  - It can be run with script: bash [scripts/run_transcribe_folder_example.sh](scripts/run_transcribe_folder_example.sh). The first time you run it will download the model files.

## 5. Folder structure

This is the current folder structure:

```bash
$ tree innovation-utilities/
innovation-utilities/
├── config                                      # config files
│   └── transcribe_folder.yaml                  #   - config file for the corresponding example
├── data
│   ├── input                                   # example of input data
│   │   ├── common_voice_es_41913638.mp3
│   │   ├── common_voice_es_41913640.mp3
│   │   └── common_voice_es_42044997.mp3
│   └── output                                  # example of output data
│       ├── common_voice_es_41913638.json
│       ├── common_voice_es_41913640.json
│       └── common_voice_es_42044997.json
├── Dockerfile
├── examples                                    # examples showing how the classes can be used
│   └── transcribe_folder_example.py            #   - ASR applied to a folder
├── poetry.lock                                 # poetry env related file
├── pyproject.toml                              # poetry env related file
├── README.md                                   # this readme file
├── requirements.txt                            # do not edit this file, generaed using scripts/poetry2requirements.sh
├── scripts                                     # bash scripts
│   ├── activate_poetry_env.sh                  #   - used to activate poetry env
│   ├── poetry2requirements.sh                  #   - used to generate requirements.txt
│   └── run_example.sh                          #   - used to run the transcribe_folder.py
└── src                                         # package src folder
    └── innovation_utilities                    # package main folder
        ├── __init__.py
        ├── modules                             # modules classes
        │   ├── transcribe_audios_module.py     #   - for asr
        │   ├── collect_data_module.py          #   - for data collection
        │   └── __init__.py
        └── utils                               # utils functions
            ├── __init__.py
            └── io_utils.py
```