# -*- coding: utf-8 -*-
'''
PyQQ test case
'''

import unittest
import logging
import datetime
import time

import pyqq

pyqq.log.verbose = True

from testbase import logger
logger.addHandler(logging.StreamHandler())

# 测试环境接口（注意访问测试环境需要配置host testing.sdet.sng.local(10.187.15.95)）

class TestServerList(object):
    def __init__(self):
        self._srvs = [
                      #("172.25.0.19",80), 
                      #("10.187.15.95",80), 
                      ("testing.sdet.sng.local",8081)
                      ]
    def get_address(self):
        return self._srvs[0]
    def next(self):
        raise RuntimeError("没有可用的服务器")
        
#pyqq.serverlist.ServerList = TestServerList

test_qqacc = pyqq.QQAccount('1516465285', 'tencent@123')
test_qqacc2 = pyqq.QQAccount('2242936390', 'tencent@123')

class QQAccountTest(unittest.TestCase):
    """QQAccount类测试
    """
    def test_acquire_release(self):
        """测试申请释放
        """
        #申请
        qqacc = pyqq.account.QQAccount.acquire(dict(groupName='pyqqtest'))
        self.assertEqual(qqacc.uin, '123456789')
        self.assertEqual(qqacc.password, '111111111')
        
        #释放
        del qqacc
        
        #再申请
        qqacc = pyqq.account.QQAccount.acquire(dict(groupName='pyqqtest'))
        self.assertEqual(qqacc.uin, '123456789')
        self.assertEqual(qqacc.password, '111111111')
        
    def test_release_all(self):
        """测试释放全部
        """
        qqacc = pyqq.account.QQAccount.acquire(dict(groupName='pyqqtest'))
        self.assertEqual(qqacc.uin, '123456789')
        self.assertEqual(qqacc.password, '111111111')
        
        #释放
        pyqq.account.QQAccount.release_all()
        
        #再申请
        qqacc = pyqq.account.QQAccount.acquire(dict(groupName='pyqqtest'))
        self.assertEqual(qqacc.uin, '123456789')
        self.assertEqual(qqacc.password, '111111111')
        
class FriendTest(unittest.TestCase):
    """好友列表测试
    """
    def test_add_friend(self):
        """测试添加好友
        """
        qqacc1 = pyqq.QQAccount.acquire()
        qqacc2 = pyqq.QQAccount.acquire()
        qq1 = pyqq.PyQQ(qqacc1)
        qq2 = pyqq.PyQQ(qqacc2)
        qq1.friend.add(qqacc2.uin)
        qq2.friend.add(qqacc1.uin)
        self.assertTrue(qq1.uin in qq2.friend.all())
        self.assertTrue(qq1.friend.contain(qqacc2.uin))
        
    def test_remove_friend(self):
        """测试删除好友
        """
        qqacc1 = pyqq.QQAccount.acquire()
        qqacc2 = pyqq.QQAccount.acquire()
        qq1 = pyqq.PyQQ(qqacc1)
        qq2 = pyqq.PyQQ(qqacc2)
        qq1.friend.remove(qqacc2.uin, True)
        self.assertTrue(qq1.uin not in qq2.friend.all())
        self.assertTrue(qq2.uin not in qq1.friend.all())
        qq2.friend.contain(qq1.uin)
        
    def test_auto_remove_friend(self):
        """测试退出时自动删除好友
        """
        qqacc1 = pyqq.QQAccount.acquire()
        qqacc2 = pyqq.QQAccount.acquire()
        qq1 = pyqq.PyQQ(qqacc1)
        qq2 = pyqq.PyQQ(qqacc2)
        qq1.friend.add(qqacc2.uin)
        qq2.friend.add(qqacc1.uin)
        self.assertTrue(qq1.uin in qq2.friend.all())
        self.assertTrue(qq1.friend.contain(qqacc2.uin))
        qq1.quit()
        qq2.quit()
        
        self.assertTrue(qq1.uin not in qq2.friend.all())
        self.assertTrue(qq2.uin not in qq1.friend.all())
        
    def test_auto_remove_friend2(self):
        """测试退出时自动删除好友
        """
        qqacc1 = pyqq.QQAccount.acquire()
        qqacc2 = pyqq.QQAccount.acquire()
        qq1 = pyqq.PyQQ(qqacc1)
        qq2 = pyqq.PyQQ(qqacc2)
        qq1.friend.add(qqacc2.uin)
        qq2.friend.add(qqacc1.uin)
        self.assertTrue(qq1.uin in qq2.friend.all())
        self.assertTrue(qq1.friend.contain(qqacc2.uin))
        
        pyqq.relation.RelationManager().revert_all()
        
        self.assertTrue(qq1.uin not in qq2.friend.all())
        self.assertTrue(qq2.uin not in qq1.friend.all())
        
    def test_remark(self):
        """测试好友备注
        """
        qqacc1 = pyqq.QQAccount.acquire()
        qqacc2 = pyqq.QQAccount.acquire()
        qq1 = pyqq.PyQQ(qqacc1)
        qq2 = pyqq.PyQQ(qqacc2)
        qq1.friend.add(qqacc2.uin)
        qq2.friend.add(qqacc1.uin)
        
        qq1.friend(qq2.uin).remark = "Test中文"
        self.assertTrue(qq1.friend(qq2.uin).remark, "Test中文")
        
    def test_category(self):
        """测试好友分组
        """
        qq  = pyqq.PyQQ(test_qqacc)
        name_friends = {}
        for it in qq.friend.category.all():
            name_friends[it.name] = str(it)
        expect = {
                   "我的好友":"[773609733, 1516465285]",
                    "朋友": "[]",     
                    "家人" :"[1455526613]",
                    "同学": "[]",     
                    "Test": "[]",     
        }
        self.assertEqual(name_friends, expect)
        
        
