from asyncio import queues
from winpcapy import WinPcapDevices
from winpcapy.winpcapy import WinPcapUtils, WinPcap
import winpcapy.winpcapy_types as wtypes
import os, time, json, threading
import protocol_types as p_types
from colorama import init, Fore, Back, Style

import asyncio
import websocket as ws

# DEVICE = "Intel(R) Ethernet Connection (2) I219-V"


test_package = b"Xil_\xb3\xea\x00\xd8a\x11Dt\x08\x00E\x00\x01\x14\xeb\xd8\x00\x00\x80\x11\x00\x00\n\x80\x81\\/to\x89\xd7\x8bVV\x01\x00+\xeb\xb7Q\x00\x00\xb2\x93\xb0)Q\x00\x00\x01\xc7#.\xe4\xb0\x7f\x02\x00^\x17\x01\x00\xdc\x00\x00\x00\xd8\x94\xb4-\x01\xda9\xfe\x14\x19\xa2u\xb51d)\x86D\xa0\x07\x8aH\x92\x1bRZ\xfdqg\xcf\xf9\xfa\x87\x88\x83\xe44qu\xc3\xf9\xda\x93\xdc1!D\xc2\x1b\xf7 \x0cPDY\x03\xc5;k&Iu3\xef\x98t\x19\xbf\xc9\xc0\xd4>\x12\xfc.\x1f[\x9a\xeb\xcd#\xcf,<\xf1Z\xcb\xb8\xa58\xe71T\xda\xbc\x15\xd2\x1c>\x1aM:'\xf6\x18k\xb1[\x89qT8\xd5j\xbb\xe1\xdf\xe44z\xf1Ew\x14\xa0\xf6\x03,\xa2]k0x\x06\xda\xf3\xeb5\x8f\xbe\xd3\x17\xc1\x01\x9a\xc4[\xbf\x0eV\xac&\xa8\t\xce\xd5~\x84\xd8i}\x169ug\xc1t\xb6l\xa1\xe6\xc4\xdd6\x18y\xeb\xcef\xa7\x95\x8f\x87`\xde\xdf\x01\xfb\xbf\xd4\xfb\x8d\xf2\xe7\x9bH\x04\xb0=P\xf2w\xcaq\x15\x7f\x84\xe2\xa7\xa5\x9a\xc5\x92\"0\xc6`\xcd=\xe0"


class Package:
    def __init__(self, raw_data):
        # data link layer
        self.frame_type_dict = {
            2048: "ipv4",
            2054: "arp",
            34916: "PPPoE",
            33024: "802.1Q",
            34525: "ipv6",
        }
        self.frame_header, self.frame_tail = raw_data[:14], raw_data[-4:]
        self.frame_type = self.frame_type_dict.get(
            int.from_bytes(self.frame_header[12:14], "big")
        )
        self.frame_type = "Unknown" if not self.frame_type else self.frame_type
        self.ip_package = raw_data[14:-4] if raw_data != None else None
        # ip header
        self.ip_version = None
        self.ihl = None
        # self.ver_ihl = None # ip version and ip package head length
        self.tos = None  # type of service
        self.tlen = None  # total length
        self.identification = None  # 标识(Identification)
        self.flags = None
        self.offset = None
        self.flags_fo = None  # 标志位(Flags) (3 bits) + 段偏移量(Fragment offset) (13 bits)
        self.ttl = None  # 存活时间(Time to live)
        self.proto = None  # 协议(Protocol)
        self.crc = None  # 首部校验和(Header checksum)
        self.saddr = None  # 源地址(Source address) with 4 byte
        self.daddr = None  # 目的地址(Destination address)
        self.op_pad = None  # 选项与填充(Option + Padding)
        # udp header
        self.src_port = None  # 源端口(Source port)
        self.dist_port = None  # 目的端口(Destination port)
        self.len = None  # UDP数据包长度(Datagram length)
        self.crc = None  # 校验和(Checksum)

        self.parse()

    @staticmethod
    def parse_ip(ip_raw):
        return ".".join([str(i) for i in ip_raw])

    def _frame_header(self):
        frame = {
            "source_mac": self.smac,
            "destination_src": self.dmac,
            "frame_type": self.frame_type,
            "frame_check_sequence": bin(int.from_bytes(self.frame_tail, "big")),
        }
        return json.dumps(frame)

    @staticmethod
    def _to_int_str(b):
        return int.from_bytes(b)

    @staticmethod
    def _to_hex_str(b):
        return " ".join([hex(i)[2:].zfill(2) for i in b])

    @staticmethod
    def get_protocol(protocol):
        return (
            p_types.unassigned
            if not p_types.protocols.get(protocol)
            else p_types.protocols.get(protocol)
        )

    def _ip_header(self):
        ip = {
            "ip_version": self.ip_version,
            "ip_head_length": self.ihl,
            "type_of_service": self.tos,
            "tlen": self.tlen,
            "identification": self._to_hex_str(self.identification),
            "flags": self.flags,
            "fragment_offset": self.offset,
            "time_to_live": self.ttl,
            "protocol": self.get_protocol(self.proto),
            "header_checksum": str(bin(self.crc)),
            "source_address": self.parse_ip(self.saddr),
            "destination_address": self.parse_ip(self.daddr),
            "option": self._to_hex_str(self.option_padding),
            "data": self._to_hex_str(self.ip_data),
        }
        return json.dumps(ip)

    @staticmethod
    def parse_mac(raw):
        if len(raw) != 6:
            return ""
        return ":".join([hex(i)[2:].zfill(2) for i in raw])

    def parse(self):
        # frame head parsing
        self.dmac, self.smac = self.parse_mac(self.frame_header[:6]), self.parse_mac(
            self.frame_header[6:12]
        )

        # ip package head parsing
        self.ip_version, self.ihl = self.ip_package[0] >> 4, self.ip_package[0] & 15
        self.tos = self.ip_package[1]
        self.tlen_raw = self.ip_package[2:4]
        self.tlen = int.from_bytes(self.tlen_raw, "big")
        self.identification = self.ip_package[4:6]
        self.flags_fo = int.from_bytes(self.ip_package[6:8], "big")
        self.flags, self.offset = self.flags_fo >> 13, self.flags_fo & ((1 << 14) - 1)
        self.ttl, self.proto = self.ip_package[8], self.ip_package[9]
        self.crc = int.from_bytes(self.ip_package[10:12], "big")
        self.saddr = self.ip_package[12:16]
        # self.saddr = int.from_bytes(self.ip_package[12:16], 'big')
        self.daddr = self.ip_package[16:20]
        # self.daddr = int.from_bytes(self.ip_package[16:20], 'big')
        self.option_padding = self.ip_package[20 : self.ihl << 2]
        self.ip_data = self.ip_package[(self.ihl << 2) :]
        # parse data


