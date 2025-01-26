from openpyxl.workbook import Workbook
from pydantic import BaseModel
import image_extraction
import excel_utils
import logging

logger: logging.Logger = logging.getLogger(__name__)


class ImageDataTabler:
    def __init__(self, image_extractor: image_extraction.ImageDataExtractor):
        self.image_extractor: image_extraction.ImageDataExtractor = image_extractor
        self._image_data_model_type: type(BaseModel) = image_extractor.schema

        class ModelWithPath(self._image_data_model_type):
            image_path: str
        self._model_type_with_path = ModelWithPath

        self.table: Workbook = excel_utils.initialize_table(ModelWithPath)

    def process_image_to_table(self, image_path: str) -> image_extraction.ImageData:
        image_data = self.image_extractor.extract_data_from_image(image_path)
        logging.info(f"extracted data from image {image_path}")
        excel_utils.write_model_to_table(self._model_type_with_path.
                                         model_construct(**image_data.data.model_dump(),
                                                       image_path=image_path), self.table)
        logging.info(f"tabled image {image_path}")
        return image_data

    def batch_process_images_from_folder(self, folder_path: str):
        logger.info(f"processing images in folder {folder_path}")
        image_paths = image_extraction.get_images_from_directory(folder_path)
        for image_path in image_paths:
            try:
                self.process_image_to_table(image_path)
            except Exception as e:
                logger.error(f"An error occurred processing image {image_path}, skipping: {e}")
                continue
        logger.info(f"finished processing images in folder {folder_path}")

    def export(self, file_path: str):
        excel_utils.save_table_to_file(self.table, file_path)
