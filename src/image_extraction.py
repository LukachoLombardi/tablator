from openai import OpenAI
import base64


class ImageExtractor:
    def __init__(self, api_key):
        self.api_key = api_key

    def extract_text_from_image(self, image_path: str) -> str:
        image_base64 = _image_to_base64(image_path)


def _image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


