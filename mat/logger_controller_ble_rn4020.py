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

    def ble_write(self, data, response=False):  # pragma: no cover
        binary_data = [data[i:i + 1] for i in range(len(data))]
        for each in binary_data:
            self.characteristic.write(each, withResponse=response)
