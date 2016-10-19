# -*-  coding: UTF-8  -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
__modified__ = '2011.05 - 2012.03 - 2012.05.30'
__description__ = '3.x (中文输入输出仅使用Unicode字符集)'
__author__ = 'tommyzhang'
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
#2008年10月: v0.0;   构思成型，搁置研究，后积累一年自动化经验
#2009年11月: v0.0;   实施预研，Selenium项目二次开发于下半年失败
#2009年12月: v1.x;   完成原型，继承了Win32GUI硬编译高封装的对象库的概念
#2010年03月: v1.x;   03月份之前完成动态内核对象的改造，并投入群空间的自动化测试至2010年09月份
#2010年12月: v1.x;   完成投入WebQQ的自动化预测试
#2011年03月: v1.x;   完成投入WebQQ的API自动化白盒测试，持续至2011年05月份（跟进了WebQQ两个大版本）
#2011年07月: v2.x;   投入Q+的API自动化白盒测试，整合至QTA
#2011年12月: v3.x;   弃用原IEBundle，WIE3.x正式命名为IEDriver（兼容IE6、7、8、9、10）
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
import re, gc, time, urllib, threading, comtypes, win32ext
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-


# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- FramesXPathsParser

class FramesXPathsParser:
    
    def __init__(self):
        self.parsed = []
        self.buffer = ''
        self.closer = ''
        self.closer_pattern = '''(?<!\\\\)'$|(?<!\\\\)"$'''
        self.frames_pattern = '''\(?/{1,2}frame$|\(?/{1,2}iframe$'''
        self.nodes_pattern = '''\(?/{1,2}\w+$|\(?/{1,2}\.{1,2}$|\(?/{1,2}\*$'''
        self.found_frames = False
    
    def __add_byte__(self, byte):
        self.buffer += byte
        if re.search(self.closer_pattern, self.buffer):
            if self.closer == byte : self.closer = ''
            elif self.closer == '' : self.closer = byte
        if '' == self.closer and re.search(self.frames_pattern, self.buffer, re.IGNORECASE):
            self.found_frames = True;return
        if '' == self.closer and self.found_frames and re.search(self.nodes_pattern, self.buffer, re.IGNORECASE):
            cur_buffer = re.findall(self.nodes_pattern, self.buffer, re.IGNORECASE)[0]
            cur_parsed = re.sub('\\' + cur_buffer + '$', '', self.buffer)
            self.parsed.append(cur_parsed)
            self.buffer = cur_buffer
            self.found_frames = False
    
    def __parse__(self, xpaths):
        if xpaths == None           : return []
        if isinstance(xpaths, list) : return xpaths
        if not isinstance(xpaths, basestring):raise Exception('Error: xpaths type')
        for byte in xpaths:self.__add_byte__(byte)
        if '' != self.buffer:self.parsed.append(self.buffer)
        return self.parsed
    
    @classmethod
    def parse(cls, xpaths):return cls().__parse__(xpaths)


# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- IEDriver

