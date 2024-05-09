from PIL import Image
import pytesseract


def get_image_text(image: Image) -> str:
    text = pytesseract.image_to_string(
        image, lang='chi_tra+eng', config='--psm 6 -c tosp_min_sane_kn_sp=2.8 preserve_interword_spaces=1')
    text = text.replace("\n", " ")

    return text
