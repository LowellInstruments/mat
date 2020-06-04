def read_ble_linux_parameters():
    min_ce = '/sys/kernel/debug/bluetooth/hci0/conn_min_interval'
    max_ce = '/sys/kernel/debug/bluetooth/hci0/conn_max_interval'

    try:
        with open(min_ce,'r') as f_min_ce:
            l1 = f_min_ce.readline()
        with open(max_ce,'r') as f_max_ce:
            l2 = f_max_ce.readline()
        print('BLE parameters current linux system:')
        print('\tmin_ce {}'.format(l1), end='')
        print('\tmax_ce {}'.format(l2), end='')
    except:
        print('Cannot open /sys/kernel/ files to check')