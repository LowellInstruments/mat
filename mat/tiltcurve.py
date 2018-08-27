import numpy as np


class TiltCurve:
    def __init__(self, path):
        self.path = path
        self.model = None
        self.washers = None
        self.salinity = None
        self.table = None
        self._parse_file()

    def _parse_file(self):
        with open(self.path, 'r') as fid:
            while True:
                line = fid.readline()
                if line.startswith('//'):
                    continue
                else:
                    break

            self.model = line.split(' ')[1].strip()
            line = fid.readline()
            self.washers = line.split(' ')[1].strip()
            line = fid.readline()
            self.salinity = line.split(' ')[1].strip()
            line = fid.readline()

            self.table = np.loadtxt(fid, delimiter=',')

    def speed_from_tilt(self, tilt):
        return np.interp(tilt, self.table[:, 0], self.table[:, 1])

    def calc_current(self, accel, mag, declination=0):
        """
        accel and mag are 3x1 matrices of acceleration and magnetometer data
        """

        """
        roll        = atan2d(ay,az);
        pitch       = atan2d(-ax,ay.*sind(roll)+az.*cosd(roll));
        by          = mz.*sind(roll)-my.*cosd(roll);
        bx          = mx.*cosd(pitch)+my.*sind(pitch).*sind(roll)+mz.*sind(pitch).*cosd(roll);
        yaw         = atan2d(by,bx);
        """
        roll = np.arctan2(accel[1], accel[2])
        pitch = np.arctan2(-accel[0], accel[1] * np.sin(roll) + accel[2] * np.cos(roll))
        by = mag[2] * np.sin(roll) - mag[1] * np.cos(roll)
        bx = mag[0] * np.cos(pitch) + mag[1] * np.sin(pitch) * np.sin(roll) + mag[2] * np.sin(pitch) * np.cos(roll)
        yaw = np.arctan2(by, bx)

        """
        x           = -cosd(roll).*sind(pitch);
        y           = sind(roll);
        z           = cosd(roll).*cosd(pitch);
        tilt        = acosd(az./sqrt(ax.^2+ay.^2+az.^2));
        isUsd       = tilt > 90; %upside down
        tilt(isUsd) = 180 - tilt(isUsd);
        """

        x = -np.cos(roll) * np.sin(pitch)
        y = np.sin(roll)

        tilt = np.arccos(accel[2] / np.sqrt(accel[0] ** 2 + accel[1] ** 2 + accel[2] ** 2))
        is_usd = tilt > np.pi / 2
        tilt[is_usd] = np.pi - tilt[is_usd]
        tilt = np.rad2deg(tilt)

        point = np.arctan2(y, x) + yaw
        point = np.mod(point + np.deg2rad(declination), 2*np.pi)
        point_e = np.sin(point)
        point_n = np.cos(point)

        flow = self.speed_from_tilt(tilt)
        flow_n = flow * point_n
        flow_e = flow * point_e

        return np.array([flow, np.rad2deg(point), flow_n, flow_e])
