#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''Server (Qweather) to grab data from the Rigol DS1104Z oscilloscope'''
from qweather import QWeatherServer, QMethod
import visa
import numpy as np
import time
import struct
import sys
__author__ = 'Asbjorn Arvad Jorgensen'
__version__ = '0.9'
__email__ = 'Asbjorn.Arvad@nbi.ku.dk'

class Server(QWeatherServer):

    def __init__(self,servername,serveradress):
        self.QWeatherStationIP = "tcp://10.90.61.231:5559"
        self.servername = servername + 'OSC'
        self.address = 'TCPIP0::' + serveradress + '::INSTR'
        self.verbose = False
        self.debug = False
        self.initialize_sockets()
        print('*'*50)
        print('Server Online')
        self.initialize_hardware()
        

    def initialize_hardware(self):
        """Open the connection to the hardware using visa"""
        rm = visa.ResourceManager()
        self.hardware = rm.open_resource(self.address)
        print('Oscilloscope server running Made contact with:')
        print(self.hardware.query('*IDN?'))
        print('*'*50)
        self.hardware.write('WAV:MODE MAX')
        self.hardware.write('WAV:FORM ASC')
        self.hardware.timeout=2000



    def get_channel_data(self,channels):
        """Get data from channels

        :param channels: List of channels, or single channel to get data from
        :type channels: list, int
        :return: List of data in the form [tlist, datalist ,header]
        :rtype: list"""
        if not isinstance(channels,list):
            self.hardware.write('CHAN{:d}:DATA:POIN MAX'.format(channels))
            head = self.hardware.query('CHAN{:d}:DATA:HEAD?'.format(channels)).split(',')
            data = self.hardware.query_binary_values('CHAN{:d}:DATA?'.format(channels),datatype='f',is_big_endian=True)
        else:
            head = self.hardware.query('CHAN{:d}:DATA:HEAD?'.format(channels[0])).split(',')
            data = []
            for i in range(len(channels)):
                data.append(self.hardware.query_binary_values('CHAN{:d}:DATA?'.format(channels[i]),datatype='f',is_big_endian=True))
        head = [float(ah.strip()) for ah in head]
        tlist = np.linspace(head[0],head[1],head[2]*head[3])

        return [tlist,data,head]

    def get_ref_channel_data(self,channels):
        """Get data from reference channels

        :param channels: List of channels, or single channel to get data from
        :type channels: list, int
        :return: List of data in the form [tlist, datalist ,header]
        :rtype: list"""
        if not isinstance(channels,list):
            head = self.hardware.query('REFC{:d}:DATA:HEAD?'.format(channels)).split(',')
            data = self.hardware.query_binary_values('REFC{:d}:DATA?'.format(channels),datatype='f',is_big_endian=True)
        else:
            head = self.hardware.query('REFC{:d}:DATA:HEAD?'.format(channels[0])).split(',')
            data = []
            for i in range(len(channels)):
                data.append(self.hardware.query_binary_values('REFC{:d}:DATA?'.format(channels[i]),datatype='f',is_big_endian=True))
        head = [float(ah.strip()) for ah in head]
        tlist = np.linspace(head[0],head[1],head[2]*head[3])

        return [tlist,data,head]

    def get_time_data(self,channels):
        """Get the timearray corresponding to the current measurement

        :param channels: List of channels, or single channel to get data from
        :type channels: list, int
        :return: timearray
        :rtype: list"""
        if not isinstance(channels,list):
            self.hardware.write('CHAN{:d}:DATA:POIN MAX'.format(channels))
            head = self.hardware.query('CHAN{:d}:DATA:HEAD?'.format(channels)).split(',')
        else:
            head = self.hardware.query('CHAN{:d}:DATA:HEAD?'.format(channels[0])).split(',')
        head = [float(ah.strip()) for ah in head]
        tlist = np.linspace(head[0],head[1],head[2]*head[3])

        return tlist

    @QMethod
    def single_measurement(self,channels,rerun=False,ref=False):
        """
        **QMethod**

        Does a single measurement of the data
        
        Args:
            channels(list,int): List of channels to measure
            rerun (bool): Default False, If True, set Oscilloscope running after data taken
            ref (bool): Default False, if True, get reference channel data
        Returns:
            A list of data in the form [timelist,data]. If data from multiple channels, then data is a list of lists

        """
        if ref:
            tlist,data,head = self.get_ref_channel_data(channels)
        else:
            tlist,data,head = self.get_channel_data(channels)
        Nsamples = head[2]
        samplerate = (head[1] - head[0])/Nsamples
        if rerun:
            self.hardware.write('RUN')
            if self.verbose:
                print('Returning Data')
        return [tlist,data]

    @QMethod
    def get_timedata(self,channels,rerun=False):
        """
        **QMethod**
        Gets the timearray corresponding to the current data. Calls :py:meth:`get_time_data`.
        
        Args:
            channels(list,int): List of channels to measure
            rerun (bool,optional): Set Oscilloscope running after data taken, Defaults to False
        Returns:
            A timearray

        """
        tlist = self.get_time_data(channels)
        if rerun:
            self.hardware.write('RUN')
            if self.verbose:
                print('Returning time')
        return tlist   

    @QMethod
    def get_data(self,channels,rerun=False):
        """
        **QMethod**
        Gets the data from a channel, or list of channels Calls :py:meth:`get_channel_data`.
        
        Args:
            channels(list,int): List of channels to measure
            rerun (bool,optional): Set Oscilloscope running after data taken, Defaults to False
        Returns:
            A list of data in the form [timelist,data]. If data from multiple channels, then data is a list of lists

        """
        trash,data,trash2 = self.get_channel_data(channels)
        if rerun:
            self.hardware.write('RUN')
            if self.verbose:
                print('Returning time')
        return data   


    @QMethod 
    def repeat_measurements(self,channels,Nmeas):
        """
        **QMethod**
        Initialize the measurement and RUN oscilloscope when done. Repeat N times. Each iteration is a new trigger on the oscilloscope.

        Args:
            channels(list,int): List of channels to measure
            Nmeans (int): Number of times to repeat taking data
        Returns:
            A list of lists of lists containing [timearray,data,[number of samples,samplerate]]xNmeans

        """
        data = []
        #self.hardware.write('STOP')
        for i in range(Nmeas):
            self.hardware.write('STOP')
            data.append([])
            data[-1] = self.get_channel_data(channels)
            self.hardware.write('RUN')
            time.sleep(0.1)
        #self.hardware.write('RUN')
        return data



    @QMethod
    def get_history_data(self,channels):
        #self.hardware.write('RUN')
        #time.sleep(2)
        self.hardware.write('STOP')
        if not isinstance(channels,list):
            head = self.hardware.query('CHAN{:d}:DATA:HEAD?'.format(channels)).split(',')
            self.hardware.write('CHAN{:d}:DATA:POIN MAX'.format(channels))
            data = self.hardware.query_binary_values('CHAN{:d}:DATA?'.format(channels),datatype='f',is_big_endian=True)
        else:
            head = self.hardware.query('CHAN{:d}:DATA:HEAD?'.format(channels[0])).split(',')
            data = []
            for i in range(len(channels)):
                self.hardware.write('CHAN{:d}:DATA:POIN MAX'.format(channels[i]))
                print('getting data from channel ',i)
                data.append(self.hardware.query_binary_values('CHAN{:d}:DATA?'.format(channels[i]),datatype='f',is_big_endian=True))
        head = [float(ah.strip()) for ah in head]
        tlist = np.linspace(head[0],head[1],head[2]*head[3])
