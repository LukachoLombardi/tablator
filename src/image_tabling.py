import os
from openai import AuthenticationError

from openpyxl.workbook import Workbook
from pydantic import BaseModel
import image_extraction
import excel_utils
import logging

logger: logging.Logger = logging.getLogger(__name__)


class ImageDataTabler:
    def __init__(self, image_extractor: image_extraction.ImageDataExtractor):
        self.image_extractor: image_extraction.ImageDataExtractor = image_extractor
        self.__image_data_model_type: type(BaseModel) = image_extractor.schema

        class ModelWithPath(image_extractor.schema):
            image_path: str
            error: str
        self.__model_type_with_meta = ModelWithPath

        workbook_name = self.__image_data_model_type.__name__
        self.table: Workbook = excel_utils.initialize_table(self.__model_type_with_meta, workbook_name)
        logger.info(f"table {workbook_name} initialized")

    def process_image_to_table(self, image_path: str) -> image_extraction.ImageData:
        image_data = self.image_extractor.extract_data_from_image(image_path)
        logging.info(f"extracted data from image {image_path}")
        excel_utils.write_model_to_table(self.__model_type_with_meta.
                                         model_construct(**image_data.data.model_dump(),
                                                         image_path=image_path,
                                                         error=("None" if image_data.error is None else str(image_data.error))),
                                                         self.table)
        logging.info(f"tabled image {image_path}")
        return image_data

    def batch_process_images_from_folder(self, folder_path: str):
        logger.info(f"processing images in folder {folder_path}")
        image_paths = self.image_extractor.get_images_from_directory(folder_path)
        for image_path in image_paths:
            try:
                self.process_image_to_table(image_path)
            except Exception as e:
                if isinstance(e, AuthenticationError):
                    raise
                else:
                    logger.error(f"An error occurred processing image {image_path}, skipping: {e}")
                    continue
        logger.info(f"finished processing images in folder {folder_path}")

    def export(self, file_path: str):
        logger.info("exporting table to file")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        excel_utils.save_table_to_file(self.table, file_path)
