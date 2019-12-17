import qweather
import numpy as np
import time
from subprocess import Popen, PIPE
import os
import sys
import datetime

cnx = qweather.QWeatherClient("tcp://10.90.61.13:5559")

with Popen(['python', "Z:/Dataprogrammer/Qweather/Servers/RSMultimeter.py", "RSMultimeter2", "TCPIP0::10.90.61.205::INSTR"]) as mm2process:
    time.sleep(5)
        mm2 = cnx.RSMultimeter2

        tic = time.time()


        Nseconds = 5
        fname = 'Z:/ClockLasers/referenceLaser/cavityTemp/191211/TempLogging1600.txt'
        print('{:d} s measurement initiated at: '.format(Nseconds) + str(datetime.datetime.now().astimezone()) + '\n')
        print(' ')
        with open(fname,'w') as f:
            f.write('#Measurement initiated on: ' + str(datetime.datetime.now().astimezone()) + '\n')
            f.write('#Time         T_cav [kOhm]\n')
            tstamp = time.time()-tic
            while tstamp < Nseconds:
                # serv.startSequence(run_only_once=True)
                time.sleep(0.2)
                #analogdata = serv.readAnalogValues(2000)
                # print(analogdata)
                res2 = mm2.single_measurement()
                # f.write("{:.10f}, {:.5f}, {:.5f}, {:.10f}, {:.10f} \n".format(tstamp,res2,res3,analogdata['AI4'],analogdata['AI5']))
                f.write("{:.10f}, {:.5f}\n".format(tstamp,res2))
                time.sleep(0.8)
                tstamp = time.time()-tic
                print('Elapsed time: {:.1f} s \r'.format(tstamp), end="\r")


        toc = time.time()
        print(toc-tic)