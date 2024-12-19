docker build -t search-service .
docker run -d -p 8000:80 search-service