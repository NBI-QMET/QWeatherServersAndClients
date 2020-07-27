import qweather

cnx = qweather.QWeatherClient("tcp://10.90.61.231:5559")

serv = cnx.StrontiumBrain
print('connected')

serv.clearDigitalSequence()
trigdelay = 0#10e-9
sequencetime = 109e-6#+trigdelay
MOToff = 45.8e-6
MOTon = 46.1e-6#46.5e-6
MOTpulse = 500e-9
AIbegin = 20e-3
AIend =  50e-3
#serv.addAnalogInput('TestIn',-1,1)
#serv.addDigitalOutput('Capture',AIbegin,AIend)
#serv.addAnalogOutput('TestOut',10e-3,80e-3,50e-3)
#serv.addAnalogOutput('TestOut',80e-3,100e-3,-50e-3)

serv.addDigitalOutput('BlueMOT',MOToff,MOTon)
serv.addDigitalOutput('BlueMOT',MOTon+MOTpulse,sequencetime)
#serv.addDigitalOutput('BlueMOT',MOTon,MOTon+MOTpulse)

#serv.addDigitalOutput('BlueMOT',45e-6,MOToff)
#serv.addDigitalOutput('BlueMOT',MOTon+MOTpulse,sequencetime)

#serv.addDigitalOutput('BlueMOT',MOTon+MOTpulse+trigdelay,sequencetime-1e-6+trigdelay)
#serv.addDigitalOutput('Capture',0.00005,0.000052)
serv.addDigitalOutput('PulseTrigger',0.0,100e-9)

serv.armSequence()
print('armed')
serv.startSequence()
print('started')

running = True

while True:
	if running:
		input("Press Enter to stop...")
		serv.stopSequence()
		print('stopped')
		running = False
	else:
		input("Press Enter to start...")
		serv.startSequence()
		print('started')		
		running = True


