import json
import multiprocessing
import os
import subprocess as sp
import threading
import time
from getmac import get_mac_address
from pika.exceptions import AMQPError
from mat.n2ll_utils import (AG_N2LL_ANS_BYE, AG_N2LL_ANS_ROUTE_ERR_PERMISSIONS,
                            AG_N2LL_ANS_ROUTE_ERR_ALREADY, AG_N2LL_ANS_ROUTE_OK_FULL,
                            AG_N2LL_CMD_WHO, AG_N2LL_CMD_BYE, AG_N2LL_CMD_QUERY,
                            AG_N2LL_CMD_ROUTE, AG_N2LL_CMD_UNROUTE,
                            AG_N2LL_ANS_NOT_FOR_US, check_ngrok_can_be_run,
                            AG_N2LL_CMD_KILL_DDH, AG_N2LL_CMD_INSTALL_DDH, create_populated_crontab_file_for_ddh,
                            create_empty_crontab_file_for_ddh, AG_N2LL_CMD_DDH_VESSEL, AG_N2LL_CMD_BLE_SERVICE_RESTART,
                            AG_N2LL_CMD_XR_START, AG_N2LL_CMD_XR_VIEW, AG_N2LL_CMD_XR_KILL, AG_N2LL_CMD_NGROK_VIEW,
                            _url_n2ll)
from mat.utils import is_process_running_by_name, get_pid_of_a_process, linux_is_rpi
from mat.xr import xr_ble_server, XR_PID_FILE, XR_DEFAULT_PORT
from mat.n2ll_utils import (
    mq_exchange_for_masters,
    mq_exchange_for_slaves)


def _p(s):
    print(s, flush=True)


def _cmd_who(_, macs):
    return 0, ' '.join([m for m in macs if m and m != '*'])


def _cmd_bye(_, macs):
    return 0, '{} in {}'.format(AG_N2LL_ANS_BYE, macs)


def _cmd_query(_, macs):
    """ asks if DDH or ngrok are running here """

    mac = macs[0][-8:]
    ddh = int(is_process_running_by_name('ddh/main.py'))
    ngk = int(is_process_running_by_name('ngrok'))
    xr = _cmd_xr_view(None, macs)

    ddh = 'DDH' if ddh != -1 else '-'
    ngk = 'NGK' if ngk != -1 else '-'
    xr = 'XR' if xr[0] == 0 else '-'
    return 0, '{} => {} / {} / {}'.format(mac, ddh, ngk, xr)


