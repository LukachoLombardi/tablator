import importlib
import inspect
import os
import pkgutil
from pathlib import Path
from types import ModuleType
import sys
from util import get_running_path, sanitize_str_path
from datamodel_code_generator import InputFileType
from pydantic import BaseModel
import datamodel_code_generator
import logging

logger: logging.Logger = logging.getLogger(__name__)


def _get_classes_in_module(module) -> list[type]:
    classes = []
    for name, obj in inspect.getmembers(module):
        if inspect.isclass(obj) and obj.__module__ == module.__name__:
            classes.append(getattr(module, name))
    return classes


def _import_modules_in_folder(folder_path: str) -> list[ModuleType]:
    modules = []
    for _, module_name, _ in pkgutil.iter_modules([folder_path]):
        module_path = Path(folder_path).as_posix()
        sys.path.append(module_path)
        modules.append(importlib.import_module(module_name))
    return modules


def _get_files_in_folder(folder_path: str) -> list[str]:
    try:
        files = [folder_path+"/"+f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
        return files
    except Exception as e:
        logger.warning(f"An error occurred reading files in folder: {e}")
        return []


def get_model_collection(folder_path: str = sanitize_str_path(f"{get_running_path(sys.argv[0])}/../resources/schemas/templates"),
                         output_path: str = sanitize_str_path(f"{get_running_path(sys.argv[0])}/../resources/schemas/generated")) -> list[type(BaseModel)]:
    logger.info(f"reading in available schemas from {folder_path}")
    files = _get_files_in_folder(folder_path)
    for file in files:
        logger.debug(f"found schema file: {file}")
        try:
            with open(file, "r") as f:
                datamodel_code_generator.generate(input_=f.read(), input_file_type=InputFileType.JsonSchema, output=Path(f"{output_path}/{Path(file).stem}.py"))
        except Exception as e:
            logger.error(f"An error occurred parsing schema: {e}")
            continue
    classes: list[type(BaseModel)] = []
    for module in _import_modules_in_folder(output_path):
        module_classes = _get_classes_in_module(module)
        classes.extend(module_classes)
    logger.info(f"found generated {classes}")
    return classes
