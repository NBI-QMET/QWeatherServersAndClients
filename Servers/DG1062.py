#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''Server (Qweather) to control the Rigol DG1062 DDS'''
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
        self.QWeatherStationIP = "tcp://10.90.61.13:5559"
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
    def program_AW(self,waveshape):
        self.hardware.write(':SOUR1:DATA VOLATILE' + [',' + str(i) for i in waveshape])




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