#        with open('Z:/Acetylene/AllanDevs/181026/1225/OscilloscopeTrace.txt'):
        data = [tlist,data]

        return data

    @QMethod
    def measure_peakpeak(self,channel,place,stat=False,stattime = 3):
        """
        **QMethod**
        Measure peakpeak value of signal. Calls :py:meth:`_measure_value`.

        Args:
            channel(int): Channel to measure
            place (int): measurement place on the oscilloscope
            stat (bool,optional): Do statistics, defaults to False
            stattime (int,optional): How long to do statistics over,  defaults to 3

        Returns:
            Peak Peak value Float
        """
        return self._measure_value(channel,place,'PEAK',stat,stattime)
    
    @QMethod
    def measure_mean(self,channel,place,stat=False,stattime = 3):
        """
        **QMethod**
        Measure mean value of signal. Calls :py:meth:`_measure_value`.

        Args:
            channel(int): Channel to measure
            place (int): measurement place on the oscilloscope
            stat (bool,optional): Do statistics, defaults to False
            stattime (int,optional): How long to do statistics over, defaults to 3

        Returns:
            mean value Float
        """
        return self._measure_value(channel,place,'MEAN',stat,stattime)
        
    @QMethod
    def measure_std(self,channel,place,stat=False,stattime = 3):
        """
        **QMethod**
        Measure std value of signal. Calls :py:meth:`_measure_value`.

        Args:
            channel(int): Channel to measure
            place (int): measurement place on the oscilloscope
            stat (bool,optional): Do statistics, defaults to False
            stattime (int,optional): How long to do statistics over, defaults to 3

        Returns:
            std value Float
        """
        return self._measure_value(channel,place,'STDD',stat,stattime)

    @QMethod
    def measure_minval(self,channel,place,stat=False,stattime = 3):
        """
        **QMethod**
        Measure min value of signal. Calls :py:meth:`_measure_value`.

        Args:
            channel(int): Channel to measure
            place (int): measurement place on the oscilloscope
            stat (bool,optional): Do statistics, defaults to False
            stattime (int,optional): How long to do statistics over, defaults to 3

        Returns:
            min value Float
        """
        return self._measure_value(channel,place,'LPE',stat,stattime)

    @QMethod
    def measure_maxval(self,channel,place,stat=False,stattime = 3):
        """
        **QMethod**
        Measure max value of signal. Calls :py:meth:`_measure_value`.

        Args:
            channel(int): Channel to measure
            place (int): measurement place on the oscilloscope
            stat (bool,optional): Do statistics, defaults to False
            stattime (int,optional): How long to do statistics over, defaults to 3

        Returns:
            Max value Float
        """
        return self._measure_value(channel,place,'UPE',stat,stattime)

    def _measure_value(self,channel,place,measurement,stat,stattime):
        """
        Measure some value of the signal

        Args:
            channel(int): Channel to measure
            place (int): measurement place on the oscilloscope
            measurement(str): PEAK-peak peak; MEAN-mean; STDD-std; LPE-min; UPE-max
            stat (bool): Do statistics
            stattime (int): How long to do statistics over

        Returns:
            measurement value Float
        """
        if not isinstance(channel,list):
            self.hardware.write('MEAS{:d}:SOUR CH{:d}'.format(place,channel))
            if stat:
                self.hardware.write('MEAS{:d}:STAT ON'.format(place))
                self.hardware.write('MEAS{:d}:STAT:RES'.format(place))
                time.sleep(stattime)
                avgval = float(self.hardware.query('MEAS{:d}:RES:AVG?').format(place))
                std = float(self.hardware.query('MEAS{:d}:RES:STDD?').format(place))
                minval = float(self.hardware.query('MEAS{:d}:RES:NPE?').format(place))
                maxval = float(self.hardware.query('MEAS{:d}:RES:PPE?').format(place))
                trigevents = int(self.hardware.query('MEAS{:d}:RES:WFMC?').format(place))

                data = [avgval,std,minval,maxval,trigevents]

            else:
                data = float(self.hardware.query('MEAS{:d}:RES? {:s}'.format(place,measurement)))
        else:
            for achan in channel:
                self.hardware.write('MEAS{:d}:SOUR CH{:d}'.format(achan,achan))
                if stat:
                    self.hardware.write('MEAS{:d}:STAT ON'.format(achan))
                    self.hardware.write('MEAS{:d}:STAT:RES'.format(achan))
            time.sleep(stattime)
            data = []
            for achan in channel:
                if stat:
                    avgval = float(self.hardware.query('MEAS{:d}:RES:AVG?'.format(achan)))
                    std = float(self.hardware.query('MEAS{:d}:RES:STDD?'.format(achan)))
                    minval = float(self.hardware.query('MEAS{:d}:RES:NPE?'.format(achan)))
                    maxval = float(self.hardware.query('MEAS{:d}:RES:PPE?'.format(achan)))
                    trigevents = int(self.hardware.query('MEAS{:d}:RES:WFMC?'.format(achan)))

                    data.append([avgval,std,minval,maxval,trigevents])
                else:
                    data.append(float(self.hardware.query('MEAS{:d}:RES? {:s}'.format(achan,measurement))))
        return data



if __name__ == "__main__":
    server = Server(*sys.argv[1:])
    server.run()


