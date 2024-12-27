.PHONY: all clean docker-build docker-run

# Create build directory if it doesn't exist
build:
	mkdir -p build
# Original targets 
all: build/article.md

build/article.ipynb: article.py build
	jupytext $< --to ipynb --output build/article.ipynb
build/article.md: build/article.ipynb
	jupyter nbconvert $< --to markdown --execute --allow-errors --output-dir build

clean:
	rm -rf build
	rm -f example_file
# Docker targets
# wow claude is good
docker-build: Dockerfile
	docker build -t markdown-render .

docker-run: docker-build
	docker run --network host \
		-v ./:/workspace \
		-v /var/run/docker.sock:/var/run/docker.sock \
		--rm \
		markdown-render

# Run with specific target
docker-run-%: docker-build
	docker run --network host \
		-v ./:/workspace \
		-v /var/run/docker.sock:/var/run/docker.sock \
		--rm \
		markdown-render $*
