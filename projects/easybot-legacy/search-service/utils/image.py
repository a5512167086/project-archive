import base64
import io
import time

from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import (
    ComputerVisionOcrErrorException,
)
from config import AZURE_VISION_ENDPOINT, AZURE_VISION_KEY
from msrest.authentication import CognitiveServicesCredentials

ocr_client = ComputerVisionClient(
    AZURE_VISION_ENDPOINT, CognitiveServicesCredentials(AZURE_VISION_KEY)
)


def extract_text_from_base64_image(base64_image):
    max_retries = 5
    retry_delay = 2

    image_data = base64.b64decode(base64_image)
    image_stream = io.BytesIO(image_data)
    for attempt in range(max_retries):
        try:
            response = ocr_client.read_in_stream(image_stream, raw=True)
            operation_id = response.headers["Operation-Location"].split("/")[-1]

            while True:
                result = ocr_client.get_read_result(operation_id)
                if result.status not in ["notStarted", "running"]:
                    break
                time.sleep(1)

            if result.status == "succeeded":
                return " ".join(
                    [
                        line.text
                        for page in result.analyze_result.read_results
                        for line in page.lines
                    ]
                )
        except ComputerVisionOcrErrorException as e:
            if "Too Many Requests" in str(e):
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
            else:
                raise e

    raise RuntimeError("OCR operation failed after maximum retries")


def extract_text_from_image(image_url):
    max_retries = 5
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            response = ocr_client.read(image_url, raw=True)
            operation_id = response.headers["Operation-Location"].split("/")[-1]

            while True:
                result = ocr_client.get_read_result(operation_id)
                if result.status not in ["notStarted", "running"]:
                    break
                time.sleep(1)

            if result.status == "succeeded":
                return " ".join(
                    [
                        line.text
                        for page in result.analyze_result.read_results
                        for line in page.lines
                    ]
                )
        except ComputerVisionOcrErrorException as e:
            if "Too Many Requests" in str(e):
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
