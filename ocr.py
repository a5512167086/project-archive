from PIL import Image
import pytesseract


def get_image_text(image: Image) -> str:
    text = pytesseract.image_to_string(image, lang='chi_tra+eng')

    return text
