#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Client (Qweather) to run two Gamma Vacuum pumps using a single Arduino microcontroller using firmata protocol'''

from qweather import QWeatherServer, QMethod
#import numpy as np
import pyfirmata
import time

__author__ = 'Julian Robinson-Tait'
__version__ = '1.0'
__credits__ = 'Asbjorn Arvad Jorgensen'
__email__ = 'Asbjorn.Arvad@nbi.ku.dk'

class GammaVac(QWeatherServer):

    def __init__(self, name = None):

        self.QWeatherStationIP = "tcp://10.90.61.231:5559"
        if name is None:
            print('No name specified, running aborted')
        else:
            self.servername = name + 'Minivac'
        self.verbose = False
        self.debug = False
        self.demo = False
        self.initialize_sockets()
        self.serialport = 'COM5'
        print('*'*50)
        print('Server Online')
        self.initialize_hardware()

    def initialize_hardware(self):
        '''Connect to arduino through serial communication port (e.g. COM5), and create pin objects for each channel'''
        arduino = pyfirmata.Arduino(self.serialport)
        self.analog_input_0 = arduino.get_pin('a:0:i')

        self.it = pyfirmata.util.Iterator(arduino)
        self.it.start()

    @QMethod
    def get_state_0(self):
        return self.digital_input_0.read()

    @QMethod
    def get_pressure_0(self):
        return self.analog_input_0.read()

    # @QMethod
    # def get_state_1(self):
    #     return self.digital_input_1.read()
    #
    # @QMethod
    # def get_pressure_1(self):
    #     return self.analog_input_1.read()
