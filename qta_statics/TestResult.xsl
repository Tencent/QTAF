<?xml version="1.0" encoding="utf-8"?>
<!-- DWXMLSource="tmp/qqtest.hello.HelloW.xml" -->
<!DOCTYPE xsl:stylesheet  [
    
<!ENTITY nbsp   "&#160;">
<!ENTITY copy   "&#169;">
<!ENTITY reg    "&#174;">
<!ENTITY trade  "&#8482;">
<!ENTITY mdash  "&#8212;">
<!ENTITY ldquo  "&#8220;">
<!ENTITY rdquo  "&#8221;">
<!ENTITY pound  "&#163;">
<!ENTITY yen    "&#165;">
<!ENTITY euro   "&#8364;">
]>
<xsl:stylesheet version="1.0"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:strip-space elements="*"/>
	<xsl:template match="/TEST">
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
                .subtable{
                border:solid 1px #0099CC;
                border-collapse:collapse;
                margin: 0px auto auto 0px;
                }
                .subtable td
                {
                border:solid 1px #0099CC;
                padding: 6px 6px;
                }
                .td_title
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
                .suc_step_title
                {
                background-color:#B3E8B8;
                padding:2px 2px
                }
                
            .STYLE1 {font-size: 16px}
            .STYLE3 {font-size: 14px; color:#666666;}
            .STYLE4 {color: #999999}
            .STYLE5 {
                color: #FF0000;
                font-weight: bold;
            }
            .STYLE6 {
                color: #FF9900;
                font-weight: bold;
            }
            </style>
			</head>
			<body>
				<div>
					<table class="subtable">
						<tr>
							<td class='td_title'>用例名字：</td>
							<td>
								<xsl:value-of select="@name"/>
							</td>
							<td class='td_title'>运行结果：</td>
							<td>
								<span>
									<xsl:attribute name="style">
										<xsl:if test="@result='True'">color: #00FF00</xsl:if>
										<xsl:if test="@result='False'">color: #FF0000</xsl:if>
									</xsl:attribute>
									<xsl:apply-templates select="@result"/>
								</span>
							</td>
						</tr>
						<tr>
							<td class='td_title'>开始时间：</td>
							<td>
								<xsl:value-of select="@begintime"/>
							</td>
							<td class='td_title'>负责人：</td>
							<td>
								<xsl:value-of select="@owner"/>
							</td>
						</tr>
						<tr>
							<td class='td_title'>结束时间：</td>
							<td>
								<xsl:value-of select="@endtime"/>
							</td>
							<td class='td_title'>优先级：</td>
							<td>
								<xsl:value-of select="@priority"/>
							</td>
						</tr>
						<tr>
							<td class="td_title">运行时间：</td>
							<td>
								<xsl:value-of select="@duration"/>
							</td>
							<td class='td_title'>用例超时：</td>
							<td>
								<xsl:value-of select="@timeout"/>分钟
							</td>
						</tr>
					</table>
				</div>
				<xsl:apply-templates/>
			</body>
		</html>
	</xsl:template>
	<xsl:template name="break_lines">
		<xsl:param name="text" select="string(.)"/>
		<xsl:choose>
			<xsl:when test="contains($text, '&#xd;')">
				<xsl:value-of select="substring-before($text, '&#xd;')"/>
				<br/>
				<xsl:call-template name="break_lines">
					<xsl:with-param 
          name="text" 
          select="substring-after($text, '&#xd;')"
        />
				</xsl:call-template>
			</xsl:when>
			<xsl:otherwise>
				<xsl:value-of select="$text"/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>
	<xsl:template name="show_log_record">
		<xsl:value-of select="text()"/>
		<xsl:if test="ATTACHMENT">
			<xsl:for-each select="ATTACHMENT">
				<a>
					<xsl:attribute name="href">
						<xsl:value-of select="@filepath"/>
					</xsl:attribute>
                    [<xsl:value-of select="text()"/>]
				</a>
			</xsl:for-each>
		</xsl:if>
	</xsl:template>
	<xsl:template match="@result">
		<xsl:if test=".='True'">通过</xsl:if>
		<xsl:if test=".='False'">失败</xsl:if>
	</xsl:template>
	<xsl:template match="STEP">
		<hr />
		<div>
			<xsl:if test="@result='True'">
				<xsl:attribute name="style">
    padding:2px 2px; background-color:#B3E8B8
</xsl:attribute>
			</xsl:if>
			<xsl:if test="@result='False'">
				<xsl:attribute name="style">
    padding:2px 2px; background-color:#F5BCBD
</xsl:attribute>
			</xsl:if>
			<table border="0">
				<tr>
					<td>
						<span class="STYLE1">步骤：</span>
					</td>
					<td>
						<span class="STYLE1">
							<xsl:value-of select="@title"/>
						</span>
					</td>
					<td>
						<span class="STYLE1">&nbsp;
							<xsl:value-of select="@time"/>
						</span>
					</td>
					<td>
						<span class="STYLE1">&nbsp;
    
							<xsl:apply-templates select="@result"/>
						</span>
					</td>
				</tr>
			</table>
		</div>
		<hr />
		<table>
			<xsl:apply-templates/>
		</table>
	</xsl:template>
	<xsl:template match="DEBUG">
		<tr>
			<td valign="top">
				<strong>DEBUG:</strong>
				<xsl:call-template name="show_log_record"/>
			</td>
		</tr>
	</xsl:template>
	<xsl:template match="INFO">
		<tr>
			<td valign="top">
				<strong>INFO:</strong>
				<xsl:call-template name="show_log_record"/>
			</td>
		</tr>
	</xsl:template>
	<xsl:template match="WARNING">
		<tr>
			<td valign="top">
				<span class="STYLE6">WARNING:</span>
				<xsl:call-template name="show_log_record"/>
			</td>
		</tr>
	</xsl:template>
	<xsl:template match="ERROR">
		<tr>
			<td valign="top">
				<span class="STYLE5">ERROR:</span>
				<xsl:call-template name="show_log_record"/>
			</td>
			<td>
				<pre>
					<xsl:value-of select="EXCEPT/text()"/>
				</pre>
				<table border="0">
					<xsl:apply-templates select="EXPECT"/>
					<xsl:apply-templates select="ACTUAL"/>
				</table>
			</td>
		</tr>
	</xsl:template>
	<xsl:template match="EXPECT">
		<tr>
			<td>&nbsp;&nbsp;期望值：</td>
			<td>
				<xsl:value-of select="text()"/>
			</td>
		</tr>
	</xsl:template>
	<xsl:template match="ACTUAL">
		<tr>
			<td>&nbsp;&nbsp;实际值：</td>
			<td>
				<xsl:value-of select="text()"/>
			</td>
		</tr>
	</xsl:template>
</xsl:stylesheet>