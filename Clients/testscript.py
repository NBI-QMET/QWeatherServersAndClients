from qweather import QWeatherClient
import datetime
import time
import os
import numpy as np
cnx = QWeatherClient("tcp://10.90.61.231:5559")

serv1 = cnx.FreqCounter
gatetime = 10e-3

starttime = datetime.datetime.now()
savelocation = 'Z:/MicrowaveReference/data/190330/'
if not os.path.exists(savelocation):
    os.mkdir(savelocation)

#savelocation += starttime.strftime('/%H%M')

if not os.path.exists(savelocation):
    os.mkdir(savelocation)

# savelocation += '/'

#f,t = serv1.get_frequency(10000,gatetime)
#print(np.mean(np.diff(t)))
# print(serv1.get_timestamp(100,gatetime))

measTime = 600
print('starting logging')
print('{:f} s measurement initiated at: '.format(measTime) + str(starttime) + '\n')
print('will be done at ' + str(starttime + datetime.timedelta(seconds = measTime)) + '\n')
serv1.log_frequency(gatetime,savelocation,measTime,False)
if measTime<=1:
    time.sleep(measTime+1)
else:
    time.sleep(measTime)
serv1.stop_logging()
print('Measurement done at: ' + str(datetime.datetime.now()) + '\n')

print('I am done recording data, but I might be saving.')

#input('Press enter to stop')
