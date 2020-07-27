import qweather
import numpy as np
import time
import matplotlib.pyplot as plt

cnx = qweather.QWeatherClient("tcp://10.90.61.231:5559")

serv = cnx.StrontiumBrain
hp = cnx.HP8648C
print('connected')

serv.clearDigitalSequence()
sequencetime = 1e-3

MOToff = sequencetime
MOTon = 0
AIbegin = 0.1e-3
AIend =  1e-3

scanAOVoltage = np.linspace(-0.005,0,10)
frequencylist = [129.4]#np.linspace(128,130,2)
combineddata = []

serv.addDigitalOutput('Capture',AIbegin,AIend)
serv.addAnalogInput('AI0',-1,1)

tic = time.time()
for afreq in frequencylist:
	dataarray = np.zeros(len(scanAOVoltage))
	hp.setFrequency(afreq)
	setfreq = hp.getFrequency()
	for arun in range(len(scanAOVoltage)):
		serv.clearAnalogOutput()
		serv.addAnalogOutput('AO1',0,1e-3,scanAOVoltage[arun])
		serv.armSequence(sequencetime)
		serv.startSequence(run_only_once=True)
		data = serv.readAnalogValues(2)['AI0']
		#print(data)
		dataarray[arun] = np.mean(data)
	combineddata.append((setfreq,dataarray))
toc = time.time()
print(toc-tic)

#plt.figure()
#for adataset in combineddata:
#	plt.plot(scanAOVoltage,adataset[1],label='{:3.5f}'.format(adataset[0]))
#plt.legend()
#plt.show()


