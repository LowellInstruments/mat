# template
# _pre = 'YYYY'
# _sn = 'XXX'
# _sn_full = '{}{}'.format(_pre, _sn)
# _sn_to_mac = {
#     'AAA': 'FF:FF:FF:FF:FF:FF'
# }


# real, grab client file from utils_lowell
_pre = '2006'
_sn = '098'
assert len(_sn) == 3
assert len(_pre) == 4
sn_full = '{}{}'.format(_pre, _sn)
_sn_to_mac = {
    '098': '60:77:71:22:C8:49'
}
mac = _sn_to_mac[_sn]
