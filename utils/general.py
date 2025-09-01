from launchpad_py import launchpad
from utils.logger import logger

def find_opened_port(lp: launchpad.LaunchpadPro, ports: int = 256):
    for i in range(ports):
        if lp.Open(i):
            logger.info(f"The launchpad port was found in the range of ports: {ports}, port index: {i}")
            return i
    logger.warning(f"The launchpad port was not found in the range of ports: {ports}")
    return -1