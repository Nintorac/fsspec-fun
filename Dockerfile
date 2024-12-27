# Use Python 3.11 base image
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        make \
        docker.io \
    && rm -rf /var/lib/apt/lists/*

# # Install Python dependencies
RUN pip install --no-cache-dir \
    jupytext \
    jupyter \
    nbconvert \
    ipykernel

# Create and set working directory
WORKDIR /workspace

# Copy Makefile
COPY Makefile article.py .

# Set entrypoint to make
ENTRYPOINT ["make"]

# Default command is 'all' target
CMD ["all"]