import string
import random


def random_string(size=40, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in xrange(size))