class GroupTest(unittest.TestCase):
    """群接口测试
    """

    def test_add_remove_member(self):
        """测试添加删除群成员
        """
        qqacc1 = pyqq.QQAccount.acquire()
        qqacc2 = pyqq.QQAccount.acquire()
        qq1 = pyqq.PyQQ(qqacc1)
        #qq2 = pyqq.PyQQ(qqacc2)
        g = qq1.group.create()
        g.add_member(qqacc2.uin)
        self.assertTrue(qqacc1.uin in g)
        self.assertTrue(qqacc2.uin in g.members)
        self.assertTrue(qqacc2.uin in g.members)
        g.remove_member(qqacc2.uin)
        self.assertTrue(qqacc2.uin not in g.members)
        qq1.group.all()
        
    def test_auto_remove_member(self):
        """测试添加群成员自动恢复
        """
        qqacc1 = pyqq.QQAccount.acquire()
        qqacc2 = pyqq.QQAccount.acquire()
        qq1 = pyqq.PyQQ(qqacc1)
        g = qq1.group.create(auto_destroy=False)
        g.add_member(qqacc2.uin)
        self.assertTrue(qqacc2.uin in g.members)
        
        qq1.quit()
        self.assertTrue(qqacc2.uin not in g.members)
        g.destroy()
        
    def test_auto_remove_member2(self):
        """测试添加群成员自动恢复
        """
        qqacc1 = pyqq.QQAccount.acquire()
        qqacc2 = pyqq.QQAccount.acquire()
        qq1 = pyqq.PyQQ(qqacc1)
        g = qq1.group.create(auto_destroy=False)
        g.add_member(qqacc2.uin)
        self.assertTrue(qqacc2.uin in g.members)
        
        pyqq.relation.RelationManager().revert_all()
        self.assertTrue(qqacc2.uin not in g.members)
        g.destroy()
        
    def test_create_destory(self):
        qq  = pyqq.PyQQ(test_qqacc2)
        g = qq.group.create()
        self.assertTrue( g.uin in [ it.uin for it in qq.group.all()])
        pyqq.PyQQ(test_qqacc2).group(g.uin).destroy()
        pyqq.relation.RelationManager().revert_all()
        time.sleep(1)
        qq  = pyqq.PyQQ(test_qqacc)
        self.assertTrue( g.uin not in [ it.uin for it in qq.group.all()])
        
