import os
import sqlite3
import time
import mat.bleak.ble_utils_shared as bs
from mat.ble_commands import *
from mat.logger_controller import STATUS_CMD, FIRMWARE_VERSION_CMD, DIR_CMD, SET_TIME_CMD, STOP_CMD, TIME_CMD, \
    SD_FREE_SPACE_CMD, DEL_FILE_CMD, LOGGER_INFO_CMD_W, LOGGER_INFO_CMD, CALIBRATION_CMD, LOGGER_HSA_CMD_W, RUN_CMD
from mat.utils import PrintColors as PC
import datetime


MAC_LOGGER_DO2_DUMMY = '11:22:33:44:55:66'


def _is_it_running(_db):
    s = 'SELECT VALUE from OTHERS where NAME = (?)'
    ex = _db.execute(s, ('STATUS',))
    r = ex.fetchall()
    return r[0][0] == '00'


def create_dummy_database(mac):
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
        g_db.execute('''CREATE TABLE OTHERS
                 (ID INT PRIMARY KEY,
                 NAME           TEXT    NOT NULL,
                 VALUE          TEXT    NOT NULL);''')
        s = 'INSERT INTO OTHERS VALUES (null, ?, ?);'
        now = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        g_db.execute(s, ('TIME', now))
        g_db.commit()
        g_db.execute(s, ('STATUS', '01'))
        g_db.commit()
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
    return g_db


