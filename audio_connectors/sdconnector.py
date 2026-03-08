import os
import sounddevice as sd

from .abstractconnector import AbstractConnector

os.environ["SD_ENABLE_ASIO"] = "1"

print("hi")

class SDConnector:
    print(sd.query_hostapis())

