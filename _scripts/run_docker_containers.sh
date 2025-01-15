#!/bin/bash

BASE_DIR=$(pwd)

echo "Create Volume..."
docker volume create shared-volume

for dir in "$BASE_DIR"/*/; do


    DIR_NAME=$(basename "$dir")

    if [[ "$DIR_NAME" == _* ]]; then
        echo "Skipping directory beginning with '_': $dir"
        continue
    fi

    if [[ -f "$dir/Dockerfile" ]]; then
        echo "Dockerfile found in: $dir"
        
        CONTAINER_NAME="kg-tool_${DIR_NAME,,}"
        IMAGE_NAME="${CONTAINER_NAME}_image"
        echo "Create Image: $IMAGE_NAME"
        docker build -t "$IMAGE_NAME" -f "$dir/Dockerfile" "$BASE_DIR"
        
        echo "Run Container: $CONTAINER_NAME"
        docker run --name "$CONTAINER_NAME" --mount type=volume,src=shared-volume,target=/app/shared -d -p 0.0.0.0::5000 "$IMAGE_NAME"
        HOST_PORT=$(docker inspect --format='{{(index (index .NetworkSettings.Ports "5000/tcp") 0).HostPort}}' "$CONTAINER_NAME")
        echo "Container running on Host-Port: $HOST_PORT"
    else
        echo "No Dockerfile found in: $dir, skip..."
    fi
done
