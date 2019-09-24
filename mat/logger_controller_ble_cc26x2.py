import json
from mat.logger_controller_ble import (
    LoggerControllerBLE
)


class LoggerControllerBLECC26X2(LoggerControllerBLE):

    UUID_S = 'f0001130-0451-4000-b000-000000000000'
    UUID_C = 'f0001132-0451-4000-b000-000000000000'
    UUID_W = 'f0001131-0451-4000-b000-000000000000'
    MTU_SIZE = 240

    def open_after(self):
        # set_mtu() needs some time (bluepy issue 325)
        self.peripheral.setMTU(self.MTU_SIZE)
        # time.sleep(1)
        # time.sleep(0.5)

        # extra sleep to receive connection update request from cc26x2
        # time.sleep(1)

        # this is where we write to when talking to cc26x2 loggers
        self.cha = self.svc.getCharacteristics(self.UUID_W)[0]

    def ble_write(self, data, response=False):  # pragma: no cover
        if len(data) <= self.MTU_SIZE:
            self.cha.write(data, withResponse=response)

    def send_cfg(self, cfg_file_as_json_dict):  # pragma: no cover
        cfg_file_as_string = json.dumps(cfg_file_as_json_dict)
        return self.command("CFG", cfg_file_as_string, retries=1)

    # bat function, only cc26x2
    def get_bat(self):
        self.delegate.clear_delegate_buffer()
        return self.command('BAT')
