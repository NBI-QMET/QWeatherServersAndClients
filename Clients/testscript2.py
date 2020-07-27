from qweather import QWeatherClient
import datetime
import time
import os
import numpy as np
cnx = QWeatherClient("tcp://10.90.61.231:5559")

serv1 = cnx.HP8648C

serv1.setFrequency(500)
serv1.getFrequency()
print('serv1.getFrequency')

print('Done')