class IEDriver(object):
    
    def __init__(self, ies_handle):
        self.ies_handle = ies_handle
        self.__check_handle__()
        # -*-
        self.com_objs = {
            'frames' : {
                #'xpath':{
                #    'frames' : {},
                #    'engine' : None,
                #    'win2'   : None,
                #    'doc2'   : None,
                #    'url'    : None,
                #    'elem'   : com_obj
                #}
            },
            'engine' : None,
            'win2'   : None,
            'doc2'   : None,
            'url'    : None}
        self.cur_com_objs = {}
        # -*-
        iefs = win32ext.IEHandle.get_iefs_by_ies(self.ies_handle)
        self.ies_processID = iefs[            win32ext.IEConst.IES_ProcessID            ]
        self.ies_threadID = iefs[             win32ext.IEConst.IES_ThreadID             ]
        self.ies_process_creationTime = iefs[ win32ext.IEConst.IES_Process_CreationTime ]
        self.ies_thread_creationTime = iefs[  win32ext.IEConst.IES_Thread_CreationTime  ]
        self.ief_handle = iefs[               win32ext.IEConst.IEF_Handle               ]
        self.ief_processID = iefs[            win32ext.IEConst.IEF_ProcessID            ]
        self.ief_threadID = iefs[             win32ext.IEConst.IEF_ThreadID             ]
        self.ief_process_creationTime = iefs[ win32ext.IEConst.IEF_Process_CreationTime ]
        self.ief_thread_creationTime = iefs[  win32ext.IEConst.IEF_Thread_CreationTime  ]
        win32ext.Process.wait_for_input_idle_by_processID(self.ies_processID, 1000 * 30)
        IEDrivers.append(self)
    
    # -*- -*- -*-
    
    def __release__(self, com_objs):
        if not com_objs : return
        if com_objs.has_key('frames'):
            for key in com_objs['frames'].keys():self.__release__(com_objs['frames'][key])
            del com_objs['frames']
        if com_objs.has_key('engine') :
            try    : com_objs['engine'].Reset()
            except : pass
            del com_objs['engine']
        if com_objs.has_key('win2')   : del com_objs['win2']
        if com_objs.has_key('doc2')   : del com_objs['doc2']
        if com_objs.has_key('url')    : del com_objs['url']
        if com_objs.has_key('elem')   : del com_objs['elem']
    
    def release(self, com_objs=None):
        com_objs = com_objs or self.com_objs
        self.cur_com_objs = {}
        self.__release__(com_objs)
    
    # -*- -*- -*-
    
    def __check_handle__(self):
        ies_handle = object.__getattribute__(self, 'ies_handle')
        if win32ext.IEHandle.ies_is_invalid(ies_handle) : raise Exception('Error: is not a valid handle "%s"' % ies_handle)
    
    def __getattribute__(self, name):
        check_handle = object.__getattribute__(self, '__check_handle__')
        if name in ['doc2', 'win2', 'engine']:check_handle();return object.__getattribute__(self, 'cur_com_objs').get(name)
        if name not in ['__check_handle__', '__release__', 'release'] and callable(object.__getattribute__(self, name)):check_handle()
        return object.__getattribute__(self, name)
    
    # -*- -*- -*-
    
    def get_ief_rect(self):
        left, top, right, bottom = win32ext.Handle.get_windowrect(self.ief_handle)
        return {'left':left, 'top':top, 'right':right, 'bottom':bottom, 'width':right - left, 'height':bottom - top}
    
    def get_ies_rect(self):
        left, top, right, bottom = win32ext.Handle.get_windowrect(self.ies_handle)
        return {'left':left, 'top':top, 'right':right, 'bottom':bottom, 'width':right - left, 'height':bottom - top}
    
    # -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
    
    def __cur_doc_wait_for_complete__(self, timeout=60, timestep=0.005):
        doc2 = self.cur_com_objs['doc2']
        engine = self.cur_com_objs['engine']
        begin = time.time()
        while(time.time() - begin <= timeout or timeout <= 0):
            #try    :
            if doc2.readyState == 'complete'                                                                                     : break
            if engine.Eval('(function(){try{document.documentElement.doScroll("left");return true;}catch(e){return false;}})()') : time.sleep(0.2);break
            if timeout <= 0                                                                                                      : break
            #except : pass
            time.sleep(timestep)
    
    def wait_for_completed(self, timeout=120, timestep=0.005):
        begin = time.time()
        #self.__cur_doc_wait_for_complete__(timeout=timeout, timestep=timestep)
        doc2 = self.cur_com_objs['doc2']
        while(time.time() - begin <= timeout or timeout <= 0):
            if doc2.readyState == 'complete' : break
            if timeout <= 0                  : break
            time.sleep(timestep)
        return doc2.readyState == 'complete'
    
    def __cur_engine_raise_last_error__(self):
        line = self.cur_com_objs['engine'].Error.Line
        column = self.cur_com_objs['engine'].Error.Column
        description = self.cur_com_objs['engine'].Error.Description
        raise Exception('Error: line: %s; column: %s; description: %s;' % (line, column, description))
    
    def __reinit_cur_com_objs__(self):
        self.cur_com_objs['win2'] = win32ext.IECOM.get_ihtmlwindow2(self.cur_com_objs['doc2'])
        self.cur_com_objs['engine'].Reset()
        self.cur_com_objs['engine'] = None
        self.cur_com_objs['engine'] = win32ext.IECOM.get_engine(self.cur_com_objs['doc2'], self.cur_com_objs['win2'])
    
    def __cur_engine_inject__(self):
        begin = time.time()
        while time.time() - begin <= 30:
            try:
                try    :
                    if self.cur_com_objs['engine'].Eval('Boolean(atweb_api_dispatch)'):
                        self.cur_com_objs['win2'].execScript('atweb_injected=true;')
                        self.cur_com_objs['win2'].execScript('try{Boolean(atweb_api_dispatch)}catch(e){atweb_injected=false;}')
                        if self.cur_com_objs['engine'].Eval('Boolean(atweb_injected)') == False : self.__reinit_cur_com_objs__()
                    return self.cur_com_objs['engine'].Eval('Boolean(atweb_api_dispatch)')
                except : self.__reinit_cur_com_objs__()
                jscore = win32ext.IECOM.get_jscore()
                for line in jscore : self.cur_com_objs['win2'].execScript(line)
                return
            except : time.sleep(0.005)
        raise Exception('Error: inject failed')
    
    def __cur_engine_eval__(self, script):
        self.__cur_doc_wait_for_complete__()
        self.__cur_engine_inject__()
        try    : return self.cur_com_objs['engine'].Eval(script)
        except : self.__cur_engine_raise_last_error__()
    
    # -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
    
    def __top_doc_wait_for_complete__(self):
        try    :
            doc2 = win32ext.IECOM.get_ihtmldocument2(self.ies_handle)
            begin = time.time()
            while(time.time() - begin <= 30): 
                if doc2.readyState == 'complete' : break
                time.sleep(0.005)
            del doc2
        except : pass

    def __com_objs_check_for_complete__(self, doc2, win2):
        doc2.url
        doc2.title
        doc2.readyState
        doc2.parentWindow
        win2.history
        win2.location
        win2.navigator
        win2.navigator.userAgent
        win2.execScript('var qtaweb_com_complete_flag = true;')

    def __init_top_com_objs__(self):
        if self.com_objs.get('url') != None and self.com_objs.get('doc2') != None:
            try    :
                if self.com_objs.get('url') == self.com_objs.get('doc2').url : return
                else                                                         : self.release(self.com_objs)
            except : self.release(self.com_objs)

        self.__top_doc_wait_for_complete__()
        begin = time.time()
        while time.time() - begin <= 30:
            try    :
                self.com_objs['doc2'  ] = win32ext.IECOM.get_ihtmldocument2(self.ies_handle)
                self.com_objs['win2'  ] = win32ext.IECOM.get_ihtmlwindow2(self.com_objs['doc2'])
                self.com_objs['engine'] = win32ext.IECOM.get_engine(self.com_objs['doc2'], self.com_objs['win2'])
                self.com_objs['url'   ] = self.com_objs['doc2'].url
                self.com_objs['frames'] = {}

                self.__com_objs_check_for_complete__(self.com_objs['doc2'], self.com_objs['win2'])
                return
            except : self.release(self.com_objs)
            time.sleep(0.005)
        raise Exception('Error: init top failed')
    
    # -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
    
    def __cur_engine_eval_xpath_select__(self, xpath):
        return self.__cur_engine_eval__('''atweb_api_dispatch('xpath_select', '%s');''' % urllib.quote(xpath))
    
    def __cur_engine_run_set_elem__(self, xpath, cur_elem):
        new_elem = self.__cur_engine_eval_xpath_select__(xpath)
        if new_elem : 
            self.cur_com_objs['engine'].Eval('''atweb_api_buffer=function(buffer){if(buffer){atweb.api.buffer=buffer;}};''')
            self.cur_com_objs['engine'].Run('atweb_api_buffer', [new_elem])
            cur_elem = new_elem
            return cur_elem
        raise Exception('Error: not found element')
    
    def __cur_engine_eval_get_elem_rect__(self, xpath, elem):
        self.__cur_engine_run_set_elem__(xpath, elem)
        return eval(self.__cur_engine_eval__('''atweb_api_dispatch('get_ele_rect', atweb.api.buffer);'''))
    
    def __get_elem_com_objs__(self, xpath):
        elem = self.__cur_engine_eval_xpath_select__(xpath)
        if elem == None:
            raise Exception('Error: get elem failed')

        begin = time.time()
        while time.time() - begin <= 30:
            try    :
                doc2, win2, engine = win32ext.IECOM.get_com_objs(elem.contentWindow)
                self.__com_objs_check_for_complete__(doc2, win2)
                return elem, doc2, win2, engine
            except : pass
            time.sleep(0.005)
        raise Exception('Error: init elem com failed')

    def __set_cur_com_objs__(self, xpaths=[], get_rects=False):
        self.__init_top_com_objs__()
        self.cur_com_objs = self.com_objs
        if get_rects : rects = []
        for xpath in xpaths:
            try:
                if self.cur_com_objs['frames'].has_key(xpath):
                    try:
                        com_objs = self.cur_com_objs['frames'][xpath]
                        if com_objs['doc2'].url == com_objs['url'] :
                            if get_rects : rects.append(self.__cur_engine_eval_get_elem_rect__(xpath, com_objs['elem']))
                            self.cur_com_objs = com_objs;continue
                        else : self.__release__(com_objs)
                    except   : self.__release__(com_objs)
                # -*-
                elem, doc2, win2, engine = self.__get_elem_com_objs__(xpath)
                self.cur_com_objs['frames'].update({xpath:{
                        'elem'   : elem,
                        'url'    : doc2.url,
                        'doc2'   : doc2,
                        'win2'   : win2,
                        'engine' : engine,
                        'frames' : {}}})
                if get_rects : rects.append(self.__cur_engine_eval_get_elem_rect__(xpath, elem))
                self.cur_com_objs = self.cur_com_objs['frames'][xpath]
            except : raise Exception('Error: cross in %s in %s' % (xpath, xpaths))
        if get_rects : return rects
    
    # -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
    
    def set_cur_com_objs_for_frame(self, xpaths=None):
        self.__set_cur_com_objs__(FramesXPathsParser.parse(xpaths))
    
    def set_cur_com_objs_for_elem(self, xpaths, get_rects=False):
        fxpaths = FramesXPathsParser.parse(xpaths)
        expath = fxpaths.pop()
        rects = self.__set_cur_com_objs__(fxpaths, get_rects)
        return fxpaths, expath, rects
    
    def cross_in_by_xpaths(self, xpaths=None):
        self.set_cur_com_objs_for_frame(xpaths)
    
    def inject(self, script):
        self.__cur_doc_wait_for_complete__()
        try    :
            self.cur_com_objs['win2'] = win32ext.IECOM.get_ihtmlwindow2(self.cur_com_objs['doc2'])
            self.cur_com_objs['win2'].execScript(script);return True
        except : pass
        return False
    
    # -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
    
    def xpath_select_list(self, xpaths, timeout=5, timestep=0.005):
        begin = time.time()
        fxpaths, expath = self.set_cur_com_objs_for_elem(xpaths)[:-1]
        elems = []
        while(time.time() - begin <= timeout or timeout <= 0):
            elems_length = self.__cur_engine_eval__('''atweb_api_dispatch('xpath_select_list_length', '%s');''' % urllib.quote(expath))
            if elems_length > 0:
                for i in xrange(elems_length):
                    elem = self.__cur_engine_eval__('''atweb_api_dispatch('xpath_select_list_by_index', %s);''' % i)
                    elems.append((elem, ''.join(fxpaths) + '(%s)[%s]' % (expath, i + 1)))
                break
            if timeout <= 0 : break
            time.sleep(timestep)
        return elems
    
    def xpath_select(self, xpaths, timeout=5, timestep=0.005):
        begin = time.time()
        expath = self.set_cur_com_objs_for_elem(xpaths)[1]
        while(time.time() - begin <= timeout or timeout <= 0):
            elem = self.__cur_engine_eval_xpath_select__(expath)
            if elem         : return elem
            if timeout <= 0 : break
            time.sleep(timestep)
    
    def elem_get_rect(self, xpaths, elem, autoview=False):
        rect = {'top' : 0, 'left' : 0, 'width' : 0, 'height' : 0, 'right' : 0, 'bottom' : 0}
        if autoview : get_rect_count = 2
        else        : get_rect_count = 1
        for i in xrange(get_rect_count):
            xpath, rects = self.set_cur_com_objs_for_elem(xpaths, get_rects=True)[1:]
            rect = self.__cur_engine_eval_get_elem_rect__(xpath, elem)
            for item in rects:
                rect['left'] += item['left']
                rect['top'] += item['top']
            rect['right'] = rect['left'] + rect['width']
            rect['bottom'] = rect['top'] + rect['height']
            if not autoview                                                                                    : break
            self.__cur_engine_run_set_elem__(xpath, elem)
            if not self.__cur_engine_eval__('''atweb_api_dispatch('ele_is_display', atweb.api.buffer);''')     : break
            if self.__cur_engine_eval__('''atweb_api_dispatch('ele_is_hidden', atweb.api.buffer);''')          : break
            left, top, right, bottom = win32ext.Handle.get_windowrect(self.ies_handle)
            if rect['top'] >= 0 and rect['left'] >= 0 and \
               rect['right'] <= (right - left) and rect['bottom'] <= (bottom - top) and \
               self.__cur_engine_eval__('''atweb_api_dispatch('ele_is_in_display_area', atweb.api.buffer);''') : break
            try:elem.scrollIntoView()
            except:pass
            
        #兼容ie10，ie10返回的rect数据为float类，转为int类型
        for key, value in rect.items():
            rect[key] = int(value)
            
        return rect
    
    def elem_highlight(self, xpaths, elem, highlight=1, autoview=True):
        rect = self.elem_get_rect(xpaths, elem, autoview)
        try:
            if highlight == 1:
                win32ext.Handle.highlight(
                    rect=(rect['left'], rect['top'], rect['right'] + 2, rect['bottom'] + 3),
                    line_pixel=2,
                    timestep=0.085,
                    dc_handle=self.ies_handle)
            if highlight == 2:
                xpath = self.set_cur_com_objs_for_elem(xpaths)[1]
                for i in xrange(2):
                    self.__cur_engine_run_set_elem__(xpath, elem)
                    self.__cur_engine_eval__('''atweb_api_dispatch('highlight_show', atweb.api.buffer);''');time.sleep(0.075)
                    self.__cur_engine_eval__('''atweb_api_dispatch('highlight_hide);''')                   ;time.sleep(0.075)
        except:pass
        return rect
    
    def get_ele_rect(self, xpaths, elem, autoview=True, highlight=1):
        return self.elem_highlight(xpaths, elem, highlight, autoview)
    
    # -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
    
    def do_ele_event(self, xpaths, elem, event_type):
        xpath = self.set_cur_com_objs_for_elem(xpaths)[1]
        self.__cur_engine_run_set_elem__(xpath, elem)
        self.__cur_engine_eval__('''atweb_api_dispatch('do_ele_event', atweb.api.buffer, '%s');''' % event_type)
    
    def get_ele_attribute(self, xpaths, elem, name):
        xpath = self.set_cur_com_objs_for_elem(xpaths)[1]
        self.__cur_engine_run_set_elem__(xpath, elem)
        return self.__cur_engine_eval__('''atweb_api_dispatch('get_ele_attribute', atweb.api.buffer, '%s')''' % name)
    
    def get_ele_attributes(self, xpaths, elem):
        xpath = self.set_cur_com_objs_for_elem(xpaths)[1]
        self.__cur_engine_run_set_elem__(xpath, elem)
        return self.__cur_engine_eval__('''atweb_api_dispatch('get_ele_attributes', atweb.api.buffer)''')
    
    def set_ele_attribute(self, xpaths, elem, name, value):
        xpath = self.set_cur_com_objs_for_elem(xpaths)[1]
        self.__cur_engine_run_set_elem__(xpath, elem)
        self.__cur_engine_eval__('''atweb_api_dispatch('set_ele_attribute', atweb.api.buffer, '%s', '%s')''' % (name, value))
    
    def get_ele_currentStyle(self, xpaths, elem, name):
        xpath = self.set_cur_com_objs_for_elem(xpaths)[1]
        self.__cur_engine_run_set_elem__(xpath, elem)
        return self.__cur_engine_eval__('''atweb_api_dispatch('get_ele_currentStyle', atweb.api.buffer, '%s')''' % name)
    
    def get_ele_currentStyles(self, xpaths, elem):
        xpath = self.set_cur_com_objs_for_elem(xpaths)[1]
        self.__cur_engine_run_set_elem__(xpath, elem)
        return self.__cur_engine_eval__('''atweb_api_dispatch('get_ele_currentStyles', atweb.api.buffer)''')
    
    def set_ele_style(self, xpaths, elem, name, value):
        xpath = self.set_cur_com_objs_for_elem(xpaths)[1]
        self.__cur_engine_run_set_elem__(xpath, elem)
        self.__cur_engine_eval__('''atweb_api_dispatch('set_ele_style', atweb.api.buffer, '%s', '%s')''' % (name, value))
    
    # -*- -*- -*-
    
    def get_ele_HTML(self, xpaths, elem):
        xpath = self.set_cur_com_objs_for_elem(xpaths)[1]
        self.__cur_engine_run_set_elem__(xpath, elem)
        return self.__cur_engine_eval__('''atweb_api_dispatch('get_ele_HTML', atweb.api.buffer)''')
    
    def get_ele_outerHTML(self, xpaths, elem):
        xpath = self.set_cur_com_objs_for_elem(xpaths)[1]
        self.__cur_engine_run_set_elem__(xpath, elem)
        return self.__cur_engine_eval__('''atweb_api_dispatch('get_ele_outerHTML', atweb.api.buffer)''')
    
    # -*- -*- -*-
    
    def get_ele_innerHTML(self, xpaths, elem):
        xpath = self.set_cur_com_objs_for_elem(xpaths)[1]
        self.__cur_engine_run_set_elem__(xpath, elem)
        return self.__cur_engine_eval__('''atweb_api_dispatch('get_ele_innerHTML', atweb.api.buffer)''')
    
    def set_ele_innerHTML(self, xpaths, elem, html) : elem.innerHTML = html
    
    # -*- -*- -*-
    
    def get_ele_innerText(self, xpaths, elem):
        xpath = self.set_cur_com_objs_for_elem(xpaths)[1]
        self.__cur_engine_run_set_elem__(xpath, elem)
        return self.__cur_engine_eval__('''atweb_api_dispatch('get_ele_innerText', atweb.api.buffer)''')
    
    def set_ele_innerText(self, xpaths, elem, text) : elem.innerText = text
    
    # -*- -*- -*-
    
    def get_current_window_scrollInfo(self, xpaths=None):
        self.set_cur_com_objs_for_frame(xpaths)
        return self.__cur_engine_eval__('''atweb_api_dispatch('get_current_window_scrollInfo')''')
    
    def set_current_window_scrollTop(self, xpaths=None, scroll_top=0):
        self.set_cur_com_objs_for_frame(xpaths)
        self.__cur_engine_eval__('''atweb_api_dispatch('set_current_window_scrollTop', %s)''' % scroll_top)
    
    def set_current_window_scrollLeft(self, xpaths=None, scroll_left=0):
        self.set_cur_com_objs_for_frame(xpaths)
        self.__cur_engine_eval__('''atweb_api_dispatch('set_current_window_scrollLeft', %s)''' % scroll_left)
    
    # -*- -*- -*-
    
    def cookies_all(self, xpaths=None):
        self.set_cur_com_objs_for_frame(xpaths)
        return self.__cur_engine_eval__('''atweb_api_dispatch('cookies_all')''')
    
    def cookies_has(self, xpaths=None, key=None):
        if key == None : return
        self.set_cur_com_objs_for_frame(xpaths)
        return self.__cur_engine_eval__('''atweb_api_dispatch('cookies_has', '%s')''' % key)
    
    def cookies_get(self, xpaths=None, key=None):
        if key == None : return
        self.set_cur_com_objs_for_frame(xpaths)
        return self.__cur_engine_eval__('''atweb_api_dispatch('cookies_get', '%s')''' % key)
    
    def cookies_del(self, xpaths=None, key=None):
        if key == None : return
        self.set_cur_com_objs_for_frame(xpaths)
        return self.__cur_engine_eval__('''atweb_api_dispatch('cookies_del', '%s')''' % key)
    
    def cookies_clean(self, xpaths=None):
        self.set_cur_com_objs_for_frame(xpaths)
        self.__cur_engine_eval__('''atweb_api_dispatch('cookies_clean')''')
    
    def cookies_set(self, xpaths=None, key=None, value=None, expires_offset='', path='', domain='', secure=''):
        if key == None or value == None : return
        self.set_cur_com_objs_for_frame(xpaths)
        self.__cur_engine_eval__('''atweb_api_dispatch('cookies_set', '%s', '%s', '%s', '%s', '%s', '%s')''' % (key, value, expires_offset, path, domain, secure))
    
    # -*- -*- -*-
    
    def spy_start(self, xpaths=None):
        self.set_cur_com_objs_for_frame(xpaths)
        self.__cur_engine_eval__('''atweb_api_dispatch('spy_start')''')
    
    def spy_stop(self, xpaths=None):
        self.set_cur_com_objs_for_frame(xpaths)
        self.__cur_engine_eval__('''atweb_api_dispatch('spy_stop')''')
    
    def spy_get_elem(self, xpaths=None):
        self.set_cur_com_objs_for_frame(xpaths)
        return self.__cur_engine_eval__('''atweb_api_dispatch('get_spy_elem')''')
    
    def spy_get_elem_xpath(self, xpaths=None):
        self.set_cur_com_objs_for_frame(xpaths)
        return self.__cur_engine_eval__('''atweb_api_dispatch('get_spy_elem_xpath')''')
    
    # -*- -*- -*-
    
    def get_top_readyState(self):
        try:
            doc2 = win32ext.IECOM.get_ihtmldocument2(self.ies_handle)
            readyState = doc2.readyState
            del doc2
            return readyState
        except:pass
    
    def get_top_url(self):
        try:
            doc2 = win32ext.IECOM.get_ihtmldocument2(self.ies_handle)
            url = doc2.url
            del doc2
            return url
        except:pass
    
    def get_top_title(self):
        try:
            doc2 = win32ext.IECOM.get_ihtmldocument2(self.ies_handle)
            title = doc2.title
            del doc2
            return title
        except:pass


# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- IEDrivers

class IEDrivers:
    
    items = {} # { ies_handle<int> : instance<IEDriver> }
    
    @classmethod
    def remove(cls, obj):
        if isinstance(obj, int)      :ies_handle = obj
        if isinstance(obj, IEDriver) :ies_handle = obj.ies_handle
        if cls.items.has_key(ies_handle):
            cls.items.get(ies_handle).release()
            del cls.items[ies_handle]
            #gc.collect()
    
    @classmethod
    def remove_all(cls):
        for ies_handle in cls.items.keys() : cls.remove(ies_handle)
    
    @classmethod
    def remove_invalid(cls):
        for ies_handle in cls.items.keys():
            if win32ext.Handle.is_invalid(ies_handle) : cls.remove(ies_handle)
    
    @classmethod
    def append(cls, obj):
        if isinstance(obj, IEDriver):
            if cls.items.has_key(obj.ies_handle) : del obj
            else                                 : cls.items.update({obj.ies_handle:obj})
        cls.remove_invalid()
    
    @classmethod
    def select(cls, ies_handle):
        if isinstance(ies_handle, int) : return cls.items.get(ies_handle, IEDriver(ies_handle))
    
    # -*-  -*-  -*-
    
    @classmethod
    def get(cls, ies_handle):
        return cls.select(ies_handle)
    
    @classmethod
    def open_url_by_ie(cls, url=None):
        info = win32ext.IEProcess.create_ie_process(url);time.sleep(0.5)
        return cls.get(info[win32ext.IEConst.IES_Handle])

    @classmethod
    def find(cls, url=None, title=None, onlyIE=True, index=1, timeout=5, timestep=0.005):
        begin = time.time()
        if url == None and title == None : return
        while(time.time() - begin <= timeout or timeout <= 0):
            if onlyIE : all_iefs = win32ext.IEHandle.get_all_iefs(win32ext.IEConst.IEF_ClassName)
            else      : all_iefs = win32ext.IEHandle.get_all_iefs()
            match_index = 0
            for iefs in all_iefs:
                ies_handle = iefs[win32ext.IEConst.IES_Handle]
                match_obj = None
                try:
                    doc2 = win32ext.IECOM.get_ihtmldocument2(ies_handle)
                    cur_url, cur_title = doc2.url, doc2.title;del doc2
                    if url != None and title == None:
                        if url == cur_url or re.match(url, cur_url):
                            match_index += 1
                            if match_index == index : match_obj = cls.get(ies_handle)
                    if url == None and title != None:
                        if title == cur_title or re.match(title, cur_title):
                            match_index += 1
                            if match_index == index : match_obj = cls.get(ies_handle)
                    if url != None and title != None:
                        if (url == cur_url or re.match(url, cur_url)) and (title == cur_title or re.match(title, cur_title)):
                            match_index += 1
                            if match_index == index : match_obj = cls.get(ies_handle)
                except:pass
                if match_obj : return match_obj
            if timeout <= 0  : return
            time.sleep(timestep)

