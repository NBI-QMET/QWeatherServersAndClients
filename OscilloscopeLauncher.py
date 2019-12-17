#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Gui for launching and monitoring oscilloscope servers

"""

from PyQt5.QtWidgets import *
from PyQt5 import QtGui,QtCore
from qweather import QWeatherClient
import sys
import subprocess
import json


__author__ = 'Asbjorn Arvad Jorgensen'
__version__ = '0.9'
__email__ = 'Asbjorn.Arvad@nbi.ku.dk'



class OscilloscopeWatcher(QWidget):

    def __init__(self):
        super(OscilloscopeWatcher,self).__init__()
        self.listofservers = []
        self.initializeGui()
        self.guiprocess = None


    def initializeGui(self):
        layout = QVBoxLayout()

        self.serverlayout = QGridLayout()
        self.setLayout( layout)


        buttonlayout = QHBoxLayout()
        createbutton = QPushButton('Create Server')
        startbutton = QPushButton('Start data download GUI')

        buttonlayout.addWidget(createbutton)
        buttonlayout.addWidget(startbutton)

        layout.addLayout(buttonlayout)
        layout.addLayout(self.serverlayout)

        createbutton.clicked.connect(self.create_clicked)
        startbutton.clicked.connect(self.start_clicked)

        self.show()


    def create_clicked(self):
        newserverinfo = multidialog()
        if newserverinfo.exec_() == QDialog.Accepted:
            name, adress, osctype = newserverinfo.result
            if osctype == 'RTB 2004':
                path = 'Z:\Dataprogrammer\Qweather\Servers\RTB2004.py'
            elif osctype == 'HMO 3004':
                path = 'Z:\Dataprogrammer\Qweather\Servers\HMO3004.py'
            elif osctype == 'RTO 1044':
                path = 'Z:\Dataprogrammer\Qweather\Servers\RTO1044.py'
            newserver = OscilloscopeWidget(name,adress,path)
            row = self.serverlayout.rowCount()-1
            if len(self.listofservers)%3 == 0:
                self.serverlayout.addWidget(newserver,row+1,0)
            else:
                self.serverlayout.addWidget(newserver,row,len(self.listofservers)%3)
            self.listofservers.append(newserver)

    def start_clicked(self):
        if self.guiprocess is not None:
            donebox = QMessageBox()
            donebox.setText('Gui is already running')
            donebox.exec()
        else:
            self.guiprocess = QtCore.QProcess()
            self.guiprocess.finished.connect(self.reinitialize_gui_state)
            self.guiprocess.start('python',['-u','Z:\Dataprogrammer\Qweather\Clients\OscilloscopeGUI.py'])


    def reinitialize_gui_state(self):
        self.guiprocess = None

    def closeEvent(self,evnt):
        print(self.listofservers)
        for aserver in self.listofservers:
            aserver.kill_server()
        super().closeEvent(evnt)


            

class OscilloscopeWidget(QFrame):

    def __init__(self,name,adress,path):
        super(OscilloscopeWidget,self).__init__()
        self.process = None

        self.path = path
        self.name = name
        self.adress = adress
        self.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        title = QLabel(self.name)
        startbutton = QPushButton('START')
        killbutton = QPushButton('TERMINATE')
        pingbutton = QPushButton('PING')
        self.textfield = QTextEdit()
        self.textfield.setReadOnly(True)
        startbutton.pressed.connect(self.start_server)
        killbutton.pressed.connect(self.kill_server)
        pingbutton.pressed.connect(self.ping_server)
        
        sublayout = QVBoxLayout()
        sublayout.addWidget(title)
        sublayout.addWidget(startbutton)
        sublayout.addWidget(killbutton)
        sublayout.addWidget(pingbutton)
        sublayout.addWidget(self.textfield)
        self.setLayout(sublayout)

    def start_server(self):
        if self.process is None:
            self.process = QtCore.QProcess()
            self.process.readyReadStandardOutput.connect(self.read_output)
            self.process.started.connect(lambda : self.write_message('Server started')) 
            self.process.finished.connect(lambda : self.write_message('Server stopped'))
            self.process.setProcessChannelMode(QtCore.QProcess.MergedChannels)
            self.process.start('python',['-u',self.path,self.name,self.adress])
        else:
            self.write_message('Cannot start "{:}", as it is already running'.format(self.name))

    def kill_server(self):
        if self.process is not None:
            self.process.terminate()
            self.process = None
            self.write_message('Terminated server')
        else:
            self.write_message('Cannot terminate "{:}", as it is not running'.format(self.name))

    def ping_server(self):
        self.textfield.append('Ping is not implemented at the moment')
        if self.process is not None:
            state = self.process.state()
            msg = "PING: "
            if state == 0:
                msg +='Process died'
            elif state == 1:
                msg +='Process is starting up'
            elif state == 2:
                msg += 'Process is alive'
            self.textfield.append(msg)
            #cnx = labrad.connect()
            #labradserver = eval('cnx.{:}'.format(self.name))
            #msg = 'PING: Labradserver is ' + labradserver.echo('alive')
            self.textfield.append(msg)
            #cnx.disconnect()
        else:
            self.textfield.append('Cannot ping a server that is not started')

    def read_output(self):
        data = self.process.readAllStandardOutput()
        self.textfield.append(str(data, 'utf-8'))        

    def write_message(self,message):
        self.textfield.append(message)




class multidialog(QDialog):

    def __init__(self):
        super().__init__()
        with open('Z:\Dataprogrammer\Qweather\Config files\Ipadresses.json') as json_config_file:
            ipdata = json.load(json_config_file)
        self.scopedict = ipdata['Oscilloscopes']

        layout = QFormLayout()
        layout.addRow(QLabel('Add New Server'))
        self.name = QLineEdit()
        self.scope=QComboBox()
        self.ipadress = QLineEdit()
        self.type = QLineEdit()
        layout.addRow('Name',self.name)
        layout.addRow('Osilloscope',self.scope)
        layout.addRow('IP Address',self.ipadress)
        layout.addRow('Type',self.type)

        
        self.scope.addItem('-- Choose oscilloscope')
        for ascope in self.scopedict.keys():
            self.scope.addItem(ascope)

        Connectbutton = QPushButton('Connect')
        layout.addRow(Connectbutton)
        Connectbutton.clicked.connect(self.connect_clicked)
        self.scope.activated.connect(self.scope_chosen)
        self.setLayout(layout)

    def scope_chosen(self):
        scopetext = self.scope.currentText()
        scope = self.scopedict[scopetext]
        self.ipadress.setText(scope['adress'])
        self.type.setText(scope['type'])

    def connect_clicked(self):
        error = ''
        if self.name.text() == '':
            error += 'name \n'
            errorbox = QMessageBox()
            errorbox.setText('Please enter a name')
            errorbox.exec()
        else:
            adress = self.scopedict[self.scope.currentText()]['adress']
            typ = self.scopedict[self.scope.currentText()]['type']
            self.result = [self.name.text(),adress,typ]
            self.done(QDialog.Accepted)

    def closeEvent(self, evnt):
        self.done(QDialog.Rejected)


def icon():
    iconstring = ["40 40 7 1","   c #000000",".  c #FFFFFF","+  c #D3C70C","@  c #6D6D6D","#  c #0006FF","$  c #A58D06","&  c #280CD3","                                        ",
" ...................................... "," .                            .       . "," .                            .       . "," .       ++                   .       . ",
" .      ++++                  .@@@@@@@. "," .     ++  +                  .       . "," .##   ++  ++           ####  . $$ $$ . "," . #  ++    +          ##  ## .  $ $  . ",
" . ## +      +        ##     #.       . "," .  #++      ++       #       . $  $  . "," .  ##        +      ##       .   $   . "," .  +#        ++    ##        . $$ $$ . ",
" .  +##       ++    #         .       . "," . ++ #        ++   #         .       . "," .++   #        +  ##        +.@@@@@@@. "," .+    ##       +  #        ++.    $  . ",
" .      #       + ##        + . $   $ . "," .      ##      ++#        +  .  $$  $. "," .       #       ##        +  .       . "," .       ##      #         +  . $ $   . ",
" .        #     ##+       +   .     $ . "," .        ##   ## +       +   . $$ $  . "," .         #   #  ++     ++   .      $. "," .         ## ##   +     +    .@@@@@@@. ",
" .           ##    ++   ++    .       . "," .                  +   +     . $ $$  . "," .                  ++++      .   $  $. "," .                    ++      . $     . ",
" .                            . $$    . "," .............................. $ $ $ . "," .& & && && &&&   & & &&&     .       . "," .& &     & & &   &&& & &     .@@@@@@@. ",
" .&&& &&  & &&& &   & &&&     .       . "," .                            . $  $$ . "," .+ + ++ +++   +++ + +        .   $  $. "," .+ +    + +   + + +++        . $$$$ $. ",
" .+++ ++ +++ + +++   +        .  $    . "," ...................................... ","                                        "]
    return iconstring
if __name__=="__main__":
    a = QApplication(sys.argv)
    a.setWindowIcon(QtGui.QIcon(QtGui.QPixmap(icon())))
    import ctypes
    myappid = u'mycompany.myproduct.subproduct.version3' # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    w = OscilloscopeWatcher()
    sys.exit(a.exec_())


