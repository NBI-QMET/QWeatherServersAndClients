#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''Server (Qweather) to grab data from the HP531813A Frequency Counter'''
from qweather import QWeatherServer, QMethod
import visa
import numpy as np
import serial
import time
import datetime
import threading
__author__ = 'Asbjorn Arvad Jorgensen'
__version__ = '1.0'
__email__ = 'Asbjorn.Arvad@nbi.ku.dk'
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
        self.comport = 'COM10'
        self.GPIBaddr = 9
        self.QWeatherStationIP = "tcp://10.90.61.13:5559"
        self.servername = 'FreqCounterHP'

        self.verbose = False
        self.debug = False
        self.initialize_sockets()
        print('*'*50)
        print('Server Online')
        self.initialize_hardware()
        print('Getting data from: {:s}'.format(self.GPIB_ask("*IDN?;\n", 16)))


    def initialize_hardware(self):
        self.GPIB = serial.Serial( self.comport, 9600, timeout=10)
        self.GPIB.write(b"++mode 1\n")                       # Set controller mode.
        self.GPIB.write(("++addr " + str(self.GPIBaddr) + "\n").encode())  # Set GPIB address.
        self.GPIB.write(b"++auto 0\n")                       # Disable read-after-write.
        self.GPIB.write(b'*RST\n')  #Reset the counter
        self.GPIB.write(b'*CLS\n') #Clear event registers and error quere
        self.GPIB.write(b'*SRE 0\n') #clear service request enable register
        self.GPIB.write(b'*ESE 0\n') #CClear event status enable register
        self.GPIB.write(b':STAT:PRES\n') #reset enable register and transition filters for operation
                                        # questionable status structures
        #following lines will provide the higesth throughput
        print('got here')
        self.GPIB.write(b":FORMAT ASCII\n") # ASCII format for fastest throughput
        self.GPIB.write(b":FUNC 'FREQ 1'\n") #! Select frequency
        self.GPIB.write(b":EVENT1:LEVEL 0\n") # Set Ch 1 trigger level to 0 volts
        self.GPIB.write(b":FREQ:ARM:STAR:SOUR IMM\n") # These two lines enable the
        self.GPIB.write(b":FREQ:ARM:STOP:SOUR IMM\n") # AUTO arming mode.
        self.GPIB.write(b":ROSC:SOUR INT\n") # Use internal oscillator. If
                                           #you want to use an external
                                           #timebase, you must select it
                                           #290 ! and turn off the automatic
                                           #detection using:
                                           #:ROSC:EXT:CHECK OFF
        print('got here')                                   
        self.GPIB.write(b":DIAG:CAL:INT:AUTO OFF\n") # Disable automatic interpolater
                                                   #calibration. The most recent
                                                   #calibration values are used in
                                                   #the calculation of frequency
        self.GPIB.write(b":DISP:ENAB OFF\n") # Turn off the counter display
        self.GPIB.write(b":CALC:MATH:STATE OFF\n") # Disable any post processing.
        self.GPIB.write(b":CALC2:LIM:STATE OFF\n")
        self.GPIB.write(b":CALC3:AVER:STATE OFF\n")
        self.GPIB.write(b":HCOPY:CONT OFF\n") # Disable any printing operation
        self.GPIB.write(b"*DDT #15FETC?\n") #define the fetch command to work on the trigger 
#        print('got here')
        #self.GPIB.write(b":INIT:CONT ON\n")          # Put counter in Run mode
        self.GPIB.write(b":FREQ:EXP1 25M\n")  #Tell the counter what frequency
                                           #to expect on Ch 1. This number
                                           #must be within 10% of the input
                                           #frequency. Using this greatly
        print('got here')
        '''
        '''

    @QMethod
    def log_frequency(self,gatetime,savelocation,frequency,syncronization = False):
        if syncronization:
            print('syncronizing')
            self.GPIB.write(b':ROSC:EXT:CHECK OFF\n')
            self.GPIB.write(b":ROSC:SOURCE EXT\n")
            self.GPIB.write(b":FREQ:ARM:STAR:SOUR EXT\n")
            self.GPIB.write(b":FREQ:ARM:STOP:SOUR TIM\n")
            self.GPIB.write(b':FREQ:ARM:STOP:TIM .010\n')
        else:
            self.GPIB.write(b":FREQ:ARM:STAR:SOUR IMM\n") # These two lines enable the
            self.GPIB.write(b":FREQ:ARM:STOP:SOUR IMM\n")                                      
        self.GPIB.write(":FREQ:EXP1 {:d}M\n".format(frequency).encode())  #Tell the counter what frequency
                                           #to expect on Ch 1. This number
                                           #must be within 10% of the input
                                           #frequency. Using this greatl
        self.GPIB.write(b"*DDT #15FETC?\n") #define the fetch command to work on the trigger 
        self.GPIB.write(b':INIT:CONT ON\n')   
        data = self.GPIB_ask('*TRG;\n',256)
        print(data)
        self.logthread = logging_thread(target = self.do_logging,args =(gatetime,savelocation))
        self.logthread.start()

    def do_logging(self,gatetime,savelocation):
        date = str(datetime.datetime.now()).split(' ')[0]
        with open(savelocation + '/HP531813A' + date + '.txt', 'w') as f:
            f.write('Measurement started at: ' + str(datetime.datetime.now().astimezone()) + '\n')
            f.write('Counter: HP 531813A')
            f.write('Gatetime: {:f}'.format(gatetime))
            arr = []
            while not self.logthread.stopped():
                data = self.GPIB_ask('*TRG;\n',10240)
                arr.append(data)
#                print(data.strip())
            for apoint in arr:
                f.write(apoint.strip() + '\n')


    @QMethod
    def stop_logging(self):
        self.logthread.stop()


    def GPIB_ask(self,command,bytes):
        self.GPIB.write(command.encode())
        self.GPIB.write(b"++read eoi\n")
        answer = self.GPIB.readline().decode()
        return answer



if __name__ == "__main__":
    server = Server()
    server.run()
