import logging

logger: logging.Logger = logging.getLogger(__name__)
logging.basicConfig(filename="../latest.log", level=logging.INFO)
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


def nav_process_image_data():
    choice = user_input("Please input source directory. Leaving empty will assume default (.../tablator/inputs): ")
    if choice == "":
        choice = "../inputs"
    input_dir = choice
    logger.info(f"input directory: {input_dir}")


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
