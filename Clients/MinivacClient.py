import qweather
# import numpy as np
import numpy as np
import time
from subprocess import Popen, PIPE
import traceback
import sys
# from influxdb_client import InfluxDBClient
# from influxdb_client.client.write_api import SYNCHRONOUS

cnx = qweather.QWeatherClient("tcp://10.90.61.231:5559")

with Popen(['python', "Z:/Dataprogrammer/Qweather/Servers/GammaVacServer.py", "GammaVac", "TCPIP0::172.24.5.166::INSTR"]) as vacprocess:
    time.sleep(5)
    try:
        vac = cnx.GammaVac
        while True:
            print(vac.get_pressure_0())
            time.sleep(0.5)
            # print(vac.get_pressure_1())
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("Shutdown requested...exiting")
        # vacprocess.stdout.close()
    except Exception:
        traceback.print_exc(file=sys.stdout)
        # vacprocess.stdout.close()
    sys.exit(0)


# bucket = "qmet"
# org = "NBI"
#
# token = "6qiWt5JUxv4fwhqjUZKfG7cyMqtaSSevlLC_hsVqG_w09xJH5oUwJPLBLdAyeC5Qe7LgOEmAhaIoLsXLvl8hhg=="
#
# xdb = InfluxDBClient(url='http://localhost:9999',token=token,org=org)
#
# write_api = xdb.write_api()
#
# t1,T1,avg1,std1,mn1,mx1,Npoints1 = get_data(fnames1)
#
# print([np.isnan(np.sum(i)) for i in [T1,std1,avg1,mn1,mx1,Npoints1]])
# databody = []
#
# for i in range(len(t1)):
#     if np.isnan(avg1[i]):
#         databody.append( {  "measurement":"Temperature",
#
#                     "tags": {
#
#                             "Location": "Sr1 Table",
#                             },
#
#                     "fields": {
#                             "average":T1[i],
#                             "std":-1.,
#                             "min":-1.,
#                             "max":-1.,
#                             "Number of Points":-1.
#
#                             },
#                     'timestamp':int(datetime.datetime.timestamp(t1[i]))
#
#     }        )
#     else:
#         databody.append( {  "measurement":"Temperature",
#
#                             "tags": {
#
#                                     "Location": "Sr1 Table",
#                                     },
#
#                             "fields": {
#                                     "average":avg1[i],
#                                     "std":std1[i],
#                                     "min":mn1[i],
#                                     "max":mx1[i],
#                                     "Number of Points":Npoints1[i]
#
#                                     },
#                             'time':int(datetime.datetime.timestamp(t1[i]))
#
#             }        )
#
# write_api.write(bucket,org,databody,write_precision='s')