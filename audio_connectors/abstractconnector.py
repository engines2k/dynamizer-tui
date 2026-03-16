from typing import Dict, List
from abc import ABC, abstractmethod

class AbstractConnector(ABC):
    def __init__(self) -> None:
        '''__init__'''
        pass


    @abstractmethod
    def get_inputs(self) -> Dict[str, str]:
        '''List all valid input devices as a dictionary of {pretty_name: port_name}.'''
        pass


    @abstractmethod
    def activate(self) -> None:
        '''Activate the connnector to send signal.'''
        pass


    @abstractmethod
    def deactivate(self) -> None:
        '''Stop processing signal.'''
        pass

    @abstractmethod
    def get_buffer(self):        
        '''Get the current buffer of audio frames.'''
        pass


    @abstractmethod
    def change_input(self, input) -> None:
        '''Change the active input for the connector. (hot-swap ready)'''
        pass


    @abstractmethod
    def _connect_input(self) -> None:
        '''Safely connect an input.'''
        pass


    @abstractmethod
    def _disconnect_input(self) -> None:
        '''Safely disconnect an input.'''
        pass

