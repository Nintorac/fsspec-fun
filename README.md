# fsspec-fun

> this readme is majority [slop](https://en.wikipedia.org/wiki/Slop_(artificial_intelligence)) by Claude + Continue, Dockerfile and Makefile also heavily relied on the same.

> article.py is entirely handwritten

A practical guide demonstrating the power and flexibility of fsspec for working with files across different storage systems.

This repo contains the source code for [this article on my site](https://www.nintoracaudio.dev/data-engineering/2024/12/24/fsspec-fun.html)

## Overview

This project provides example code and documentation showing how to:

- Use fsspec to create a unified interface for accessing files across different storage backends
- Register custom protocols with fsspec for simplified storage access
- Work with MinIO as an S3-compatible storage system
- Use `universal-pathlib` (UPath) for pathlib like file operations
- Perform file operations between different storage systems

The main content is in `article.py` which is a Jupyter notebook-style Python file that walks through various examples and explanations.

## Getting Started

### Prerequisites

- Docker
- Python 3.11+
- Make

### Running Locally

1. Clone the repository:
```bash
git clone https://github.com/Nintorac/fsspec-fun.git
cd fsspec-fun
```

2. Run using Docker:
```bash
make docker-run
```

This will:
- Build a Docker image with all required dependencies
- Execute the examples in `article.py`
- Generate a markdown version of the article

### Project Structure

- `article.py` - Main content and examples in Python format
- `Makefile` - Build automation for generating article formats and running Docker
- `Dockerfile` - Container definition for reproducible environment
- 

## Generated Outputs

The project can generate:
- `article.ipynb` - Jupyter notebook version
- `article.md` - Markdown version of the article with cells executed

## Build Process

The Makefile provides several targets:

- `make all` - Generate all article formats
- `make clean` - Remove generated files
- `make docker-build` - Build the Docker image
- `make docker-run` - Generate all article formats in a Docker container

## License

[Insert License Information]

## Contributing

Feel free to open issues or submit pull requests for improvements.

## Acknowledgments

Thanks to the fsspec project and its contributors for creating such a versatile file system interface.
