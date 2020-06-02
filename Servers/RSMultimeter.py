#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''Server (Qweather) to grab data from the Rode&Schwartz Multimeters'''
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
    """Class for RS multimeter. If Initialized in a terminal, will create a terminal menu where the name and address can be picked"""
    def __init__(self,name = None, address = None):
        self.QWeatherStationIP = "tcp://10.90.61.13:5559"
        if name is None and address is None:
            self.servername = 'RSMultimeter1'
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
        """Open connection to hardware via visa"""
        rm = visa.ResourceManager()
        self.hardware = rm.open_resource(self.address)
        print('Multimeter server running Made contact with:')
        print(self.hardware.query('*IDN?'))
        print('*'*50)
        self.hardware.timeout=2000


    @QMethod
    def single_measurement(self):
        """
        **QMethod** Takes a single measurement of whatever is on the screen.
        Returns:
            Measurement on screen (Float)

        """
        try:
            data = float(self.hardware.query('FETC?'))
            return data
        except Exception as e:
            print(e)
            if self.emailwarning:
                port = 465  # For SSL
                password = 'strontium8256'
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
                    server.login("qmetstrontium@gmail.com", password)
                    server.sendmail("qmeststrontium@gmail.com", "schaffer@nbi.dk",' ' + time.strftime("%d/%m/%y %H:%M:%S")+
                                                                                        '\n######Incoming transmission ##############\n'+
                                                                                        ' Help us Obi Wan Kenobi (Stefan) - You are our only hope\n'+
                                                                                        '(Something has gone wrong!)\nTo the mausoleum!')
            raise

        

    @QMethod
    def enable_email_warning(self,boolean):
        """
        **QMeathod** Enables email warning. Not sure what this is used for?
        Args: 
            boolean bool: If true it enables emailwarnings on the server
        """
        if boolean is True:
            self.emailwarning = True
        else:
            self.emailwarning = False



if __name__ == "__main__":
    with open('Z:/Dataprogrammer/Qweather/Config files/Ipadresses.json') as json_config_file:
        ipdata = json.load(json_config_file)
    menu = ConsoleMenu()
    Databaselist = ipdata['Multimeters']
    InstrumentID = SelectionMenu.get_selection(Databaselist)
    InstrumentID = list(Databaselist.items())[InstrumentID]

    name = InstrumentID[0]
    addr = InstrumentID[1]['adress']

    server = Server(name=name,address=addr)
    server.run()


