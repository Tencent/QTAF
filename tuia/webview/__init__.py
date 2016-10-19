# -*- coding: UTF-8 -*-

'''IWebWiew接口定义及Windows平台上的实现
'''

# 2015/11/6 shadowyang 创建

import sys, logging
fmt = logging.Formatter('%(asctime)s %(thread)d %(message)s')
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(fmt)
logging.root.addHandler(handler)