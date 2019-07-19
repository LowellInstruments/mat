import json
from mat.logger_controller_ble import (
    LoggerControllerBLE,
    Delegate
)


class LoggerControllerBLECC26X2(LoggerControllerBLE):

    UUID_S = 'f0001130-0451-4000-b000-000000000000'
    UUID_C = 'f0001132-0451-4000-b000-000000000000'
    UUID_W = 'f0001131-0451-4000-b000-000000000000'

    def open_after(self):
        # set_mtu() needs some time (bluepy issue 325)
        self.peripheral.setMTU(240)
        self.cha = self.svc.getCharacteristics(self.UUID_W)[0]

    def ble_write(self, data, response=False):  # pragma: no cover
        # todo: study this length but it is better than byte by byte
        if len(data) < 200:
            self.cha.write(data, withResponse=response)

    def send_cfg(self, cfg_file_as_json_dict):  # pragma: no cover
        cfg_file_as_string = json.dumps(cfg_file_as_json_dict)
        return self.command("CFG", cfg_file_as_string, retries=1)
