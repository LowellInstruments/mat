import json
import subprocess as sp
from getmac import get_mac_address
from pika.exceptions import AMQPError
from mat.n2ll_beta.n2ll_utils import (AG_N2LL_ANS_BYE, AG_N2LL_ANS_ROUTE_ERR_PERMISSIONS,
                                      AG_N2LL_ANS_ROUTE_ERR_ALREADY, AG_N2LL_ANS_ROUTE_OK_FULL,
                                      AG_N2LL_CMD_WHO, AG_N2LL_CMD_BYE, AG_N2LL_CMD_QUERY,
                                      AG_N2LL_CMD_ROUTE, AG_N2LL_CMD_UNROUTE,
                                      AG_N2LL_ANS_NOT_FOR_US,
                                      AG_N2LL_CMD_DDH_VESSEL,
                                      AG_N2LL_CMD_XR_START, AG_N2LL_CMD_XR_VIEW, AG_N2LL_CMD_XR_KILL,
                                      AG_N2LL_CMD_NGROK_VIEW,
                                      n2ll_url,
                                      )
from mat.utils import linux_is_process_running_by_name, linux_get_pid_of_a_process
from mat.n2ll_beta.n2ll_utils import (
    mq_exchange_for_masters,
    mq_exchange_for_slaves)
from mat.ble.bluepy.xc_ble_lowell import *
from mat.ble.bluepy.xs_ble_lowell import *


def _p(s):
    print(s, flush=True)


def _n2ll_cmd_who(_, macs) -> tuple:
    return 0, ' '.join([m for m in macs if m and m != '*'])


def _n2ll_cmd_bye(_, macs) -> tuple:
    return 0, '{} in {}'.format(AG_N2LL_ANS_BYE, macs)


def _n2ll_cmd_query(_, macs) -> tuple:
    """ asks if DDH, ngrok and XR are running here """

    mac = macs[0][-8:]
    ddh = int(linux_is_process_running_by_name('ddh/main.py'))
    ngk = int(linux_is_process_running_by_name('ngrok'))
    xr = _n2ll_cmd_xs_view(None, macs)

    ddh = 'DDH' if ddh != -1 else '-'
    ngk = 'NGK' if ngk != -1 else '-'
    xr = 'XR' if xr[0] == 0 else '-'
    return 0, '{} => {} / {} / {}'.format(mac, ddh, ngk, xr)


