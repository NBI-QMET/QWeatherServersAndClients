#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Server (Qweather) to run the NI PCI 6341 board connected to the BNC 2110 in the SR1 experiment'''


from qweather import QWeatherServer, QMethod
from collections import defaultdict,namedtuple
from time import sleep
from PyDAQmx import *
import numpy as np
from ctypes import c_int, byref

__author__ = 'Asbjorn Arvad Jorgensen'
__version__ = '0.1'
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


class AcetyleneADC(QWeatherServer):


    def __init__(self):
        self.QWeatherStationIP = "tcp://10.90.61.13:5559"
        self.verbose = False
        self.debug = False
        self.demo = False
        self.servername = 'AcetyleneDAQBoard'
        self.initialize_sockets()
        print('*'*50)
        print('Server Online')
        print('*'*50)
        self.initializeHardware()


    def initializeHardware(self):   
        self.channelsAI = defaultdict(Channel) # Dictionary which defaults to adding new key entries as lists if they do not exist
        self.channelsAO = defaultdict(Channel)
        self.channelsDI = defaultdict(Channel)
        self.channelsDO = defaultdict(Channel)

        self.clock = "100kHzTimebase"
        self.clockrate = int(100e3)#int(10e6)
        self.maxtime = 100e-3 #longest time in seconds
        if self.demo:
            print('Initializing in DEMO mode')


        self.channellistDO = {}

        self.channellistAI = {'AI0':'Dev3/ai0',
                              'AI1':'Dev3/ai1'
                              #'AI2':'Dev3/ai2',
                              #'AI3':'Dev3/ai3',
                              #'AI4':'Dev3/ai4',
                              #'AI5':'Dev3/ai5',
                              #'AI8':'Dev3/ai8'
                              }


        self.channellistAO = {}


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
        '''Clears the digital output sequence'''
        self.channelsAO = defaultdict(Channel)



    @QMethod
    def armSequence(self,user_Max_Time = None):
        '''arms sequence'''
        if user_Max_Time is None:
            user_Max_Time = self.maxtime
        
 
        #############################################
        #                                           #
        #              Analog input                 #
        #                                           #
        #############################################
        
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
#        self.AItask.CfgDigEdgeStartTrig('PFI9',#Source of trigger
 #                                        DAQmx_Val_Rising) #Rising edge
        #self.AItask.CfgDigEdgeRefTrig('PFI9',#Source of trigger
        #                                 DAQmx_Val_Falling, #Falling Edge
        #                                 2) #Number of samples to aquire before recognizing a trigger signal

        self.AItask.CfgSampClkTiming(self.clock,#Clock to use
                                    float64(self.clockrate), #clock frequency of said clock
                                    DAQmx_Val_Rising, #Sample/generate on rising or falling edge
                                    DAQmx_Val_FiniteSamps, #Generate continous samples or finite samples
                                    int(self.clockrate*user_Max_Time)); #How many samples to generate/aquire if in Finite mode
        self.AItask.TaskControl(DAQmx_Val_Task_Commit)

        '''
        #############################################
        #                                           #
        #              Analog output                #
        #                                           #
        #############################################
        
        self.AOtask = CallBackTask()
        self.compileAnalogOutput(user_Max_Time)

        for aname,achannel in self.channelsAO.items():
            minvolt = min(achannel.dataArray)
            maxvolt = max(achannel.dataArray)
            self.AOtask.CreateAOVoltageChan(self.channellistAO[aname],#Terminal name
                                            aname, #channel name
                                            -5, #Minimum value
                                            5, #Maximum value
                                            DAQmx_Val_Volts, #Units
                                            None) #Custom scale name

        self.AOtask.CfgSampClkTiming(self.clock,#Clock to use
                                    float64(self.clockrate), #clock frequency of said clock
                                    DAQmx_Val_Rising, #Sample/generate on rising or falling edge
                                    DAQmx_Val_FiniteSamps, #Generate continous samples or finite samples
                                    int(self.clockrate*user_Max_Time)); #How many samples to generate/aquire if in Finite mode

        writtenSampsAO = c_int()
        data = np.array([],dtype='uint8')
        for aname,achan in self.channelsAO.items():
            data = np.append(data,achan.dataArray)
            lenAO = len(achan.dataArray)
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

        self.DOtask = CallBackTask()
        self.compileDigitalOutput(user_Max_Time)

        digitalChannelNames = list(self.channelsDO.keys()) + list(self.channelsDI.keys()) #list of names of digital lines used
        lineadress = ','.join([self.channellistDO[aname] for aname in digitalChannelNames])
        linename = ','.join(digitalChannelNames)

        self.DOtask.CreateDOChan(lineadress, # Lines, only specify those needed
                                 linename, # Name of lines, identical to the dictionary names/keys
                                 DAQmx_Val_ChanPerLine) #Make one channel per line

        self.DOtask.CfgSampClkTiming(self.clock,#Clock to use
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
        '''
        
    @QMethod
    def startSequence(self,run_only_once = False):
        '''Starts the sequence'''
