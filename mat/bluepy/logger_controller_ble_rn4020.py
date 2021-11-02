from mat.bluepy.logger_controller_ble_lowell import LoggerControllerBLELowell
from mat.bluepy.logger_controller_ble_rn4020_utils import ble_connect_rn4020_logger


class LoggerControllerBLERN4020(LoggerControllerBLELowell):  # pragma: no cover

    def open(self):
        return ble_connect_rn4020_logger(self)

    def _ble_write(self, data, response=False):
        b = [data[i:i + 1] for i in range(len(data))]
        for _ in b:
            self.cha.write(_, withResponse=response)

    def _ble_cmd(self, *args):  # pragma: no cover
        # RN4020 answers have \r\n and \r\n
        a = super()._ble_cmd(*args)
        a = a[2:] if a and a.startswith(b'\n\r') else a
        a = a[:-2] if a and a.endswith(b'\r\n') else a
        return a

    # def get_file(self, lc, file, fol, size, sig=None) -> bool:  # pragma: no cover
    #     assert(lc.und.type == self.type)
    #     lc.purge()
    #
    #     # ensure fol string, not path_lib
    #     fol = str(fol)
    #
    #     # ask for file, mind RN4020 particular behavior to send GET answer
    #     dl = False
    #     cmd = 'GET {:02x}{}\r'.format(len(file), file)
    #     lc.ble_write(cmd.encode())
    #     till = time.perf_counter() + 5
    #     while 1:
    #         lc.per.waitForNotifications(.1)
    #         if time.perf_counter() > till:
    #             break
    #         _ = lc.dlg.buf.decode().strip()
    #         if _ == 'GET 00':
    #             dl = lc.xmd_rx_n_save(file, fol, size, sig)
    #             break
    #
    #     # clean-up
    #     return dl
