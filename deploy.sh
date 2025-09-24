#!/bin/bash

# Stop and remove the old container if it exists
sudo docker rm -f easybot_rag_api

# Build the new image
sudo docker build -t easybot_rag_api:latest .

# Run the new container
sudo docker run --rm -d \
  --network="host" \
  --gpus device=3 \
  --env-file .env \
  -e OLLAMA_HOST="http://127.0.0.1:11434" \
  --name easybot_rag_api \
  easybot_rag_api:latest