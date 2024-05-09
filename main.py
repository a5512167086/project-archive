from fastapi import FastAPI, File, HTTPException, UploadFile, Form
from fastapi.responses import JSONResponse
from PIL import Image
from ocr import get_image_text
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

        current_article = answer[page - 1]
        # Remove all space, change ， to , and split to array
        text_segments = current_article.replace(
            "，", ",").replace(" ", "").split("。")

        # Remove all space
        image_text = get_image_text(image).replace(" ", "")

        result = []

        # Random pick text segments to check is match ocr text
        for text_segment in random.sample(text_segments, random.randint(1, len(text_segments))):
            result.append({"text_segment": text_segment,
                          "isMatchOcrText": text_segment in image_text})

        return result
    except Exception:
        raise HTTPException(status_code=500, detail='Something went wrong')
    finally:
        file.file.close()
        image.close()
