from mat.ble.bleak_beta.examples.do2.download import download


if __name__ == "__main__":
    name = 'dummy_4151.lid'
    size = 4151
    download(name, size, dummy=True)

