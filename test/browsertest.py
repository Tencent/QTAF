# -*- coding:UTF-8 -*-
'''用于测试浏览器
'''
from browser.ie import IEBrowser
from browser.chrome import ChromeBrowser
from qt4w.webcontrols import FrameElement,WebElement
from qt4w import XPath


def test_for_ie():
    webview = IEBrowser().open_url('https://passport.qcloud.com/')
    print webview.exec_script('location.href')
    
    account_xpth = r'//iframe[@id="login_frame"]//input[@id="u"]'
    pwd_xpth = r'//iframe[@id="login_frame"]//input[@id="p"]'
    webview.get_element(account_xpth).inner_text = '123456'
    webview.get_element(pwd_xpth).inner_text = '123456'

def test_chrome():
    import time
    browser=ChromeBrowser()
    page=browser.open_url('http://www.qq.com/')
    locators={
        '输入框':{'type':WebElement,'root':page,'locator':XPath("//input[@id='sougouTxt']")},
        '搜索':{'type':WebElement,'root':page,'locator':XPath("//button[@id='searchBtn']")},
    }
    page.updateLocator(locators)
    page.Controls['输入框'].attributes['value']='赵日天'
    page.Controls['搜索'].hover()
    time.sleep(2)
    page.Controls['搜索'].highlight()
    page.Controls['输入框'].right_click()
    time.sleep(2)
    page.Controls['搜索'].click()
    print page.url
    print page.title
    print page.browser_type
    
if __name__ == "__main__":
    test_for_ie()
#     test_chrome()