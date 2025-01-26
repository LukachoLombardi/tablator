import logging
import os
import sys
from pathlib import Path
from util import get_running_path, sanitize_str_path
from pydantic import BaseModel
import schemas
from image_extraction import ImageExtractor, ImageData

logger: logging.Logger = logging.getLogger(__name__)
logging.basicConfig(filename=sanitize_str_path(f"{get_running_path(sys.argv[0])}/../latest.log"),
                    level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    filemode='w')
credentials_file_path = sanitize_str_path(f"{get_running_path(sys.argv[0])}/../credentials.txt")
openai_key: str = ""


def print_welcome_message():
    print("""
  _        _     _       _             
 | |      | |   | |     | |            
 | |_ __ _| |__ | | __ _| |_ ___  _ __ 
 | __/ _` | '_ \| |/ _` | __/ _ \| '__|
 | || (_| | |_) | | (_| | || (_) | |   
  \__\__,_|_.__/|_|\__,_|\__\___/|_|   
                                      
Lukas Wößner (c) - 2025                                       
    """)


def user_input(prompt: str):
    logger.debug(f"prompting user: {prompt}")
    print("\033[H\033[J", end="")
    print_welcome_message()
    input_str = input(prompt)
    return input_str


def prompt_credentials() -> str:
    key = user_input("Please enter your OpenAI API key, make sure it's valid!: ")
    with open(credentials_file_path, "w") as f:
        f.write(key)
    logger.info("credentials written to file")
    return key


def check_credentials() -> bool:
    with open(credentials_file_path, "rt") as f:
        if f.read() == "":
            logger.info("no credentials found")
            return False
    logger.info("found credentials")
    return True


def setup_credentials() -> str:
    logger.info(f"setting up credentials from {credentials_file_path}")
    if check_credentials():
        with open(credentials_file_path, "rt") as f:
            return f.read()
    else:
        return prompt_credentials()


def nav_process_image_data_choose_schema() -> type(BaseModel):
    classes = schemas.get_model_collection()
    str_builder: str = ""
    str_builder += "Available schemas:\n"
    for i, cls in enumerate(classes):
        str_builder += f"{i + 1} - {cls.__name__}"
    str_builder += "\nPlease select a schema: "
    try:
        choice = int(user_input(str_builder)) - 1
        return classes[choice]
    except Exception as e:
        logger.error(f"An error occurred selecting schema: {e}")
        nav_process_image_data_choose_schema()


def nav_get_valid_directory(prompt: str, default: str = "") -> str:
    directory = user_input(prompt)
    if directory == "" and default != "":
        return default
    if not os.path.isdir(directory):
        nav_get_valid_directory("Invalid Path!\n" + prompt, default)
    return directory


def nav_process_image_data():
    input_dir = nav_get_valid_directory(
        "Please input source directory. Leaving empty will assume default (.../tablator/inputs): ",
        sanitize_str_path(f"{get_running_path(sys.argv[0])}/../inputs"))
    logger.info(f"input directory: {input_dir}")

    output_dir = nav_get_valid_directory(
        "Please input output directory. Leaving empty will assume default (.../tablator/outputs): ",
        sanitize_str_path(f"{get_running_path(sys.argv[0])}/../outputs"))
    logger.info(f"output directory: {output_dir}")

    schema: type(BaseModel) = nav_process_image_data_choose_schema()
    logger.info(f"selected schema: {schema.__name__}")

    logger.info("processing image data")

    extractor = ImageExtractor(api_key=openai_key, schema=schema)
    result = extractor.extract_text_from_image(Path(input_dir + "/test.jpg").resolve().as_posix())

    for key, value in result.data.model_dump().items():
        print(f"{key}: {value}")
    exit()


def nav_main():
    choice = user_input("""Welcome. Please select an option:
1 - Process image data
2 - Set api key
3 - Exit
    
Input: """)
    if choice == "1":
        logger.info("navigating to process image data")
        nav_process_image_data()
    elif choice == "2":
        logger.info("navigating to set api key")
        global openai_key
        openai_key = prompt_credentials()
    elif choice == "3":
        logger.info("exiting on user request")
        exit()
    nav_main()


def main():
    print_welcome_message()
    global openai_key
    openai_key = setup_credentials()
    nav_main()


if __name__ == '__main__':
    main()
