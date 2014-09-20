import string
import random
from hashlib import sha256

from dnsforever.config import hash_salt


def random_string(size=40, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in xrange(size))


def password_hash(data):
    for i in xrange(9999):
        data = sha256(data + hash_salt).digest()
    return sha256(data + hash_salt).hexdigest()