import logging
import os
import sys
from pathlib import Path
from image_tabling import ImageDataTabler
from util import get_running_path, sanitize_str_path, user_input, print_welcome_message
from pydantic import BaseModel
import schemas
from image_extraction import ImageDataExtractor, ImageData
from openai import AuthenticationError

logger: logging.Logger = logging.getLogger(__name__)
logger_format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(filename=sanitize_str_path(f"{get_running_path(sys.argv[0])}/../latest.log"),
                    level=logging.INFO,
                    format=logger_format,
                    filemode='a')
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter(logger_format))
logging.root.addHandler(console_handler)

credentials_file_path = sanitize_str_path(f"{get_running_path(sys.argv[0])}/../credentials.txt")
openai_key: str = ""


def prompt_credentials() -> str:
    key = user_input("Please enter your OpenAI API key, make sure it's valid!: ")
    with open(credentials_file_path, "w") as f:
        f.write(key)
    logger.info("credentials written to file")
    return key


def check_credentials() -> bool:
    if not os.path.exists(credentials_file_path):
        Path(credentials_file_path).touch()
        logger.info("credentials file created")
    with open(credentials_file_path, "r") as f:
        if f.read() == "":
            logger.info("no credentials found")
            return False
    logger.info("found credentials")
    return True


def setup_credentials() -> str:
    logger.info(f"setting up credentials from {credentials_file_path}")
    if check_credentials():
        with open(credentials_file_path, "r") as f:
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
        return nav_process_image_data_choose_schema()


def nav_get_valid_directory(prompt: str, default: str = "") -> str:
    directory = user_input(prompt)
    if directory == "" and default != "":
        directory = default
        os.makedirs(directory, exist_ok=True)
    if not os.path.isdir(directory):
        return nav_get_valid_directory("Invalid Path!\n" + prompt, default)
    else:
        return directory


def get_last_output_index(output_dir: str, basename: str) -> int:
    files = [f for f in os.listdir(output_dir) if os.path.isfile(os.path.join(output_dir, f)) and f.startswith(basename)]
    if len(files) == 0:
        return 0
    return max([int(f.split("_")[1].split(".")[0]) for f in files])


def nav_process_image_data() -> bool:
    success: bool = False
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

    extractor = ImageDataExtractor(api_key=openai_key, schema=schema)
    tabler = ImageDataTabler(extractor)
    try:
        tabler.batch_process_images_from_folder(sanitize_str_path(input_dir))
        success = True
    except AuthenticationError:
        logger.error("There was a problem with your API key. Please make sure your credentials are valid.")
    except Exception as e:
        logger.error(f"An unknown error occurred processing image data: {e}")
    finally:
        tabler.export(sanitize_str_path(output_dir + f"/output_{get_last_output_index(output_dir, 'output')+1}.xlsx"))
    return success


def nav_main():
    prompt: str = """
Welcome. Please select an option:
1 - Process image data
2 - Set api key
3 - Help
4 - show logs
0 - Exit

Input: """
    choice = user_input(prompt, 3)
    if choice == "1":
        logger.info("navigating to process image data")
        if nav_process_image_data():
            logger.info("FINISHED: image batch data processed")
    elif choice == "2":
        logger.info("navigating to set api key")
        global openai_key
        openai_key = prompt_credentials()
    elif choice == "3":
        os.startfile(sanitize_str_path(f"{get_running_path(sys.argv[0])}/../README.md"))
    elif choice == "4":
        logger.info("navigating to show logs")
        os.startfile(sanitize_str_path(f"{get_running_path(sys.argv[0])}/../latest.log"))
    elif choice == "0":
        logger.info("exiting on user request")
        exit()
    nav_main()


def main():
    try:
        # Add 4 newlines to the log file
        with open(sanitize_str_path(f"{get_running_path(sys.argv[0])}/../latest.log"), 'a') as log_file:
            log_file.write('\n' * 4)
        print_welcome_message()
        global openai_key
        openai_key = setup_credentials()
        nav_main()
    except Exception as e:
        logger.fatal(f"An unprocessed error occurred, restarting application: {e}")
        main()


if __name__ == '__main__':
    main()