def _n2ll_cmd_ngrok_route(_, macs) -> tuple:
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

    # see log file to run a 'cat' on it
    time.sleep(2)
    cmd = 'cat {} | grep \'started tunnel\''.format(log_file)
    _rv = sp.run(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    if _rv.returncode:
        e = AG_N2LL_ANS_ROUTE_ERR_ALREADY
        return 1, e.format(macs[0])

    # grab the output of 'cat' as most current ngrok url
    g = _rv.stdout
    u = g.decode().strip().split('url=')[1]
    s = AG_N2LL_ANS_ROUTE_OK_FULL.format(macs[0], port, u)
    return 0, s


def _n2ll_cmd_ngrok_unroute(_, macs) -> tuple:
    """ kill ngrok """

    sp.run('killall ngrok', shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    mac = macs[0][-8:]
    return 0, 'un-routed {}'.format(mac)


def _n2ll_cmd_ngrok_view(_, macs) -> tuple:
    mac = macs[0][-8:]
    pid = linux_get_pid_of_a_process('ngrok')
    if pid == -1:
        return 1, 'ngrok not running at {}'.format(mac)
    return 0, 'ngrok pid = {} at {}'.format(pid, mac)


def _n2ll_cmd_ddh_vessel(_, macs) -> tuple:
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


def _n2ll_cmd_xs_view(_, macs) -> tuple:
    mac = macs[0][-8:]
    cmd = 'netstat -an | grep {} | grep LISTEN'.format(XS_DEFAULT_PORT)
    rv = sp.run(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    if rv.stdout:
        return 0, '{} => XS view, yes, there'.format(mac)
    return 1, '{} => XS view, not there'.format(mac)


def _n2ll_cmd_xs_kill(_, macs):

    # check no XR is currently running
    mac = macs[0][-8:]
    rv = _n2ll_cmd_xs_view(_, macs)
    if rv[0] != 0:
        return 0, '{} => XS kill, was not running'

    # a XR server writes its pid at boot, check it
    # todo -> I wrongly removed this because windows just add it again
    pid = 0
    try:
        with open(XS_PID_FILE) as f:
            pid = int(f.read())
    except FileNotFoundError:
        return 0, '{} => XS kill, no pid_file'.format(mac)

    # file exists but not pid in it
    if not pid:
        return 1, '{} => XS kill, unknown'.format(mac)

    # murder any XR server
    s = 'kill -9 {}'.format(pid)
    rv = sp.run(s, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    if rv.returncode == 0:
        return 0, '{} => XS killed'.format(mac)
    return 1, '{} => XS kill, error'.format(mac)


def _n2ll_cmd_xs_start(_, macs):

    # check XR is already running
    mac = macs[0][-8:]
    rv = _n2ll_cmd_xs_view(_, macs)
    if rv[0] == 0:
        return 0, '{} => XS already running'.format(mac)

    # launch XR server as thread, fork() gives RabbitMQ error
    run_thread(xs_run)
    time.sleep(2)

    # check launched properly
    rv = _n2ll_cmd_xs_view(_, macs)
    if rv[0] == 0:
        return 0, '{} => XS started'.format(mac)
    return 1, '{} => XS start error'.format(mac)


# ====================== N2LL flowchart =========================
# loop_n2ll_agent -> sub_rx -> ans = _parse_n2ll_cmd -> pub(ans)
# ===============================================================

def _parse_n2ll_cmd(s: bytes):
    """ see N2LL command is for me, parse it """

    # s: AG_N2LL_n2ll_cmd_QUERY <mac> <port>
    if not s:
        return 1, 'error, cmd empty'
    s = s.decode().split(' ')

    # debug
    # _p('-> N2LL: rx_cb {}'.format(s))

    # get all my own mac addresses
    _my_macs = [
                get_mac_address(interface='eth0'),
                get_mac_address(interface='wlo1'),
                get_mac_address(interface='wlan0'),
                '*']

    # remove Nones
    _my_macs = [i for i in _my_macs if i]

    # map: received command -> N2LL function
    cmd = s[0]
    fxn_map = {
        AG_N2LL_CMD_BYE: _n2ll_cmd_bye,
        AG_N2LL_CMD_WHO: _n2ll_cmd_who,
        AG_N2LL_CMD_QUERY: _n2ll_cmd_query,
        AG_N2LL_CMD_ROUTE: _n2ll_cmd_ngrok_route,
        AG_N2LL_CMD_UNROUTE: _n2ll_cmd_ngrok_unroute,
        AG_N2LL_CMD_NGROK_VIEW: _n2ll_cmd_ngrok_view,
        AG_N2LL_CMD_DDH_VESSEL: _n2ll_cmd_ddh_vessel,
        AG_N2LL_CMD_XR_START: _n2ll_cmd_xs_start,
        AG_N2LL_CMD_XR_VIEW: _n2ll_cmd_xs_view,
        AG_N2LL_CMD_XR_KILL: _n2ll_cmd_xs_kill,
    }
    fxn = fxn_map[cmd]

    # check command addressed to us
    if len(s) >= 2:
        mac = s[-1]
        if mac not in _my_macs:
            return 1, '{} {}'.format(AG_N2LL_ANS_NOT_FOR_US, _my_macs)
    else:
        # these commands do not need mac
        if not cmd.startswith(AG_N2LL_CMD_WHO):
            return 1, 'cmd bad number of parameters'

    # noinspection PyArgumentList
    return fxn(s, _my_macs)


class AgentN2LL(threading.Thread):

    def __init__(self, url):

        """ ClientN2LL pubs  to channel 'li_masters', subs to 'li_slaves'
            AgentN2LL (n of them) pub to 'li_slaves', sub to 'li_masters' """

        # if not linux_check_ngrok_can_be_run():
        #     os._exit(1)

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

    def sub_n_rx(self):
        _p('N2LL: listening on {}'.format(self.url.split('/')[-1]))
        while 1:
            try:
                self._sub_n_rx()
            except (Exception, AMQPError) as e:
                _p('N2LL: agent exc -> {}'.format(e))
                break

    def _pub(self, _what):
        """ agent publishes to channel slaves """

        self._get_ch_pub()
        self.ch_pub.basic_publish(exchange='li_slaves', routing_key='', body=_what)
        # _p('<- N2LL: pub {}'.format(_what))
        self.ch_pub.close()

    def _sub_n_rx(self):
        """ agent receives from channel masters """

        def _rx_cb(ch, method, properties, body):

            # receive command, pub answer, check quitting
            ans = _parse_n2ll_cmd(body)
            self._pub(ans[1])
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
    ag = AgentN2LL(n2ll_url())
    th = threading.Thread(target=ag.sub_n_rx)
    th.start()
    print('n2ll_agent thread ends')

