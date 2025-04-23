 #!/bin/bash

IMAGE_NAME="innovation-utilities"

# ensure poetry.lock is up to date
cmd="poetry lock"
echo $cmd && eval $cmd

# build the docker image
cmd="docker build -t $IMAGE_NAME ."
echo $cmd && eval $cmd
