#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''Server (Qweather) to grab data from the HP8561B Spectrum analyzer'''
from qweather import QWeatherServer, QMethod
import visa
import serial
import numpy as np
import time
import struct
__author__ = 'Asbjorn Arvad Jorgensen'
__version__ = '1.0'
__email__ = 'Asbjorn.Arvad@nbi.ku.dk'

class Server(QWeatherServer):

    def __init__(self):
        self.QWeatherStationIP = "tcp://10.90.61.13:5559"
        self.servername = 'SpectrumAnalyzer'
        self.comport = 2       # Comport for the GPIB-to-USB controller
        self.GPIB_addr = 18 # GPIB address of the HPIB.
        self.verbose = False
        self.debug = False
        self.initialize_sockets()
        print('*'*50)
        print('Server Online')
        self.initialize_hardware()
        self.saveSpectrum('Z:/Sr1/Repumpers/Locking/Beats/20191212 - Clock laser')

    def initialize_hardware(self):
        self.GPIB = serial.Serial( 'COM5', 9600, timeout=10) # Initialise the serial port.
        self.GPIB.write(b"++mode 1\n")                       # Set controller mode.
        self.GPIB.write(("++addr " + str(self.GPIB_addr) + "\n").encode())  # Set GPIB address.
        self.GPIB.write(b"++auto 0\n")                       # Disable read-after-write.
        GPIB_id = self.GPIB_ask("ID?;\n", 16)
        print(GPIB_id)
        print('*'*50)

    def GPIB_ask(self,cmd_str, bytes):
        self.GPIB.write(cmd_str.encode())
        self.GPIB.write("++read eoi\n".encode())
        answer = self.GPIB.readline().decode()
        return answer

    @QMethod
    def getSpectrum(self):
        '''Gets the spectrum currently on the spectrum analyzer'''
        self.GPIB.write("TDF P;\n".encode())             # Formats trace data to ASCII decimal values.
        data = self.GPIB_ask("TRA?;\n", 10240)   # Asks for the amplitudes of trace A.
        amplitudes = data.split(',')
        n = len(amplitudes)

        frequency = []
        start_freq = self.GPIB_ask("FA?;\n",16)  # Asks for the start frequency.
        end_freq = self.GPIB_ask("FB?;\n",16)    # Asks for the stop frequency.

        for i in range(n):  # Loop that converts amplitude from datatype string to float 
                            # and creates an array of frequency values corresponding to 
                            # start_freq and slut_freq.
            amplitudes[i] = float(amplitudes[i])
            frequency.append( float(start_freq)+(i)*(float(end_freq)-float(start_freq))/(n-1))
        return [frequency,amplitudes]


    @QMethod
    def saveSpectrum(self,savelocation):
        frequency,amplitudes = self.getSpectrum()
        filename = savelocation + "/SpectrumAnalyzerData_" + time.strftime("%H%M%S") + ".csv"
        with open(filename, "w") as myfile:
            myfile.writelines("Frequency [Hz], Amplitude [dBm]\n")
            for i in range(len(frequency)):
                myfile.write(str(frequency[i]) + '\t' + str(amplitudes[i]) + '\n')
        myfile.close()



if __name__ == "__main__":
    server = Server()
    server.run()


