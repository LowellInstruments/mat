import os
import sqlite3
import threading
import time
from mat.bleak.ble_commands import *
from mat.bleak.ble_logger_do2_utils import (
    BleakClientDummyDO2,
    ENGINE_CMD_SCAN,
    ENGINE_CMD_CON,
    ENGINE_CMD_DISC,
    ENGINE_CMD_BYE, ENGINE_CMD_EXC, EngineException, is_answer_done
)
from mat.examples.bleak.do2.macs import MAC_DO2_0_DUMMY
from mat.logger_controller import (
    STATUS_CMD,
    FIRMWARE_VERSION_CMD,
    DIR_CMD,
    SET_TIME_CMD,
    STOP_CMD,
    TIME_CMD, DEL_FILE_CMD, LOGGER_INFO_CMD, LOGGER_INFO_CMD_W, SD_FREE_SPACE_CMD, LOGGER_HSA_CMD_W, CALIBRATION_CMD
)
from mat.utils import PrintColors as PC


# global variables used in this module
g_ans = bytes()
g_cmd = ''
g_ans_done = False
g_db = None


def _cmd_wait_ans():
    global g_cmd
    global g_ans_done

    # simulate some time for answer to arrive
    time.sleep(.2)
    g_ans_done = is_answer_done(g_cmd, g_ans)

    # indicate success degree
    s = '[ OK ]' if g_ans_done else '[ NA ]'
    print('    {} {}'.format(s, g_cmd))
    g_cmd = ''


def _cmd_send(_, s):
    # s: 'STS \r'
    global g_cmd
    g_cmd = s
    tag = g_cmd.split()[0]

    # use database for more realism
    global g_db

    # fake an answer
    global g_ans
    if tag == STATUS_CMD:
        g_ans = b'STS 0201'

    if tag == BAT_CMD:
        g_ans = b'STS 049908'

    if tag == DIR_CMD:
        g_ans = b'\n\r.\t\t\t0\n\r\n\r..\t\t\t0\n\r'
        ex = g_db.execute("SELECT NAME, SIZE from FILES")
        for _ in ex:
            s = '\n\r{}\t\t\t{}\n\r'.format(_[0], _[1])
            g_ans += s.encode()
        g_ans += '\x04\n\r'.encode()

    if tag == SET_TIME_CMD:
        g_ans = b'STM 00'

    if tag == TIME_CMD:
        g_ans = b'GTM 132005/09/05 10:46:45'

    if tag == FIRMWARE_VERSION_CMD:
        g_ans = b'GFV 063.0.00'

    if tag == STOP_CMD:
        g_ans = b'STP 00'

    if tag == DWG_FILE_CMD:
        g_ans = b'DWG 00'

    if tag == SLOW_DWL_CMD:
        g_ans = b'SLW 0201'

    if tag == DWL_CMD:
        g_ans = b'*' * 2048

    if tag == LED_CMD:
        for i in range(3):
            # green dots
            print(PC.OKGREEN + u'\u25cf' + PC.ENDC)
            time.sleep(.5)
        g_ans = b'LED 00'

    if tag == MY_TOOL_SET_CMD:
        size = 1 + int(time.time() % 10000)
        s = 'dummy_{}.lid'.format(size)
        g_db.execute('INSERT INTO FILES VALUES (null, ?, ?);', (s, size))
        g_db.commit()
        g_ans = b'MTS 00'

    if tag == DEL_FILE_CMD:
        file_name = g_cmd.split()[1][2:]
        s = 'SELECT NAME, SIZE from FILES where NAME = (?)'
        cursor = g_db.execute(s, (file_name, ))
        if len(cursor.fetchall()) == 0:
            g_ans = b'ERR'
            return
        s = 'DELETE from FILES where NAME = (?)'
        g_db.execute(s, (file_name, ))
        g_db.commit()
        g_ans = b'DEL 00'

    if tag == FORMAT_CMD:
        g_ans = b'FRM 00'
        g_db.execute('DELETE from FILES')
        g_db.commit()

    if tag == LOGGER_INFO_CMD_W:
        # WLI 09SN1111111
        what = g_cmd.split()[1][2:4]
        v = g_cmd.split()[1][4:]
        if what not in ('SN', 'BA', 'MA', 'BA'):
            g_ans = b'ERR'
            return
        if len(v) < 4 or len(v) > 7:
            g_ans = b'ERR'
            return
        s = 'UPDATE INFO set VALUE = (?) where NAME = (?);'
        g_db.execute(s, (v, what))
        g_db.commit()
        g_ans = b'WLI 00'

    if tag == LOGGER_INFO_CMD:
        # RLI 02SN
        what = g_cmd.split()[1][2:4]
        s = 'SELECT * from INFO where NAME = (?);'
        cur = g_db.execute(s, (what, ))
        rows = cur.fetchall()
        n = len(rows[0][2])
        s = '{} {:02X}{}'.format('RLI', n, rows[0][2])
        g_ans = s.encode()

    if tag == SD_FREE_SPACE_CMD:
        g_ans = b'CFS 080040CC05'

    if tag == CONFIG_CMD:
        g_ans = b'CFG 00'

    if tag == OXYGEN_SENSOR_CMD:
        g_ans = b'GDO 0C001100220033'

    if tag == LOGGER_HSA_CMD_W:
        # WHS 09TMO12345
        what = g_cmd.split()[1][2:5]
        v = g_cmd.split()[1][5:]
        if what not in ('TMO', 'TMA', 'TMB', 'TMC', 'TMR'):
            g_ans = b'ERR'
            return
        if len(v) != 5:
            g_ans = b'ERR'
            return
        s = 'UPDATE HSA set VALUE = (?) where NAME = (?);'
        g_db.execute(s, (v, what))
        g_db.commit()
        g_ans = b'WHS 00'

    if tag == CALIBRATION_CMD:
        # RHS 03TMO
        what = g_cmd.split()[1][2:5]
        s = 'SELECT * from HSA where NAME = (?);'
        cur = g_db.execute(s, (what, ))
        rows = cur.fetchall()
        n = len(rows[0][2])
        s = '{} {:02X}{}'.format('RHS', n, rows[0][2])
        g_ans = s.encode()

    if tag == LOG_EN_CMD:
        g_ans = b'LOG 0201'

    if tag == MOBILE_CMD:
        g_ans = b'MBL 0201'

    if tag == SIZ_CMD:
        file_name = g_cmd.split()[1][2:]
        s = 'SELECT NAME, SIZE from FILES where NAME = (?)'
        cur = g_db.execute(s, (file_name, ))
        rows = cur.fetchall()
        if len(rows) == 0:
            g_ans = b'ERR'
            return
        n = len(str(rows[0][1]))
        s = '{} {:02X}{}'.format('SIZ', n, rows[0][1])
        g_ans = s.encode()

    if tag == WAKE_CMD:
        g_ans = b'WAK 0201'


