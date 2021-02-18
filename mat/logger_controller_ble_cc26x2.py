import time


class LoggerControllerBLECC26X2:  # pragma: no cover

    def __init__(self, base):
        self.type = 'cc26x2'
        self.base = base
        self.UUID_S = 'f0001130-0451-4000-b000-000000000000'
        self.UUID_C = 'f0001132-0451-4000-b000-000000000000'
        self.UUID_W = 'f0001131-0451-4000-b000-000000000000'
        self.MTU_SIZE = 247

    def open_post(self):
        # notification size up to MTU_SIZE - 3B ATT header
        self.base.per.setMTU(self.MTU_SIZE)
        self.base.cha = self.base.svc.getCharacteristics(self.UUID_W)[0]

    def ble_write(self, data, response=False):
        if len(data) <= self.MTU_SIZE:
            self.base.cha.write(data, withResponse=response)

    def _know_mtu(self):
        return self.base.per.status()['mtu'][0]

    def get_file(self, lc, file, fol, size, sig=None) -> bool:  # pragma: no cover
        """ sends GET command and downloads file """
        assert (lc.und.type == self.type)

        # separates file downloads, allows logger x-modem to boot
        lc.purge()
        time.sleep(1)

        # ensure fol string, not path_lib
        fol = str(fol)

        # ask for file, mind CC26x2 particular behavior to send GET answer
        dl = False
        cmd = 'GET {:02x}{}\r'.format(len(file), file)
        lc.ble_write(cmd.encode())
        lc.per.waitForNotifications(10)
        if lc.dlg.buf and lc.dlg.buf.endswith(b'GET 00'):
            dl = lc.xmd_rx_n_save(file, fol, size, sig)

        # don't remove, allows logger x-modem to finish
        time.sleep(1)

        # clean-up
        return dl
