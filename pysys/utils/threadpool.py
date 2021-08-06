#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2021 M.B. Grieve

# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

"""
Thread pool implementation used by BaseRunner. 

:meta private: Deprecated (and hidden) as of 1.5.1; there is no need for PySys to provide a general-purpose thread pool 
	especially as Python 3 now includes simliar functionality. 
"""
 
# Note that the threadpool implementation is based from that proposed
# by Christopher Arndt (http://chrisarndt.de/en/software/python/threadpool/)
# with minor modifications.
 
import sys, time, threading, traceback
if sys.version_info[0] == 2:
	import Queue
else:
	import queue as Queue

from pysys import log

# exceptions
class NoResultsPending(Exception):
	"""All work requests have been processed."""
	pass


class NoWorkersAvailable(Exception):
	"""No worker threads available to process remaining requests."""
	pass


# internal module helper functions
def _handle_thread_exception(request, exc_info):
	"""Default exception handler callback function.

	This just prints the exception info via ``traceback.print_exception``.

	"""
	traceback.print_exception(*exc_info)



class WorkerThread(threading.Thread):
	"""Thread to perform work requests managed by the thread pool object.
	
	The thread polls the thread safe queue of the thread pool instance to retrieve
	work requests in the form of a callable reference with parameters. On completion 
	of a work request the thread places the results on another thread safe queue of the 
	thread pool and waits to get a new request. 
	
	"""
  
	def __init__(self, requests_queue, results_queue, poll_timeout=5, **kwds):
		"""Class constructor.
		
		:param requests_queue: Reference to the threadpool's request queue
		:param results_queue: Reference to the threadpool's results queue
		:param poll_timeout: The timeout when trying to obtain a request from the request queue
		:param kwds: Variable arguments to be passed to the threading.Thread constructor
		
		"""
		threading.Thread.__init__(self, **kwds)
		log.debug("[%s] Creating thread for test execution" % self.getName())
		self.daemon = True
		self._requests_queue = requests_queue
		self._results_queue = results_queue
		self._poll_timeout = poll_timeout
		self._dismissed = threading.Event()
		self.start()

	def run(self):
		"""Start running the worker thread."""
		while True:
			if self._dismissed.isSet():
				break
			try:
				request = self._requests_queue.get(True, self._poll_timeout)
			except Queue.Empty:
				continue
			else:
				if self._dismissed.isSet():
					self._requests_queue.put(request)
					break
				try:
					result = request.callable(*request.args, **request.kwds)
					self._results_queue.put((request, self.getName(), result))
				except:
					request.exception = True
					self._results_queue.put((request, self.getName(), sys.exc_info()))
			time.sleep(0.1)
					
	def dismiss(self):
		"""Stop running of the worker thread."""
		self._dismissed.set()



class WorkRequest(object):
	"""Holds the details of a request placed on the thread pool request queue. 
	
	"""

	def __init__(self, callable_, args=None, kwds=None, requestID=None,
			callback=None, exc_callback=_handle_thread_exception):
		"""Class constructor.
		
		:param callable_: The callable object or function
		:param args: The argument list to the callable object or function
		:param kwds: The keyword arguments to the callable object or function
		:param requestID: An ID for the request
		:param callback: A callback on completion of the request
		:param exc_callback: A callback when the request throws an excetion
	
		"""
		if requestID is None:
			self.requestID = id(self)
		else:
			try:
				self.requestID = hash(requestID)
			except TypeError:
				raise TypeError("requestID must be hashable.")
		self.exception = False
		self.callback = callback
		self.exc_callback = exc_callback
		self.callable = callable_
		self.args = args or []
		self.kwds = kwds or {}

	def __str__(self): return str(self.callable) # typically a TestContainer

class ThreadPool(object):
	"""Main pool to manage worker threads processing an internal request queue.

	"""

	def __init__(self, num_workers, q_size=0, resq_size=0, poll_timeout=0.7, requests_queue=None):
		"""Class constructor.
		
		:param num_workers: The number of worker threads processing the queue
		:param q_size: The request queue size; ignored if a custom requests_queue is specified
		:param resq_size: The response queue size
		:param requests_queue: a custom queue instance which can be used to implement any desired logic 
			for deciding which job to execute next. Must implement the get() and put() methods 
			from the queue.Queue class.
		:param poll_timeout: The polling timeout of worker threads when getting requests from the queue
		"""
		self._requests_queue = Queue.Queue(q_size) if requests_queue is None else requests_queue
		self._results_queue = Queue.Queue(resq_size)
		self.workers = []
		self.dismissedWorkers = []
		self.workRequests = {}
		self.createWorkers(num_workers, poll_timeout)


	def createWorkers(self, num_workers, poll_timeout=5):
		"""Create additional threads on the workers stack.

		:param num_workers: The number of workers to add to the stack
		:param poll_timeout: The timeout of the threads when waiting for a request on the queue
		
		"""
		for i in range(num_workers):
			self.workers.append(WorkerThread(self._requests_queue,
				self._results_queue, poll_timeout=poll_timeout))


	def dismissWorkers(self, num_workers, do_join=False):
		"""Dismiss worker threads from the workers stack.
			
		Stops a set number of workers in the workers list by popping the workers of the 
		list stack. 
		
		:param num_workers: The number of workers to dismiss
		:param do_join: If True wait for all threads to terminate before returning from the call
		
		"""
		dismiss_list = []
		for i in range(min(num_workers, len(self.workers))):
			worker = self.workers.pop()
			worker.dismiss()
			dismiss_list.append(worker)

		if do_join:
			for worker in dismiss_list:
				worker.join()
		else:
			self.dismissedWorkers.extend(dismiss_list)


	def joinAllDismissedWorkers(self):
		"""Join all dismissed workers.
		
		Blocks until all dismissed worker threads terminate. Use when calling dismissWorkers 
		with do_join = False.
		
		"""
		for worker in self.dismissedWorkers:
			worker.join()
		self.dismissedWorkers = []


	def putRequest(self, request, block=True, timeout=0):
		"""Place a WorkRequest on the request queue. 
		
		:param request: The WorkRequest to place on the request queue
		:param block: If set to True, block queue operations until complete, otherwise use timeout
		:param timeout: The timeout to use for queue operations when block is set to False
		
		"""
		assert isinstance(request, WorkRequest)
		assert not getattr(request, 'exception', None)
		self._requests_queue.put(request, block, timeout)
		self.workRequests[request.requestID] = request


	def poll(self, block=False):
		"""Poll the request queue until the queue is empty.
		
		Raises a NoResultsPending or NoWorkersAvailable exception if the results queue 
		is initially empty, or there are no available workers. Otherwise processes the 
		results queue and calls the request callback with the result of the request.
		
		"""
		while True:
			if not self.workRequests:
				raise NoResultsPending
			elif block and not self.workers:
				raise NoWorkersAvailable
			try:
				request, name, result = self._results_queue.get(block=block)
				if request.exception and request.exc_callback:
					request.exc_callback(name, result)
				if request.callback and not \
					   (request.exception and request.exc_callback):
					request.callback(name, result)
				del self.workRequests[request.requestID]
			except Queue.Empty:
				break


	def wait(self):
		"""Block until there are no request results pending on the queue.
		
		Callbacks for work requests are executed by this method until all results have been dealt with. """
		while 1:
			try:
				self.poll(True)
			except NoResultsPending:
				break

