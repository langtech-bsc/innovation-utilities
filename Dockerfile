FROM python:3.12-slim

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Set the working directory in the container
WORKDIR /code/innovation-utilities

# Install system dependencies
RUN apt-get update && \
    apt-get install curl -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - --version 2.1.2

# Add Poetry to PATH
ENV PATH="${PATH}:/root/.local/bin"

# Copy the pyproject.toml (and optionally poetry.lock) file into the container
COPY pyproject.toml poetry.lock* README.md ./

# Install Poetry dependencies
RUN poetry install --no-root && rm -rf $POETRY_CACHE_DIR

# Copy the package files into the container
COPY . .

# RUN source .venv/bin/activate && poetry install
RUN poetry install

# Start virtual env when bash starts
RUN echo 'source .venv/bin/activate' >> ~/.bashrc

#########################

# RUN apt update && \
#     apt install pipx --yes && \
#     pipx ensurepath && \
#     apt upgrade pipx --yes && \
#     pipx install poetry && \
#     pipx upgrade poetry

# RUN pip install --upgrade pip

# # /root/.local/pipx/venvs/poetry/bin/poetry install

# WORKDIR /code/innovation-utilities
# COPY . .
# ENV PATH="/root/.local/pipx/venvs/poetry:$PATH"
# # RUN poetry config virtualenvs.create false && \
# #     poetry install --no-interaction --no-ansi

# Use an official Python runtime as a base image
# FROM python:3.11-slim-buster