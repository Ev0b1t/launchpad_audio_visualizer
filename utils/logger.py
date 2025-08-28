import os
from datetime import datetime
from loguru import logger

LOGS_DIR = os.path.join('..', 'logs')

os.makedirs(LOGS_DIR, exist_ok=True)
LOG_NAME = f"{datetime.now().date()}.log"
LOG_FPATH = os.path.join(LOGS_DIR, LOG_NAME)

FILE_FORMAT = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {name}:{line} - {message}\n"

def file_format(record):
    return FILE_FORMAT.format(
        time=record["time"],
        level=record["level"].name,
        name=record["name"].replace(".", "/"),
        line=record["line"],
        message=record["message"]
    )

def add_file_logging(level='DEBUG', rotation='10 MB', compression='zip'):
    logger.add(
        sink=LOG_FPATH,
        level=level,
        rotation=rotation,
        compression=compression,
        format=file_format
    )

def log_start():
    logger.info("\n------------------- START NEW SESSION -------------------")

add_file_logging()
# add_console_logging()
log_start()

if __name__ == "__main__":
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")