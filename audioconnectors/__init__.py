import platform

__all__ = ['AudioConnectorFactory']

class AudioConnectorFactory:
    @staticmethod
    def create(process_callback):
        system = platform.system().lower()
        
        if system == 'linux':
            from .jackconnector import JACKConnector
            return JACKConnector(process_callback)
        elif system == 'windows':
                from .paconnector import PAConnector
                return PAConnector(process_callback)
        else:
            raise RuntimeError(f"Unsupported platform: {system}")
