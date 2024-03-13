# Use Ubuntu as the base image
FROM ubuntu:latest

# Set environment variables (example)
ENV DEBIAN_FRONTEND=noninteractive

# Run any necessary commands
RUN apt-get update && apt-get install -y \
    git \
    sudo \
    curl \
    gpg \
    curl \
    vim \
    wget \
    bash \
    && rm -rf /var/lib/apt/lists/*

# Set the Miniconda version to install
ENV MINICONDA_VERSION=latest
ENV CONDA_DIR=/opt/conda

# Determine the architecture and install Miniconda

RUN ARCH=$(uname -m) && \
    if [ "$ARCH" = "x86_64" ]; then \
        MINICONDA_ARCH="Linux-x86_64"; \
    elif [ "$ARCH" = "aarch64" ]; then \
        MINICONDA_ARCH="Linux-aarch64"; \
    else \
        echo "Unsupported architecture: $ARCH"; \
        exit 1; \
    fi && \
    wget https://repo.anaconda.com/miniconda/Miniconda3-${MINICONDA_VERSION}-${MINICONDA_ARCH}.sh -O /miniconda.sh && \
    /bin/bash /miniconda.sh -b -p $CONDA_DIR && \
    rm /miniconda.sh

# Add conda to the PATH
ENV PATH=$CONDA_DIR/bin:$PATH

# Initialize Miniconda in bash, make conda command available in shell scripts
RUN echo ". $CONDA_DIR/etc/profile.d/conda.sh" >> ~/.bashrc && \
    echo "conda activate base" >> ~/.bashrc

# Set the Python version to install
ENV PYTHON_VERSION=3.12

# Install Python ${PYTHON_VERSION} and pip in the base environment
RUN conda install -y python=${PYTHON_VERSION} pip

# Cleanup
RUN conda clean --all --yes
