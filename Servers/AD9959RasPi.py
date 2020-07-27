#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Client (Qweather) to run the AD9959 board from a Raspberry Pi'''


from qweather import QWeatherServer, QMethod
import spidev
import RPi.GPIO as gpio
from time import sleep

__author__ = 'Asbjorn Arvad Jorgensen'
__version__ = '1.0'
__credits__ = 'Martin Romme Henriksen'
__email__ = 'Asbjorn.Arvad@nbi.ku.dk'


class AD9959(QWeatherServer):
    __regCSR = 0x00 #address (Channel select register)
    __regFR1 = 0x01 #address (Function register 1)
    __regFTW = 0x04 #address (Frequency tuning word)
    __regPOW = 0x05 #address (Phase offset word)
    __regACR = 0x06 #address (Amplitude control register)


    def __init__(self,name = None):
        self.QWeatherStationIP = "tcp://10.90.61.231:5559"
        if name is None:
            print('No name specified, running aborted')
        else:
            self.servername = name + 'DDS'
        self.verbose = False
        self.debug = False
        self.demo = False
        self.initialize_sockets()
        print('*'*50)
        print('Server Online')
        self.initialize_hardware()

    def initialize_hardware(self):
        self.freqdoubling = True
        if self.demo:
            print('Initializing in DEMO mode')
        else:
            gpio.setmode(gpio.BCM)
            gpio.setup(25,gpio.OUT) # IOupdata pin
            gpio.setup(24,gpio.OUT) # Chip reset pin
            self.spi = spidev.SpiDev()
            self.spi.open(0,0)
            self.chipReset()
        
    def setChannel(self,ch):
        '''Sets the channel of the DDS to be used (0,1,2,3) -1 means all channels'''
        if self.demo:
            return ch
        else:
            if ch == 3:
                chSelect = 0x82
            elif ch == 2:
                chSelect = 0x42
            elif ch == 1:
                chSelect = 0x22
            elif ch == 0:
                chSelect = 0x12
            elif ch == -1:
                chSelect = 0xF2 # Select all channels
            else:
                return 'Error: Illegal channel number: ',ch
            self.spi.xfer2([self.__regCSR, chSelect])

    @QMethod
    def setFrequency(self,channel,freq):
        '''Sets the frequency of the channel
        setFrequency(int Channel, float Frequency (MHz))
        return None'''
        self.setChannel(channel)
        data = [self.__regFTW]
        F_clk = 500.
        if self.freqdoubling:
            setfreq = (F_clk-freq/2)
        else:
            setfreq = F_clk-freq
        FTW = int(round(2**32*(setfreq/F_clk)))
        data.extend([FTW >> (8*i) & 0xff for i in range(3,-1,-1)])
        if self.demo:
            return channel,freq,data
        else:
            self.spi.xfer2(data[:])
            self.IOupdate()
            # print('frequency set',setfreq)

    @QMethod
    def setPhase(self,channel,phase):
        '''Sets the Phase of the channel
        setPhase(int Channel, float Phase(Degrees))
        return None'''
        self.setChannel(channel)
        data = [self.__regPOW]
        POW = int(round(2**14*(phase/360.)))
        data.extend([POW >> (8*i) & 0xff for i in range(1,-1,-1)]) 
        if self.demo:
            return channel,phase,data
        else:
            self.spi.xfer2(data[:])
            self.IOupdate()
            
    @QMethod
    def setAmplitude(self,channel,amplitude):
        '''Sets the Phase of the channel
        setPhase(int Channel, float Phase(Degrees))
        return None'''
        self.setChannel(channel)
        ASF = int(round(2**10*(amplitude/100.)))-1
        data = [self.__regACR, 0x00]
        data.extend([(ASF >> 8*1 & 0xff) + int('00010000',2), ASF >> 8*0 & 0xff])
        if self.demo:
            return channel,amplitude,data
        else:
            self.spi.xfer2(data[:])
            self.IOupdate()

    def chipReset(self): # Master reset command
        gpio.output(24, gpio.HIGH)
        sleep(0.1)
        gpio.output(24, gpio.LOW)
        data = [self.__regCSR, 0xF2] # (Ch0-3 enabled, 3 wire setup, MSB first)
        self.spi.xfer2(data[:])

        data = [self.__regFR1, 0x80, 0x00, 0x20]
        self.spi.xfer2(data[:])
        self.IOupdate()
        print('Chip was reset')


    def IOupdate(self):
        gpio.output(25, gpio.HIGH)
        sleep(0.5)
        gpio.output(25, gpio.LOW)

    @QMethod
    def read(self,register,bytelength):
        '''Reads the registry specified
        read(hex register, int bytelegnth))
        return string'''
        data = [register | 0x80]
        if self.demo:
            return register,bytelength,data
        else:
            self.spi.xfer2(data[:])
            return self.spi.readbytes(bytelength)

if __name__ == "__main__":
    from multiprocessing import Process


    name = input('Please write DDS server name (AceA, AceB, Sr1, Maus)')
    print(name)

    server = AD9959(name=name)
    #serverB = AD9959(1)
    server.run()
    '''
    pA = Process(target=serverA.run())
    pB = Process(target=serverB.run())
    pA.start()
    pB.start()
    try:
        while True:
            pass #'Run run run little servers'
    except KeyboardInterrupt:
        print('Shutting down servers')
        pA.terminate()
        pB.terminate()
        print('Servers shut down')
    '''
