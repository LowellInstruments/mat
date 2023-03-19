from mat.water_detect import WaterDetect


class TestWaterDetect:
    def test_water_detect(self):
        wd = WaterDetect()
        assert wd.convert(1500) == 50
