<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

<xsl:template match="/">
	<html>
	<head>
		<title>Auto-test detailed results - 4.0.1.0 (int/4.0.1.0@90593)</title>
		<style>
			body {
				font-family: Tahoma;
				font-size: x-small;
			}
			table {
				border-collapse: collapse;
				font-size: x-small;
			}
			table th {
				border-bottom: 2px solid #FFFFFF;
			}
			table tr.header {
				border-bottom: 2px solid #FFFFFF;
				background: #3366CC
			}
			table tr {
				border-bottom: 2px solid #FFFFFF;
				background: #E8F3F9;
			}			
		</style>
	</head>

	<h1>PySys Test Results</h1>
	<p class="header">Status: <b><xsl:value-of select="pysyslog/@status"/></b> (<b><xsl:value-of select="pysyslog/@completed"/></b>) </p>
	<p class="header">Start time: <b><xsl:value-of select="pysyslog/timestamp"/></b></p>
	<p class="header">Platform: <b><xsl:value-of select="pysyslog/platform"/></b></p>
	<p class="header">Host: <b><xsl:value-of select="pysyslog/host"/></b></p>
	<p class="header">Project root directory: <a href=""><xsl:value-of select="pysyslog/root"/></a></p>
	<hr/>
	<body>
		<table cellspacing="0" cellpadding="4" border="1" class="table">
			<thead> <tr class="header">
				<th>Test ID</th>
				<th>Links</th>
				<th>Outcome</th>
			</tr> </thead>
			<xsl:for-each select="pysyslog/results/result">
				<tr>
				    <td><xsl:value-of select="@id"/></td>
					<td>
						<a ><xsl:attribute name="href"><xsl:value-of select="descriptor"/></xsl:attribute>
						descriptor</a>, 
						<a><xsl:attribute name="href"><xsl:value-of select="output"/></xsl:attribute>
						output</a>
					</td>
					<xsl:choose>
						<xsl:when test="@outcome='BLOCKED' or @outcome='DUMPEDCORE' or @outcome='TIMEDOUT' or @outcome='FAILED'">
							<td bgcolor="#FF0011">
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
	<hr/>	
	</html>
</xsl:template>

</xsl:stylesheet>