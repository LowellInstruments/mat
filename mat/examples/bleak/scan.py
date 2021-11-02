import asyncio
from bleak import BleakScanner


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


if __name__ == '__main__':
    print(ble_scan_bleak())
