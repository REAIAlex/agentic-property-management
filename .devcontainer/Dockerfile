FROM mcr.microsoft.com/devcontainers/python:3.11

# Node.js is installed via devcontainer features (see devcontainer.json)
# Only install additional OS-level tools here

RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*
