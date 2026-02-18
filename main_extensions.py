from flask_seasurf import SeaSurf

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


csrf = SeaSurf()

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[]
)
