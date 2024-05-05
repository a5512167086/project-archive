FROM python:3.9-slim

COPY . .

RUN apt-get update && \
    apt-get install -y \
        build-essential \
        python3-dev \
        python3-setuptools \
        tesseract-ocr \
        tesseract-ocr-eng \
        tesseract-ocr-chi-tra \
        libgl1 \
        make \
        gcc \
    && python3 -m pip install -r requirements.txt


CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]