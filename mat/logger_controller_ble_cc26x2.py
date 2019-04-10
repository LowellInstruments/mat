import bluepy.btle as btle
import time
from mat.logger_controller_ble import LoggerControllerBLE, Delegate


class LoggerControllerBLECC26X2(LoggerControllerBLE):

    def open(self):
        try:
            self.peripheral = btle.Peripheral()
            self.delegate = Delegate()
            self.peripheral.setDelegate(self.delegate)
            self.peripheral.connect(self.address)
            # bluepy needs some time to set mtu
            self.peripheral.setMTU(50)
            time.sleep(1)
            uuid_service = 'f0001130-0451-4000-b000-000000000000'   # p0
            # uuid_service = '0000fff0-0000-1000-8000-00805f9b34fb'
            # uuid_char = '0000fff5-0000-1000-8000-00805f9b34fb'
            uuid_char = 'f0001131-0451-4000-b000-000000000000'  # p0
            self.service = self.peripheral.getServiceByUUID(uuid_service)
            self.characteristic = self.service.getCharacteristics(uuid_char)[0]
            return True
        except AttributeError:
            return False

    def _wait_for_command_answer(self, cmd):
        wait_time = self.WAIT_TIME[cmd[:3]] if cmd[:3] in self.WAIT_TIME else 1
        time.sleep(wait_time)
        return self.characteristic.read()

    def ble_write(self, data, response=False):  # pragma: no cover
        # ex: b'STS \r'
        self.characteristic.write(data, withResponse=response)
