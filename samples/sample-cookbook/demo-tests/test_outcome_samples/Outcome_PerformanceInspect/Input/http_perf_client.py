import sys, time, random
print ('Started My Lovely (fake) performance tool')

plannedIterations = 1000
latencySamplingPeriod = 100
responses = 0

currentTime = startTime = time.time()
for i in range(plannedIterations):
	if i % 1000 == 0: 
		print(f'Progress: iteration={i:,} (={100.0*i/plannedIterations:0.1f}%)')
		sys.stdout.flush()

	if (i % latencySamplingPeriod == 0): latencyStartTime = currentTime
	
	currentTime += random.random()/100.0 # simulate the passage of time for demonstration purposes
	
	if (i % latencySamplingPeriod == 0): print(f'Response latency sample: {currentTime-latencyStartTime} seconds')
	responses += 1

print(f'Completed {responses:,} response iterations in {currentTime-startTime} seconds')

for n in [4, 8]:
	with open('my_performance_graph_n=%d.svg'%n, 'w') as f:
		f.write("""<svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
 <g>
  <title>background</title>
  <rect fill="#fff" id="canvas_background" height="602" width="802" y="-1" x="-1"/>
  <g display="none" overflow="visible" y="0" x="0" height="100%" width="100%" id="canvasGrid">
   <rect fill="url(#gridpattern)" stroke-width="0" y="0" x="0" height="100%" width="100%"/>
  </g>
 </g>
 <g>
  <title>Layer 1</title>
  <line stroke="#000" stroke-linecap="undefined" stroke-linejoin="undefined" id="svg_1" y2="504.05476" x2="54.5" y1="84.05" x1="54.5" stroke-width="1.5" fill="none"/>
  <line stroke="#000" stroke-linecap="undefined" stroke-linejoin="undefined" id="svg_2" y2="505.05" x2="53.49917" y1="505.05" x1="734.49997" stroke-width="1.5" fill="none"/>
  <text xml:space="preserve" text-anchor="start" font-family="Helvetica, Arial, sans-serif" font-size="10" id="svg_3" y="73.05" x="15.5" stroke-width="0" stroke="#000" fill="#000000">Throughput rate</text>
  <text xml:space="preserve" text-anchor="start" font-family="Helvetica, Arial, sans-serif" font-size="10" id="svg_10" y="528.05" x="712.5" stroke-width="0" stroke="#000" fill="#000000">Time</text>
  <text xml:space="preserve" text-anchor="start" font-family="Helvetica, Arial, sans-serif" font-size="20" id="svg_12" y="44.05" x="274.5" fill-opacity="null" stroke-opacity="null" stroke-width="0" stroke="#000" fill="#000000">@TITLE@</text>
  <line stroke="#000" stroke-linecap="undefined" stroke-linejoin="undefined" id="svg_16" y2="505.05" x2="123.5" y1="504.05" x1="53.5" fill-opacity="null" stroke-opacity="null" stroke-width="1.5" fill="none"/>
  <line stroke="#000" stroke-linecap="undefined" stroke-linejoin="undefined" id="svg_17" y2="248.05" x2="298.5" y1="505.05" x1="122.5" stroke-opacity="null" stroke-width="1.5" fill="none"/>
  <line stroke-linecap="undefined" stroke-linejoin="undefined" id="svg_19" y2="372.05" x2="737.5" y1="371.05" x1="737.5" stroke-opacity="null" stroke-width="1.5" stroke="#000" fill="none"/>
  <line stroke-linecap="undefined" stroke-linejoin="undefined" id="svg_21" y2="503.05" x2="730.5" y1="494.05" x1="665.5" stroke-opacity="null" stroke-width="1.5" stroke="#000" fill="none"/>
  <line stroke-linecap="undefined" stroke-linejoin="undefined" id="svg_24" y2="397.05" x2="315.5" y1="251.05" x1="298.5" stroke-opacity="null" stroke-width="1.5" stroke="#000" fill="none"/>
  <line stroke-linecap="undefined" stroke-linejoin="undefined" id="svg_25" y2="201.05" x2="430.5" y1="393.05" x1="318.5" stroke-opacity="null" stroke-width="1.5" stroke="#000" fill="none"/>
  <line stroke-linecap="undefined" stroke-linejoin="undefined" id="svg_26" y2="199.05" x2="430.5" y1="437.05" x1="504.5" stroke-opacity="null" stroke-width="1.5" stroke="#000" fill="none"/>
  <line stroke-linecap="undefined" stroke-linejoin="undefined" id="svg_27" y2="442.05" x2="506.5" y1="133.05" x1="589.5" stroke-opacity="null" stroke-width="1.5" stroke="#000" fill="none"/>
  <line stroke-linecap="undefined" stroke-linejoin="undefined" id="svg_29" y2="494.05" x2="666.5" y1="134.05" x1="588.5" stroke-opacity="null" stroke-width="1.5" stroke="#000" fill="none"/>
  <line stroke-linecap="undefined" stroke-linejoin="undefined" id="svg_30" y2="65.05" x2="851.5" y1="64.05" x1="849.5" stroke-opacity="null" stroke-width="1.5" stroke="#000" fill="none"/>
 </g>
</svg>""".replace('@TITLE@', 'Performance graph (fake) with n=%d'%n))