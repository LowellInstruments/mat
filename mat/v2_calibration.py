from mat.calibration import Calibration
from mat.utils import _trim_start


class V2Calibration(Calibration):
    @classmethod
    def load_from_string(cls, calibration_string):
        coefficients = {}
        for tag, value in cls._generate_tag_value_pairs(calibration_string):
            coefficients[tag] = value
        return cls(coefficients)

    @staticmethod
    def _generate_tag_value_pairs(calibration_string):
        calibration_string = _trim_start(calibration_string, 3)
        while True:
            tag = calibration_string[0:3]
            if tag == 'HSE':
                break
            length = int(calibration_string[3], 16)
            value = calibration_string[4:4+length]
            calibration_string = _trim_start(calibration_string, 4+length)
            yield tag, value

    def make_serial_string(self):
        """
        This generator function formats the host storage dict for writing
        to the logger.
        """
        yield 'RVN12'
        for key in self.coefficients:
            if key == 'RVN':
                continue
            # TODO this may need to be changed to a number of decimal
            value = str(self.coefficients[key])
            length_hex = '%x' % len(value)
            yield key + length_hex + value
