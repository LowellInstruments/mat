from redis import Redis


r = Redis('localhost')


def r_set(k, v):
    try:
        return r.set(k, v)
    except (Exception, ) as ex:
        print(f'error: r_set -> {ex}')



def r_exp(k, t):
    try:
        return r.expire(k, t)
    except (Exception, ) as ex:
        print(f'error: r_exp -> {ex}')