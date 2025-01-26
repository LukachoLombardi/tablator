import logging
import os
import time
from PIL import Image
from openai import OpenAI, RateLimitError
import base64
from pydantic import BaseModel
from dataclasses import dataclass
from logging import Logger, getLogger

from util import sanitize_str_path

logger: Logger = logging.getLogger(__name__)


@dataclass
class ImageData:
    image_path: str
    schema: type(BaseModel)
    data: BaseModel


class ImageDataExtractor:
    def __init__(self, api_key: str, schema: type(BaseModel)):
        self._openai: OpenAI = OpenAI(api_key=api_key)
        self.__schema: type(BaseModel) = schema
        self.retry_secs: int = 10
        self.image_prompt: str = "extract all the matching data from the image."
        self.schema_prompt: str = "fill in the schema with the extracted data the user will give you."

        self.image_dimensions: list[int] = [1280, 720]

    @property
    def schema(self) -> type(BaseModel):
        return self.__schema

    def _scale_image(self, image_path: str):
        logger.info(f"scaling image {image_path}")
        with Image.open(image_path) as img:
            img.thumbnail(tuple[float, float](self.image_dimensions))
            img.save(image_path)

    def _request_completion(self, image_path: str) -> ImageData:
        if not image_path.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
            raise ValueError("image must be a jpg, png, or webp file")
        self._scale_image(image_path)
        image_base64 = _image_to_base64(image_path)
        logger.info(f"extracting data from image {image_path}")
        response = self._openai.beta.chat.completions.parse(
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
            ],
            response_format=self.__schema
        )
        logger.info("got response")
        return ImageData(image_path=image_path, schema=self.__schema, data=response.choices[0].message.parsed)

    def extract_data_from_image(self, image_path: str) -> ImageData:
        while True:
            try:
                return self._request_completion(image_path)
            except RateLimitError as e:
                logger.info(f"got rate limited, retrying in {self.retry_secs} seconds")
                time.sleep(self.retry_secs)

    def batch_extract_data_from_images(self, image_paths: list[str]) -> list[ImageData]:
        if len(image_paths) == 0:
            logger.warning("no images to process")
            return []
        return [self.extract_data_from_image(image_path) for image_path in image_paths]


def get_images_from_directory(directory: str) -> list[str]:
    return [sanitize_str_path(os.path.join(directory, f)) for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f)) and f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]


def _image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")
