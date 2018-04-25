#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Server (Qweather) to run the NI PCI 6259 board connected to the BNC 2110 in the SR1 experiment'''


from qweather import QWeatherServer, QMethod
from collections import defaultdict,namedtuple
from time import sleep

__author__ = 'Asbjorn Arvad Jorgensen'
__version__ = '0.1'
__credits__ = 'Mikkel Tang'
__email__ = 'Asbjorn.Arvad@nbi.ku.dk'


class StrontiumBrain(QWeatherServer):

    class Channel:
        def __init__(self, timings = [], init_value = 0):
            self.timings = []
            self.initial_value = init_value
            self.dataArray = None

    def __init__(self):
        self.QWeatherStationIP = "tcp://172.24.22.3:5559"
        self.verbose = False
        self.debug = False
        self.demo = True
        self.initialize_sockets()
        print('*'*50)
        print('Server Online')
        self.initialize_hardware()

    def initializeHardware(self):
        self.channelsAI = defaultdict(Channel) # Dictionary which defaults to adding new key entries as lists if they do not exist
        self.channelsAO = defaultdict(Channel)
        self.channelsDI = defaultdict(Channel)
        self.channelsDO = defaultdict(Channel)

        self.DOclock = "/Dev1/100kHzTimebase"
        self.DOclockrate = 100e3

        if self.demo:
            print('Initializing in DEMO mode')



    @QMethod
    def addDigitalOutput(self,channel,tstart,tstop):
        '''Adds a digital output to the sequence already created. addDigitalOutput(str channelname, float tstart, float tstop) Returns None'''
        if self.verbose:
            print('Creating Digital Output Sequence')
        self.channelsDO[channel].timings.apped((tstart,tstop))

    @QMethod
    def clearDigitalSequence(self):
        '''Clears the digital output sequence'''
        self.channelsDO = defaultdict(Channel)

    @Qmethod
    def startSequence(self):
        '''Starts sequence'''
        self.DOtask = Task()
        self.compileDigitalOutput()
        self.DOtask.CreateDOchan('Dev1/port0/line0:{:d}'.format(len(self.channelsDO.keys() + self.channelsDI.keys())), # Lines, only specify those needed
                                  list(self.channelsDO.keys()) + list(self.channelsDI.keys()), # Name of lines, identical to the dictionary names/keys
                                    DAQmx_Val_ChanPerLine) #Make one channel per line
        self.DOtask.WriteDigitalLines()
        for aname,achannel in self.channelsDO.items():
            self.DOtask.WriteDigitalLines()



    def compileDigitalOutput(self):
        for aname,achannel in self.channelsDO.items():
            timings = achannel.timings
            timings.sort(key=lambda x: x[0]) # Sort timings according to tstart
            currenttime = 0
            sequencedata = [achannel.initial_value]

            for tStart,tStop in timings:
                if tStart>currenttime:
                    dt = (tStart-currenttime)*self.DOClockrate
                    if sequencedata[-1] == 1:
                        sequencedata += [1]*dt
                    else:
                        sequencedata += [0]*dt
                    currentime = tStart
                dt = (tStop - tStart)*self.DOClockrate
                if sequencedata[-1] == 1:
                    sequencedata += [0]*dt
                else:
                    sequencedata += [1]*dt
                currentime = tStop
            achannel.dataArray = np.array(sequencedata,dtype='uint8')







if __name__ == "__main__":
    from multiprocessing import Process

    #serverA = AD9959(0)
    serverB = AD9959(1)
    serverB.run()
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
