class LoggerControllerBLECC26X2:  # pragma: no cover

    UUID_S = 'f0001130-0451-4000-b000-000000000000'
    UUID_C = 'f0001132-0451-4000-b000-000000000000'
    UUID_W = 'f0001131-0451-4000-b000-000000000000'
    MTU_SIZE = 247

    def __init__(self, mac):
        self.address = mac
        self.peripheral = None
        self.svc = None
        self.cha = None

    def open_after(self):
        # e.g. MTU_SIZE = 247 - 3B ATT header, notifications up to 244 bytes
        self.peripheral.setMTU(self.MTU_SIZE)
        self.cha = self.svc.getCharacteristics(self.UUID_W)[0]
        # print(self._know_mtu())

    def ble_write(self, data, response=False):
        if len(data) <= self.MTU_SIZE:
            self.cha.write(data, withResponse=response)

    def _know_mtu(self):
        return self.peripheral.status()['mtu'][0]