def _cmd_ngrok_route(_, macs):
    """ route ngrok toward this node """

    # _: ['route', '4000', <mac>]
    assert len(_) == 3

    # kill any current local ngrok already running
    sp.run('killall ngrok', shell=True, stdout=sp.PIPE, stderr=sp.PIPE)

    # remove any previous ngrok log file
    log_file = '/dev/shm/my_ngrok.log'
    cmd = 'rm {}'.format(log_file)
    _rv = sp.run(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    if b'permission denied' in _rv.stderr:
        return 1, AG_N2LL_ANS_ROUTE_ERR_PERMISSIONS

    # Popen() daemons ngrok, although cannot check return code
    port = _[1]
    cmd = 'ngrok tcp {} --log {}'.format(port, log_file)
    _rv = sp.Popen(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)

    # see log file, grep ngrok url
    time.sleep(2)
    cmd = 'cat {} | grep \'started tunnel\''.format(log_file)
    _rv = sp.run(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    if _rv.returncode:
        e = AG_N2LL_ANS_ROUTE_ERR_ALREADY
        return 1, e.format(macs[0])

    # grab the output of cat as ngrok url
    g = _rv.stdout
    u = g.decode().strip().split('url=')[1]
    s = AG_N2LL_ANS_ROUTE_OK_FULL.format(macs[0], port, u)
    return 0, s


def _cmd_ngrok_unroute(_, macs):
    """ kill ngrok """

    sp.run('killall ngrok', shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    mac = macs[0][-8:]
    return 0, 'un-routed {}'.format(mac)


def _cmd_ngrok_view(_, macs):
    pid = get_pid_of_a_process('ngrok')
    if pid == -1:
        return 1, 'ngrok process not running'
    return 0, 'ngrok process running pid = {}'.format(pid)


def _cmd_ddh_rpi(_, macs):
    """ delete DDH folder and get new version of it """

    mac = macs[0][-8:]

    if not linux_is_rpi():
        return 0, 'nah, won\'t do DDH on a non-rpi {}'.format(mac)

    # 1st, call function '_cmd_unddh_rpi()'
    _cmd_unddh_rpi(_, macs)

    # todo: test this on a DDH

    # 2nd, delete DDH folder
    cmd = 'rm -rf /home/pi/li/ddh'
    _rv = sp.run(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)

    # 3rd, clone DDH git repo
    cmd = 'mkdir -p /home/pi/li/ddh'
    _rv = sp.run(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    url = 'https://github.com/LowellInstruments/ddh.git'
    cmd = 'git clone {} /home/pi/li/ddh'.format(url)
    _rv = sp.run(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    if _rv.returncode != 0:
        return _rv.returncode, 'DDH git clone failed'

    # 4th, create crontab
    create_populated_crontab_file_for_ddh()
    return 0, 'installed DDH on {}'.format(mac)


def _cmd_unddh_rpi(_, macs):
    """ delete DDH folder """

    mac = macs[0][-8:]

    # 1st, disable any crontab controlling DDH
    if linux_is_rpi():
        create_empty_crontab_file_for_ddh()

    # 2nd, killall DDH
    s = 'ddh/main.py'
    pid = get_pid_of_a_process(s)
    if pid == -1:
        return 1, 'DDH process not running'
    cmd = 'kill -9 {}'.format(pid)
    _rv = sp.run(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    if _rv.returncode != 0:
        return _rv.returncode, 'DDH killing failed'
    return 0, 'DDH killed OK on {}'.format(mac)


def _cmd_ddh_vessel(_, macs):
    mac = macs[0][-8:]
    path = '/home/pi/li/ddh/ddh/settings/ddh.json'
    try:
        with open(path) as f:
            cfg = json.load(f)
            ans = cfg['ship_name']
            ans = '{} => vessel {}'.format(mac, ans)
    except FileNotFoundError:
        ans = 'no ddh.json file found'

    return 0, ans


def _cmd_bled(_, macs):
    mac = macs[0][-8:]
    cmd = 'systemctl restart bluetooth'
    rv = sp.run(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    s = 'mac => {} bluetooth restart {}'
    if rv.returncode == 0:
        return 0, s.format(mac, 'OK')
    return 1, s.format(mac, 'ERR')


def _cmd_xr_view(_, macs):
    mac = macs[0][-8:]
    cmd = 'netstat -an | grep {} | grep LISTEN'.format(XR_DEFAULT_PORT)
    rv = sp.run(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    if rv.stdout:
        return 0, '{} => XR view, yes, there'.format(mac)
    return 1, '{} => XR view, not there'.format(mac)


def _cmd_xr_kill(_, macs):

    # check any running
    mac = macs[0][-8:]
    rv = _cmd_xr_view(_, macs)
    if rv[0] != 0:
        return 0, '{} => XR kill, was not running'

    # a XR writes its pid at boot, check it
    pid = 0
    try:
        with open(XR_PID_FILE) as f:
            pid = int(f.read())
    except FileNotFoundError:
        return 0, '{} => XR kill, no pid_file'.format(mac)

    if not pid:
        return 1, '{} => XR kill, unknown'.format(mac)

    # murder it
    s = 'kill -9 {}'.format(pid)
    rv = sp.run(s, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    if rv.returncode == 0:
        return 0, '{} => XR killed'.format(mac)
    return 1, '{} => XR kill, error'.format(mac)


def _cmd_xr_start(_, macs):
    mac = macs[0][-8:]
    rv = _cmd_xr_view(_, macs)
    if rv[0] == 0:
        return 0, '{} => XR start, no need'.format(mac)

    # thread a xr_ble_server, forking gives rabbitMQ errors
    th = threading.Thread(target=xr_ble_server)
    th.start()
    time.sleep(2)
    rv = _cmd_xr_view(_, macs)
    if rv[0] == 0:
        return 0, '{} => XR start, no need'.format(mac)
    return 1, '{} => XR start, error'.format(mac)


# ====================== N2LL flowchart =========================
# loop_n2ll_agent -> sub_rx -> ans = _parse_n2ll_cmd -> pub(ans)
# ===============================================================

def _parse_n2ll_cmd(s: bytes):
    """ see N2LL command is for me, parse it """

    if not s:
        return 1, 'error, cmd empty'

    # s: AG_N2LL_CMD_QUERY <mac> <port>
    s = s.decode().split(' ')
    # _p('-> N2LL: rx_cb {}'.format(s))

    # which are my own mac addresses
    _my_macs = [
                get_mac_address(interface='eth0'),
                get_mac_address(interface='wlo1'),
                get_mac_address(interface='wlan0'),
                '*']

    # remove Nones
    _my_macs = [i for i in _my_macs if i]

    # search the N2LL function
    cmd = s[0]

    fxn_map = {
        AG_N2LL_CMD_BYE: _cmd_bye,
        AG_N2LL_CMD_WHO: _cmd_who,
        AG_N2LL_CMD_QUERY: _cmd_query,
        AG_N2LL_CMD_ROUTE: _cmd_ngrok_route,
        AG_N2LL_CMD_UNROUTE: _cmd_ngrok_unroute,
        AG_N2LL_CMD_NGROK_VIEW: _cmd_ngrok_view,
        AG_N2LL_CMD_INSTALL_DDH: _cmd_ddh_rpi,
        AG_N2LL_CMD_KILL_DDH: _cmd_unddh_rpi,
        AG_N2LL_CMD_DDH_VESSEL: _cmd_ddh_vessel,
        AG_N2LL_CMD_BLE_SERVICE_RESTART: _cmd_bled,
        AG_N2LL_CMD_XR_START: _cmd_xr_start,
        AG_N2LL_CMD_XR_VIEW: _cmd_xr_view,
        AG_N2LL_CMD_XR_KILL: _cmd_xr_kill,
    }
    fxn = fxn_map[cmd]

    # is this N2LL frame for us?
    if len(s) >= 2:
        mac = s[-1]
        if mac not in _my_macs:
            return 1, '{} {}'.format(AG_N2LL_ANS_NOT_FOR_US, _my_macs)
    else:
        # commands w/o mac
        if not cmd.startswith(AG_N2LL_CMD_WHO):
            return 1, 'cmd bad number of parameters'

    # noinspection PyArgumentList
    return fxn(s, _my_macs)


class AgentN2LL(threading.Thread):

    def __init__(self, url):

        """ ClientN2LL pubs  in channel 'li_masters', subs to 'li_slaves'
            AgentN2LL (n of them) pub to 'li_slaves', sub to 'li_masters' """
        assert(check_ngrok_can_be_run())
        super().__init__()
        self.url = url
        self.ch_pub = None
        self.ch_sub = None

    def _get_ch_pub(self):
        self.ch_pub = mq_exchange_for_slaves()

    def _get_ch_sub(self):
        self.ch_sub = mq_exchange_for_masters()

    @staticmethod
    def _do_i_quit(ans):
        if AG_N2LL_ANS_BYE in ans:
            # give time answer to travel back
            time.sleep(5)
            _p('quitting AG_N2LL')
            os._exit(0)

    def loop_n2ll_agent(self):
        """ AgentN2LL spawns no threads: receives at rx and tx back """

        _p('N2LL: listening on {}'.format(self.url.split('/')[-1]))
        while 1:
            try:
                self._sub_n_rx()
            except (Exception, AMQPError) as e:
                _p('N2LL: agent exc -> {}'.format(e))
                break

    def _pub(self, _what):
        """ publishes in channel slaves """

        self._get_ch_pub()
        self.ch_pub.basic_publish(exchange='li_slaves', routing_key='', body=_what)
        # _p('<- N2LL: pub {}'.format(_what))
        self.ch_pub.close()

    def _sub_n_rx(self):
        # receive from channel 'li_masters'

        def _rx_cb(ch, method, properties, body):

            # receive command from remote n2ll_client
            ans = _parse_n2ll_cmd(body)

            # ans: (0, description) send to channel 'li_slaves'
            self._pub(ans[1])
            # maybe time to end myself
            self._do_i_quit(ans[1])

        self._get_ch_sub()
        rv = self.ch_sub.queue_declare(queue='', durable=True, exclusive=True)
        q = rv.method.queue
        self.ch_sub.queue_bind(exchange='li_masters', queue=q)
        self.ch_sub.basic_consume(queue=q, on_message_callback=_rx_cb, auto_ack=True)
        self.ch_sub.start_consuming()


# running this on Rpi / BASH may need root and:
# PRE_REQ=/usr/lib/arm-linux-gnueabihf/libatomic.so.1
# sudo LD_PRELOAD=$PRE_REQ python3 n2ll_agent.py

if __name__ == '__main__':
    ag_n2ll = AgentN2LL(_url_n2ll())
    th_ag_n2ll = threading.Thread(target=ag_n2ll.loop_n2ll_agent)
    th_ag_n2ll.start()
    print('n2ll_agent th_main ends')

