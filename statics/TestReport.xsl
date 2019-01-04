<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:template match="/RunResult">
<html>
    <head>
    <style>
    *{
    font-size:12px; 
    font-family: '宋体' , 'Courier New', Arial, 'Arial Unicode MS', '';
    }
    .title
    {
    font-size:14px;
    font-weight: bold;
    margin: 20px auto 5px auto;
    }
    table{
    border:solid 1px #0099CC;
    border-collapse:collapse;
    margin: 0px auto;
    }
    td
    {
    border:solid 1px #0099CC;
    padding: 6px 6px;
    }
    .td_Title
    {
    color:#FFF;
    font-weight: bold;
    background-color:#66CCFF;
    }
    .tr_pass
    {
    background-color:#B3E8B8;
    }
    .tr_fail
    {
    background-color:#F5BCBD;
    }
    .success
    {
    color:#0000FF;
    }
    .fail
    {
    color:#FF0000;
    }
    .exception
    {
    color:#00AA00;
    }
    
    </style>
    </head>
    <body>
    <div class='title'>
        <td>测试报告链接：</td>
        <td><a><xsl:attribute name="href"><xsl:value-of select="TestReportLink/Url"/></xsl:attribute>点击这里</a></td>
    </div>
    <div class='title'>测试运行环境：</div>
    <table>
        <tr>
            <td class='td_Title'>主机名</td>
            <td><xsl:value-of select="TestEnv/PC"/></td>
        </tr>
        <tr>
            <td class='td_Title'>操作系统</td>
            <td><xsl:value-of select="TestEnv/OS"/></td>
        </tr>
    </table>
    <div class='title'>测试运行时间:</div>
    <table>
        <tr>
            <td class='td_Title'>Run开始时间</td>
            <td><xsl:value-of select="RunTime/StartTime"/></td>
        </tr>
        <tr>
            <td class='td_Title'>Run结束时间</td>
            <td><xsl:value-of select="RunTime/EndTime"/></td>
        </tr>
        <tr>
            <td class='td_Title'>Run执行时间</td>
            <td><xsl:value-of select="RunTime/Duration"/></td>
        </tr>
    </table>
    <div class='title'>测试用例汇总：</div>
    <table>
    <tr>
        <td class='td_Title'>用例总数</td>
        <td class='td_Title'>通过用例数</td>
        <td class='td_Title'>失败用例数</td>
    </tr>
    <tr>
        <td>
        <xsl:value-of select="count(TestResult)"/>
        </td>
        <td>
        <xsl:value-of select="count(TestResult[@result='True'])"/>
        </td>
        <td>
        <xsl:value-of select="count(TestResult[@result='False'])"/>
        </td>
    </tr>
    </table>
    <div class='title'>加载失败模块：</div>
    <table>
    <tr>
    <td class='td_Title'>模块名</td>
    <td class='td_Title'>失败Log</td>
    </tr>
    <tr>
    <xsl:for-each select="LoadTestError">
        <tr>
        <td><xsl:value-of select="@name"/></td>
        <td><a><xsl:attribute name="href">
                <xsl:value-of select="@log"/>
            </xsl:attribute>
            Log
        </a></td>
        </tr>
    </xsl:for-each>
    </tr>
    </table>
    <div class='title'>测试用例详细信息：</div>
    <table>
    <tr>
    <td class='td_Title'>测试结果</td>
    <td class='td_Title'>测试用例</td>
    <td class='td_Title'>负责人</td>
    <td class='td_Title'>用例描述</td>
    <td class='td_Title'>用例状态</td>
    <td class='td_Title'>用例Log</td>
    </tr>
    <xsl:for-each select="TestResult">
    <xsl:if test="@result='False'">
        <tr class='tr_fail'>
            <td>失败</td>
            <td><xsl:value-of select="@name"/></td>
            <td><xsl:value-of select="@owner"/></td>
            <td><xsl:value-of select="."/></td>
            <td><xsl:value-of select="@status"/></td>
            <td><a><xsl:attribute name="href">
                    <xsl:value-of select="@log"/>
                    </xsl:attribute>
                    Log
            </a></td>
        </tr>
    </xsl:if>
    <xsl:if test="@result='True'">
        <tr class='tr_pass'>
            <td>通过</td>
            <td><xsl:value-of select="@name"/></td>
            <td><xsl:value-of select="@owner"/></td>
            <td><xsl:value-of select="."/></td>
            <td><xsl:value-of select="@status"/></td>
            <td><a><xsl:attribute name="href">
                    <xsl:value-of select="@log"/>
                    </xsl:attribute>
                    Log
            </a></td>
        </tr>
    </xsl:if>
    </xsl:for-each>
    </table>
    </body>
</html>
</xsl:template>
</xsl:stylesheet>