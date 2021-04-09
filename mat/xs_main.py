import threading
import xmlrpc
from xmlrpc.client import Binary
import time
from xmlrpc.server import SimpleXMLRPCServer
from xs import XS


def launch_xml_rpc_server():
    server = SimpleXMLRPCServer(('localhost', 9000),
                                logRequests=True,
                                allow_none=True)
    server.register_instance(XS())

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('bye XS')


def launch_xml_rpc_client():
    time.sleep(1)
    server = xmlrpc.client.ServerProxy('http://localhost:9000', allow_none=True)
    print('Ping: ', server.ping())
    print('None: ', server.send_none())
    print('SB: ', server.send_back_binary(b'abc'))
    print('scan ', server.scan_bluetooth())
    rv = server.bluetooth_status('80:6f:b0:1e:3d:18')
    print('status:', rv[0], rv[1])


if __name__ == '__main__':
    th_xc = threading.Thread(target=launch_xml_rpc_client)
    th_xs = threading.Thread(target=launch_xml_rpc_server)
    th_xs.start()
    th_xc.start()
