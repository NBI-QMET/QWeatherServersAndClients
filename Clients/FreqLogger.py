'''Client to '''

from qweather import QWeatherClient
import numpy as np
import matplotlib.pyplot as plt

client = QWeatherClient('tcp://172.24.22.3:5559')
print('Connection Established')
freqserver = client.FreqCounter
print("Frequency Counter Server Found")
Npoints = 10000 # Number of points
gatetime = 20e-9 # gatetime
loggingtime = 1 #logging time, in seconds
data = freqserver.get_frequency(10000,20e-9)

data = data.split(',')
data = [float(i[1:]) for i in data]

plt.figure()
plt.hist(data)