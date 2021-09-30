import asyncio
from bleak import BleakScanner


def detection_callback(dev, adv_data):
    if dev.name:
        print('{}\t{}\t{}'.format(dev.address, dev.name, dev.rssi))
    # print(adv_data)


async def run():
    scanner = BleakScanner()
    scanner.register_detection_callback(detection_callback)
    await scanner.start()
    await asyncio.sleep(5.0)
    await scanner.stop()


# so other files can call this function
def main_scan():
    print('scanning...')
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())


if __name__ == '__main__':
    main_scan()

