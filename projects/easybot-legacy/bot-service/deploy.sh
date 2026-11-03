docker build -t bot-service .
docker run -d -p 8000:80 bot-service
