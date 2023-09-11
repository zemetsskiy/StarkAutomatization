from src.config.logger import logger
from pathlib import Path

current_dir = Path(__file__).parent.absolute()
parent_dir = current_dir.parent.parent
keys_file_path = parent_dir / "keys.txt"

global KEYS_LIST

try:
    with open(keys_file_path, 'r') as file:
        KEYS_LIST = [x.rstrip() for x in file.readlines()]
except FileNotFoundError:
    logger.error(f"File {keys_file_path} was not found")
except Exception as err:
    logger.error(f"Error while reading file: {err}")

