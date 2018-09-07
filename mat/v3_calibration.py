from mat import ascii85
from mat.calibration import Calibration


class V3Calibration(Calibration):
    def __init__(self, coefficients):
        for tag in coefficients:
            if 'RVN' in tag:
                coefficients[tag] = float(coefficients[tag])
                continue
            coefficients[tag] = ascii85.ascii85_to_num(coefficients[tag])
        super().__init__(coefficients)

    @classmethod
    def load_from_string(cls, calibration_string):
        coefficients = {'RVN': 3}
        calibration_string = calibration_string[8:]
        tag = calibration_string[:3]
        while tag != 'HSE':
            value = calibration_string[3:8]
            coefficients[tag] = value
            calibration_string = calibration_string[8:]
            tag = calibration_string[0:3]
        return cls(coefficients)

    def make_serial_string(self):
        """
        This generator function formats the host storage dict for writing
        to the logger.
        """
        yield 'RVN13'
        for key in self.coefficients:
            if key == 'RVN':
                continue
            value = ascii85.num_to_ascii85(self.coefficients[key])
            yield key + value
