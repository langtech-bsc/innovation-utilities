#!/bin/bash

# DEFAULT PARAMETERS
SCRIPT_DIR=$(dirname "$0")
DEFAULT_PYTHON_SCRIPT="$SCRIPT_DIR/../../examples/speech/transcribe_folder_example.py"
DEFAULT_YAML_CONFIG="$SCRIPT_DIR/../../config/speech/transcribe_folder.yaml"

# PARAMETERS
PYTHON_SCRIPT=$(realpath ${1:-$DEFAULT_PYTHON_SCRIPT})
YAML_CONFIG=$(realpath ${2:-$DEFAULT_YAML_CONFIG})

# VALIDATE INPUTS
[ ! -f "$PYTHON_SCRIPT" ] && { echo "Python script not found: $PYTHON_SCRIPT"; exit 1; }
[ ! -f "$YAML_CONFIG" ] && { echo "Python YAML file not found: $YAML_CONFIG"; exit 1; }

cmd="time poetry run python $PYTHON_SCRIPT --yaml_config $YAML_CONFIG"
echo $cmd && eval $cmd