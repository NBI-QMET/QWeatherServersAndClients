#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''Server (Qweather) to control the Rigol DG1022 DDS'''
from qweather import QWeatherServer, QMethod
import visa
import numpy as np
import time
import smtplib,ssl
from consolemenu import *
from consolemenu.items import *
import json
import struct
import sys
__author__ = 'Asbjorn Arvad Jorgensen'
__version__ = '1.0'
__email__ = 'Asbjorn.Arvad@nbi.ku.dk'

class Server(QWeatherServer):
    def __init__(self,name = None, address = None):
        self.QWeatherStationIP = "tcp://10.90.61.231:5559"
        if name is None and address is None:
            self.servername = 'Rigol DDS1'
            self.address = 'TCPIP0::10.90.61.204::INSTR'
        else:
            self.servername = name
            self.address = 'TCPIP0::' + address + '::INSTR'

        self.verbose = False
        self.debug = False
        self.initialize_sockets()
        print('*'*50)
        print('Server Online')
        self.initialize_hardware()

    def initialize_hardware(self):
        rm = visa.ResourceManager()
        self.hardware = rm.open_resource(self.address)
        print('Rigol DDS server running Made contact with:')
        print(self.hardware.query('*IDN?'))
        print(self.servername)
        print('*'*50)
        self.hardware.timeout=2000


    @QMethod
    def set_dc(self,channel,level):
        if channel==1:
            self.hardware.write("SOUR1:APPL:DC DEF,DEF,{:2.3f}".format(level))
        elif channel==2:
            self.hardware.write("SOUR2:APPL:DC DEF,DEF,{:2.3f}".format(level))

    @QMethod
    def set_load(self,channel,load):
        if channel==1:
            if load == 50:
                self.hardware.write("OUTP1:LOAD 50")
            elif load.lower()=='inf':
                self.hardware.write("OUTP1:LOAD INF")
            else:
                return 'Wrong load chosen'
        elif channel==2:
            if load == 50:
                self.hardware.write("OUTP2:LOAD 50")
            elif load.lower()=='inf':
                self.hardware.write("OUTP2:LOAD INF")
            else:
                return 'Wrong load chosen'

    @QMethod
    def turn_on(self,channel):
        if channel==1:
            self.hardware.write('OUTP1 ON')
        elif channel==2:
            self.hardware.write('OUTP2 ON')

    @QMethod
    def turn_off(self,channel):
        if channel==1:
            self.hardware.write('OUTP1 OFF')
        elif channel==2:
            self.hardware.write('OUTP2 OFF')

    @QMethod
    def load_custom_pattern(self,channel,period,amplitude_low,amplitude_high,pattern):
        freq = int(1/period)
        if channel==1:
            self.hardware.write('FUNC USER')
            self.hardware.write('FUNC:USER VOLATILE')
            self.hardware.write('FREQ {:d}'.format(freq))
            self.hardware.write('VOLT:UNIT VPP')
            self.hardware.write('VOLT:HIGH {:f}'.format(amplitude_high))
            self.hardware.write('Volt:LOW {:f}'.format(amplitude_low))
        self.upload_pattern_to_dds(pattern)


    def upload_pattern_to_dds(self,data):
        #self.hardware.write('FUNC USER')
        patternstring = ''.join(",{:.2f}".format(e) for e in data)
        print(self.hardware.write('DATA VOLATILE'+patternstring))

    @QMethod
    def set_burst_mode(self,state):
        if state:
            self.hardware.write("BURS:STAT ON")
            self.hardware.write("BURS:NSYC 1")
            self.hardware.write("BURS:MODE TRIG")
        else:
            self.hardware.write("BURS:STAT OFF")

    @QMethod
    def set_trigger_source(self,mode):
        if mode.lowercase() == "int":
            self.harware.write("TRIG:SOUR IMM")
        elif mode.lowercase() == "ext":
            self.harware.write("TRIG:SOUR EXT")
        elif mode.lowercase() == "man":
            self.harware.write("TRIG:SOUR BUS")





if __name__ == "__main__":
    with open('Z:/Dataprogrammer/Qweather/Config files/Ipadresses.json') as json_config_file:
        ipdata = json.load(json_config_file)
    menu = ConsoleMenu()

    Databaselist = ipdata['DDS']
    InstrumentID = SelectionMenu.get_selection(Databaselist)
    InstrumentID = list(Databaselist.items())[InstrumentID]
    name = InstrumentID[0]
    addr = InstrumentID[1]['adress']

    server = Server(name=name,address=addr)
    server.run()