def _engine(q_cmd, q_ans):
    """
    loop: send BLE command to logger and receive answer
    """

    cli = None

    while 1:
        # thread: dequeue external command such as 'STS \r'
        global g_cmd
        global g_db
        g_cmd = q_cmd.get()

        # command: special 'quit thread'
        if g_cmd == ENGINE_CMD_BYE:
            if cli:
                cli.disconnect()
            q_ans.put(b'bye OK')
            g_db.close()
            break

        # command: special exception COMMAND testing
        if g_cmd.startswith(ENGINE_CMD_EXC):
            raise EngineException('test')

        # command: special 'disconnect', takes ~ 2 seconds
        if g_cmd == ENGINE_CMD_DISC:
            if cli:
                cli.disconnect()
            cli = None
            q_ans.put(b'disconnect OK')
            g_db.close()
            continue

        # command: special 'connect', also enables config descriptor
        if g_cmd.startswith(ENGINE_CMD_CON):
            mac = g_cmd.split()[1]
            cli = BleakClientDummyDO2(mac)
            cli.connect()
            create_dummy_database(mac)
            q_ans.put(cli.address)
            continue

        # command: special 'scan'
        if g_cmd.startswith(ENGINE_CMD_SCAN):
            rv = (MAC_DO2_0_DUMMY, )
            q_ans.put(rv)
            continue

        # coroutines: send dequeued CMD, enqueue answer back
        global g_ans
        global g_ans_done
        g_ans = bytes()
        g_ans_done = False
        _cmd_send(cli, g_cmd)
        _cmd_wait_ans()
        q_ans.put(g_ans)


# thread with exceptions
def __engine(q_cmd, q_ans):
    try:
        _engine(q_cmd, q_ans)
    except EngineException as ex:
        print('\t\t(en) exception in BLE engine dummy: {}'.format(ex))
        q_ans.put(ENGINE_CMD_EXC)


# called at logger controller's constructor
def ble_engine_do2_dummy(q_in, q_out):

    # thread BLE do2_dummy engine
    print('starting thread ble_engine_do2_dummy...')
    th = threading.Thread(target=__engine, args=(q_in, q_out, ))
    th.start()


def create_dummy_database(mac):
    global g_db
    db_name = '_{}.db'.format(mac.replace(':', '-'))
    if not os.path.isfile(db_name):
        g_db = sqlite3.connect(db_name)
        g_db.execute('''CREATE TABLE FILES
                 (ID INT PRIMARY KEY,    
                 NAME           TEXT    NOT NULL,
                 SIZE           INT     NOT NULL);''')
        g_db.execute('''CREATE TABLE INFO
                 (ID INT PRIMARY KEY, 
                 NAME           TEXT    NOT NULL,
                 VALUE          TEXT    NOT NULL);''')
        g_db.execute('''CREATE TABLE HSA
                 (ID INT PRIMARY KEY, 
                 NAME           TEXT    NOT NULL,
                 VALUE          TEXT    NOT NULL);''')
        s = 'INSERT INTO INFO VALUES (null, ?, ?);'
        g_db.execute(s, ('SN', '1234567'))
        g_db.commit()
        g_db.execute(s, ('CA', '1111'))
        g_db.commit()
        g_db.execute(s, ('BA', '2222'))
        g_db.commit()
        g_db.execute(s, ('MA', '3333'))
        g_db.commit()
        s = 'INSERT INTO HSA VALUES (null, ?, ?);'
        g_db.execute(s, ('TMO', '12345'))
        g_db.commit()
        g_db.execute(s, ('TMA', '3g37`'))
        g_db.commit()
        g_db.execute(s, ('TMB', '3HeWD'))
        g_db.commit()
        g_db.execute(s, ('TMC', '1U\\q^'))
        g_db.commit()
        g_db.execute(s, ('TMR', '7N=Yn'))
        g_db.commit()
    else:
        g_db = sqlite3.connect(db_name)
