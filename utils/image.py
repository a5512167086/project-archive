import time

from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import (
    ComputerVisionOcrErrorException,
)
from msrest.authentication import CognitiveServicesCredentials

from config import AZURE_VISION_ENDPOINT, AZURE_VISION_KEY

ocr_client = ComputerVisionClient(
    AZURE_VISION_ENDPOINT, CognitiveServicesCredentials(AZURE_VISION_KEY)
)


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
