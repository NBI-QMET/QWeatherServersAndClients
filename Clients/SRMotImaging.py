import qweather
import numpy as np
import time
import matplotlib.pyplot as plt

cnx = qweather.QWeatherClient("tcp://10.90.61.231:5559")
serv = cnx.StrontiumBrain
print('connected')


for j in range(1):
	serv.clearDigitalSequence()
	sequencetime = 2000e-3

	Camtrigger = 301e-3
	AOMtriggerstart = 301e-3
	AOMduration = 0.07e-3#0.4e-3
	Delay = 50e-3 + j*10e-3
	Delay2 = 50e-3
	Time_of_flight=1100e-6
	Camtrigger+=Time_of_flight
	AOMtriggerstart+=Time_of_flight


	serv.addDigitalOutput('BlueMOT',300e-3,Camtrigger+Delay+20e-3)
	serv.addDigitalOutput('CamTrigger',Camtrigger,Camtrigger + 20e-3)
	serv.addDigitalOutput('ImagingAOM',0,AOMtriggerstart)
	serv.addDigitalOutput('ImagingAOM',AOMtriggerstart+AOMduration,AOMtriggerstart+Delay)
	serv.addDigitalOutput('ImagingAOM',AOMtriggerstart+Delay+AOMduration,sequencetime)

	serv.addDigitalOutput('CamTrigger',Camtrigger+Delay,Camtrigger+Delay+20e-3)
	serv.addDigitalOutput('CamTrigger',Camtrigger+Delay+Delay2,Camtrigger+Delay+Delay2+20e-3)


#serv.addDigitalOutput('ImagingAOM',100e-3,AOMtrigger)
	#serv.addDigitalOutput('ImagingAOM',AOMtrigger + 100e-3,1)
#input('press enter to start')
#while True:
	print(Delay)
	serv.armSequence(sequencetime)
	print('armed')
	serv.startSequence()
	print('started')
	input('enter to stop')
	serv.stopSequence()
#	while True:
		#time.sleep(1)
	#serv.stopSequence()
	#print('stopped')
print('done')
'''
for i in range(1,500,50):
	j = 0
	i = 0
	serv.addDigitalOutput('BlueMOT',500e-3,sequencetime)
	serv.addDigitalOutput('CamTrigger',Camtrigger+j*100e-6,Camtrigger+j*100e-6 + 100e-3)
	serv.addDigitalOutput('ImagingAOM',0,AOMtriggerstart+i*1e-6)
	serv.addDigitalOutput('ImagingAOM',AOMtriggerstart+i*1e-6+AOMduration,800e-3)
	serv.addDigitalOutput('ImagingAOM',801e-3,sequencetime)

	serv.addDigitalOutput('CamTrigger',677e-3,778e-3)

	#serv.addDigitalOutput('ImagingAOM',100e-3,AOMtrigger)
	#serv.addDigitalOutput('ImagingAOM',AOMtrigger + 100e-3,1)

	serv.armSequence(sequencetime)
	print('armed')
	serv.startSequence()
	input('press enter to stop')
	#print('started')
	print(500 + i*1e-3)
	#time.sleep(2)
	serv.stopSequence()
'''

