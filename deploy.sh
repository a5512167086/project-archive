docker build -t bot-service .
docker run -d -p 8001:8000 bot-service