async def cmd_tx(_, s):
    bs.g_cmd = s
    tag = bs.g_cmd.split()[0]

    # use database for more realism
    g_db = create_dummy_database(MAC_LOGGER_DO2_DUMMY)

    # fake an answer
    if tag == STATUS_CMD:
        s = 'SELECT VALUE from OTHERS where NAME = (?)'
        ex = g_db.execute(s, ('STATUS', ))
        r = ex.fetchall()
        bs.g_ans = b'STS 02' + r[0][0].encode()

    if tag == BAT_CMD:
        bs.g_ans = b'STS 049908'

    if tag == DIR_CMD:
        if _is_it_running(g_db):
            bs.g_ans = b'ERR'
            return
        bs.g_ans = b'\n\r.\t\t\t0\n\r\n\r..\t\t\t0\n\r'
        ex = g_db.execute("SELECT NAME, SIZE from FILES")
        for _ in ex:
            s = '\n\r{}\t\t\t{}\n\r'.format(_[0], _[1])
            bs.g_ans += s.encode()
        bs.g_ans += '\x04\n\r'.encode()

    if tag == SET_TIME_CMD:
        if _is_it_running(g_db):
            bs.g_ans = b'ERR'
            return
        now = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        s = 'UPDATE OTHERS set VALUE = (?) where NAME = (?);'
        g_db.execute(s, (now, 'TIME',))
        g_db.commit()
        bs.g_ans = b'STM 00'

    if tag == TIME_CMD:
        s = 'SELECT VALUE from OTHERS where NAME = (?)'
        ex = g_db.execute(s, ('TIME', ))
        r = ex.fetchall()
        bs.g_ans = b'GTM 13' + r[0][0].encode()

    if tag == FIRMWARE_VERSION_CMD:
        bs.g_ans = b'GFV 063.0.00'

    if tag == STOP_CMD:
        s = 'UPDATE OTHERS set VALUE = (?) where NAME = (?);'
        g_db.execute(s, ('01', 'STATUS',))
        g_db.commit()
        bs.g_ans = b'STP 00'

    if tag == RUN_CMD:
        if _is_it_running(g_db):
            bs.g_ans = b'ERR'
            return
        s = 'UPDATE OTHERS set VALUE = (?) where NAME = (?);'
        g_db.execute(s, ('00', 'STATUS',))
        g_db.commit()
        bs.g_ans = b'RUN 00'

    if tag == DWG_FILE_CMD:
        if _is_it_running(g_db):
            bs.g_ans = b'ERR'
            return
        file_name = bs.g_cmd.split()[1][2:]
        s = 'SELECT NAME, SIZE from FILES where NAME = (?)'
        cursor = g_db.execute(s, (file_name, ))
        if len(cursor.fetchall()) == 0:
            bs.g_ans = b'ERR'
            return
        bs.g_ans = b'DWG 00'

    if tag == SLOW_DWL_CMD:
        bs.g_ans = b'SLW 0201'

    if tag == DWL_CMD:
        if _is_it_running(g_db):
            bs.g_ans = b'ERR'
            return
        bs.g_ans = b'*' * 2048

    if tag == LED_CMD:
        for i in range(3):
            # green dots
            print(PC.OKGREEN + u'\u25cf' + PC.ENDC)
            time.sleep(.5)
        bs.g_ans = b'LED 00'

    if tag == MY_TOOL_SET_CMD:
        if _is_it_running(g_db):
            bs.g_ans = b'ERR'
            return
        size = 1 + int(time.time() % 10000)
        s = 'dummy_{}.lid'.format(size)
        g_db.execute('INSERT INTO FILES VALUES (null, ?, ?);', (s, size))
        g_db.commit()
        bs.g_ans = b'MTS 00'

    if tag == DEL_FILE_CMD:
        if _is_it_running(g_db):
            bs.g_ans = b'ERR'
            return
        file_name = bs.g_cmd.split()[1][2:]
        s = 'SELECT NAME, SIZE from FILES where NAME = (?)'
        cursor = g_db.execute(s, (file_name, ))
        if len(cursor.fetchall()) == 0:
            bs.g_ans = b'ERR'
            return
        s = 'DELETE from FILES where NAME = (?)'
        g_db.execute(s, (file_name, ))
        g_db.commit()
        bs.g_ans = b'DEL 00'

    if tag == FORMAT_CMD:
        if _is_it_running(g_db):
            bs.g_ans = b'ERR'
            return
        bs.g_ans = b'FRM 00'
        g_db.execute('DELETE from FILES')
        g_db.commit()

    if tag == LOGGER_INFO_CMD_W:
        # WLI 09SN1111111
        what = bs.g_cmd.split()[1][2:4]
        v = bs.g_cmd.split()[1][4:]
        if what not in ('SN', 'BA', 'MA', 'BA'):
            bs.g_ans = b'ERR'
            return
        if len(v) < 4 or len(v) > 7:
            bs.g_ans = b'ERR'
            return
        s = 'UPDATE INFO set VALUE = (?) where NAME = (?);'
        g_db.execute(s, (v, what))
        g_db.commit()
        bs.g_ans = b'WLI 00'

    if tag == LOGGER_INFO_CMD:
        # RLI 02SN
        what = bs.g_cmd.split()[1][2:4]
        s = 'SELECT * from INFO where NAME = (?);'
        cur = g_db.execute(s, (what, ))
        rows = cur.fetchall()
        n = len(rows[0][2])
        s = '{} {:02X}{}'.format('RLI', n, rows[0][2])
        bs.g_ans = s.encode()

    if tag == SD_FREE_SPACE_CMD:
        bs.g_ans = b'CFS 080040CC05'

    if tag == CONFIG_CMD:
        if _is_it_running(g_db):
            bs.g_ans = b'ERR'
            return
        bs.g_ans = b'CFG 00'

    if tag == OXYGEN_SENSOR_CMD:
        bs.g_ans = b'GDO 0C001100220033'

    if tag == LOGGER_HSA_CMD_W:
        # WHS 09TMO12345
        what = bs.g_cmd.split()[1][2:5]
        v = bs.g_cmd.split()[1][5:]
        if what not in ('TMO', 'TMA', 'TMB', 'TMC', 'TMR'):
            bs.g_ans = b'ERR'
            return
        if len(v) != 5:
            bs.g_ans = b'ERR'
            return
        s = 'UPDATE HSA set VALUE = (?) where NAME = (?);'
        g_db.execute(s, (v, what))
        g_db.commit()
        bs.g_ans = b'WHS 00'

    if tag == CALIBRATION_CMD:
        # RHS 03TMO
        what = bs.g_cmd.split()[1][2:5]
        s = 'SELECT * from HSA where NAME = (?);'
        cur = g_db.execute(s, (what, ))
        rows = cur.fetchall()
        n = len(rows[0][2])
        s = '{} {:02X}{}'.format('RHS', n, rows[0][2])
        bs.g_ans = s.encode()

    if tag == LOG_EN_CMD:
        bs.g_ans = b'LOG 0201'

    if tag == MOBILE_CMD:
        bs.g_ans = b'MBL 0201'

    if tag == SIZ_CMD:
        if _is_it_running(g_db):
            bs.g_ans = b'ERR'
            return
        file_name = bs.g_cmd.split()[1][2:]
        s = 'SELECT NAME, SIZE from FILES where NAME = (?)'
        cur = g_db.execute(s, (file_name, ))
        rows = cur.fetchall()
        if len(rows) == 0:
            bs.g_ans = b'ERR'
            return
        n = len(str(rows[0][1]))
        s = '{} {:02X}{}'.format('SIZ', n, rows[0][1])
        bs.g_ans = s.encode()

    if tag == WAKE_CMD:
        bs.g_ans = b'WAK 0201'


async def ans_rx():
    # answer already in bs.g_ans
    # just simulate some delay
    time.sleep(.2)
    s = '[ OK ]'
    print('    {} {}'.format(s, bs.g_cmd))
    bs.g_cmd = ''
