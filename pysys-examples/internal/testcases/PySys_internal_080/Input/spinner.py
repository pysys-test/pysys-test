import time,threading
time.sleep(0.1)
# spin on a background thread so we notice if monitoring excluded bg threads
def bgthread():
	while True: pass # spin
# non daemon thread
threading.Thread(target=bgthread, name="bg-spinner").start()