#        self.DOtask.Begin_Task()
        self.AItask.Begin_Task()
 #       self.AOtask.Begin_Task()
        if run_only_once:
  #          self.DOtask.run=False
            self.AItask.run=False
   #         self.AOtask.run=False
    #    self.COtask.StartTask() # Starts the clock the lat

    @QMethod
    def stopSequence(self):
        '''Ends the sequence after the next repetition'''
        
     #   self.DOtask.End_Task()
        self.AItask.End_Task()
      #  self.AOtask.End_Task()
       # self.COtask.StopTask()

    @QMethod
    def readAnalogValues(self,Npoints):
        '''Reads the values from the analog input and returns them as a dictionary with "channelname" : dataarray'''
        raw_data = self.AItask.readValues(Npoints)
        data = np.zeros(len(self.channellistAI.keys()))
        data[0] = np.mean(raw_data[0:int(Npoints/2-1)])
        data[1] = np.mean(raw_data[int(Npoints/2):int(Npoints-1)])

        #print( data)
        if len(self.channellistAI.keys()) > 1:
            datadict = {name:adata for name,adata in zip(self.channellistAI.keys(),data)}
        else:
            datadict = {list(self.channellistAI.keys())[0]:data}
        return datadict


    def compileDigitalOutput(self,max_time):
        for aname,achannel in self.channelsDO.items():
            timings = achannel.timings
            timings.sort(key=lambda x: x[0]) # Sort timings according to tstart
            currentTime = 0
            sequencedata = np.zeros(int(self.clockrate*max_time),dtype='uint8') #Use initial value, default is 0 (low)
            for tStart,tStop in timings:
                nStart = int(self.clockrate*tStart+0.5)
                nStop = int(self.clockrate*tStop+0.5)
                sequencedata[nStart:nStop] = np.ones(nStop-nStart,dtype='uint8')


#                if tStart>currentTime: #If there is a gap between the previous pulse and this one, or if it does not start immediatly
 #                   dt = int((tStart-currentTime)*self.clockrate+0.5)
  #                  sequencedata = seque[0]*dt
   #                 currentime = tStart
    #            dt = int((tStop - tStart)*self.clockrate+0.5)
     #           if sequencedata[-1] == 1:
      #              sequencedata += [0]*dt
       #         else:
        #            sequencedata += [1]*dt
         #       currentTime = tStop
            #pad array until it is as long as total pattern
          #  sequencedata += [0]*(int(self.clockrate*max_time - len(sequencedata)))
            achannel.dataArray = np.array(sequencedata,dtype='uint8')

    def compileAnalogOutput(self,max_time):
        for aname,achannel in self.channelsAO.items():
            timings = achannel.timings
            timings.sort(key=lambda x: x[0]) # Sort timings according to tstart
            sequencedata = np.zeros(int(self.clockrate*max_time),dtype='float64') #Use initial value, default is 0 (low)
            for tStart,tStop,volt in timings:
                nStart = int(self.clockrate*tStart+0.5)
                nStop = int(self.clockrate*tStop+0.5)
                sequencedata[nStart:nStop] = np.ones(nStop-nStart,dtype='float64')*volt
            achannel.dataArray = np.array(sequencedata,dtype='float64')







if __name__ == "__main__":
    server = AcetyleneADC()
    server.run()