class DiscussTest(unittest.TestCase):
    """讨论组接口测试
    """
    def test_all(self):
        qqacc1 = pyqq.QQAccount.acquire()
        qq1 = pyqq.PyQQ(qqacc1)
        qq1.discuss.all()
        
    def test_add_member(self):
        
        qqacc2 = pyqq.QQAccount.acquire()
        qq1 = pyqq.PyQQ(test_qqacc)
        discuss = qq1.discuss.all()[0]
        discuss.add_member(qqacc2.uin)
        self.assertTrue(qqacc2.uin in discuss)
        
        pyqq.relation.RelationManager().revert_all()
        self.assertTrue(qqacc2.uin not in discuss.members)
        
    def test_create_destory(self):
        qqacc = pyqq.QQAccount.acquire()
        qq = pyqq.PyQQ(qqacc)
        discuss = qq.discuss.create(name='xxxxxxx作为', uins=[test_qqacc.uin])
        
        self.assertTrue(discuss.uin in [it.uin for it in qq.discuss.all()])
        self.assertTrue(discuss.name, 'xxxxxxx作为')
        members = discuss.members
        self.assertTrue(len(members)==2)
        self.assertTrue(qqacc.uin in members)
        self.assertTrue(test_qqacc.uin in members)
        
        discuss.destroy()
        self.assertTrue(discuss.uin not in [it.uin for it in qq.discuss.all()])
        
        testqq = pyqq.PyQQ(test_qqacc)
        self.assertTrue(discuss.uin not in [it.uin for it in testqq.discuss.all()])
        
class UserInfoTest(unittest.TestCase):
    """用户信息
    """
    def test_get_self(self):
        """获取
        """ 
        qqacc = test_qqacc
        qq = pyqq.PyQQ(qqacc)
        self.assertEqual(qq.profile.nickname, "pyqqtest")
        self.assertEqual(qq.profile.age, 27)
        loc = qq.profile.location
        self.assertEqual(loc[0], '中国')
        self.assertEqual(loc[1], '广东')
        self.assertEqual(loc[2], '广州')
        self.assertEqual(qq.profile.country, '中国')
        self.assertEqual(qq.profile.province, '广东')
        self.assertEqual(qq.profile.city, '广州')
        self.assertEqual(qq.profile.gender, 0) 
        self.assertEqual(qq.profile.birthday, datetime.date(1988, 03, 30)) 
        
    def test_get_friend(self):
        qqacc = test_qqacc
        qq = pyqq.PyQQ(qqacc)
        qq.friend.all()[0].nickname
        
    def test_get_group(self):
        qqacc = test_qqacc
        qq = pyqq.PyQQ(qqacc)
        qq.group.all()[0].name
        
    def test_get_discuss(self):
        qqacc = test_qqacc
        qq = pyqq.PyQQ(qqacc)
        qq.discuss.all()[0].name
        
