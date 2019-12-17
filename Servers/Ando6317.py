#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''Server (Qweather) to grab data from the AndoAQ6317 Optical Spectrum analyzer'''
from qweather import QWeatherServer, QMethod
import serial
import numpy as np
import time
import struct
import matplotlib.pyplot as plt

__author__ = 'Asbjorn Arvad Jorgensen'
__version__ = '1.0'
__email__ = 'Asbjorn.Arvad@nbi.ku.dk'

class Server(QWeatherServer):

    def __init__(self):
        self.QWeatherStationIP = "tcp://10.90.61.13:5559"
        self.servername = 'OpticalSpectrumAnalyzer'
        self.comport = 7       # Comport for the GPIB-to-USB controller
        self.GPIB_addr = 2 # GPIB address of the HPIB.
        self.verbose = False
        self.debug = False
        self.initialize_sockets()
        print('*'*50)
        print('Server Online')
        self.initialize_hardware()
        print('polling')
        print(self.GPIB_read_srq())
        print('Polled')

    def initialize_hardware(self):
        try:
            self.GPIB = serial.Serial( 'COM{:d}'.format(self.comport), 9600, timeout=10) # Initialise the serial port.
        except serial.serialutil.SerialException as e:
            print('Wrong com port specified (',str(self.comport),') try running "python -m serial.tools.list_ports"')
            raise e 
        self.GPIB.write(b"++mode 1\n")                       # Set controller mode.
        self.GPIB.write(("++addr " + str(self.GPIB_addr) + "\n").encode())  # Set GPIB address.
        self.GPIB.write(b"++auto 0\n")                       # Disable read-after-write.
        self.GPIB.write(b"++eoi 1\n")      
        self.GPIB.write("SRMSK0\n".encode())
        self.GPIB.write("SRQ1\n".encode())
#        self.GPIB.write(b"++status 48\n")    
        print(self.GPIB_ask('SRQ?\n',16))   

        GPIB_id = self.GPIB_ask("*IDN?\n", 16)
        print(GPIB_id)
        print('*'*50)

    def GPIB_ask(self,cmd_str, bytes):
        self.GPIB.write(cmd_str.encode())
        time.sleep(2)
        self.GPIB.write("++read eoi\n".encode())
        answer = self.GPIB.readline().decode()
        return answer

    def GPIB_read_srq(self):
        print(self.GPIB.write(b"++srq"))
        answer = self.GPIB.read()
        return answer

    @QMethod
    def getSpectrum(self):
        '''Gets the spectrum currently on the spectrum analyzer'''
        sampling = self.GPIB_ask("SMPL?\n", 16)
        print(sampling)
        sampling = int(sampling)
        readlist = [i for i in range(0,sampling,1000)]
        rest = sampling%1000
        amplitudes = []
        wavelength = []
        if sampling > 1000:
            for j in range(len(readlist)):
                print('Getting amplitude data {:d} to {:d}'.format(readlist[j] +1,readlist[j]+1000))
                data = self.GPIB_ask("LDATA R{:d}-R{:d}\n".format(readlist[j] +1,readlist[j]+1000), 16)   # Asks for the amplitudes of trace A.            
                for apoint in data.strip().split(',')[1:]:
                    amplitudes.append(float(apoint))
                print(len(amplitudes))
            if rest > 1:
                data = self.GPIB_ask("LDATA R{:d}-R{:d}\n".format(readlist[-1] +1,readlist[-1]+rest), 16)   # Asks for the amplitudes of trace A.            
                for apoint in data.strip().split(',')[1:]:
                    amplitudes.append(float(apoint))
        

            
            for j in range(len(readlist)):
                print('Getting wavelength data {:d} to {:d}'.format(readlist[j] +1,readlist[j]+1000))
                data = self.GPIB_ask("WDATA R{:d}-R{:d}\n".format(readlist[j] +1,readlist[j]+1000), 16)   # Asks for the amplitudes of trace A.            
                for apoint in data.strip().split(',')[1:]:
                    wavelength.append(float(apoint))
            if rest > 1:
                data = self.GPIB_ask("WDATA R{:d}-R{:d}\n".format(readlist[-1] +1,readlist[-1]+rest), 16)   # Asks for the wavelength of trace A.            
                for apoint in data.strip().split(',')[1:]:
                    wavelength.append(float(apoint))

        else:
            print('Getting amplitude data 1 to {:d}'.format(sampling))
            data = self.GPIB_ask("LDATA R1-R{:d}\n".format(sampling), 16)   # Asks for the amplitudes of trace A.            
            for apoint in data.strip().split(',')[1:]:
                amplitudes.append(float(apoint))
            print(len(amplitudes))

            print('Getting wavelength data 1 to {:d}'.format(sampling))
            data = self.GPIB_ask("WDATA R1-R{:d}\n".format(sampling), 16)   # Asks for the amplitudes of trace A.            
            for apoint in data.strip().split(',')[1:]:
                wavelength.append(float(apoint))
            print(len(wavelength))
            self.GPIB.write("++read eoi\n".encode())
            answer = self.GPIB.readline().decode()
            print(answer)
            fname = 'Z:/SPOC/Mikroringe/Chalmers Ringe/Wafer242-singlering-D500/20191213/wafer242-singlering-D500-Gap2-W1540p81-P27p5dBm-OSA-sweep3'
            with open(fname + '.txt','w') as f:
                print('Saving data...')
                f.write('Wavelength [nm] \t Amplitude [dBm]\n')
                for wav,amp in zip(wavelength,amplitudes):
                    f.write(str(wav) + '\t' + str(amp) + '\n')
        return [wavelength,amplitudes]




if __name__ == "__main__":
    server = Server()
    server.run()


