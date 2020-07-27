import time
import datetime
import numpy as np
import struct
from qweather import QWeatherServer, QMethod
import threading
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt

import visa
import os
class logging_thread(threading.Thread):
    
    def __init__(self, *args, **kwargs):
        super(logging_thread, self).__init__(*args, **kwargs)
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()

class Server(QWeatherServer):

    def __init__(self):
        self.QWeatherStationIP = "tcp://10.90.61.231:5559"
        self.servername = 'FreqCounter'
        self.USBport = 'USB0::0x14EB::0x0090::410690::INSTR'
        self.verbose = False
        self.debug = False
        self.initialize_sockets()
        print('*'*50)
        print('Server Online')
        self.initialize_hardware()

        #measTime = 6000
        #print('{:d} s measurement initiated at: '.format(measTime) + str(datetime.datetime.now().astimezone()) + '\n')
        #self.log_frequency(10000,100e-3,measTime,'Z:/Acetylene/AllanDevs/180918/PendulumLogging2343.txt')
        #print('Measurement done at: ' + str(datetime.datetime.now().astimezone()) + '\n')

    def initialize_hardware(self):
        rm = visa.ResourceManager()
        self.hardware = rm.open_resource(self.USBport)
        print('Frequency counter server running. Made contact with:')
        print(self.hardware.query('*IDN?'))
        print('*'*50)
        self.hardware.write('*cls;*rst')
        self.hardware.write('*ese 0;*sre 0')
        self.hardware.write('AUTO ONCE;:INP:IMP 50;')

        self.hardware.timeout=15000



    @QMethod
    def get_frequency(self,Npoints = None,gatetime = None, chan = 1,binary = False):
        """Return the currently measured frequency"""
        if Npoints is None:
            num = self.hardware.query('MEAS:FREQ?,(@{:d})'.format(chan))
            print(num)
        else:
#            self.hardware.write(':DISP:ENAB OFF;:CAL:INT:AUTO 0;:FREQ:REGR OFF;')
            self.hardware.write(':CONF:ARR:FREQ ({:d}),(@{:d});:DISP:ENAB OFF;:CAL:INT:AUTO 0;:FREQ:REGR OFF;:FORM:TINF ON;:FORM PACK;:INP2:IMP 50;:ACQ:APER {:.9f};:INIT;'.format(Npoints,chan,gatetime))

            while True:
                try:
                    check = self.hardware.query('*OPC?')
                    break
                except Exception:
                    pass
            self.hardware.write('FETC:ARR? {:d}'.format(Npoints))
            num = self.hardware.read_raw()
            #print(num)
