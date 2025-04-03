#!/bin/bash

# This scripts generates the requirements.txt file from the poetry environment
# Might be useful for deployment or for other environments that do not support poetry

cmd="poetry export --without-hashes --format=requirements.txt > requirements.txt"
echo $cmd && eval $cmd