from qweather import QWeatherClient
import os
import numpy
import datetime

cnx = QWeatherClient('tcp://10.90.61.13:5559')

serv = cnx.FreqCounter

tempDir = 'C:/Windows/Temp/Pendulum/'
saveDir = 'Z:/MicrowaveReference/data/190330'
gateTime = 0.1e-3	# Gate time in seconds
measTime = 10	# Total measuring time in seconds
nPoints = measTime/gateTime;
# bufferSize = 10000	# Number of points i coounter buffer. Measure time will be minimum bufferSize*gateTime

print('Fetching frequency')
a = serv.log_frequency(gateTime,tempDir,measTime,False)
# a = serv.log_frequency(bufferSize,gateTime,measTime,False,tempDir)
#a = serv.log_frequency(10,20e-3,5)
print('Measuremenmt done')

hexFiles = os.listdir(tempDir)

if not os.path.exists(saveDir):
    os.mkdir(saveDir)

timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
fileHandleCSV = open(saveDir + timestamp + '.csv','w')

print('Saving data')
counterData = []
for i in range(len(hexFiles)):
	fileHandleHex = open(tempDir + hexFiles[i],'rb')
	counterData = (serv.convert_binary_to_float(fileHandleHex.read(),nPoints))
	
	for ii in range(len(counterData[0])):
		fileHandleCSV.write('{:f}, {:f}\n'.format(counterData[0,ii],(counterData[1,ii]-counterData[1,0])*1e-12))
	fileHandleHex.close()

	os.remove(tempDir + hexFiles[i])

print('All done!')
fileHandleCSV.close()

