from winpcapy import WinPcapDevices
from winpcapy import WinPcapUtils, WinPcap
import winpcapy.winpcapy_types as wtypes
import os, time
from colorama import init,Fore,Back,Style

DEVICE = 'Intel(R) Ethernet Connection (2) I219-V'


test_package = b'Xil_\xb3\xea\x00\xd8a\x11Dt\x08\x00E\x00\x01\x14\xeb\xd8\x00\x00\x80\x11\x00\x00\n\x80\x81\\/to\x89\xd7\x8bVV\x01\x00+\xeb\xb7Q\x00\x00\xb2\x93\xb0)Q\x00\x00\x01\xc7#.\xe4\xb0\x7f\x02\x00^\x17\x01\x00\xdc\x00\x00\x00\xd8\x94\xb4-\x01\xda9\xfe\x14\x19\xa2u\xb51d)\x86D\xa0\x07\x8aH\x92\x1bRZ\xfdqg\xcf\xf9\xfa\x87\x88\x83\xe44qu\xc3\xf9\xda\x93\xdc1!D\xc2\x1b\xf7 \x0cPDY\x03\xc5;k&Iu3\xef\x98t\x19\xbf\xc9\xc0\xd4>\x12\xfc.\x1f[\x9a\xeb\xcd#\xcf,<\xf1Z\xcb\xb8\xa58\xe71T\xda\xbc\x15\xd2\x1c>\x1aM:\'\xf6\x18k\xb1[\x89qT8\xd5j\xbb\xe1\xdf\xe44z\xf1Ew\x14\xa0\xf6\x03,\xa2]k0x\x06\xda\xf3\xeb5\x8f\xbe\xd3\x17\xc1\x01\x9a\xc4[\xbf\x0eV\xac&\xa8\t\xce\xd5~\x84\xd8i}\x169ug\xc1t\xb6l\xa1\xe6\xc4\xdd6\x18y\xeb\xcef\xa7\x95\x8f\x87`\xde\xdf\x01\xfb\xbf\xd4\xfb\x8d\xf2\xe7\x9bH\x04\xb0=P\xf2w\xcaq\x15\x7f\x84\xe2\xa7\xa5\x9a\xc5\x92"0\xc6`\xcd=\xe0'

# class PKG_Filter:
#   def __init__(self):
#     self.
# WinPcapDevices.list_devices()
class MyPcap:
  def __init__(self,device_name, snap_length=65536, promiscuous=1, timeout=1000):
    self.pcap = WinPcap(device_name)
    self.pcap.__enter__()
    self._handler = None
  def listener(self, handler):
    self.pcap._callback = self._handler = handler
  def open(self, name):
    self.pcap._name = name
    self.pcap.__enter__()
  def run(self):
    if not self._handler:
      print("\033[30;1m ERROR: No handler")
    self.pcap.run(self._handler)
  def stop(self):
    self.pcap.stop()
  def close(self):
    self.pcap.__exit__(None, None, None)


mp = MyPcap('Intel(R) Ethernet Connection (2) I219-V')
@mp.listener
def pkg_callback(win_pcap, param, header, pkt_data):
  time.sleep(5)
  # if(os.path.exists("x.bin")):
  #   pass
  # else:
  #   with open("x.bin", 'wb') as f:
  #     f.write(pkt_data)
  print(pkt_data)
  print("-------------------")


class myThread (threading.Thread): 
    def __init__(self, threadID, name, counter):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
        self.stop = False
    def terminate(self):
        self.stop = True
    def pkg_callback(self, win_pcap, param, header, pkt_data):
      self.counter += 1
      if(self.counter > 5):
        return
      time.sleep(5)
      print(pkt_data)
      if(os.path.exists("x.bin")):
        self.terminate = True
        pass
      else:
        with open("x.bin", 'wb') as f:
          f.write(pkt_data)
    def run(self):  
        print("Starting " + self.name)
        devices = list(WinPcapDevices.list_devices().values())[0]
        WinPcapUtils.capture_on(pattern=devices, callback=self.pkg_callback)
        print( "Exiting " + self.name)



class A:
  def __init__(self):
    self.handler = None
  def listener(self, handler):
    self.handler = handler
  def run(self):
    if not self.handler:
      print("ERROR")
    else:
      self.handler()

app = A()
@app.listener
def myhandler():
  print("Im handler!")

app.run()