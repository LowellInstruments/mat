import bluepy.btle as btle
import time
from mat.logger_controller_ble import LoggerControllerBLE, Delegate


class LoggerControllerBLERN4020(LoggerControllerBLE):

    def open(self):
        try:
            self.peripheral = btle.Peripheral()
            self.delegate = Delegate()
            self.peripheral.setDelegate(self.delegate)
            self.peripheral.connect(self.address)
            # one second required by RN4020
            time.sleep(1)
            uuid_service = '00035b03-58e6-07dd-021a-08123a000300'
            uuid_char = '00035b03-58e6-07dd-021a-08123a000301'
            self.service = self.peripheral.getServiceByUUID(uuid_service)
            self.characteristic = self.service.getCharacteristics(uuid_char)[0]
            descriptor = self.characteristic.valHandle + 1
            self.peripheral.writeCharacteristic(descriptor, b'\x01\x00')
            return True
        except AttributeError:
            return False

    def _wait_for_command_answer(self, cmd):
        end_time = self.WAIT_TIME[cmd[:3]] if cmd[:3] in self.WAIT_TIME else 1
        wait_time = time.time() + end_time
        while time.time() < wait_time:
            self.peripheral.waitForNotifications(0.1)
        return self.delegate.buffer

    def ble_write(self, data, response=False):  # pragma: no cover
        binary_data = [data[i:i + 1] for i in range(len(data))]
        for each in binary_data:
            self.characteristic.write(each, withResponse=response)
