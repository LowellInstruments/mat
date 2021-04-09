from xmlrpc.client import Binary

from mat.logger_controller import STATUS_CMD
from mat.logger_controller_ble import ble_scan
from mat.logger_controller_ble_factory import LcBLEFactory


class XS:
    """ XS: XML RPC server """

    def __init__(self):
        self.lc = None

    @staticmethod
    def ping():
        """ check server is alive """
        return True

    @staticmethod
    def exception(msg):
        """ exception example """
        raise RuntimeError(msg)

    @staticmethod
    def send_back_binary(b):
        """ unpack, re-pack, send-back binary """
        data = b.data
        print('send_back_binary({!r})'.format(data))
        response = Binary(data)
        return response

    @staticmethod
    def send_none():
        return None

    @staticmethod
    def scan_bluetooth():
        sr = ble_scan(0)
        sr_f = [each_sr.addr for each_sr in sr]
        return sr_f

    def bluetooth_status(self, mac):
        lc = LcBLEFactory.generate(mac)
        with lc(mac) as lc:
            return lc.command(STATUS_CMD)

