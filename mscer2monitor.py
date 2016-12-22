
import clr, clrtype

clr.AddReference("Peach.Core")
clr.AddReference("Peach.Pro")

import System
import Peach.Core
from Peach.Core import Variant
from Peach.Core.Agent import IterationStartingArgs, MonitorData
from Peach.Core.Agent.MonitorData import Info
from Peach.Pro.Core.Agent.Monitors import BasePythonMonitor

import mscer2
import time


# Create wrappers for class attributes we will use
MonitorAttr = clrtype.attribute(Peach.Core.Agent.MonitorAttribute)
DescriptionAttr = clrtype.attribute(System.ComponentModel.DescriptionAttribute)
ParameterAttr = clrtype.attribute(Peach.Core.ParameterAttribute)

class MSCER2Monitor(BasePythonMonitor):

	__metaclass__ = clrtype.ClrClass
	_clrnamespace = "PythonExamples"   

	_clrclassattribs = [
		MonitorAttr("MSCER2Monitor"),
		DescriptionAttr("MSCER2 Monitor"),
	]

	@clrtype.accepts(clr.GetClrType(str))
	@clrtype.returns()
	def __init__(self, name):
		#print ">>>> MONITOR INIT %s" % name
		pass
	
	
	
	def cercallback(self, appName, appPath, eventType, params):
		#print "GOT CALLBACK", appName, appPath, eventType, params
		
		with open("appNames.txt", "a") as fd:
			fd.write(appName + "," + appPath + "\r\n")
			
		for trigger in self._triggers:
			if trigger.lower() in appPath.lower():
				self._faulted = True
				self._faultedData = (appName, eventType, params)
				break
	
	

	@clrtype.returns()
	@clrtype.accepts(System.Collections.Generic.Dictionary[clr.GetClrType(str), clr.GetClrType(str)])
	def StartMonitor(self, args):
		#print ">>>> START MONITOR '%s/%s' FROM PYTHON" % (self.Name, self.Class)
		
		self._faulted = False
		self._faultedData = None
		self._triggers = []
		port = 8881
		host = "127.0.0.1"
		for kv in args:
			#print ">>>>   PARAM '%s' = '%s'" % (kv.Key, kv.Value)
			if kv.Key == 'Triggers':
				self._triggers = kv.Value.split(';')
				#print ">>>>", repr(self._triggers)
				
			if kv.Key == 'Port':
				port = int(kv.Value)
			
			if kv.Key == 'Host':
				host = kv.Value
				
			
			
		self._server = mscer2.ServerThread(self.cercallback, mscer2.MSCER2Handler, port, host)
		self._server.daemon = True
		self.count = 0
		pass



	@clrtype.accepts()
	@clrtype.returns()
	def StopMonitor(self):
		#print ">>>> STOP MONITOR FROM PYTHON"
		self._server.shutdown()
		pass

	@clrtype.accepts()
	@clrtype.returns()
	def SessionStarting (self):
		#print ">>>> SESSION STARTING FROM PYTHON"
		self._server.start()
		pass

	@clrtype.accepts()
	@clrtype.returns()
	def SessionFinished(self):
		#print ">>>> SESSION FINISHED FROM PYTHON"
		self._server.shutdown()
		pass

	@clrtype.accepts(IterationStartingArgs)
	@clrtype.returns()
	def IterationStarting(self, args):
		#print ">>>> ITERATION STARTING FROM PYTHON"
		self.isReproduction = args.IsReproduction
		self.lastWasFault = args.LastWasFault
		self.count += 1
		pass

	@clrtype.accepts()
	@clrtype.returns()
	def IterationFinished(self):
		#print ">>>> ITERATION FINISHED FROM PYTHON"
		pass

	@clrtype.accepts()
	@clrtype.returns(clr.GetClrType(bool))
	def DetectedFault(self):
		time.sleep(3)
		#time.sleep(0.25)
		fault = self._faulted
		#print ">>>> DETECTED FAULT: %s" % fault
		return fault


	@clrtype.accepts()
	@clrtype.returns(MonitorData)
	def GetMonitorData(self):
		#print ">>> GET MONITOR DATA"
		data = MonitorData()
		if self._faulted:
			appName, eventType, params = self._faultedData
			self._faultedData = None
			self._faulted = False
			print "name", appName, "evtType", eventType, "params", params
			
			ex = ''
			mod = ''
			addr = ''
			
			if 'Exception Code' in params.keys():
				ex = params['Exception Code']
			if 'Fault Module Name' in params.keys():
				mod = params['Fault Module Name']
			if 'Exception Offset' in params.keys():
				addr = params['Exception Offset']
			
			
			data.Title = "%s %s in %s!%s" % (eventType, ex, appName, mod)
			data.Fault = MonitorData.Info()
			data.Fault.Description = "im: %s ex: %s mod: %s addr: %s\r\n\r\n%s" % (appName, ex, mod, addr, repr(params))
			data.Fault.MajorHash = self.Hash(appName + eventType)
			data.Fault.MinorHash = self.Hash(ex + mod + addr)
			data.Fault.Risk = "UNKNOWN"
			data.Fault.MustStop = False
		return data

	@clrtype.accepts(clr.GetClrType(str))
	@clrtype.returns()
	def Message(self, name):
		#print ">>>> MESSAGE '%s' FROM PYTHON" % name
		pass

# end


