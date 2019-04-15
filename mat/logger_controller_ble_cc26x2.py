import bluepy.btle as ble
import json
from mat.logger_controller_ble import LoggerControllerBLE, Delegate


class LoggerControllerBLECC26X2(LoggerControllerBLE):

    def open(self):
        try:
            self.peripheral = ble.Peripheral()
            self.delegate = Delegate()
            self.peripheral.setDelegate(self.delegate)
            self.peripheral.connect(self.address)
            # project_zero DS_STREAM characteristic notification
            uuid_service = 'f0001130-0451-4000-b000-000000000000'
            uuid_char = 'f0001132-0451-4000-b000-000000000000'
            self.service = self.peripheral.getServiceByUUID(uuid_service)
            self.characteristic = self.service.getCharacteristics(uuid_char)[0]
            descriptor = self.characteristic.valHandle + 1
            self.peripheral.writeCharacteristic(descriptor, b'\x01\x00')
            # project_zero DS_STRING characteristic
            uuid_char = 'f0001131-0451-4000-b000-000000000000'
            self.characteristic = self.service.getCharacteristics(uuid_char)[0]
            return True
        except AttributeError:
            return False

    def ble_write(self, data, response=False):  # pragma: no cover
        # todo: study this length but it is better than byte by byte
        if len(data) < 200:
            self.characteristic.write(data, withResponse=response)

    def send_cfg(self, cfg_file_as_json_dict):
        self.command("CFG ", json.dumps(cfg_file_as_json_dict), retries=1)
