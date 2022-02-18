import asyncio
from bleak import BleakScanner

from mat.ble.bleak_beta.logger_mat import LoggerMAT


async def run():
    scanner = BleakScanner()
    await scanner.start()
    await asyncio.sleep(2.0)
    await scanner.stop()

    rv = {}
    for each in scanner.discovered_devices:
        rv[each.address.lower()] = each.rssi, each.name
    return rv


def ble_scan_bleak() -> dict:
    loop = asyncio.get_event_loop()
    a = loop.run_until_complete(run())
    return a