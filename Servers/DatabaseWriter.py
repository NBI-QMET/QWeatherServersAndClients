#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''Server (Qweather) to recieve data from anywhere and write it into the influxDB database'''
from qweather import QWeatherServer, QMethod
import numpy as np
import time
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
__author__ = 'Asbjorn Arvad Jorgensen'
__version__ = '0.9'
__email__ = 'Asbjorn.Arvad@nbi.ku.dk'

class Server(QWeatherServer):
    """Class for our databaseWriter"""
    def __init__(self):
        self.QWeatherStationIP = "tcp://10.90.61.231:5559"
        self.servername = 'Database'
           

        self.verbose = False
        self.debug = False
        self.initialize_sockets()
        print('*'*50)
        print('Server Online')
        self.connect_to_database()

    def connect_to_database(self):
        """Open connection to our InfluxDB database"""

        self.bucket = "qmet"
        self.org = "NBI"
        token = "6qiWt5JUxv4fwhqjUZKfG7cyMqtaSSevlLC_hsVqG_w09xJH5oUwJPLBLdAyeC5Qe7LgOEmAhaIoLsXLvl8hhg=="
        self.dbclient = InfluxDBClient(url='http://localhost:9999',token=token,org=self.org)
        self.writer = self.dbclient.write_api()

        print('Got access to the Influxdatabase')
        print('*'*50)
        

    @QMethod
    def write(self,measurement,tags,fields,time=None):
        """
        **QMethod** Takes a single measurement of whatever is on the screen.
        Returns:
            Measurement on screen (Float)

        """
        if not isinstance(tags,dict):
            print('Tags were not formatted correctly. Not saving')
        if not isinstance(fields,dict):
            print('Tags were not formatted correctly. Not saving')
        data=[{"measurement":measurement,
                                  "tags":tags,
                                  "fields":fields}]
                                   #timestamp = timestamp
        self.writer.write(self.bucket,self.org,data)  
        return 'Wrote successfully'
    



if __name__ == "__main__":
    
    server = Server()
    server.run()


