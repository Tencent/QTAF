# -*- coding: utf-8 -*-
'''
资源管理系统使用接口

使用方法示例::

    #查询资源
    accmgr = ResourceManager('account')
    print accmgr.query().filter({'vip':'True'}).count()
    for it in accmgr.query('pcFriend1700').filter({'vip':'True'}):
        print it.resource_id, type(it.resource_id), it.group, it.res_type, it.status, it.acquired
        
    #申请释放资源
    session = accmgr.create_session(60, EnumRequestPriority.High)
    try:
        resources = session.acquire('pcFriend1700', {'vip':'True'}, 1, 1, timeout=10)
        session.release(resources)        
    finally:
        session.destroy()

    #申请释放资源（异步）
    session = accmgr.create_session(60, EnumRequestPriority.High)
    try:
        request = session.async_acquire('pcFriend1700', {'vip':'True'}, 1, 1)
        request.wait_result()
        request.release_all()      
    finally:
        session.destroy()
        
    #新增和移除移除资源
    resource = accmgr.add('pcFriend1700', EnumResourceStatus.OK, {"vip":True})
    print resource.resource_id
    accmgr.remove(resource)
    
    #更新资源属性
    resource = accmgr.query('qt4a', {"vip":True})[0]
    resource["xxx"] = 222
    del resource["vip"]
    resource.save()
    
    #更新资源状态
    resource = accmgr.query('qt4a', {"vip":True})[0]
    resource.set_status(EnumResourceStatus.OK, "eeelin test")
    
'''

#2015/06/24 eeelin 新建

import getpass
import socket
from testbase.platform.jsonrpc import ServerProxy, Error
from testbase.conf import settings
from testbase.testresult import EnumLogLevel
from testbase import logger

RESOURCE_ERROR = -1

_resapi = None


class EnumResourceStatus(object):
    '''资源状态值
    '''
    UNKNOWN, OK, BROKEN = 'unknown', 'ok', 'broken'
    
class EnumSessionPriority(object):
    '''会话优先级
    '''
    High, Medium, Low = 30, 20, 10
    
class _ResMgrApi(object):
    '''资源管理系统接口
    '''
    class _LazyServerProxy(object):
        
        def __init__(self, parent, name):
            self.__name = name
            self.__parent = parent
        
        def __getattr__(self, attrname ):
            obj = ServerProxy(settings.RESMGR_JSONRPC_URL+'%s/'%self.__name, encoding='utf8')
            setattr(self.__parent, self.__name, obj)
            attr = getattr(obj, attrname)
            del self.__parent
            del self.__name
            return attr
        
    def __init__(self):
        self.resource = self._LazyServerProxy(self, 'resource')
        self.session = self._LazyServerProxy(self, 'session')
        self.request = self._LazyServerProxy(self, 'request')
        self.pool = self._LazyServerProxy(self, 'pool')
        self.dypool = self._LazyServerProxy(self, 'dypool')
        
class _ResourceProperties(dict):
    '''资源属性
    '''
    def __init__(self, api, restype, resource_id, prop_dict ):
        '''构造函数
        '''
        self._api = api
        self._restype = restype
        self._resid = resource_id
        self.update(prop_dict)
        self._valid = True
        self._props_updated = {}
        
    def save(self):
        '''保存修改
        '''
        if not self._valid:
            raise RuntimeError("已失效")
        self._api.resource.update_resource_properties(self._restype, self._resid, self._props_updated)
        self._props_updated = {}
        
    def __setitem__(self, name, value):
        self._props_updated[name] = value
        super(_ResourceProperties, self).__setitem__(name, value)
        
    def __delitem__(self, name):
        raise RuntimeError("不支持删除属性")
        
    
