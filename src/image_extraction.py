from openai import OpenAI
from openai.lib import ResponseFormatT
import base64
from pydantic import BaseModel
from dataclasses import dataclass
from logging import Logger

logger: Logger = Logger(__name__)


@dataclass
class ImageData:
    image_path: str
    schema: type(BaseModel)
    data: BaseModel


class ImageExtractor:
    def __init__(self, api_key: str, schema: type(BaseModel)):
        self.openai: OpenAI = OpenAI(api_key=api_key)
        self.schema: type(BaseModel) = schema
        self.image_prompt: str = "extract all the matching data from the image."
        self.schema_prompt: str = "fill in the schema with the extracted data the user will give you."

    def _modify_prompt(self, prompt: str):
        self.image_prompt = prompt

    def extract_text_from_image(self, image_path: str) -> ImageData:
        image_base64 = _image_to_base64(image_path)
        logger.info(f"extracting text from image {image_path}")
        unparsed_response = self.openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": self.image_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}",
                                "detail": "high"
                            },
                        }
                    ]
                },
            ]
        )
        parsed_response = self.openai.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": self.schema_prompt,
                },
                {
                    "role": "user",
                    "content": unparsed_response.choices[0].message.content,
                },
            ],
            response_format=self.schema
        )

        return ImageData(image_path=image_path, schema=self.schema, data=parsed_response.choices[0].message.parsed)


def _image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")
