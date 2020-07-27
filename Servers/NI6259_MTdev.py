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
__version__ = '0.2'
__credits__ = 'Mikkel Tang'
__email__ = 'Asbjorn.Arvad@nbi.ku.dk'

class Channel:
    def __init__(self):
        self.timings = []
        self.minvolt = None
        self.maxvolt=None
        self.dataArray = None

class CallBackTask(Task):
    def __init__(self):
        Task.__init__(self)
        self.run = False
        self.AutoRegisterDoneEvent(0)
        self.readable= False
    def DoneCallback(self,status):
        #print('Status',status)
        #print('Starting again')
        self.TaskControl(DAQmx_Val_Task_Stop)
        if self.run:
            self.TaskControl(DAQmx_Val_Task_Start)
        else:
            pass#print('stopped')
        return 0

    def Begin_Task(self):
        self.run = True
        self.TaskControl(DAQmx_Val_Task_Start)

    def End_Task(self):
        self.run = False
        self.TaskControl(DAQmx_Val_Task_Stop)

    def readValues(self,Npoints):
        analogdata = np.zeros((Npoints,), dtype=np.float64)
        self.ReadAnalogF64(DAQmx_Val_Auto, #Number of samples to read for each channel
                                  10, # timeout for reading, in seconds
                                  DAQmx_Val_GroupByChannel,#Fill mode (interleaed or not)
                                  analogdata,
                                  Npoints, #Length of array to read asmples into
                                  None, #Number of samples read
                                  None) #Reserved for later
        return analogdata