class Resource(object):
    '''一个资源
    '''
    def __init__(self, api, restype, resid, group, status, session_id, pool_id, properties ):
        '''构造函数
        
        :param resid: 资源ID
        :type resid: string
        :param data: 资源数据
        :type data: dict
        :param request: 对应占用此资源的请求
        :type request: Request
        '''
        self._api = api
        self._restype = restype
        self._resid = resid
        self._group = group
        self._status = status
        self._session_id = session_id
        self._pool_id = pool_id
        self._props = _ResourceProperties(self._api, self._restype, resid, properties)
        
    def __str__(self):
        return '<Resource type:%s id:%s>' % (self._restype, self._resid)
        
    def __eq__(self, resource ):
        if isinstance(resource, Resource):
            return self.resource_id == resource.resource_id
        else:
            return False
        
    @property
    def resource_id(self):
        '''资源ID
        
        :returns: string
        '''
        return self._resid
    
    @property
    def group(self):
        '''分组名
        
        :returns: string
        '''
        return self._group
    
    @group.setter
    def group(self, group_name ):
        '''修改分组
        
        :param group_name: 分组名
        :type group_name: stirng
        '''
        self._api.resource.change_resource_group(self._restype, self._resid, group_name)
        self._group = group_name
    
    @property
    def res_type(self):
        '''资源类型
        
        :returns: string
        '''
        return self._restype
        
    @property
    def status(self):
        '''状态
        
        :returns: string    
        '''
        return self._status
    
    @property
    def properties(self):
        '''资源属性
        '''
        return self._props
    
    @properties.setter
    def properties(self, props ):
        '''替换资源属性
        '''
        self._api.resource.set_resource_properties(self._restype, self._resid, props)        
        self._props._valid = False
        self._props = _ResourceProperties(self._api, self._restype, self._resid, props)
        
    @property
    def acquired(self):
        '''资源是否被占用
        
        :returns: boolean
        '''
        return self._session_id != None
    
    @property
    def session_id(self):
        '''对应的会话ID
        '''
        return self._session_id
    
    @property
    def pool(self):
        '''对应的资源池
        '''
        return ResourcePoolManager().get(self.res_type, self._pool_id)

    def update_status(self, status, event_info="", event_source=None ):
        '''更新资源状态
        '''
        if event_source is None:
            event_source = '%s@%s'%(getpass.getuser(), socket.gethostname())
        self._api.resource.update_resource_status(self._restype, self._resid, self.status, status, event_source, event_info)
        self._status = status

class _QueryResult(object):
    '''查询结果
    '''
    def __init__(self, resmgr, group, status, properties, pool_id ):
        '''构造函数
        '''
        self._resmgr = resmgr
        self._cond = {}
        if group:
            self._cond['res_group'] = group
        if status:
            self._cond['status'] = status
        if properties:
            self._cond['properties'] = properties
        if pool_id:
            self._cond['pool_id'] = pool_id

    def __iter__(self):
        return self._resmgr._query(self._cond).__iter__()
    
    def __len__(self):
        return self.count()
    
    def __getitem__(self, idx ):
        return self._resmgr._query(self._cond)[idx]
    
    def count(self):
        '''结果数目
        '''
        return self._resmgr._query_count(self._cond)

class Session(object):
    '''会话
    '''
    def __init__(self, api, sessionid, restype ):
        '''构造函数
        '''
        self._api = api
        self._restype = restype
        self._sessionid = sessionid
        
    def __str__(self):
        return '<Session id:%s>' % self._sessionid
    
    def destroy(self):
        '''销毁会话，释放该会话的全部资源
        '''
        self._api.session.destroy_session(self._sessionid)

    def hold(self, timeout ):
        '''保持会话
        
        :param timeout: 超时时间
        :type timeout: int
        '''
        self._api.session.hold_session(self._sessionid, timeout)
        
    def acquire(self, group=None, cond={}, pool=None ):
        '''申请资源
        
        :param group: 资源分组
        :type group: string
        :param cond: 申请条件
        :type cond: dict
        :returns: 资源列表
        '''
        if pool:
            return pool._acquire(self._sessionid, group, cond)
        
        if self._restype is None:
            raise RuntimeError("session with unknown restype could not 'acquire' resource")
            
        try:
            resource = self._api.request.acquire_resource(self._sessionid, self._restype, group, cond)
            return Resource ( self._api,
                              self._restype, 
                          resource['id'], 
                          resource['res_group'], 
                          resource['status'], 
                          resource['session_id'],
                          resource['pool_id'],
                          resource['properties'])
        
        except Error, e:
            if e.code == 1 and settings.LOG_RESOURCE_NOT_READY:
                logger.log(EnumLogLevel.RESNOTREADY, 'resource(type="%s", group="%s", condition=%s) is not ready' % (self._restype, group, cond))
            raise
        
    def release(self, resource, pool=None):
        '''释放资源
        
        :param resource: 一个资源
        :type resource: Resource
        '''
        if pool:
            return pool._release(self._sessionid, resource.resource_id)
        
        if self._restype is None:
            raise RuntimeError("session with unknown restype could not 'release' resource")
        return self._api.request.release_resource(self._sessionid, self._restype, resource.resource_id)
    
    
    
