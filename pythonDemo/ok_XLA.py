import ok
import sys
import string
import time

class XLink:
	def __init__(self):
		return

	def InitializeDevice(self):
		# Open the first device we find.
		self.xem = ok.okCFrontPanel()
		if (self.xem.NoError != self.xem.OpenBySerial("")):
			print ("A device could not be opened.  Is one connected?")
			return(False)

		# Get some general information about the device.
		self.devInfo = ok.okTDeviceInfo()
		if (self.xem.NoError != self.xem.GetDeviceInfo(self.devInfo)):
			print ("Unable to retrieve device information.")
			return(False)
		print("         Product: " + self.devInfo.productName)
		print("Firmware version: %d.%d" % (self.devInfo.deviceMajorVersion, self.devInfo.deviceMinorVersion))
		print("   Serial Number: %s" % self.devInfo.serialNumber)
		print("       Device ID: %s" % self.devInfo.deviceID)

		# Download the configuration file.
		if (self.xem.NoError != self.xem.ConfigureFPGA("ok_XLA.bit")):
			print ("FPGA configuration failed.")
			return(False)

		# Check for FrontPanel support in the FPGA configuration.
		if (False == self.xem.IsFrontPanelEnabled()):
			print ("FrontPanel support is not available.")
			return(False)

		print ("FrontPanel support is available.")
		return(True)

	def GetDateCode(self):
		self.xem.UpdateWireOuts()
		date = self.xem.GetWireOutValue(0x20)
		print ("FW Date Code: %04x" % date)

	def ResetFW(self):
		self.xem.ActivateTriggerIn(0x40, 0)
		
	def GetCurrTBID(self):
		self.xem.UpdateWireOuts()
		TBID0 = self.xem.GetWireOutValue(0x23)
		print ("TBID0 = %04x" % TBID0)

	def GetSyncStatus(self):
		self.xem.UpdateWireOuts()
		xlrxstatus = self.xem.GetWireOutValue(0x21)
		print ("xlrxstatus = %04x" % xlrxstatus)

	def ToggleLED(self, val, index):
		self.xem.SetWireInValue(0x00, val, index) # endpoint, value, mask
		self.xem.UpdateWireIns()

	def EnableDebug(self):
		self.xem.SetWireInValue(0x02, 0x0359, 0xFFFF) # set frame threshold (857)
		self.xem.SetWireInValue(0x03, 0x5555, 0xFFFF) # set payload word
		self.xem.SetWireInValue(0x01, 0x0B, 0xFF) # enable debug, framer, sync
		self.xem.UpdateWireIns()

	def EnableRealTime(self):
		self.xem.SetWireInValue(0x02, 0x0359, 0xFFFF) # set frame threshold
		self.xem.SetWireInValue(0x03, 0x5555, 0xFFFF) # set payload word
		self.xem.SetWireInValue(0x01, 0x07, 0xFF) # enable feedthrough, framer, sync
		self.xem.UpdateWireIns()
		
	def DisableDevice(self):
		self.xem.SetWireInValue(0x01, 0x00, 0xFF) # disable all
		self.xem.UpdateWireIns()	
	
	def PipeBuff0(self):
		# Reset the RAM address pointer.
		self.xem.ActivateTriggerIn(0x50, 0)
		self.xem.ReadFromPipeOut(0xa0, buf)

		
	def PipeBuff1(self):	
		# Reset the RAM address pointer.
		self.xem.ActivateTriggerIn(0x50, 1)
		self.xem.ReadFromPipeOut(0xa1, buf)

	def PipeTest(self):	
		# Reset the pipe data counter
#		buf = bytearray('\x00'*128)
		buf = bytearray(64)
		self.xem.ActivateTriggerIn(0x50, 2)
		self.xem.ReadFromPipeOut(0xA2, buf)
		print('Pipe data received from Opal Kelly...')
		for x in range(0, 64):
			sys.stdout.write("%02x" % buf[x])
		print

                  


# Main code
ledval0 = 0xFF
ledval1 = 0xFF
loopcnt = 0

print ("------ Python Opal Kelly XLink Analyzer ------")
xlink = XLink()
if (False == xlink.InitializeDevice()):
	exit

# print firmware revision
xlink.GetDateCode()

mode = raw_input('Enter \'d\' for debug mode or \'r\' for real-time mode: ')
if mode == 'd':
	xlink.EnableDebug()
else:
	xlink.EnableRealTime()                


# start main loop
while(True):

	try:
		time.sleep(0.5)
		xlink.ToggleLED(ledval0, 1)
		ledval0 = (~ledval0 & 0xFF) # converts to an 8-bit unsigned value
		loopcnt+=1
		if (loopcnt == 10):
			xlink.ToggleLED(0xFF, 2) # value, bit mask
			time.sleep(0.1)
			xlink.ToggleLED(0x00, 2) # value, bit mask
			xlink.PipeTest()
			loopcnt = 0

	except KeyboardInterrupt:
		print 'Cleaning up and exiting...'
		xlink.DisableDevice()
		xlink.ResetFW()
		xlink.ToggleLED(0xFF, 1)
		xlink.ToggleLED(0xFF, 2)
		sys.exit(0)



