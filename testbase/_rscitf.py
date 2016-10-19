# -*- coding: UTF-8 -*-
'资源平台接口模块，内部使用'
'''
功能：资源申请函数，申请后的资源销毁函数
变量：1）设定web_url：server生成的XML文件的服务脚本
      2)globalres：全局变量，申请到的资源
注：其他语言申请资源，可以按标准的URL写法，(区分大小写)，申请个数默认为1，
如需要设定，请加上num=10,完整的URL如下,依次为：用户名，密码，查询条件，数量，字典属性)
http://10.6.58.46:8888/cgi-bin/index.py?username=yourname&password=pwd&command=query&num=10&vip=True
3)需要注销变量，加上变量&command=release
4)查看资源状态，加上变量&command=query
'''

#10/11/25 leefang     created
#10/11/25 aaronlai    去除Error模块的import
#10/12/06 aaronlai    使用hashlib模块替换md5模块
#10/12/08 aaronlai    修改urlopen函数的参数
#12/06/14 jonliang    迁移至testbase并重命名

from xml.dom import minidom
import urllib
#import md5
import hashlib
import socket
import json

_version_ = '1.0.0.2'
web_url = 'http://testing.sng.local:80/cgi-bin/resource/index.py' #定义全局变量
globalres = {}
gUserName = 'fredhu'
gPassWord = '123456'
gUser = 'gresname'
gRespwd = 'grespwd'
hostname = socket.gethostname()

class ResourceError(Exception):
    '''测试资源异常
    '''
    pass

#将字典编码为utf8格式
def encodeDictToUtf8(dictData):

    encodeData = {}
    if type(dictData)<>dict:
        return encodeData
    for k, v in dictData.items(): 
        encodeData[k.encode('utf-8')] = v.encode('utf-8')
    return encodeData

#申请资源返回json数据格式            
def jsonParse(data):
    dics = []
    if type(data) != list:
        data = [data]     
    resCount = len(data)
    for index in range(resCount):
        attr = data[index]
        resId = attr.get('id', 0)
        attrDict = attr.get('attr',{})
        globalres[resId] = encodeDictToUtf8(attrDict)
        dics.append((resId, encodeDictToUtf8(attrDict)))
    return dics

#改成字典形式{1:{{}}
#groupName 群组属性
def ApplyRes(attrDic, cnt=1, groupName='tuia', blacklist=[], resType='1'):
    #2011/03/25 aaronlai    修改异常提示
    #2011/06/15 aaronlai    增加资源类型
    #2011/11/29 aaronlai    修改提示内容
    global web_url,gUserName,gPassWord,gUser,gRespwd,hostname
    surl = web_url + '?' + gUser + "=" + md5string(gUserName) + "&"\
           + gRespwd + "=" + md5string(gPassWord)  + "&command=apply&cnt=" + str(cnt)\
           + "&hostname=" + hostname +'&groupName=' + groupName + '&resType=' + str(resType)
    params = urllib.urlencode(attrDic)
    content = None
    surl += "&"+params
    if len(blacklist)>0:
        for black in blacklist:
            if black<>'':
                surl += '&cb_lack='+black
    print surl
    try: content = urllib.urlopen(surl, proxies={})
    except: raise ResourceError('网络连接错误!') #return False
    if not content: 
        raise ResourceError('urlopen返回空内容!') #return False
#    xmlcontent = content.read()
#    appdic = parseXML(xmlcontent)
#    
#    if not appdic: 
#        raise ResourceError('资源申请失败,查看原因:\n\t\"%s\"!' % xmlcontent) #return False
#    else: 
#        return m_res(appdic)
    
    result = content.read()
    try:
        jsondata = json.loads(result)
    except:
        raise ResourceError('返回数据不为json格式!%s'%result) 
    if jsondata.get('isSuccess')==1:
        jsonparsedata = []
        data = jsondata.get('data','None')
        if data<>'None':
            jsonparsedata = jsonParse(data)
        return m_res(jsonparsedata)

