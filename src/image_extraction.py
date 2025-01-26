from openai import OpenAI
from openai.lib import ResponseFormatT
import base64
from pydantic import BaseModel
from dataclasses import dataclass


@dataclass
class ImageData:
    image_path: str
    schema: type(BaseModel)
    data: BaseModel
    prompt: str


class ImageExtractor:
    def __init__(self, api_key: str, schema: type(BaseModel)):
        self.openai: OpenAI = OpenAI(api_key=api_key)
        self.schema: type(BaseModel) = schema
        self.prompt: str = "extract the matching data from the image and fill it in the schema"

    def _modify_prompt(self, prompt: str):
        self.prompt = prompt

    def extract_text_from_image(self, image_path: str) -> ImageData:
        image_base64 = _image_to_base64(image_path)
        response = self.openai.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": self.prompt,
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "content": {
                                "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
                            },
                        }
                    ]
                },
            ],
            response_format=ResponseFormatT(self.schema),
        )
        return ImageData(image_path=image_path, schema=self.schema, data=response.choices[0].message.parsed, prompt=self.prompt)


def _image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")
