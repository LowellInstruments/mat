from mat.logger_controller_ble import (
    LoggerControllerBLE,
    Delegate
)


class LoggerControllerBLERN4020(LoggerControllerBLE):

    UUID_S = '00035b03-58e6-07dd-021a-08123a000300'
    UUID_C = '00035b03-58e6-07dd-021a-08123a000301'

    def ble_write(self, data, response=False):  # pragma: no cover
        binary_data = [data[i:i + 1] for i in range(len(data))]
        for each in binary_data:
            self.cha.write(each, withResponse=response)