class MessageTest(unittest.TestCase):
    
    richmsg_url = "http://data.music.qq.com/playsong.html?songid=7420329&souce=qqaio"
    richmsg_xml = """
<?xml version='1.0' encoding='UTF-8' standalone='yes' ?>
<msg serviceID="2" 
     templateID="1" 
     action="web" 
     actionData="" 
     a_actionData="" 
     i_actionData="" 
     brief="[分享] 漂洋过海来看你" 
     m_resid="" 
     m_fileName="" 
     m_fileSize="0" 
     url="http://data.music.qq.com/playsong.html?songid=7420329&amp;souce=qqaio" 
     flag="0">
     <item layout="2">
        <audio cover="http://url.cn/PRHWgX" src="http://ws.stream.qqmusic.qq.com/7420329.m4a?fromtag=30" />
        <title>漂洋过海来看你</title>
        <summary>丁当</summary>
    </item>
    <source name="QQ音乐" 
            icon="http://i.gtimg.cn/open/app_icon/00/49/73/08/100497308_100_m.png" 
            url="http://web.p.qq.com/qqmpmobile/aio/app.html?id=100497308" 
            action="app" 
            actionData="" 
            a_actionData="com.tencent.qqmusic" 
            i_actionData="tencent100497308://" appid="100497308" />
</msg>
"""


    def test_mix(self):
        qqacc = test_qqacc
        qq = pyqq.PyQQ(qqacc)
        friend = qq.friend('773609733')
        friend.send_message(pyqq.Text("test")+pyqq.Picture(r"\\tencent.com\tfs\跨部门项目\SNG-Test\QTA\测试资源\pyqq\pic.png"))
    
    def test_c2c(self):
        qqacc = test_qqacc
        qq = pyqq.PyQQ(qqacc)
        friend = qq.friend('773609733')
        friend.send_message("test")
        time.sleep(0.2)
        
        friend.send_message(pyqq.Text("test"))
        time.sleep(0.2)
        
        friend.send_message(pyqq.Face(12))
        time.sleep(0.2)
        
        friend.send_message(pyqq.Picture(r"\\tencent.com\tfs\跨部门项目\SNG-Test\QTA\测试资源\pyqq\pic.png"))
        time.sleep(0.2)
        
        friend.send_message(pyqq.Ptt(r"\\tencent.com\tfs\跨部门项目\SNG-Test\QTA\测试资源\pyqq\test_3s.amr"))
        time.sleep(0.2)
        
        friend.send_message(pyqq.MarketFace( name="[惊讶]", faceid="\x79\x8f\xf3\x68\x93\xae\xc1\x54\x94\x69\x97\x91\x26\x1c\xd1\x98", tabid=11141, facekey="66ffe16a218e1dba", facetype=3, facesize=(200,200) ))
        time.sleep(0.2)
        
        friend.send_message(pyqq.File(r"\\tencent.com\tfs\跨部门项目\SNG-Test\QTA\测试资源\pyqq\test_3s.amr"))
        
        time.sleep(0.2)
        friend.send_message(pyqq.RichMsg(2, self.richmsg_xml, self.richmsg_url))
        
        
    def test_group(self):
        qqacc = test_qqacc
        qq = pyqq.PyQQ(qqacc)
        group = qq.group.all()[0]
        
        group.send_message("hello")
        time.sleep(0.2)
        
        group.send_message(pyqq.Text("test"))
        time.sleep(0.2)
        
        group.send_message(pyqq.Face(12))
        time.sleep(0.2)
        
        group.send_message(pyqq.Picture(r"\\tencent.com\tfs\跨部门项目\SNG-Test\QTA\测试资源\pyqq\pic.png"))
        time.sleep(0.2)
        
        group.send_message(pyqq.Ptt(r"\\tencent.com\tfs\跨部门项目\SNG-Test\QTA\测试资源\pyqq\test_3s.amr"))
        time.sleep(0.2)
        
        group.send_message(pyqq.MarketFace( name="[惊讶]", faceid="\x79\x8f\xf3\x68\x93\xae\xc1\x54\x94\x69\x97\x91\x26\x1c\xd1\x98", tabid=11141, facekey="66ffe16a218e1dba", facetype=3, facesize=(200,200) ))
        time.sleep(0.2)
        
        group.send_message(pyqq.RichMsg(2, self.richmsg_xml, self.richmsg_url))
        
    def test_diss(self):
        qqacc = test_qqacc
        qq = pyqq.PyQQ(qqacc)
        group = qq.discuss.all()[0]
        
        group.send_message("hello")
        time.sleep(0.2)
        
        group.send_message(pyqq.Text("test"))
        time.sleep(0.2)
        
        group.send_message(pyqq.Face(12))
        time.sleep(0.2)
        
        group.send_message(pyqq.Picture(r"\\tencent.com\tfs\跨部门项目\SNG-Test\QTA\测试资源\pyqq\pic.png"))
        time.sleep(0.2)
        
        group.send_message(pyqq.Ptt(r"\\tencent.com\tfs\跨部门项目\SNG-Test\QTA\测试资源\pyqq\test_3s.amr"))
        time.sleep(0.2)
        
        group.send_message(pyqq.MarketFace( name="[惊讶]", faceid="\x79\x8f\xf3\x68\x93\xae\xc1\x54\x94\x69\x97\x91\x26\x1c\xd1\x98", tabid=11141, facekey="66ffe16a218e1dba", facetype=3, facesize=(200,200) ))
        time.sleep(0.2)
        
        group.send_message(pyqq.File(r"\\tencent.com\tfs\跨部门项目\SNG-Test\QTA\测试资源\pyqq\test_3s.amr"))
        time.sleep(0.2)
        
        group.send_message(pyqq.RichMsg(2, self.richmsg_xml, self.richmsg_url))
        
        
    def test_group_member_c2c(self):
        qqacc = test_qqacc
        qq = pyqq.PyQQ(qqacc)
        qq.group.all()[0].get_member('773609733').send_message("xxx")
        
    def test_multiple(self):
        qqacc = test_qqacc
        qq = pyqq.PyQQ(qqacc)
        for i in range(20):
            qq.friend('773609733').send_message("test_%s"%i)
            
    def test_send_compound(self):
        qqacc = test_qqacc
        qq = pyqq.PyQQ(qqacc)
        qq.friend('773609733').send_message(pyqq.Text("sss") + pyqq.Face(26) + pyqq.Text("sss") )
        
    def test_group_member_name(self):
        qqacc = test_qqacc
        qq = pyqq.PyQQ(qqacc)
        name = qq.group.all()[0].get_member('773609733').name
        self.assertEqual(name, "教主")
        
    def test_recv_message(self):
        
        qq1 = pyqq.PyQQ(test_qqacc)
        qq2 = pyqq.PyQQ(test_qqacc2)
        qq1.friend.add(qq2.account.uin)
        qq2.friend.add(qq1.account.uin)
        
        qq2.status.switch_online(True)
        msg = 'text_%s' % time.time()
        qq1.friend(qq2.uin).send_message(msg)
        qq2.friend(qq1.uin).wait_for_message(pyqq.Text(msg))

        
