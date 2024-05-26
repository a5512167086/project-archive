from fastapi import FastAPI, File, HTTPException, UploadFile, Form
from fastapi.responses import JSONResponse
from PIL import Image
from ocr import get_image_text
import re
import random
import json

app = FastAPI()
answer = None
with open("answer.json", "r", encoding="utf-8") as json_file:
    json_data = json.load(json_file)
    answer = json_data["answer"]


@app.post("/extract_text")
def extract_text(page: int = Form(), file: UploadFile = File()):
    try:
        image = Image.open(file.file)

        if page <= 0:
            return JSONResponse(
                status_code=404,
                content={"detail": "Page not found"},
            )

        # Remove all space and change fullwidth punctuation marks to halfwidth punctuation marks
        current_article = (
            answer[page - 1]
            .replace("，", ",")
            .replace(" ", "")
            .replace("", "")
            .replace("（", "(")
            .replace("）", ")")
            .replace("：", ":")
        )

        # Split to array by punctuation marks
        text_segments = re.split(
            r"[;, ；, 。, \,, (, ), :, \s, 【, 】, /, ., 、]", current_article
        )
        text_segments = list(filter(None, text_segments))

        # Remove all space
        image_text = get_image_text(image).replace(" ", "")

        result = []
        correct_time = 0

        if len(text_segments) > 100:
            text_segments = random.sample(text_segments, 100)

        for text_segment in text_segments:
            isMatch = text_segment in image_text
            if isMatch:
                correct_time = correct_time + 1
            result.append({"text_segment": text_segment, "is_match_ocr_text": isMatch})

        accuracy = 100 * (correct_time / len(text_segments))

        return {
            "accuracy": "%.2f" % accuracy + "%",
            "result": result,
            "original_text": current_article,
            "ocr_text": image_text,
        }
    except Exception:
        raise HTTPException(status_code=500, detail="Something went wrong")
    finally:
        file.file.close()
        image.close()


@app.post("/only_extract_text")
def extract_text(file: UploadFile = File()):
    try:
        image = Image.open(file.file)

        # Remove all space
        image_text = get_image_text(image).replace(" ", "")

        return {
            "ocr_text": image_text,
        }
    except Exception:
        raise HTTPException(status_code=500, detail="Something went wrong")
    finally:
        file.file.close()
        image.close()
