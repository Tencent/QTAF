
x ='''api/app
api/testcase
api/env
api/exception
api/keyboard
api/mouse
api/qpath
api/qpathparser
api/control
api/gfcontrols
api/qpappcontrols
api/wincontrols
api/webcontrols
api/accessible
api/remoteprocessing
api/wintypes
api/util'''


t = ''':mod:`tuia.%(name)s` Package
============================

.. automodule:: tuia.%(name)s
    :members:
    :show-inheritance:

'''


for it in x.split('\n'):
    name = it.split('/')[1]
    content = t % {'name':name}
    with open('%s.rst'%name, 'w') as fd:
        fd.write(content)