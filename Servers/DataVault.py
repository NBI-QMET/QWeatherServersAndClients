#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""DataVault which handles saving of datafiles

"""

import sys
import asyncio
from qweather import QWeatherServer, QMethod
import time
import numpy as np
import pyqtgraph as pg

__author__ = 'Asbjorn Arvad Jorgensen'
__version__ = '0.9'
__email__ = 'Asbjorn.Arvad@nbi.ku.dk'




class Server(QWeatherServer):

    def __init__(self):
        self.QWeatherStationIP = "tcp://10.90.61.13:5559"
        self.servername = 'DataVault'
        self.verbose = False
        self.debug = False
        self.initialize_sockets()
        print('*'*50)
        print('Server Online')

    @QMethod
    def saveData(self,data,savelocation,datatype = None):
        format = savelocation.split('.')[-1]
        if type(data) is np.ndarray:
            if format in ['txt','csv']:
                np.savetxt(savelocation, data, delimiter=",")


if __name__ == "__main__":
    server = Server()
    server.run()


