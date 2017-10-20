# -*- coding: utf-8 -*-
'''QTAF执行入口
'''

#2015/04/28 eeelin 新建
#2016/10/14 eeelin 将命令的实现统一迁移到testbase.management模块

from testbase.management import qta_manage_main

if __name__ == '__main__':
    qta_manage_main()
    
    