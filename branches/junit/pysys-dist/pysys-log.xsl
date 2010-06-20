<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:strip-space elements="output" />

<xsl:template match="/">
	<html>
		<head>
			<title>PySys Test Summary</title>
			<style>
			 	h1 {
					font-family: Tahoma;
					font-size: large;
					border-bottom: medium groove #DCDCDC
				}
				h2 {
					font-family: Tahoma;
					font-size: small;
					border-bottom: thin groove #DCDCDC
				}
				body {
					font-family: Tahoma;
					font-size: x-small;
				}
				table {
					border-collapse: collapse;
					font-size: x-small;
				}
				table tr {
					background: #E8F3F9;
				}
				table tr.header {
					background: #4682B4;
				}
				table tr.odd {
				    background-color: #DBE2F1; 
				}			
			</style>
		</head>
	
		<h1>PySys Test Summary<input style="position:absolute; left:86%; background:#DCDCDC    " type="button" value="Reload" onClick="window.location.reload()"/></h1>
		<p class="header">Status: <b><xsl:value-of select="pysyslog/@status"/></b> (<b><xsl:value-of select="pysyslog/@completed"/></b>) </p>
		<p class="header">Start time: <b><xsl:value-of select="pysyslog/timestamp"/></b></p>
		<p class="header">Platform: <b><xsl:value-of select="pysyslog/platform"/></b></p>
		<p class="header">Host: <b><xsl:value-of select="pysyslog/host"/></b></p>
		<p class="header">Project root directory: <b><a><xsl:attribute name="href"><xsl:value-of select="normalize-space(pysyslog/root)"/></xsl:attribute>
		<xsl:value-of select="pysyslog/root"/></a></b></p>
		<p class="header">-X Arguments: 
			<b>
				<xsl:for-each select="pysyslog/xargs/xarg">
					<xsl:value-of select="@name"/>=<xsl:value-of select="@value"/> <xsl:if test="position()!=last()">, </xsl:if> 
				</xsl:for-each>
			</b>
		</p>
		
		<h2>Test Failures:</h2>
		<body>
			<table cellspacing="0" cellpadding="4" border="1" class="table">
				<thead> <tr class="header">
					<th>Test ID</th>
					<th>Links</th>
					<th>Outcome</th>
				</tr> </thead>
				<xsl:for-each select="pysyslog/results/result[@outcome='BLOCKED' or @outcome='DUMPEDCORE' or @outcome='TIMEDOUT' or @outcome='FAILED']">
						<tr>		
						<xsl:attribute name="class">
							<xsl:choose><xsl:when test="position() mod 2 = 1">odd</xsl:when></xsl:choose>
						</xsl:attribute> 
						<td><xsl:value-of select="@id"/></td>
						<td>
							<a><xsl:attribute name="href"><xsl:value-of select="normalize-space(descriptor)"/></xsl:attribute>
							descriptor</a>, 
							<a><xsl:attribute name="href"><xsl:value-of select="normalize-space(output)"/></xsl:attribute>
							output</a>
						</td>
						<td><xsl:value-of select="@outcome"/></td>
					</tr>
				</xsl:for-each>
			</table>
		</body>
		<h2>Test Results:</h2>
		<body>
			<table cellspacing="0" cellpadding="4" border="1" class="table">
				<thead><tr class="header">
					<th>Test ID</th>
					<th>Links</th>
					<th>Outcome</th>
				</tr> </thead>
				<xsl:for-each select="pysyslog/results/result">
					<tr>
						<xsl:attribute name="class">
							<xsl:choose><xsl:when test="position() mod 2 = 1">odd</xsl:when></xsl:choose>
						</xsl:attribute> 
						<td><xsl:value-of select="@id"/></td>
						<td>
							<a ><xsl:attribute name="href"><xsl:value-of select="normalize-space(descriptor)"/></xsl:attribute>
							descriptor</a>, 
							<a><xsl:attribute name="href"><xsl:value-of select="normalize-space(output)"/></xsl:attribute>
							output</a>
						</td>
						<xsl:choose>
							<xsl:when test="@outcome='BLOCKED' or @outcome='DUMPEDCORE' or @outcome='TIMEDOUT' or @outcome='FAILED'">
								<td bgcolor="#CD5C5C">
								<xsl:value-of select="@outcome"/></td>
							</xsl:when>
							<xsl:otherwise>
								<td><xsl:value-of select="@outcome"/></td>
							</xsl:otherwise>
						</xsl:choose>
					</tr>
				</xsl:for-each>
			</table>
		</body>
	</html>
</xsl:template>

</xsl:stylesheet>