import sys
import time
from pathlib import Path


def get_running_path(arg: str):
    return Path(arg).parent.resolve()


def sanitize_str_path(path: str) -> str:
    return Path(path).resolve().as_posix()


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


def user_input(prompt: str, wait: int = 1):
    time.sleep(wait)
    print("\033[H\033[J", end="")
    print_welcome_message()
    input_str = input(prompt)
    return input_str