# class PKG_Filter:
#   def __init__(self):
#     self.
# WinPcapDevices.list_devices()
class MyPcap(object):
    def __init__(self, device_name, snap_length=65536, promiscuous=1, timeout=1000):
        self.device_name = device_name
        self.pcap = None
        self._handler = None
        self.pcap_pkthdr = wtypes.pcap_pkthdr()

    def listener(self, handler):
        self._handler = handler

    def open(self, name):
        self.pcap._name = name
        self.pcap.__enter__()

    def run(self):
        device_real_name, desc = WinPcapDevices.get_matching_device(self.device_name)
        with WinPcap(device_real_name) as capture:
            if not self._handler:
                print("\033[30;1m ERROR: No handler")
            else:
                capture.run(callback=self._handler, limit=4)
        return True

    def next(self):
        # if not self._handler:
        # print("\033[30;1m ERROR: No handler")
        s = wtypes.pcap_next(callback=self.pcap._handle, limit=self.pcap_pkthdr)
        print(s)

    def stop(self):
        self.pcap.stop()

    def close(self):
        self.pcap.__exit__(None, None, None)
package_queue = []
# mp = MyPcap("Intel(R) Ethernet Connection (2) I219-V")
con = None
t1 = None
mp = None
class myThread(threading.Thread):
    def __init__(self, threadID, name, counter):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.package_queue = []
        self.stop = False

    def terminate(self):
        self.stop = True

    def run(self):
        global con
        package_queue = self.package_queue
        print("Starting " + self.name)
        while not self.stop:
            time.sleep(1)

            print("Current queue: " + str(len(package_queue)))
            if len(package_queue) == 0:
                continue
            print("inner con:",con)
            con.send(package_queue.pop(0)._ip_header())
            
        print("Exiting " + self.name)
# async def check_connection(_ws):
#   while True:
#     response_str = await _ws.recv()
#     if len(response_str) > 0:
#       print("RESPONSE: {}".format(str(response_str)))
#       return True
#     time.sleep(1)
#     print("Connecting...")

# def onmessage(ws, msg):
#   if msg.
def mainprocess():
    global package_queue, mp, con, t1
    con = ws.create_connection("ws://127.0.0.1:8083/")
    mp = MyPcap("Intel(R) Ethernet Connection (2) I219-V")
    @mp.listener
    def pkg_callback(win_pcap, param, header, pkt_data):
        global package_queue,con
        time.sleep(5)
        p = Package(pkt_data)
        con.send(p._ip_header())
        print(p._ip_header())
        print(pkt_data)
        print("-------------------")
    mp.run()
    con.close()
        # mp.run()





mainprocess()


# with WinPcap(DEVICE) as capture:
# capture.run(callback=pkg_callback)
# def capture_on(pattern, callback):
#         """
#         :param pattern: a wildcard pattern to match the description of a network interface to capture packets on
#         :param callback: a function to call with each intercepted packet
#         """
#         device_name, desc = WinPcapDevices.get_matching_device(pattern)
#         print(type(device_name), device_name)
#         if device_name is not None:
#             with WinPcap(device_name) as capture:
#                 capture.run(callback=callback, limit=5)

# capture_on(DEVICE, pkg_callback)





# class A:
#   def __init__(self):
#     self.handler = None
#   def listener(self, handler):
#     self.handler = handler
#   def run(self):
#     if not self.handler:
#       print("ERROR")e
#     else:
#       self.handler()

# app = A()
# @app.listener
# def myhandler():
#   print("Im handler!")

# app.run()