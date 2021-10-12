g_ans = bytes()
g_cmd = ''
g_hooks = {
    'uuid_c': '',
    'cmd_cb': None,
    'ans_cb': None
}


class EngineException(Exception):
    pass
