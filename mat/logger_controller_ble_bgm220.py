import time


class LoggerControllerBLEBGM220:  # pragma: no cover

    def __init__(self, base):
        self.type = 'bgm220'
        self.base = base
        # todo: adjust these
        self.UUID_S = ''
        self.UUID_C = ''
        self.UUID_W = ''
        self.MTU_SIZE = 247

    def open_post(self):
        # notification size up to MTU_SIZE - 3B ATT header
        self.base.per.setMTU(self.MTU_SIZE)
        # self.base.cha = self.base.svc.getCharacteristics(self.UUID_W)[0]

    def ble_write(self, data, response=False):
        if len(data) <= self.MTU_SIZE:
            self.base.cha.write(data, withResponse=response)

    def _know_mtu(self):
        return self.base.per.status()['mtu'][0]
