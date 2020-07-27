import qweather
import numpy as np
import time
from subprocess import Popen, PIPE
import os
import sys
import datetime

cnx = qweather.QWeatherClient("tcp://10.90.61.231:5559")

with Popen(['python', "Z:/Dataprogrammer/Qweather/Servers/RSMultimeter.py", "RSMultimeter1", "TCPIP0::172.24.5.166::INSTR"]) as mm1process:
    time.sleep(5)
    with Popen(['python', "Z:/Dataprogrammer/Qweather/Servers/RSMultimeter.py", "RSMultimeter2", "TCPIP0::172.24.19.41::INSTR"]) as mm2process:
        time.sleep(5)

        serv = cnx.AcetyleneADCBoard
        mm2 = cnx.RSMultimeter1
        mm3 = cnx.RSMultimeter2
        serv.clearDigitalSequence()
        sequencetime = 0.5e-4

        serv.addAnalogInput('AI0',0,1)
        serv.addAnalogInput('AI8',0,1)
        serv.addAnalogInput('AI4',-1,1)
        serv.addAnalogInput('AI5',-1,1)
        serv.armSequence(sequencetime)

        tic = time.time()


        Nseconds = 4500
        fname = 'Z:/Acetylene/AllanDevs/180724/NIlogging1444.txt'
        print('{:d} s measurement initiated at: '.format(Nseconds) + str(datetime.datetime.now().astimezone()) + '\n')
        print(' ')
        with open(fname,'w') as f:
            f.write('#Measurement initiated on: ' + str(datetime.datetime.now().astimezone()) + '\n')
            f.write('#time         res2        res3        PCavIn2       PCavIn3       CAVI2         CAVI3 \n')
            tstamp = time.time()-tic
            while tstamp < Nseconds:
                serv.startSequence(run_only_once=True)
                analogdata = serv.readAnalogValues(4)
                res2 = mm2.single_measurement()
                res3 = mm3.single_measurement()
                f.write("{:.10f}, {:.4f}, {:.4f}, {:.10f}, {:.10f}, {:.10f}, {:.10f}  \n".format(tstamp,res2,res3,analogdata['AI0'],analogdata['AI8'],analogdata['AI4'],analogdata['AI5']))
                time.sleep(0.05)
                tstamp = time.time()-tic
                print('Elapsed time: {:.1f} s \r'.format(tstamp), end="\r")


        toc = time.time()
        print(toc-tic)

