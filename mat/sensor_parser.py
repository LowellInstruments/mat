from numpy import array


class SensorParser:
    def __init__(self, data, converter):
        self.data = data
        self.converter = converter

    def sensors(self):
        data = self.data
        channels = []
        if not data or not (len(data) == 32 or len(data) == 40):
            return None

        n_sensors = 8 if len(data) == 32 else 10
        for i in range(n_sensors):
            dataHex = data[i * 4:i * 4 + 4]
            dataHex = dataHex[2:4] + dataHex[0:2]
            dataInt = int(dataHex, 16)
            # Convert to negative unless temperature or pressure
            if i not in [0, 8]:
                if dataInt > 32768:
                    dataInt -= 65536
            channels.append(dataInt)

        temp_raw = channels[0]
        accel_raw = array([[channels[1]], [channels[2]], [channels[3]]])
        mag_raw = array([[channels[4]], [channels[5]], [channels[6]]])
        batt = array([float(channels[7]) / 1000])

        if n_sensors == 10:
            pressure_raw = channels[8]
            pressure = self.converter.pressure(pressure_raw)[0]
            light_raw = channels[9]
            light = self.converter.light(array([light_raw]))

        else:
            light_raw = 0
            light = 0
            pressure_raw = 0
            pressure = 0

        if temp_raw == 0:  # Avoid 0 right after power up
            temp_raw = 1

        temp = self.converter.temperature(temp_raw)
        accel = self.converter.accelerometer(accel_raw)
        mag = self.converter.magnetometer(mag_raw, array([temp]))

        sensors = {}
        sensors['temp_raw'] = temp_raw
        sensors['temp'] = temp

        sensors['ax_raw'] = accel_raw[0]
        sensors['ax'] = accel[0]

        sensors['ay_raw'] = accel_raw[1]
        sensors['ay'] = accel[1]

        sensors['az_raw'] = accel_raw[2]
        sensors['az'] = accel[2]

        sensors['mx_raw'] = mag_raw[0]
        sensors['mx'] = mag[0]

        sensors['my_raw'] = mag_raw[1]
        sensors['my'] = mag[1]

        sensors['mz_raw'] = mag_raw[2]
        sensors['mz'] = mag[2]

        sensors['batt'] = batt
        sensors['light_raw'] = light_raw
        sensors['light'] = light

        sensors['pressure'] = pressure
        sensors['pressure_raw'] = pressure_raw
        return sensors
