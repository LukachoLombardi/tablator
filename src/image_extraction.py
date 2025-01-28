import io
import logging
import os
import time
from PIL import Image
from openai import OpenAI, RateLimitError, AuthenticationError
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
    error: Exception | None
    data: BaseModel


class ImageDataExtractor:
    def __init__(self, api_key: str, schema: type(BaseModel)):
        self._openai: OpenAI = OpenAI(api_key=api_key)
        self.__schema: type(BaseModel) = schema
        self.retry_secs: int = 10
        self.retry_attempts: int = 3
        self.sneaky_write_errors: bool = True
        self.__compatible_image_formats: list[str] = [".jpg", ".jpeg", ".png", ".webp", ".tiff", ".tif", ".bmp", ".gif"]
        self.prompt: str = "extract all the matching data from the image. If unsure, write 'null'."

        self.image_dimensions: list[int] = [1280, 720]

    @property
    def compatible_image_formats(self) -> list[str]:
        return self.__compatible_image_formats

    @property
    def schema(self) -> type(BaseModel):
        return self.__schema

    def _build_desc_prompt_from_model(self) -> str:
        prompt: str = "Here are descriptions for some data fields that you must adhere to:\n"
        for field_name, field_info in self.__schema.__fields__.items():
            if field_info.description is not None:
                description = field_info.description
                if description:
                    prompt += f"- {str(field_name)}: {description}\n"
        return prompt

    def _request_completion(self, image_path: str) -> BaseModel:
        if not image_path.lower().endswith(tuple(self.__compatible_image_formats)):
            raise ValueError(f"image {image_path} type is not in {self.__compatible_image_formats}")
        image_base64 = self._image_to_openai_compatible(image_path)
        logger.info(f"extracting data from image {image_path}")
        combined_prompt = f"{self.prompt}\n{self._build_desc_prompt_from_model()}"
        logger.info(combined_prompt)
        response = self._openai.beta.chat.completions.parse(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": combined_prompt},
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
        logger.debug(response)
        return response.choices[0].message.parsed

    def extract_data_from_image(self, image_path: str) -> ImageData:
        for _ in range(self.retry_attempts):
            try:
                completion = self._request_completion(image_path)
                for key, value in completion.model_dump().items():
                    if value == "null":
                        setattr(completion, key, None)
                return ImageData(image_path=image_path, schema=self.__schema, data=self._request_completion(image_path),
                                 error=None)
            except RateLimitError as e:
                logger.info(f"got rate limited, retrying in {self.retry_secs} seconds")
                time.sleep(self.retry_secs)
            except Exception as e:
                if isinstance(e, AuthenticationError):
                    logger.error(f"authentication/api-key error: {e}")
                    raise
                elif self.sneaky_write_errors:
                    logger.error(f"An error occurred processing image, sneaky writing error {image_path}: {e}")
                    return ImageData(image_path=image_path, schema=self.__schema, data=self.__schema.construct(),
                                     error=e)
                else:
                    logger.error(f"An error occurred processing image, bubbling error {image_path}: {e}")
                    raise

    def batch_extract_data_from_images(self, image_paths: list[str]) -> list[ImageData]:
        if len(image_paths) == 0:
            logger.warning("no images to process")
            return []
        return [self.extract_data_from_image(image_path) for image_path in image_paths]

    def get_images_from_directory(self, directory: str) -> list[str]:
        return [sanitize_str_path(os.path.join(directory, f)) for f in os.listdir(directory) if
                os.path.isfile(os.path.join(directory, f)) and f.lower().endswith(tuple(self.__compatible_image_formats))]

    def _image_to_openai_compatible(self, image_path: str) -> str:
        with Image.open(image_path) as img:
            with io.BytesIO() as buffer:
                logger.info(f"adjusting image {image_path}. To dimensions: {self.image_dimensions}")
                img.convert("RGB").save(buffer, format="JPEG")
                img.thumbnail(tuple[float, float](self.image_dimensions))
                return base64.b64encode(buffer.getvalue()).decode("utf-8")
