# delegated from LoggerControllerBLE, some symbols might not resolve
class LoggerControllerBLERN4020:

    UUID_S = '00035b03-58e6-07dd-021a-08123a000300'
    UUID_C = '00035b03-58e6-07dd-021a-08123a000301'

    def __init__(self, mac):
        self.address = mac
        self.peripheral = None
        self.svc = None
        self.cha = None

    def open_after(self):
        pass

    def ble_write(self, data, response=False):  # pragma: no cover
        binary_data = [data[i:i + 1] for i in range(len(data))]
        for each in binary_data:
            self.cha.write(each, withResponse=response)
