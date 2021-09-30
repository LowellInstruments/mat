import time


class LoggerControllerBLERN4020:  # pragma: no cover

    def __init__(self, base):
        self.type = 'rn4020'
        self.base = base
        self.UUID_S = '00035b03-58e6-07dd-021a-08123a000300'
        self.UUID_C = '00035b03-58e6-07dd-021a-08123a000301'

    def open_post(self):
        pass

    def ble_write(self, data, response=False):  # pragma: no cover
        b_data = [data[i:i + 1] for i in range(len(data))]
        for each in b_data:
            self.base.cha.write(each, withResponse=response)

    def get_file(self, lc, file, fol, size, sig=None) -> bool:  # pragma: no cover
        assert(lc.und.type == self.type)
        lc.purge()

        # ensure fol string, not path_lib
        fol = str(fol)

        # ask for file, mind RN4020 particular behavior to send GET answer
        dl = False
        cmd = 'GET {:02x}{}\r'.format(len(file), file)
        lc.ble_write(cmd.encode())
        till = time.perf_counter() + 5
        while 1:
            lc.per.waitForNotifications(.1)
            if time.perf_counter() > till:
                break
            _ = lc.dlg.buf.decode().strip()
            if _ == 'GET 00':
                dl = lc.xmd_rx_n_save(file, fol, size, sig)
                break

        # clean-up
        return dl
