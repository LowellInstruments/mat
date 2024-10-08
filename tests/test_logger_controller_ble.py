from mat.logger_controller_ble import (
    FILE_EXISTS_CMD, SIZ_CMD, OXYGEN_SENSOR_CMD, BAT_CMD, WAT_CMD, BTC_CMD, TEST_CMD,
    FORMAT_CMD, CONFIG_CMD, DDP_CONFIG_CMD, UP_TIME_CMD, MY_TOOL_SET_CMD, LOG_EN_CMD,
    WAKE_CMD, ERROR_WHEN_BOOT_OR_RUN_CMD, CRC_CMD, ERR_MAT_ANS,
    GET_FILE_CMD, DWG_FILE_CMD, DWL_CMD, LED_CMD,
    GET_SENSOR_DO_INTERVAL, GET_COMMON_SENSOR_INTERVAL)


class TestLoggerControllerBle:
    def test_all_definitions(self):
        for each in [
            FILE_EXISTS_CMD,
            SIZ_CMD,
            OXYGEN_SENSOR_CMD,
            BAT_CMD,
            WAT_CMD,
            BTC_CMD,
            TEST_CMD,
            FORMAT_CMD,
            CONFIG_CMD,
            DDP_CONFIG_CMD,
            UP_TIME_CMD,
            MY_TOOL_SET_CMD,
            LOG_EN_CMD,
            WAKE_CMD,
            ERROR_WHEN_BOOT_OR_RUN_CMD,
            CRC_CMD,
            ERR_MAT_ANS,
            GET_FILE_CMD,
            DWG_FILE_CMD,
            DWL_CMD,
            LED_CMD,
            GET_SENSOR_DO_INTERVAL,
            GET_COMMON_SENSOR_INTERVAL,
        ]:
            assert "''" not in each
