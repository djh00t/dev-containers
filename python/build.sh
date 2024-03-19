#!/bin/bash

# Ensure docker buildx is available and in use
docker buildx version > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "docker buildx not available. Install it before running this script."
    exit 1
fi

# Create a new builder which gives access to the new multi-architecture features
docker buildx create --name mybuilder --use

# Start up the builder
docker buildx inspect --bootstrap

# Build and push the image for both amd64 and arm64 architectures
VERSION=$(cat ./VERSION)
echo "Building version $VERSION"
docker buildx build --platform linux/amd64,linux/arm64 --tag myimage:$VERSION --push .
if [ $? -ne 0 ]; then
    echo "Build failed, version number will not be incremented."
    exit 1
fi

# Increment version number
NEW_VERSION=$(echo $VERSION | awk -F. '{ printf("%d.%d.%d", $1, $2, $3+1) }')
echo $NEW_VERSION > ./VERSION
echo "Build succeeded, version number incremented to $NEW_VERSION."
docker buildx build --platform linux/amd64,linux/arm64 --tag myimage:latest --push .

# Remove the builder when done
docker buildx rm mybuilder
