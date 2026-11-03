docker build -t user-service .
docker run -d -p 8000:80 user-service