class ResourceManager(object):
    '''资源管理系统使用接口
    '''
    
    def __init__(self, res_type ):
        '''构造函数
        
        :param res_type: 资源类型
        :type res_type: string
        '''
        self._res_type = res_type
        self._api = _ResMgrApi()
        
    @property
    def res_type(self):
        '''资源类型
        '''
        return self._res_type

    def query(self, group=None, status=None, properties={}, pool_id=None):
        '''查询资源
        
        :param group: 分组，为空则表示不匹配此条件
        :type group: string
        :param status: 状态，为空则表示不匹配此条件
        :type status: string
        :param properties: 属性条件，为空则表示不匹配此条件
        :type properties: dict
        :returns: QueryResult
        '''
        return _QueryResult(self, group, status, properties, pool_id)
    
    def _query(self, cond ):
        '''查询资源
        '''
        results = self._api.resource.query_resource(self._res_type, cond )
        for it in results:
            yield Resource(self._api,
                           self._res_type, 
                           it['id'], 
                           it['res_group'], 
                           it['status'], 
                           it['session_id'],
                           it['pool_id'], 
                           it['properties'])
        
    def _query_count(self, cond ):
        '''查询资源数目
        '''
        return self._api.resource.query_resource_count(self._res_type, cond)
    
    def get(self, resource_id ):
        '''获取一个资源
        
        :param resource_id: 资源ID
        :type resource_id: string
        '''
        info = self._api.resource.get_resource(self._res_type, resource_id)
        return Resource ( self._api,
                          self._res_type, 
                          info['id'], 
                          info['res_group'], 
                          info['status'], 
                          info['session_id'],
                          info['pool_id'],
                          info['properties'])
        
    def add(self, group, props ):
        '''新增一个资源
        
        :param group: 分组
        :type group: string
        :param status: 状态
        :type status: string
        :param props: 资源属性
        :type props: dict
        '''
        resource_id = self._api.resource.add_resource(self._res_type, group, props)
        return self.get(resource_id)
    
    def add_if_not_exist(self, query_props, group, props ):
        '''如果资源存在则更新属性并返回对应的资源，否则新增一个资源
        
        :param props: 查询的资源属性
        :type props: dict
        :param group: 分组
        :type group: string
        :param status: 状态
        :type status: string
        :param props: 资源属性
        :type props: dict
        '''
        resource_id = self._api.resource.add_resource_if_not_exist(self._res_type, query_props, group, props)
        return self.get(resource_id)
    
    def remove(self, resource ):
        '''移除一个资源
        
        :param resources: 一个资源
        :type resources: Resource
        '''
        self._api.resource.remove_resource(self._res_type, resource.resource_id)    
        
    def create_session(self, timeout, user=None, domain=None ):
        '''创建一个会话
        
        :param timeout: 会话超时时间
        :type timeout: int
        :param user: 用户名，默认为当前用户名
        :type user: string
        :param domain: 域名，默认为当前主机名
        :type domain: string
        :returns: Session
        '''
        return create_session(self._res_type, timeout, user, domain)
        
    def destroy_session_by_user(self, user, domain):
        '''根据用户销毁会话，并释放对应的资源
        '''
        return destroy_session_by_user(user, domain)
    
    def destroy_session_by_domain(self, domain ):
        '''根据域销毁会话，并释放对应的资源
        '''
        return destroy_session_by_domain(domain)
        
