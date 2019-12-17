import qweather
import numpy as np
import time
from subprocess import Popen, PIPE
import os
import sys
import datetime

cnx = qweather.QWeatherClient("tcp://10.90.61.13:5559")

with Popen(['python', "Z:/Dataprogrammer/Qweather/Servers/RSMultimeter.py", "RSMultimeter1", "TCPIP0::10.90.61.204::INSTR"]) as mm1process:
    time.sleep(5)
    with Popen(['python', "Z:/Dataprogrammer/Qweather/Servers/RSMultimeter.py", "RSMultimeter2", "TCPIP0::10.90.61.205::INSTR"]) as mm2process:
        time.sleep(5)
        # serv = cnx.AcetyleneDAQBoard
        mm1 = cnx.RSMultimeter1
        mm2 = cnx.RSMultimeter2
       # serv.clearDigitalSequence()
        # sequencetime = 0.01# 0.5e-4

        #serv.addAnalogInput('AI0',-0.5,0.5)
        #serv.addAnalogInput('AI1',-0.5,0.5)
        # serv.addAnalogInput('AI4',-1,1)
        # serv.addAnalogInput('AI5',-1,1)
        #serv.armSequence(sequencetime)

        tic = time.time()


        Nseconds = 2000
        fname = 'Z:/Acetylene/phaseTracking/190306/TempLogging1910.txt'
        print('{:d} s measurement initiated at: '.format(Nseconds) + str(datetime.datetime.now().astimezone()) + '\n')
        print(' ')
        with open(fname,'w') as f:
            f.write('#Measurement initiated on: ' + str(datetime.datetime.now().astimezone()) + '\n')
            f.write('#time         T_ace2       RAM_ace2\n')
            tstamp = time.time()-tic
            while tstamp < Nseconds:
                # serv.startSequence(run_only_once=True)
                time.sleep(0.1)
                #analogdata = serv.readAnalogValues(2000)
                # print(analogdata)
                volt1 = mm1.single_measurement()
                res2 = mm2.single_measurement()
                # f.write("{:.10f}, {:.5f}, {:.5f}, {:.10f}, {:.10f} \n".format(tstamp,res2,res3,analogdata['AI4'],analogdata['AI5']))
                f.write("{:.10f}, {:.5f}, {:.5f}\n".format(tstamp,res2,volt1))
                time.sleep(0.8)
                tstamp = time.time()-tic
                print('Elapsed time: {:.1f} s \r'.format(tstamp), end="\r")


        toc = time.time()
        print(toc-tic)

