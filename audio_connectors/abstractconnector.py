from typing import List
from abc import ABC, abstractmethod

class AbstractConnector(ABC):

    channel_config: str

    def __init__(self) -> None:
        '''__init__'''
        pass


    @abstractmethod
    def get_inputs(self) -> List[str]:
        '''Lists all valid input devices as a dictionary of {pretty_name: port_name}.'''
        pass


    @abstractmethod
    def activate(self) -> None:
        '''Activates the connnector to send signal.'''
        pass


    @abstractmethod
    def deactivate(self) -> None:
        '''Stops processing signal and deactivates internal client if applicable.'''
        pass


    @abstractmethod
    def get_buffers(self) -> List:
        '''Gets the channel buffers of audio frames.'''
        pass


    @abstractmethod
    def switch_input(self, input: str) -> None:
        '''
        Switches the active input for the connector and notifies subscribers via
        callback that the input has changed, so they can respond if the new
        input has different properties (eg. switch from mono to stereo input).
        '''
        pass


    @abstractmethod
    def _connect_input(self) -> None:
        '''Safely connects an input.'''
        pass


    @abstractmethod
    def _disconnect_input(self) -> None:
        '''Safely disconnects an input.'''
        pass
