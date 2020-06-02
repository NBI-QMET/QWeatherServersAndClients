import qweather
import numpy as np
import time
import matplotlib.pyplot as plt

cnx = qweather.QWeatherClient("tcp://172.24.22.3:5559")
serv = cnx.StrontiumBrain

sequencetime = 1e-3
scanAOVoltage = np.linspace(-0.005,0,10)
serv.clearAnalogOutput()
serv.addAnalogOutput('AO1',0,1e-3,scanAOVoltage[0])
serv.armSequence(sequencetime)
serv.startSequence(run_only_once=True)