import sys
from pathlib import Path


def get_running_path(arg: str):
    return Path(arg).parent.resolve()


def sanitize_str_path(path: str) -> str:
    return Path(path).resolve().as_posix()
