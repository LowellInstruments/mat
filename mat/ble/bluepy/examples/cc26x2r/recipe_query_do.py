import yaml
from mat.ble.bluepy.cc26x2r_logger_controller import LoggerControllerCC26X2R
import os


# -----------------------------------------------
# grabs an input YML file like <mac>: <SN>
# queries the MAC for a dissolved oxygen measure
# if measure goes wrong, logs mac to output file
# -----------------------------------------------


def _is_do_sensor_working(mac):
    lc = LoggerControllerCC26X2R(mac)
    if lc.open():
        rv = lc.ble_cmd_stp()
        print('\t> stop: {}'.format(rv))
        rv = lc.ble_cmd_gdo()
        print('\t> gdo: {}'.format(rv))
    else:
        print('{} connection error'.format(__name__))
        rv = False
    lc.close()
    return rv


def query_do(file_in, file_out, pre_rm=False):

    if pre_rm:
        os.remove(file_out)

    # read input file
    with open(file_in) as f_in:
        list_of_loggers_in = yaml.load(f_in, Loader=yaml.FullLoader)
    length_in = len(list_of_loggers_in)

    # write output file
    list_of_bad_loggers_out = {}
    for i, mac in enumerate(list_of_loggers_in.keys()):
        s = '\n\nquerying {}/{} -> {}'
        print(s.format(i + 1, length_in, mac))

        # try several times
        if _is_do_sensor_working(mac):
            continue
        if _is_do_sensor_working(mac):
            continue
        if _is_do_sensor_working(mac):
            continue

        # to bad list
        print('\tadding {} to bad list'.format(mac))
        list_of_bad_loggers_out[mac] = list_of_loggers_in[mac]
        with open(file_out, 'w') as f_out:
            yaml.dump(list_of_bad_loggers_out, f_out)


if __name__ == '__main__':
    query_do(file_in='_query_do_in.yml',
             file_out= '_query_do_out.yml')
