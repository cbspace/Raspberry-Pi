import smbus
import time
import string
import ctypes

class BMP085:

        # Constructor
        def __init__(self):
                self.bus = smbus.SMBus(1)
                self.address = 0x77
                self.b5 = 0
                self.temperature = 0.0
                self.pressure = 0.0

        # Write byte to i2c
        def write(self, reg, value):
                self.bus.write_byte_data(self.address, reg, value)
                return -1
                
        # Read byte from i2c
        def read(self, reg):
                data = self.bus.read_word_data(self.address, reg)
                low = data >> 8
                high = (data & 0x00FF) << 8
                data = low + high
                return data
                
        # Format hex number
        def nicehex(self,n):
                return format(n,'x').upper()
                
        # Read config registers
        def getconfig(self):
                for a in range(0xAA,0xBF,2):
                        data = self.read(a)
                        print self.nicehex(a),":",self.nicehex(data)
                        
        # Calcualate Temperature
        def calc_temp(self,ut):
                
                ac5 = 0x5F18
                ac6 = 0x4ACE
                mc = ctypes.c_short(0xD4BD).value
                md = ctypes.c_short(0x980).value

                ut = ctypes.c_long(ut).value
                x1 = (ut - ac6) * ac5 / 32768
                x1 = ctypes.c_long(x1).value
                x2 = mc * 2048 / (x1 + md)
                x2 = ctypes.c_long(x2).value
                self.b5 = x1 + x2
                self.b5 = ctypes.c_long(self.b5).value
                t = (self.b5 + 8) / 16
                t = ctypes.c_long(t).value
                t = t / 10.0
                return t

        # Calculate Pressure
        def calc_pressure(self,up):
                
                #constants
                oss = 0
                ac1 = ctypes.c_short(0x22E8).value
                ac2 = ctypes.c_short(0xFB2A).value
                ac3 = ctypes.c_short(0xC7C9).value
                ac4 = 0x8A32
                ac5 = 0x5F18
                ac6 = 0x4ACE
                b1 = ctypes.c_short(0x157A).value
                b2 = ctypes.c_short(0x43).value
                mb = ctypes.c_short(0x8000).value
                mc = ctypes.c_short(0xD4BD).value
                md = ctypes.c_short(0x980).value

                #calculations
                up = ctypes.c_long(up).value
        ##	print up
                b6 = self.b5 - 4000
                b6 = ctypes.c_long(b6).value
        ##	print b6
                x1 = (b2 * (b6 * b6 / 4096)) / 2048
                x1 = ctypes.c_long(x1).value
        ##	print x1
                x2 = ac2 * b6 / 2048
                x2 = ctypes.c_long(x2).value
        ##	print x2
                x3 = x1 + x2
                x3 = ctypes.c_long(x3).value
        ##	print x3
                b3 = (((ac1*4+x3) << oss) + 2) / 4
                b3 = ctypes.c_long(b3).value
        ##	print b3
                x1 = ac3 * b6 / 8192
                x1 = ctypes.c_long(x1).value
        ##	print x1
                x2 = (b1 * (b6 * b6 / 4096)) / 65536
                x2 = ctypes.c_long(x2).value
        ##	print x2
                x3 = ((x1 + x2) +2) / 4
                x3 = ctypes.c_long(x3).value
        ##	print x3
                b4 = ac4 * ctypes.c_ulong((x3 + 32768)).value / 32768
        ##	print b4
                b7 = (ctypes.c_ulong(up).value - b3) * (50000 >> oss)
        ##	print b7
                p = (b7 * 2 ) / b4 if (b7 < 0x80000000) else (b7/b4) * 2
                p = ctypes.c_long(p).value
        ##	print p
                x1 = (p / 256) * (p/256)
                x1 = ctypes.c_long(x1).value
        ##	print x1
                x1 = (x1 * 3038) / 65536
                x1 = ctypes.c_long(x1).value
        ##	print x1
                x2 = (-7357 * p) / 65536
                x2 = ctypes.c_long(x2).value
        ##	print x2
                p = p + (x1 + x2 + 3791) / 16
                p = ctypes.c_long(p).value
                p = p/100.0
                return p

        def update(self):
                # Update Temperature
                self.write(0xF4,0x2E)
                time.sleep(0.1)
                t = self.read(0xF6)
                self.temperature = self.calc_temp(t)
                # Update Pressure
                self.write(0xF4,0x34)
                time.sleep(0.1)
                p = self.read(0xF6)
                self.pressure = self.calc_pressure(p)

        def calc_alt(self,p):
                po = 1016.6
                alt = 44330*(1-pow(p/po,1/5.255))
                return alt

        def get_temp(self):
                return self.temperature

        def get_pressure(self):
                return self.pressure


