#-*- coding: utf-8 -*

import warnings
warnings.warn("`tuia.util` is depressed, please use `qt4c.util` instead", DeprecationWarning)
try:
    from qt4c.util import *
except ImportError:
    pass

from testbase.util import Timeout
from tuia.exceptions import TimeoutError