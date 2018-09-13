class Accelerometer(ABC):
    @abstractmethod
    def __init__(self, hs):
        pass

    @abstractmethod
    def convert(self, raw_accelerometer, temperature=None):
        pass
