import threading
import xmlrpc
from xmlrpc.client import Binary
import time
from xmlrpc.server import SimpleXMLRPCServer
from mat.xs import XS


def xs_ble_xml_rpc_server():
    server = SimpleXMLRPCServer(('localhost', 9000),
                                logRequests=True,
                                allow_none=True)
    server.register_instance(XS())

    try:
        print('launching XS')
        server.serve_forever()
    except KeyboardInterrupt:
        print('bye XS')


def launch_xml_rpc_client():
    time.sleep(1)
    xp = xmlrpc.client.ServerProxy('http://localhost:9000', allow_none=True)
    print('Ping: ', xp.xs_ping())
    # print('None: ', server.send_none())
    # print('SB: ', server.send_back_binary(b'abc'))
    # print('scan ', server.xs_ble_scan())
    # print('status:', rv[0], rv[1])
    print('xs_ble_connect', xp.xs_ble_connect('80:6f:b0:1e:3d:18'))
    # print('xs_ble_get_mac_connected_to', xp.xs_ble_get_mac_connected_to())
    # print('xs_ble_get_mac_connected_to', xp.xs_ble_get_mac_connected_to())
    print('xs_ble_status', xp.xs_ble_cmd_status())
    print('xs_ble_disconnect', xp.xs_ble_disconnect())
    print('xs_ble_set_hci_0', xp.xs_ble_set_hci(0))
    print('xs_ble_set_hci_1', xp.xs_ble_set_hci(1))


if __name__ == '__main__':
    th_xc = threading.Thread(target=launch_xml_rpc_client)
    th_xs = threading.Thread(target=xs_ble_xml_rpc_server)
    th_xs.start()
    th_xc.start()
