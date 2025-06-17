# Use an official Python image as the base image
FROM python:3.12-slim AS base

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    gfortran \
    build-essential \
    libopenblas-dev \
    liblapack-dev \
    wget \
    && rm -rf /var/lib/apt/lists/*

FROM base AS sfdmap

ENV GALSYNTHSPEC_DATA_DIR=/mydata
ENV SFDMAP_DATA_DIR=/sfddata

# Create directories for data
RUN mkdir -p $GALSYNTHSPEC_DATA_DIR \
    && mkdir -p $SFDMAP_DATA_DIR

RUN wget https://github.com/kbarbary/sfddata/archive/master.tar.gz
RUN tar -xzf master.tar.gz -C $SFDMAP_DATA_DIR --strip-components=1 \
    && rm master.tar.gz

FROM sfdmap AS fsps

ENV SPS_HOME=/fsps

RUN git clone --depth=1 https://github.com/cconroy20/fsps $SPS_HOME
RUN make --directory=$SPS_HOME/src

FROM fsps AS final

# Copy the project files into the container
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -e ".[dev]"

# Install pre-commit hooks
RUN pre-commit install

# Set the default command to run the CLI
ENTRYPOINT ["galsynthspec"]