#            num = self.hardware.query_binary_values('FETC:ARR? {:d}'.format(Npoints), datatype='s', is_big_endian=True)
        if not binary:
            num = self.convert_binary_to_float(num,Npoints)
        return num

    @QMethod
    def get_timestamp(self,Npoints = None,gatetime = None, binary = False):
        """Return the timestamps of zerocrossings"""
        print('measuring timestamp')
        self.hardware.write(":DISP:ENAB OFF;:CAL:INT:AUTO 0;:FREQ:REGR OFF;TRIG:SOUR TIM; :TRIG:TIM {:.9f};:FORM:TINF OFF".format(gatetime,gatetime))
        num = self.hardware.query('MEAS:ARR:TSTA? 9600').split(',')
        print(len(num))
        num  = [float(i) for i in num]
        print(len(num))
        Tneg = num[1::4]
        Npos = num[2::4]
        Tpos = num[3::4]
        for i in range(0,len(Tneg),2):
            freq1 = (Npos[i+1] - Npos[i])/(Tpos[i+1] - Tpos[i])
            freq2 = (Npos[i+1] - Npos[i])/(Tneg[i+1] - Tneg[i])
            print(i,freq1*1e-3,freq2*1e-3,(Npos[i+1] - Npos[i]),(Tpos[i+1] - Tpos[i]))

        return num

    @QMethod
    def log_frequency(self,gatetime,savelocation,logtime,chan,syncronize = False):
        """Logs the frequency at a certain gatetime and stores it in a textfile at a location"""
        self.hardware.write(':CONF:FREQ (@{:d})'.format(chan))
        self.hardware.write(':DISP:ENAB OFF;:CAL:INT:AUTO 0;:FREQ:REGR OFF;')
        self.hardware.write(':TRIG:COUN 1;:ARM:COUN 750000;:FORM:TINF ON')
        self.hardware.write(':FORM PACK')
        self.hardware.write(':INP{:d}:IMP 50;:ACQ:APER {:.9f}s'.format(chan,gatetime))

        self.hardware.write(':INP{:d}:LEV:AUTO OFF;:INP{:d}:LEV 0'.format(chan,chan))
        if syncronize:
            self.hardware.write(':ARM:SOUR EXT4')
        else:
            self.hardware.write(':ARM:SOUR IMM')

        self.logthread = logging_thread(target = self.do_logging,args =(gatetime,savelocation,logtime))
        self.logthread.start()


    def do_logging(self,gatetime,savelocation,logtime):
        date = datetime.datetime.now().strftime('%H%M')
        with open(savelocation + '/' +  date + '.txt', 'w') as f:

            f.write('Measurement started at: ' + str(datetime.datetime.now()) + '\n')
            f.write('Counter: Pendulum CNT90\n')
            f.write('Gatetime: {:f}\n'.format(gatetime))
            self.hardware.write(':INIT') #initiate measurement
            print(self.hardware.query(':SYST:ERR?'))
            if gatetime<10e-6:
                time.sleep(10e-3)
                self.hardware.write(':ABOR')    
            else:
                while not self.logthread.stopped():
                    pass
                print('stopping')
                self.hardware.write(':ABOR')


            Npoints = 2
            self.hardware.write('FETC:ARR? ({:d})'.format(Npoints))
            data = self.hardware.read_raw()
            print(data)
            data = self.convert_binary_to_float(data,Npoints)
            numarray = data
            print(data)
            t0 = data[1][0]
            tend = data[1][-1]- t0
            tendprev = 0
            failed=False
            while (tend < logtime and  tend > tendprev and Npoints > 0):
                print('getting data')
                self.hardware.write('FETC:ARR? ({:d})'.format(Npoints))
                data = self.hardware.read_raw()
                data = self.convert_binary_to_float(data,Npoints)
                if data is None:
                    Npoints = Npoints//2
                    print('smaller array',Npoints)
                else:
                    tendprev = tend 
                    tend = data[1][-1] - t0
                    if tend > tendprev:
                        numarray = np.append(numarray,data,axis=1)
                    if Npoints < 10000:
                        Npoints = 10000
                        print('larger array',Npoints)

            for i in range(len(numarray[0])):
                freq = numarray[0][i]
                times = numarray[1][i]
                f.write("{:.10f}, {:.10f}\n".format(times,freq))
            print('Done writing file')
            time.sleep(0.5)




    @QMethod
    def stop_logging(self):
        self.logthread.stop()


    @QMethod
    def recall_frequency(self,memlocation,Npoints=32000):
        print('Recalling points from {:d}'.format(memlocation))
        timestamp,freq = [[],[]]
        self.hardware.write(':MEM:DATA:REC:FETC:STAR {:d}'.format(memlocation) )
        if Npoints == 32000:
            for _ in range(3):
                self.hardware.write(':MEM:DATA:REC:FETC:ARR? {:d},10000'.format(memlocation) )
                a = self.hardware.read_raw()
                a = self.convert_binary_to_float(a,10000)
                timestamp = np.append(timestamp,a[1])
                freq = np.append(freq,a[0])
            self.hardware.write(':MEM:DATA:REC:FETC:ARR? {:d},2000'.format(memlocation) )
            a = self.hardware.read_raw()
            a = self.convert_binary_to_float(a,2000)
            timestamp = np.append(timestamp,a[1])
            freq = np.append(freq,a[0])
        return [timestamp,freq]

    @QMethod
    def convert_binary_to_float(self,binary,Npoints):
        data = [[],[]]
        if binary[:4] == b'#216':
            print('Bad reading, error message. Probably tried to read more points than was available')
            return None
        cleanbinary = binary[int(4+np.floor(np.log10(Npoints))):-1]

        if len(cleanbinary)%16 == 1:
            #For some odd reason the last measurement in the output buffer has a tendency of having an extra bit?
            cleanbinary = binary[int(5+np.floor(np.log10(Npoints))):-1]
        if len(cleanbinary)%16 != 0:
            cleanbinary = cleanbinary[:len(cleanbinary)-len(cleanbinary)%16]
        if len(cleanbinary) == 0:
            #print('length is zero')
            return None
        else:
            adata = np.zeros((2,int(len(cleanbinary)/16)))
            for i in range(0,len(cleanbinary),16):
                freqb = cleanbinary[i:i+8]
                timeb = cleanbinary[i+8:i+16]
                freq = struct.unpack('>d',freqb)[0]
                time = int.from_bytes(timeb, 'big')
                adata[0,int(i/16)] = freq
                adata[1,int(i/16)] = time*1e-12 #To make it from pico seconds to seconds
            data = np.append(data,adata,axis=1)
            return data

if __name__ == "__main__":
    server = Server()
    server.run()