class ResourcePool(object):
    '''资源池
    '''
    def __init__(self, api, res_type, pool_id, pool_url ):
        '''构造函数
        '''
        self._api = api
        self._res_type = res_type
        self._pool_id = pool_id
        self._pool_url = pool_url
        self._pool = None
        
    def __str__(self):
        return '<ResourcePool id:%s>' % self._pool_id
    
    @property
    def pool_id(self):
        '''资源池ID
        
        :returns: string
        '''
        return self._pool_id
    
    @property
    def res_type(self):
        '''资源类型
        
        :returns: string
        '''
        return self._res_type
    
    def destroy(self):
        '''销毁资源池
        '''
        self._api.pool.destroy_resource_pool(self._res_type, self._pool_id)
        
    @property
    def resources(self):
        '''资源列表
        '''
        return ResourceManager(self._res_type).query(pool_id=self._pool_id)
        
    def _acquire(self, session_id, group, cond={}):
        '''从资源池中申请资源
        '''
        if not self._pool:
            self._pool = ServerProxy(self._pool_url, encoding='utf8')
        try:
            resource = self._pool.acquire_resource(session_id, self._res_type, group, cond)
            return Resource ( self._api,
                              self._res_type,
                              resource['id'], 
                              resource['res_group'], 
                              resource['status'], 
                              resource['session_id'],
                              resource['pool_id'],
                              resource['properties'])
                    
        except Error, e:
            if e.code == 1 and settings.LOG_RESOURCE_NOT_READY:
                logger.log(EnumLogLevel.RESNOTREADY, 'resource(type="%s", group="%s", condition=%s) is not ready' % (self._res_type, group, cond))
            raise    

    def _release(self, session_id, resource_id):
        '''从资源池中释放资源
        '''
        if not self._pool:
            self._pool = ServerProxy(self._pool_url, encoding='utf8')
        self._pool.release_resource(session_id, self._res_type, resource_id)
            
class ResourcePoolManager(object):
    '''资源池管理
    '''
    def __init__(self):
        '''构造函数
        '''
        self._api = _ResMgrApi()
        
    def get(self, res_type, pool_id ):
        '''获取对应的资源池
        '''
        pool_info = self._api.pool.get_resource_pool(res_type, pool_id)
        return ResourcePool(self._api, res_type, pool_info['id'], pool_info['url'])
            
    def create(self, res_type, group, cond, max_cnt, min_cnt, owner):
        '''创建资源池

        :param res_type: 资源类型
        :type res_type: string
        :param group: 分组
        :type group: string
        :param cond: 资源属性条件
        :type cond: dict
        :param max_cnt: 最大数
        :type max_cnt: int
        :param min_cnt: 最小数
        :type min_cnt: int
        :param owner: 资源池所属人
        :type owner: string
        :returns: ResourcePool
        '''
        pool_info = self._api.pool.create_resource_pool(res_type, group, cond, max_cnt, min_cnt, owner)
        return ResourcePool(self._api, res_type, pool_info['id'], pool_info['url'])
    
    def destroy(self, pool):
        '''销毁资源池
        '''
        self._api.pool.destroy_resource_pool(pool.res_type, pool.pool_id)
    
    def batch_create(self, pool_constraints):
        '''批量创建资源池
        '''
        pool_infos = self._api.pool.batch_create_resource_pool(pool_constraints)
        pools = []
        for idx, pool_info in enumerate(pool_infos):
            pool_constraint = pool_constraints[idx]
            pools.append(ResourcePool(self._api, pool_constraint['res_type'], pool_info['id'], pool_info['url']))
        return pools
    
    def batch_destroy(self, pools):
        '''批量销毁资源池
        '''
        self._api.pool.batch_destroy_resource_pool([pool.pool_id for pool in pools])


class DynamicResource(object):
    '''一个资源
    '''
    def __init__(self, pool, resid, properties, session_id ):
        '''构造函数
        '''
        self._pool = pool
        self._resid = resid
        self._props = properties
        self._session_id = session_id
        
    def __str__(self):
        return '<DynamicResource id:%s>' % (self._resid)
        
    def __eq__(self, resource ):
        if isinstance(resource, Resource):
            return self.resource_id == resource.resource_id
        else:
            return False
        
    @property
    def resource_id(self):
        '''资源ID
        
        :returns: string
        '''
        return self._resid
    
    @property
    def properties(self):
        '''资源属性
        '''
        return self._props
    
    @property
    def acquired(self):
        '''资源是否被占用
        
        :returns: boolean
        '''
        return self._session_id != None
    
    @property
    def session_id(self):
        '''对应的会话ID
        '''
        return self._session_id
    
    @property
    def pool(self):
        '''对应的资源池
        '''
        return self._pool
        