def QueryRes(attrDic, cnt = 1):
    #2011/03/25 aaronlai    修改异常提示
    #2011/12/02 aaronlai    修改提示内容
    global web_url,gUserName,gPassWord,gUser,gRespwd
    surl = web_url + '?' + gUser + "=" + md5string(gUserName) +'&'+ gRespwd + "=" + md5string(gPassWord) + "&command=query&cnt=" + str(cnt) + "&hostname=" + hostname
    params=urllib.urlencode(attrDic)
    content = None
    try: 
        content = urllib.urlopen(surl + "&" + params, proxies={} )
    except: 
        raise ResourceError('网络连接错误!')
    if not content: 
        raise ResourceError('urlopen返回空内容!') #return False
    xmlcontent = content.read()
    appdic = parseXML(xmlcontent,False)
    return mdic(appdic)

def ReleaseRes(idList = []):
    #2011/03/02 aaronlai    当释放资源失败抛出异常
    #2011/03/25 aaronlai    修改异常提示
    global web_url,gUserName,gPassWord,gUser,gRespwd,hostname
    cstr = ''
    if type(idList) == list:
        surl = web_url + '?' + gUser + '=' + md5string(gUserName) + "&" + gRespwd + "=" + md5string(gPassWord) + '&command=release' + "&"
        plist = globalres.keys()
        idList = idList or plist
        for pid in idList:
            if pid in plist: cstr += 'id=%s&' %pid
        
        if cstr == '': return True
        surl += cstr + "&hostname=" + hostname
        try: 
            content = urllib.urlopen(surl, proxies={})
        except: 
            raise ResourceError('网络连接错误!') #return False
        if(out_result(content)): return True
        else: raise ResourceError('释放资源失败!')
    else: raise TypeError('传入参数必须为列表!') #return False

#不提供此接口，兼容性
def QueryAndReleaseRes(attrDic, cnt = 1):
    return True

def out_result(usock):
    xmldoc = minidom.parse(usock) 
    if xmldoc.getElementsByTagName('returndata'):
        usock.close()
        result = xmldoc.getElementsByTagName('returndata')[0].firstChild.data
        return eval(result)
    else:
        return True
   
def parseXML(xmlcontent, flag = True):
    xmldoc = minidom.parseString(xmlcontent)
#    xmldoc = minidom.parse(xmlcontent)
    if not xmldoc.getElementsByTagName('resource'):
        return False
    else:
        dics = []
        for tm in xmldoc.getElementsByTagName('param'):
            indic = {}
            for q in tm.getElementsByTagName('title'):
                qdata = q.firstChild.data
                if qdata == '':continue
                if q.attributes["name"].value == 'id':
                    gid = changetype(qdata,'int')
                else:
                    if flag:
                        indic[q.attributes["name"].value.encode('utf-8')] = changetype(qdata.encode('utf-8'),q.attributes["datatype"].value)
                    else:
                        indic[q.attributes["name"].value.encode('utf-8')] = changetype(qdata.encode('utf-8'),'int')
            dics.append((gid,indic))
            globalres[gid] = indic 
        return dics

def md5string(cstr=''):
    m=hashlib.md5()
    m.update(cstr)
    return m.hexdigest()

'''转换资源类型
'''
def changetype(attrdic, _type=''):
    if _type == 'int':
        return int(attrdic)
    elif _type == 'bool':
        mystr = 'myattr=' + attrdic.capitalize()
        exec mystr
        return myattr
    else:
        return attrdic

def changeli(dic):
    _dic = (changetype(dic[0], 'int'),)
    clist = {}
    for i in dic[1] :
        clist[i] = changetype(dic[1][i],globaldic.get(i, 'str'))
    return _dic + (clist,)

def m_res(sv):
    if len(sv) == 1:
        return sv[0]
    else:
        return sv

#处理内部,转换成字典形式
def mdic(attrDic):
    rdic = []
    if len(attrDic) == 1:
        rdata = ()
        rdata += (attrDic[0][0],)
        rdata += (attrDic[0][1]['occupied'],)
        return rdata
    else:
        for odic in attrDic:
            rdata = ()
            rdata += (odic[0],)
            rdata += (odic[1]['occupied'],)
            rdic.append(rdata)
    return rdic


if __name__ == '__main__':
    id,rsc = ApplyRes({'account':'1125000434'},groupName='wiizhangTest')

#    print 'rsc',id,rsc
    ReleaseRes([id])
