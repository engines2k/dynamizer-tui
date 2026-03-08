from typing import List
from abc import ABC, abstractmethod

class AbstractConnector(ABC):
    def __init__(self) -> None:
        '''__init__'''
        pass


    @property
    @abstractmethod
    def inputs(self) -> List:
        '''List all valid input devices.'''
        pass


    @abstractmethod
    def activate(self) -> None:
        '''Activate the connnector to send signal.'''
        pass


    @abstractmethod
    def change_input(self, input) -> None:
        '''Change the active input for the connector. (hot-swap ready)'''
        pass


    @abstractmethod
    def deactivate(self) -> None:
        '''Stop processing signal.'''
        pass


    @abstractmethod
    def _connect_input(self) -> None:
        '''Safely connect an input.'''
        pass

    @abstractmethod
    def _disconnect_input(self) -> None:
        '''Safely disconnect an input.'''
        pass