class DynamicResourcePool(object):
    '''动态资源池
    '''
    def __init__(self, api, pool_id ):
        self._api = api
        self._pool_id = pool_id
        
    def __str__(self):
        return '<DynamicResourcePool id:%s>' % self._pool_id
    
    @property
    def pool_id(self):
        '''资源池ID
        
        :returns: string
        '''
        return self._pool_id
    
    @property
    def resources(self):
        '''资源列表
        '''
        resources = []
        for it in self._api.dypool.query_resource(self._pool_id):
            resources.append(DynamicResource(self, it['id'], it['properties'], it['session_id']))
        return resources
    
    def destroy(self):
        '''销毁资源池
        '''
        self._api.dypool.destroy_resource_pool(self._pool_id)
    
    def get_resource(self, resource_id ):
        '''查询资源
        '''
        for it in self.resources:
            if it.resource_id == resource_id:
                return it
            
    def add_resource(self, resource_prop ):
        '''新增资源
        '''
        resource_id = self._api.dypool.add_resource(self._pool_id, resource_prop)
        return DynamicResource(self, resource_id, resource_prop, None)
    
    def remove_resource(self, resource ):
        '''移除资源
        '''
        self._api.dypool.remove_resource(self._pool_id, resource.resource_id)
        
    def query_resource(self, cond ):
        '''根据条件查询资源
        '''
        resources = []
        for it in self._api.dypool.query_resource(self._pool_id, cond):
            resources.append(DynamicResource(self,
                                             it['id'],
                                             it['properties'], 
                                             it['session_id']))
        return resources
        
    def _acquire(self, session_id, group, cond={}):
        '''从资源池中申请资源
        '''
        try:
            resource = self._api.dypool.acquire_resource(session_id, self._pool_id, cond)
            return DynamicResource(self, 
                                   resource['id'], 
                                   resource['properties'], 
                                   resource['session_id'])
        except Error, e:
            if e.code == 1 and settings.LOG_RESOURCE_NOT_READY:
                logger.log(EnumLogLevel.RESNOTREADY, 'resource(dynamic, group="%s", condition=%s) is not ready' % (group, cond))
            raise    
        
    def _release(self, session_id, resource_id):
        '''从资源池中释放资源
        '''
        self._api.dypool.release_resource(session_id, self._pool_id, resource_id )

        
class DynamicResourcePoolManager(object):
    '''动态资源池管理
    '''
    def __init__(self):
        '''构造函数
        '''
        self._api = _ResMgrApi()

    def create(self, resource_list ):
        '''创建资源池
        '''
        pool_id = self._api.dypool.create_resource_pool(resource_list)
        return DynamicResourcePool(self._api, pool_id)
    
    def get(self, pool_id ):
        '''查询资源池
        '''
        return DynamicResourcePool(self._api, pool_id)

def create_session(restype=None, timeout=None, user=None, domain=None):
    '''创建会话
    '''
    global _resapi
    if _resapi is None:
        _resapi = _ResMgrApi()
    if user is None:
        user = getpass.getuser()
    if domain is None:
        domain = socket.gethostname()
    if timeout is None:
        from testbase import context
        curr_tc = context.current_testcase()
        if curr_tc:
            timeout = curr_tc.timeout*60 + 300 + 5
        else:
            timeout = 60
    sessionid = _resapi.session.create_session(user, domain, timeout)
    return Session(_resapi, sessionid, restype)

def destroy_session( session ):
    '''销毁会话
    '''
    session.destroy()

def destroy_session_by_user( user, domain):
    '''根据用户销毁会话，并释放对应的资源
    '''
    global _resapi
    if _resapi is None:
        _resapi = _ResMgrApi()
    _resapi.session.destroy_session_by_user(user, domain)

def destroy_session_by_domain( domain ):
    '''根据域销毁会话，并释放对应的资源
    '''
    global _resapi
    if _resapi is None:
        _resapi = _ResMgrApi()
    _resapi.session.destroy_session_by_domain(domain)
