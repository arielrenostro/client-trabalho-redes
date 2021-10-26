import os


def _safe_int_env(key: str, default: int):
    val = os.getenv(key)
    try:
        if val:
            return int(val)
    except Exception as e:
        print(f'Failure to parse integer environment "{key}: {val}". {e}')
    return default


LARC_USE_IPV6 = os.getenv('LARC_USE_IPV6', 'false').lower() == 'true'
LARC_ADDRESS = os.getenv('LARC_ADDRESS', 'larc.inf.furb.br')
LARC_ENCODING = os.getenv('LARC_ENCODING', 'utf-8')
LARC_TCP_PORT = _safe_int_env('LARC_TCP_PORT', 1012)
LARC_UDP_PORT = _safe_int_env('LARC_UDP_PORT', 1011)
LARC_USER_ID = _safe_int_env('LARC_USER_ID', 8638)
LARC_USER_PASSWORD = os.getenv('LARC_USER_PASSWORD', 'hwquw')

LARC_MESSAGES_REFRESH_TIMEOUT = 1
LARC_USERS_REFRESH_TIMEOUT = 1
LARC_PLAYERS_REFRESH_TIMEOUT = 1