class StrontiumBrain(QWeatherServer):


    def __init__(self):
        self.QWeatherStationIP = "tcp://10.90.61.231:5559"
        self.verbose = False
        self.debug = False
        self.demo = False
        self.servername = 'StrontiumBrain'
        self.initialize_sockets()
        print('*'*50)
        print('Server Online')
        self.initializeHardware()
        print('Connected to StrontiumBrain')


    def initializeHardware(self):   
        self.channelsAI = defaultdict(Channel) # Dictionary which defaults to adding new key entries as lists if they do not exist
        self.channelsAO = defaultdict(Channel)
        self.channelsDI = defaultdict(Channel)
        self.channelsDO = defaultdict(Channel)
        
        self.clock = "/Dev1/Ctr0InternalOutput"#"/Dev1/100kHzTimebase"#
        # The (DO) clockrate has been lowered from 10 to 1 MHz to accomodate AO signals
        self.clockrate = int(1e6)
        self.aoclock = "OnboardClock"
        self.aoclockrate = int(1e6)
        self.maxtime = 1000e-3 #longest time in seconds
        if self.demo:
            print('Initializing in DEMO mode')

                            #name:      (line address, inv polarity(0 means on, 1 means off))
        self.channellistDO = {'(0) User2':('Dev1/port0/line0', False),
                            '(3) ImagingAOM':('Dev1/port0/line3',False),
                            '(1) Blue MOT':('Dev1/port0/line1',False),
                            '(4) PulseTrigger':('Dev1/port0/line4',False),
                            '(5) CamTrigger':('Dev1/port0/line5',False),
                            '(6) Red MOT':('Dev1/port0/line6',False)}
        self.channellistAI = {}#'AI0':'Dev1/ai0'}

        #self.channellistAO = {'AO1':'Dev1/ao1'}
        self.channellistAO = {'AO0':'Dev1/ao1',
                              'AO1':'Dev1/ao0'}


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
    def addAnalogOutput(self,channel,tstart,tstop,volt):
        self.channelsAO[channel].timings.append((tstart,tstop,volt))

    @QMethod
    def clearDigitalSequence(self):
        '''Clears the digital output sequence'''
        self.channelsDO = defaultdict(Channel)

    @QMethod
    def clearAnalogOutput(self):
        '''Clears the analog output sequence'''
        self.channelsAO = defaultdict(Channel)



    @QMethod
    def armSequence(self,AOdata0,AOdata1,user_Max_Time = None):
        '''arms sequence'''
        if user_Max_Time is None:
            user_Max_Time = self.maxtime
        
        #############################################
        #                                           #
        #              Counter (Clock)              #
        #                                           #
        #############################################
        
        self.COtask = Task()
        self.COtask.CreateCOPulseChanFreq('/Dev1/ctr0',
                                        'clock',
                                        DAQmx_Val_Hz,
                                        DAQmx_Val_Low,
                                        0,
                                        self.clockrate,#10e6,
                                        0.5)

        self.COtask.CfgImplicitTiming(DAQmx_Val_ContSamps,
                                    int(self.clockrate*user_Max_Time))

        #############################################
        #                                           #
        #              Analog input                 #
        #                                           #
        #############################################
        if len(self.channelsAI.items()) is not 0:
            self.AItask = CallBackTask()
            self.AItask.readable = True
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
            #self.AItask.CfgDigEdgeRefTrig('PFI9',#Source of trigger
            #                                 DAQmx_Val_Falling, #Falling Edge
            #                                 2) #Number of samples to aquire before recognizing a trigger signal

            self.AItask.CfgSampClkTiming('/Dev1/Ctr0InternalOutput',#Clock to use
                                        float64(self.clockrate), #clock frequency of said clock
                                        DAQmx_Val_Rising, #Sample/generate on rising or falling edge
                                        DAQmx_Val_FiniteSamps, #Generate continous samples or finite samples
                                        int(self.clockrate*user_Max_Time)); #How many samples to generate/aquire if in Finite mode
            self.AItask.TaskControl(DAQmx_Val_Task_Commit)
        
        #############################################
        #                                           #
        #              Analog output                #
        #                                           #
        #############################################
        if len(self.channelsAO.items()) is not 0:
            self.AOtask = CallBackTask()
            
            analogChannelNames = list(self.channelsAO.keys()) + list(self.channelsAI.keys()) #list of names of analog lines used
            lineadress = ','.join([self.channellistAO[aname] for aname in analogChannelNames])
            linename = ','.join(analogChannelNames)
            
            self.AOtask.CreateAOVoltageChan(lineadress, # Lines, only specify those needed
                                        linename, # Name of lines, identical to the dictionary names/keys
                                        -5, #Minimum value
                                        5, #Maximum value
                                        DAQmx_Val_Volts, #Units
                                        None) #Custom scale name
            
            self.AOtask.CfgSampClkTiming(self.aoclock,#'/Dev1/Ctr0InternalOutput',#Clock to use
                                        float64(self.aoclockrate), #AO: Max 1 MHz works
                                        DAQmx_Val_Rising, #Sample/generate on rising or falling edge
                                        DAQmx_Val_FiniteSamps, #Generate continous samples or finite samples
                                        int(self.aoclockrate*user_Max_Time)); #How many samples to generate/aquire if in Finite mode
            
            writtenSampsAO = c_int()
            data = np.array([],dtype='double')
            for aname,achan in self.channelsAO.items():
                if AOdata0 is not None and "0" in aname:
                    print("0")
                    achan.dataArray = np.array(AOdata0,dtype='float64') # Get data from AO GUI
                elif AOdata1 is not None and "1" in aname:
                    print("1")
                    achan.dataArray = np.array(AOdata1,dtype='float64') # Get data from AO GUI
                data = np.append(data,achan.dataArray)
                lenAO = len(achan.dataArray)
                print(lenAO)
                
            self.AOtask.WriteAnalogF64(lenAO, #Length of data to write
                                          False, #Autostart
                                          5.0, #Timeout for writing, in seconds
                                          DAQmx_Val_GroupByChannel, #Interleaved or noninterleaved data
                                          data, #Data to write
                                          writtenSampsAO, #Samples written
                                          None) #reserved
            self.AOtask.TaskControl(DAQmx_Val_Task_Commit)

        #############################################
        #                                           #
        #              Digital output               #
        #                                           #
        #############################################
        if len(self.channelsDO.items()) is not 0:
            self.DOtask = CallBackTask()
            self.compileDigitalOutput(user_Max_Time)

            digitalChannelNames = list(self.channelsDO.keys()) + list(self.channelsDI.keys()) #list of names of digital lines used
            lineadress = ','.join([self.channellistDO[aname][0] for aname in digitalChannelNames])
            linename = ','.join(digitalChannelNames)

            self.DOtask.CreateDOChan(lineadress, # Lines, only specify those needed
                                     linename, # Name of lines, identical to the dictionary names/keys
                                     DAQmx_Val_ChanPerLine) #Make one channel per line

            self.DOtask.CfgSampClkTiming(self.clock,#'/Dev1/Ctr0InternalOutput',#Clock to use
                                        float64(self.clockrate), #Clockrate of said clock
                                        DAQmx_Val_Rising, #Sample/generate on rising or falling edge
                                        DAQmx_Val_FiniteSamps, #Generate continous samples or finite samples
                                        int(self.clockrate*user_Max_Time)); #How many samples to generate/aquire if in Finite mode
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
            self.DOtask.TaskControl(DAQmx_Val_Task_Commit)
        
        
    @QMethod
    def startSequence(self,run_only_once = False):
        '''Starts the sequence'''
        if len(self.channelsDO.items()) is not 0:
            self.DOtask.Begin_Task()
        #self.AItask.Begin_Task()
        
        if len(self.channelsAO.items()) is not 0:
            self.AOtask.Begin_Task()
        if run_only_once:
            self.DOtask.run=False
            #self.AItask.run=False
            #self.AOtask.run=False # Suspected to cause problems when ticking DO signals on/off
        self.COtask.StartTask() # Starts the clock the last

    @QMethod
    def stopSequence(self):
        '''Ends the sequence after the next repetition'''
        
        if len(self.channelsDO.items()) is not 0:
            self.DOtask.End_Task()
        #self.AItask.End_Task()
        if len(self.channelsAO.items()) is not 0:
            self.AOtask.End_Task()
        self.COtask.StopTask()

    @QMethod
    def readAnalogValues(self,Npoints):
        '''Reads the values from the analog input and returns them as a dictionary with "channelname" : dataarray'''
        data = self.AItask.readValues(Npoints)
        if len(self.channellistAI.keys()) > 1:
            datadict = {name:adata for name,adata in zip(self.channellistAI.keys(),data)}
        else:
            datadict = {list(self.channellistAI.keys())[0]:data}
        return datadict

    @QMethod
    def getChannelList(self):
        return [list(self.channellistDO.keys()),list(self.channellistAI.keys()), list(self.channellistAO.keys())] 

    def compileDigitalOutput(self,max_time):
        for aname,achannel in self.channelsDO.items():
            invpolarity = self.channellistDO[aname][1]
            timings = achannel.timings
            timings.sort(key=lambda x: x[0]) # Sort timings according to tstart
            currentTime = 0
            if invpolarity:
                sequencedata = np.ones(int(self.clockrate*max_time),dtype='uint8') #Use initial value, default is 0 (low)
            else:
                sequencedata = np.zeros(int(self.clockrate*max_time),dtype='uint8') #Use initial value, default is 0 (low)
            for tStart,tStop in timings:
                nStart = int(self.clockrate*tStart+0.5)
                nStop = int(self.clockrate*tStop+0.5)
                try:
                    if invpolarity:
                        sequencedata[nStart:nStop] = np.zeros(nStop-nStart,dtype='uint8')
                    else:
                        sequencedata[nStart:nStop] = np.ones(nStop-nStart,dtype='uint8')
                except ValueError as e:
                    print(e,nStart,nStop)
            achannel.dataArray = np.array(sequencedata,dtype='uint8')

if __name__ == "__main__":
    server = StrontiumBrain()
    server.run()
