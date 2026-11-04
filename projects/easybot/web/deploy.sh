#!/bin/sh
IMAGE_NAME=$1
docker build -t $IMAGE_NAME .
docker run -p 8080:80 $IMAGE_NAME
