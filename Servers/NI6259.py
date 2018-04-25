#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Server (Qweather) to run the NI PCI 6259 board connected to the BNC 2110 in the SR1 experiment'''


from qweather import QWeatherServer, QMethod
from collections import defaultdict,namedtuple
from time import sleep
from PyDAQmx import *
import numpy as np
from ctypes import c_int, byref

__author__ = 'Asbjorn Arvad Jorgensen'
__version__ = '0.1'
__credits__ = 'Mikkel Tang'
__email__ = 'Asbjorn.Arvad@nbi.ku.dk'

class Channel:
    def __init__(self):
        self.timings = []
        self.minvolt = None
        self.maxvolt=None
        self.dataArray = None

class StrontiumBrain(QWeatherServer):


    def __init__(self):
        self.QWeatherStationIP = "tcp://172.24.22.3:5559"
        self.verbose = False
        self.debug = True
        self.demo = False
        self.servername = 'StrontiumBrain'
        self.initialize_sockets()
        print('*'*50)
        print('Server Online')
        self.initializeHardware()

        print('Ready to start')

        self.addDigitalOutput('Test',0.005,0.01)
        self.addDigitalOutput('Test2',0.00,0.02)
        self.addDigitalOutput('Test',0.03,0.1)
        self.addDigitalOutput('Capture',0.01,0.02)
        self.addAnalogInput('TestIn',-1,6)
        self.startSequence()

    def initializeHardware(self):
        self.channelsAI = defaultdict(Channel) # Dictionary which defaults to adding new key entries as lists if they do not exist
        self.channelsAO = defaultdict(Channel)
        self.channelsDI = defaultdict(Channel)
        self.channelsDO = defaultdict(Channel)

        self.DOclock = "/Dev1/100kHzTimebase"
        self.DOclockrate = int(100e3)
        self.maxDOtime = 2 #longest time in seconds
        if self.demo:
            print('Initializing in DEMO mode')


        self.channellistDO = {'Test':'Dev1/port0/line0',
                            'Test2':'Dev1/port0/line1',
                            'Capture':'Dev1/port0/line6', #Shorted to PFI9
                            'Unused3':'Dev1/port0/line3'}
        self.channellistAI = {'TestIn':'Dev1/ai0'}


    @QMethod
    def addDigitalOutput(self,channel,tstart,tstop):
        '''Adds a digital output to the sequence already created. addDigitalOutput(str channelname, float tstart (in seconds), float tstop (in seconds)) Returns None'''
        if self.debug:
            print('Creating Digital Output Sequence')
        self.channelsDO[channel].timings.append((tstart,tstop))

    @QMethod
    def addAnalogInput(self,channel,minvolt,maxvolt):
        self.channelsAI[channel].minvolt = minvolt
        self.channelsAI[channel].maxvolt = maxvolt

    @QMethod
    def clearDigitalSequence(self):
        '''Clears the digital output sequence'''
        self.channelsDO = defaultdict(Channel)

    @QMethod
    def startSequence(self):
        '''Starts sequence'''
        self.DOtask = Task()
        self.AItask = Task()

        for aname,achannel in self.channelsAI.items():
            self.AItask.CreateAIVoltageChan(self.channellistAI[aname],#Terminal name
                                            aname, #channel name
                                            DAQmx_Val_RSE, #Terminal type (differential, reerences single end)
                                            achannel.minvolt, #Minimum value
                                            achannel.maxvolt, #Maximum value
                                            DAQmx_Val_Volts, #Units
                                            None) #Custom scale name
        self.AItask.CfgDigEdgeStartTrig('PFI9',#Source of trigger
                                         DAQmx_Val_Rising) #Rising edge
        self.AItask.CfgDigEdgeRefTrig('PFI9',#Source of trigger
                                         DAQmx_Val_Falling, #Falling Edge
                                         2) #Number of samples to aquire before recognizing a trigger signal

        self.AItask.CfgSampClkTiming(self.DOclock,#Clock to use
                                    float64(self.DOclockrate), #Clockrate of said clock
                                    DAQmx_Val_Rising, #Sample/generate on rising or falling edge
                                    DAQmx_Val_FiniteSamps, #Generate continous samples or finite samples
                                    int(self.DOclockrate*0.2)); #How many samples to generate/aquire if in Finite mode

        self.compileDigitalOutput()

        digitalChannelNames = list(self.channelsDO.keys()) + list(self.channelsDI.keys()) #list of names of digital lines used
        lineadress = ','.join([self.channellistDO[aname] for aname in digitalChannelNames])
        linename = ','.join(digitalChannelNames)

        print(lineadress,linename,digitalChannelNames)
        print(DAQmx_Val_ChanPerLine)
        self.DOtask.CreateDOChan(lineadress, # Lines, only specify those needed
                                 linename, # Name of lines, identical to the dictionary names/keys
                                 DAQmx_Val_ChanPerLine) #Make one channel per line

        self.DOtask.CfgSampClkTiming(self.DOclock,#Clock to use
                                    float64(self.DOclockrate), #Clockrate of said clock
                                    DAQmx_Val_Rising, #Sample/generate on rising or falling edge
                                    DAQmx_Val_FiniteSamps, #Generate continous samples or finite samples
                                    self.DOclockrate*self.maxDOtime); #How many samples to generate/aquire if in Finite mode
        writtenSampsDO = c_int()
        data = np.array([],dtype='uint8')
        for aname,achan in self.channelsDO.items():
            data = np.append(data,achan.dataArray)
            lenDO = len(achan.dataArray)
        self.DOtask.WriteDigitalLines(lenDO, #Length of data to write
                                      False, #Autostart
                                      5.0, #Timeout for writing, in seconds
                                      DAQmx_Val_GroupByChannel, #Interleaved or noninterleaved data
                                      data, #Data to write
                                      writtenSampsDO, #Samples written
                                      None) #reserved
        print(writtenSampsDO)
        self.AItask.StartTask()
        print('Analog Started')
        self.DOtask.StartTask()
        print('Digital Started')
        sleep(0.2)
        analogdata = np.zeros((1000,), dtype=np.float64)
        self.AItask.ReadAnalogF64(1000,#DAQmx_Val_Auto, #Number of samples to read for each channel
                                  10, # timeout for reading, in seconds
                                  DAQmx_Val_GroupByChannel,#Fill mode (interleaed or not)
                                  analogdata,
                                  1000, #Length of array to read asmples into
                                  None, #Number of samples read
                                  None) #Reserved for later
        if self.debug:
            print('Starting Task')


    def compileDigitalOutput(self):
        for aname,achannel in self.channelsDO.items():
            timings = achannel.timings
            timings.sort(key=lambda x: x[0]) # Sort timings according to tstart
            currentTime = 0
            sequencedata = [0] #Use initial value, default is 0 (low)
            print(timings)
            for tStart,tStop in timings:
                print(tStart,tStop)
                if tStart>currentTime: #If there is a gap between the previous pulse and this one, or if it does not start immediatly
                    print('Advanced time',tStart,currentTime)
                    dt = int((tStart-currentTime)*self.DOclockrate+0.5)
                    sequencedata += [0]*dt
                    currentime = tStart
                dt = int((tStop - tStart)*self.DOclockrate+0.5)
                if sequencedata[-1] == 1:
                    sequencedata += [0]*dt
                else:
                    sequencedata += [1]*dt
                currentTime = tStop
                print(len(sequencedata),sum(sequencedata))
            #pad array until it is as long as total pattern
            sequencedata += [0]*(self.DOclockrate*self.maxDOtime - len(sequencedata))
            print(len(sequencedata),self.DOclockrate*self.maxDOtime,max(sequencedata))
            achannel.dataArray = np.array(sequencedata,dtype='uint8')







if __name__ == "__main__":
    server = StrontiumBrain()
    server.run()
