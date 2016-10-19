# -*- coding: utf-8 -*-
'''对cef的webview进行测试
'''
from qt4w.webcontrols import WebPage,WebElement
from qt4w import XPath
from tuia.webview.cef3webview import Cef3WebView
from tuia.qpath import QPath

class FindPage(WebPage):
    '''QQ查找面板封装
    '''
    def __init__(self):
        web_view = Cef3WebView(locator=QPath('/classname="TXGuiFoundation" && caption="查找" && Visible="True"\
                                             /UIType="GF" && name="WebSearchWnd"/name="ClientArea"\
                                             /name="WebSearchPage_AWK"/Type="IAFWebCtrl" && MaxDepth="2"'))
        WebPage.__init__(self, web_view)
        locators = {     
                    '找群tab':{'type':WebElement, 'root':self, 'locator':XPath('//a[@data-nav="qqun"]')},
                    '输入框':{'type':WebElement, 'root':self, 'locator':XPath("//input[@id='qu-search-input']")},
                    '查找按钮':{'type':WebElement, 'root':self, 'locator':XPath("//a[@id='qu-search-submit']")},
                    }
        self.updateLocator(locators)
        
if __name__=='__main__':   
    page = FindPage()
    page.Controls["找群tab"].click()
    page.Controls["输入框"].send_keys('赵日天')
    page.Controls['查找按钮'].click()
    a=page.Controls["输入框"].attributes['value']
    print a=='赵日天'