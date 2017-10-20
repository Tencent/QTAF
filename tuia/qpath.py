#-*- coding: utf-8 -*

import warnings

try:
    from qt4c.qpath import QPath, QPathError
    warnings.warn("`tuia.qpath` is depressed, please use `qt4c.qpath` instead", DeprecationWarning)
except ImportError:
    try:
        from qt4a.qpath import QPath, QPathError
        warnings.warn("`tuia.qpath` is depressed, please use `qt4a.qpath` instead", DeprecationWarning)
    except ImportError:
        pass