class StatusTest(unittest.TestCase):
    
    def test_status(self):
        qqacc = test_qqacc
        qq = pyqq.PyQQ(qqacc, app=pyqq.EnumApp.iPhoneQQ, device=pyqq.EnumDevice.iPhone6Plus)
        qq.status.switch_online()
        time.sleep(1)
        qq.status.switch_offline()
        
class AccountTest(unittest.TestCase):
    
    def test_bind_unbind_alt_count(self):
        pyqq.USE_UIN_SERVICE = False
#         pyqq.OIDB_TESTENV = True
        qqacc = test_qqacc
        qqacc2 = test_qqacc2
        qq1 = pyqq.PyQQ(qqacc)
        qq2 = pyqq.PyQQ(qqacc2)
        qq1.account.unbind_alternative(qqacc2.uin)
        self.assertEqual(qqacc.uin in qq2.account.alternatives, False)
        self.assertEqual(qqacc2.uin in qq1.account.alternatives, False)
        
        qq1.account.bind_alternative(qqacc2)
        self.assertEqual(qqacc.uin in qq2.account.alternatives, True)
        self.assertEqual(qqacc2.uin in qq1.account.alternatives, True)
        
        qq2.account.unbind_alternative(qqacc.uin)
        self.assertEqual(qqacc.uin in qq2.account.alternatives, False)
        self.assertEqual(qqacc2.uin in qq1.account.alternatives, False)
        
        
    def test_display_name(self):
        '''测试主显帐号
        '''
        qqacc = test_qqacc
        qq = pyqq.PyQQ(qqacc)
        #qq.account.mobilephone = '13802438884'
        qq.account.name = qq.account.mobilephone
        self.assertEqual(qq.account.name, qq.account.mobilephone)
        qq.account.name = qq.account.uin
        self.assertEqual(qq.account.name, qq.account.uin)
        qq.account.name = qq.account.email
        self.assertEqual(qq.account.name, qq.account.email)
        
        
#     def test_mobile_phone(self):
#         '''测试绑定手机号码
#         '''
#         qqacc = test_qqacc
#         qq = pyqq.PyQQ(qqacc)
#         print qq.account.mobilephone
#         qq.account.mobilephone = None
#         self.assertEqual(qq.account.mobilephone, None)
#         qq.account.mobilephone = '13802438884'
#         self.assertEqual(qq.account.mobilephone, '13802438884')
#         qq.account.mobilephone = '13539392639'
#         self.assertEqual(qq.account.mobilephone, '13539392639')
#         
#     def test_email(self):
#         '''测试绑定邮箱
#         '''
#         qqacc = test_qqacc
#         qq = pyqq.PyQQ(qqacc)
#         print qq.account.email
#         qq.account.email = None
#         self.assertEqual(qq.account.email, None)
#         qq.account.email = 'pyqqtest@qq.com'
#         self.assertEqual(qq.account.email, 'pyqqtest@qq.com')
#         qq.account.email = 'eeelin@outlook.com'
#         self.assertEqual(qq.account.email, 'eeelin@outlook.com')