from fastapi import FastAPI, File, HTTPException, UploadFile
from PIL import Image
from ocr import get_image_text

app = FastAPI()


@app.post("/extract_text")
def extract_text(file: UploadFile = File()):
    try:
        image = Image.open(file.file)
        image_text = get_image_text(image)

        return {"image_text": image_text}
    except Exception:
        raise HTTPException(status_code=500, detail='Something went wrong')
    finally:
        file.file.close()
        image.close()
