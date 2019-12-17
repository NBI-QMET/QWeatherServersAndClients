from PyQt5.QtWidgets import *
from PyQt5 import QtGui,QtCore
import pyqtgraph as pg
from qweather import QWeatherClient

import sys
sys.path.append('..')
from OscilloscopeLauncher import multidialog,OscilloscopeWidget


class AcetyleneOscilloscope(QWidget):

    def __init__(self):
        super(AcetyleneOscilloscope,self).__init__()
        self.listofservers = []
        self.initializeGui()
        self.guiprocess = None


    def initializeGui(self):
        layout = QHBoxLayout()

        osc_panel = self.make_osc_panel()
        #self.serverlayout = QVBoxLayout()
        #server_panel = self.make_server_panel()
        layout.addWidget(osc_panel)
        self.setLayout( layout)


        #self.serverlayout.addWidget(server_panel)
        buttonlayout = QHBoxLayout()

        startbutton = QPushButton('Start Oscilloscope Mirror')

        buttonlayout.addWidget(startbutton)

        layout.addLayout(buttonlayout)
        #layout.addLayout(self.serverlayout)

        startbutton.clicked.connect(self.start_clicked)

        self.show()

    def make_server_panel(self):
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
        return newserver

    def make_osc_panel(self):
        self.display = pg.PlotWidget()
        self.channels = [pg.PlotItem() for i in range(4)]
        for achan in self.channels:
            self.display.addItem(achan)
        # Axis
        a2 = pg.AxisItem("left")
        a3 = pg.AxisItem("left")
        a4 = pg.AxisItem("left")

        # ViewBoxes
        v2 = pg.ViewBox()
        v3 = pg.ViewBox()
        v4 = pg.ViewBox()

        # layout
        l = pg.GraphicsLayout()
        self.display.setCentralWidget(l)

        # add axis to layout
        ## watch the col parameter here for the position
        l.addItem(a2, row = 2, col = 3,  rowspan=1, colspan=1)
        l.addItem(a3, row = 2, col = 2,  rowspan=1, colspan=1)
        l.addItem(a4, row = 2, col = 1,  rowspan=1, colspan=1)

        # plotitem and viewbox
        ## at least one plotitem is used whioch holds its own viewbox and left axis
        pI = pg.PlotItem()
        v1 = pI.vb # reference to viewbox of the plotitem
        l.addItem(pI, row = 2, col = 4,  rowspan=1, colspan=1) # add plotitem to layout

        # add viewboxes to layout 
        l.scene().addItem(v2)
        l.scene().addItem(v3)
        l.scene().addItem(v4)

        # link axis with viewboxes
        a2.linkToView(v2)
        a3.linkToView(v3)
        a4.linkToView(v4)

        # link viewboxes
        v2.setXLink(v1)
        v3.setXLink(v2)
        v4.setXLink(v3)

        # axes labels
        pI.getAxis("left").setLabel('axis 1 in ViewBox of PlotItem', color='#FFFFFF')
        a2.setLabel('axis 2 in Viewbox 2', color='#2E2EFE')
        a3.setLabel('axis 3 in Viewbox 3', color='#2EFEF7')
        a4.setLabel('axis 4 in Viewbox 4', color='#2EFE2E')

        # slot: update view when resized
        def updateViews():

            v2.setGeometry(v1.sceneBoundingRect())
            v3.setGeometry(v1.sceneBoundingRect())
            v4.setGeometry(v1.sceneBoundingRect())

        # data
        x = [1,2,3,4,5,6]
        y1 = [0,4,6,8,10,4]
        y2 = [0,5,7,9,11,3]
        y3 = [0,1,2,3,4,12]
        y4 = [0,8,0.3,0.4,2,5]

        # plot
        v1.addItem(pg.PlotCurveItem(x, y1, pen='#FFFFFF'))
        v2.addItem(pg.PlotCurveItem(x, y2, pen='#2E2EFE'))
        v3.addItem(pg.PlotCurveItem(x, y3, pen='#2EFEF7'))
        v4.addItem(pg.PlotCurveItem(x, y4, pen='#2EFE2E'))

        # updates when resized
        v1.sigResized.connect(updateViews)

        # autorange once to fit views at start
        v2.enableAutoRange(axis= pg.ViewBox.XYAxes, enable=True)
        v3.enableAutoRange(axis= pg.ViewBox.XYAxes, enable=True)
        v4.enableAutoRange(axis= pg.ViewBox.XYAxes, enable=True)

        updateViews()    
        return self.display





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
            donebox.setText('Oscilloscope is already running')
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
    myappid = u'mycompany.myproduct.subproduct.version4' # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    w = AcetyleneOscilloscope()
    sys.exit(a.exec_())

