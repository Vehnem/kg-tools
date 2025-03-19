#!/bin/bash

BASE_DIR=$(pwd)

for dir in "$BASE_DIR"/*/; do

    DIR_NAME=$(basename "$dir")

    if [[ "$DIR_NAME" == _* ]]; then
        echo "Skipping directory beginning with '_': $dir"
        continue
    fi

    if [[ -f "$dir/DockerfileAirflow" ]]; then
        echo "Dockerfile found in: $dir"

        IMAGE_NAME="kg-tools/${DIR_NAME}_image"
        echo "Create Image: $IMAGE_NAME"
        docker build -t "$IMAGE_NAME" -f "$dir/DockerfileAirflow" "$BASE_DIR"

    else
        echo "No Dockerfile found in: $dir, skip..."
    fi
done
