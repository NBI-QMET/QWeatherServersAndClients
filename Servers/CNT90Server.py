import time
import numpy as np
import struct
from qweather import QWeatherServer, QMethod

import visa

class Server(QWeatherServer):

    def __init__(self):
        self.QWeatherStationIP = "tcp://172.24.22.3:5559"
        self.servername = 'FreqCounter'
        self.USBport = 'USB0::0x14EB::0x0090::410690::INSTR'
        self.verbose = False
        self.debug = False
        self.initialize_sockets()
        print('*'*50)
        print('Server Online')
        self.initialize_hardware()

    def initialize_hardware(self):
        rm = visa.ResourceManager()
        self.hardware = rm.open_resource(self.USBport)
        print('Frequency couner server running. Made contact with:')
        print(self.hardware.query('*IDN?'))
        print('*'*50)
        self.hardware.write('*RST')
        self.hardware.write('AUTO ONCE;:INP:IMP 50;')

        self.hardware.timeout=100000



    @QMethod
    def get_frequency(self,Npoints = None,gatetime = None, binary = False):
        """Return the currently measured frequency"""
        if Npoints is None:
            num = self.hardware.query('MEAS:FREQ?')
        else:
            self.hardware.write('ABOR;:CONF:ARR:FREQ ({:d});:FORM:TINF ON;:FORM PACK;:INP:IMP 50;:ACQ:APER {:.9f};:INIT;:DISP:ENAB 0'.format(Npoints,gatetime))
            while True:
                try:
                    check = self.hardware.query('*OPC?')
                    break
                except Exception:
                    pass
            self.hardware.write('FETC:ARR? {:d}'.format(Npoints))
            num = self.hardware.read_raw()
#            num = self.hardware.query_binary_values('FETC:ARR? {:d}'.format(Npoints), datatype='s', is_big_endian=True)
        if not binary:
            num = self.convert_binary_to_float(num)
        return num

    @QMethod
    def log_frequency(self,Npoints = None,gatetime = None,logtime = None, binary = False):
        """Logs the frequency for a set amount of time
           log_frequency(Npoints (int), gatetime (seconds), loggingtime (seconds)"""
        self.hardware.write('ABOR;:CONF:ARR:FREQ ({:d});:FORM:TINF ON;:FORM PACK;:INP:IMP 50;:ACQ:APER {:.9f};:INIT;:DISP:ENAB 0'.format(Npoints,gatetime))
        numarray = []
        tic = time.time()
        toc = time.time()
        while toc-tic < logtime:
            self.hardware.write('FETC:ARR? {:d}'.format(Npoints))
            numarray.append(self.hardware.read_raw())
            toc = time.time()
        if not binary:
            numarray = self.convert_binary_to_float(numarray)#[self.convert_binary_to_float(ameas) for ameas in numarray]
        return numarray

    def convert_binary_to_float(self,binary):
        if not isinstance(binary,list):
            binary = binary[0]
        data = [[],[]]
        for abinary in binary:
            abinary = abinary[4:-1]
            adata = np.zeros((2,int(len(abinary)/16)))
            for i in range(0,len(abinary),16):
                freqb = abinary[i:i+8]
                timeb = abinary[i+8:i+16]
                freq = struct.unpack('>d',freqb)[0]
                time = int.from_bytes(timeb,'big')
                adata[0,int(i/16)] = freq
                adata[1,int(i/16)] = time
            data = np.append(data,adata,axis=1)
        return data




if __name__ == "__main__":
    server = Server()
    server.run()


