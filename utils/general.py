from launchpad_py import launchpad

def find_opened_port(lp: launchpad.LaunchpadPro, ports: int = 256):
    for i in range(256):
        if lp.Open(i):
            return i