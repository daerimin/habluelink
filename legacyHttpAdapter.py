from requests import Session
from requests import adapters
from urllib3 import poolmanager
from ssl import create_default_context, Purpose, CERT_NONE


class CustomHttpAdapter(adapters.HTTPAdapter):
    def __init__(self, ssl_context=None, **kwargs):
        self.ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(self, connections, maxsize, block=False, **kwargs):
        self.poolmanager = poolmanager.PoolManager(
            num_pools=connections, maxsize=maxsize,
            block=block, ssl_context=self.ssl_context)


def ssl_supressed_session():
    ctx = create_default_context(Purpose.SERVER_AUTH)
    # to bypass verification after accepting Legacy connections
    ctx.check_hostname = False
    ctx.verify_mode = CERT_NONE
    # accepting legacy connections
    ctx.options |= 0x4
    session = Session()
    session.mount('https://', CustomHttpAdapter(ctx))
    return session
