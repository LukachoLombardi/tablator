import logging
import os

from pydantic import BaseModel
import schemas

logger: logging.Logger = logging.getLogger(__name__)
logging.basicConfig(filename="../latest.log",
                    level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    filemode='w')
credentials_file = open("../credentials.txt", "rt+")
openapi_key: str


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
    print("\033[H\033[J", end="")
    return input_str


def prompt_credentials() -> str:
    openai_key = user_input("Please enter your OpenAI API key: ")
    credentials_file.write(openai_key)
    logger.info("credentials written to file")
    return openai_key


def check_credentials() -> bool:
    if credentials_file.read() == "":
        logger.info("no credentials found")
        return False
    logger.info("found credentials")
    return True


def setup_credentials() -> str:
    if check_credentials():
        return credentials_file.read()
    else:
        return prompt_credentials()


def nav_process_image_data_choose_schema() -> type(BaseModel):
    classes = schemas.get_model_collection()
    str_builder: str = ""
    str_builder += "Available schemas:\n"
    for i, cls in enumerate(classes):
        str_builder += f"{i+1} - {cls.__name__}"
    str_builder += "\nPlease select a schema: "
    choice = int(user_input(str_builder))-1
    try:
        return classes[choice]
    except Exception as e:
        logger.error(f"An error occurred selecting schema: {e}")
        nav_process_image_data_choose_schema()


def nav_get_valid_directory(prompt: str, default: str = "") -> str:
    directory = user_input(prompt)
    if directory == "" and default != "":
        return default
    if not os.path.isdir(directory):
        nav_get_valid_directory("Invalid Path!\n"+prompt)
    return directory


def nav_process_image_data():
    input_dir = nav_get_valid_directory("Please input source directory. Leaving empty will assume default (.../tablator/inputs): ", "../inputs")
    logger.info(f"input directory: {input_dir}")

    output_dir = nav_get_valid_directory("Please input output directory. Leaving empty will assume default (.../tablator/outputs): ", "../outputs")
    logger.info(f"output directory: {output_dir}")

    schema: type(BaseModel) = nav_process_image_data_choose_schema()


def nav_main():
    choice = user_input("""Welcome. Please select an option:
1 - Process image data
2 - Set api key
3 - Exit
    
Input: """)
    if choice == "1":
        nav_process_image_data()
    elif choice == "2":
        prompt_credentials()
    elif choice == "3":
        exit()
    else:
        nav_main()


def main():
    print_welcome_message()
    openai_key = setup_credentials()
    nav_main()


if __name__ == '__main__':
    main()
