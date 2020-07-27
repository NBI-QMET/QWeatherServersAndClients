from qweather import QWeatherClient
import datetime
import time

QWeatherStationIP ="tcp://10.90.61.231:5559"
client = QWeatherClient(QWeatherStationIP,name='PztMeas',loop=None)

mm = client.AgiMM1
db = client.Database

while True:
	U = float(mm.measure_voltage())
	tstamp = datetime.datetime.now()
	timeNow = tstamp.timestamp()*1e9
	time.sleep(60)

	db.write('Repumper',tags={'Experiment':'Sr1'},fields={'Cavity Piezo Voltage':U},time=timeNow)
	print(("{:s}: {:.2f} Volt\n".format(str(tstamp),U)))
