'''BLackfly camera server for BFLY-U3-23S6M'''

import numpy as np
import PySpin as ps
from qweather import QWeatherServer, QMethod
import time
import atexit

demo = False
class Server(QWeatherServer):
    def __init__(self):
        if True:
            self.QWeatherStationIP = "tcp://10.90.61.13:5559"
            self.servername = 'BlackflyCamera'
            self.verbose = False
            self.debug = False
            self.initialize_sockets()
            print('*'*50)
            print('Server Online')


        self.bit8 = True
        if demo:
            self.demodata = np.genfromtxt('testpic2.csv',delimiter='\n',dtype='float')
            print('demo mode, demo data loaded')
        if not demo:
            self.initialize_hardware()
        atexit.register(self.onClosing)


    def initialize_hardware(self):
        self.system = ps.System.GetInstance() #Instantiate system object
        camlist = self.system.GetCameras()
        if camlist.GetSize() > 0:
            self.cam = camlist.GetByIndex(0)
            modelname = self.cam.TLDevice.DeviceModelName.GetValue()
            modelid =  self.cam.TLDevice.DeviceSerialNumber.GetValue()
            print('Made contact with {:s}: ID: {:s}'.format(modelname,modelid))
        else:
            print('{:d} cameras found'.format(camlist.GetSize()))

        #setup the hardware
        self.cam.Init()  #initialize camera, then we don't have to use the quickspin API but can use the genAPI (more generic)
        #self.bitFormat(12)
        self.exposureMode('timed')
        self.exposureAuto('off')
        self.gainAuto('off')
        self.blacklevel(0)
        self.acquisitionMode('single')
        self.triggerMode('on')
        self.triggerSource('hardware',risingedge = True)




    @QMethod
    def exposure(self,exposuretime = None):
        '''set or gets the exposure time of the camera, in microseconds'''
        if demo:
            return exposuretime
        if exposuretime is None:
            return self.cam.ExposureTime.GetValue()
        else:
            minexp = self.cam.ExposureTime.GetMin()
            maxexp = self.cam.ExposureTime.GetMax()
            if exposuretime < minexp or exposuretime > maxexp:
                return False
            else:
                self.cam.ExposureTime.SetValue(exposuretime) 
                return True

    @QMethod
    def exposureAuto(self,mode = None):
        '''set or get the exposure auto mode'''
        if demo:
            return mode
        if mode is None:
            return self.cam.ExposureAuto.GetCurrentEntry().GetSymbolic()
        elif mode.lower() == 'on':
            self.cam.ExposureAuto.SetValue(ps.ExposureAuto_Continuous)
        elif mode.lower() == 'off':
            self.cam.ExposureAuto.SetValue(ps.ExposureAuto_Off)
        else:
            print('Failed to set ExposureAuto, did not understand keyword: ',mode)
            return False
        return True

    @QMethod
    def exposureMode(self, mode=None):
        '''sets or gets the exposure mode (not auto or manual exposure)'''
        if demo:
            return exposureMode
        if mode is None:
            return self.cam.ExposureMode.GetCurrentEntry().GetSymbolic()
        elif mode.lower() == 'timed':
            self.cam.ExposureMode.SetValue(ps.ExposureMode_Timed)
        elif mode.lower() == 'triggerwidth':
            self.cam.ExposureMode.SetValue(ps.ExposureMode_TriggerWidth)
        else:
            print('Failed to set Exposuremode, did not understand keyword: ',mode)
            return False
        return True

    @QMethod
    def gain(self,gainvalue = None):
        '''set or gets the gain of the ADC in the camera camera, in dB'''
        if demo:
            return gainvalue
        if gainvalue is None:
            return self.cam.Gain.GetValue()
        else:
            mingain = self.cam.Gain.GetMin()
            maxgain = self.cam.Gain.GetMax()
            if gainvalue < mingain or gainvalue > maxgain:
                return False
            else:
                print(gainvalue)
                self.cam.Gain.SetValue(gainvalue) 
                return True

    @QMethod
    def gainAuto(self,mode = None):
        '''set or get the gain auto mode'''
        if demo:
            return mode
        if mode is None:
            val = self.cam.GainAuto.GetCurrentEntry().GetSymbolic()
            if val in ['Continuous', 'Once']:
                return 'on'
            elif val == 'Off':
                return 'off'
            else:
                return False
        elif mode.lower() == 'on':
            self.cam.GainAuto.SetValue(ps.GainAuto_Continuous)
        elif mode.lower() == 'off':
            self.cam.GainAuto.SetValue(ps.GainAuto_Off)
        else:
            print('Failed to set GainAuto, did not understand keyword: ',mode)
            return False
        return True


    @QMethod
    def blacklevel(self,blackvalue = None):
        '''set or gets the blacklevel of camera, in percent'''
        if demo:
            return blackvalue
        if blackvalue is None:
            return self.cam.BlackLevel.GetValue()
        else:
            minblack = self.cam.BlackLevel.GetMin()
            maxblack = self.cam.BlackLevel.GetMax()
            if blackvalue < minblack or blackvalue > maxblack:
                return False
            else:
                self.cam.BlackLevel.SetValue(blackvalue) 
                return True

    @QMethod
    def acquisitionMode(self,mode=None):
        '''sets the acquisitionmode to either 'single','multi', or 'cont'''
        if demo:
            return mode
        if mode is None:
            return self.cam.AcquisitionMode.GetValue()
        elif mode.lower() == 'single':
            self.cam.AcquisitionMode.SetValue(ps.AcquisitionMode_SingleFrame)
        elif mode.lower() == 'multi':
            self.cam.AcquisitionMode.SetValue(ps.AcquisitionMode_MultiFrame)
        elif mode.lower() == 'cont':
            print('set to cont')
            self.cam.AcquisitionMode.SetValue(ps.AcquisitionMode_Continuous)
        else:
            return False
        return True

    @QMethod
    def bitFormat(self, bitsize = None):
        if demo:
            return bitsize
        if bitsize is None:
            return (self.cam.PixelFormat.GetCurrentEntry().GetSymbolic(),self.cam.PixelSize.GetCurrentEntry().GetSymbolic())
        elif bitsize == 8:
            print('changing bitformat now to 8')
            self.cam.PixelFormat.SetValue(ps.PixelFormat_Mono8)
            self.bit8 = True
        elif bitsize == 12:
            print('changing bitformat now to 12')
            self.cam.PixelFormat.SetValue(ps.PixelFormat_Mono16)
            self.bit8 = False
        else:
            print('Failed to set Bitformat did not understand keyword: ',bitsize)
            return False
        return True

    @QMethod
    def triggerMode(self, mode = None):
        if demo:
            return mode
        if mode is None:
            return self.cam.TriggerMode.GetCurrentEntry().GetSymbolic()
        elif mode.lower() == 'on':
            self.cam.ExposureMode.SetValue(ps.ExposureMode_Timed)
            self.cam.TriggerMode.SetValue(ps.TriggerMode_On)
        elif mode.lower() == 'off':
            self.cam.TriggerMode.SetValue(ps.TriggerMode_Off)
        else:
            print('Failed to set Triggermode, did not understand keyword: ',mode)
            return False
        return True

    @QMethod
    def triggerSource(self,source=None, risingedge = True):
        if demo:
            return source
        if source is None:
            return self.cam.TriggerSource.GetCurrentEntry().GetSymbolic()
        elif source.lower() == 'software':
            self.cam.TriggerSource.SetValue(ps.TriggerSource_Software)
        elif source.lower() == 'hardware':
            self.cam.TriggerSource.SetValue(ps.TriggerSource_Line0)
            if risingedge:
                self.cam.TriggerActivation.SetValue(ps.TriggerActivation_RisingEdge)
            else:
                self.cam.TriggerActivation.SetValue(ps.TriggerActivation_FallingEdge)
        else:
            print('Failed to set TriggerSource, did not understand keyword: ',source)
            return False

    @QMethod
    def binning(self,bins = None):
        if bins is None:
            return (self.cam.BinningHorizontal.GetValue(),
                    self.cam.BinningVertical.GetValue())
        else:
            horizontalbins = bins[0]
            verticalbins = bins[1]
#            self.cam.BinningHorizontal.SetValue(horizontalbins)
            self.cam.BinningVertical.SetValue(verticalbins)
            return True

    @QMethod
    def binningMode(self,binningMode = None):
        if binningMode is None:
            return (self.cam.BinningHorizontalMode.GetCurrentEntry().GetSymbolic(),
                    self.cam.BinningVerticalMode.GetCurrentEntry().GetSymbolic())
        elif binningMode.lower() == 'average':
            #self.cam.BinningHorizontalMode.SetValue(ps.BinningHorizontalMode_Average)
            self.cam.BinningVerticalMode.SetValue(ps.BinningVerticalMode_Average)
            return True
        elif binningMode.lower() == 'sum':
            #self.cam.BinningHorizontalMode.SetValue(ps.BinningHorizontalMode_Sum)
            self.cam.BinningVerticalMode.SetValue(ps.BinningVerticalMode_Sum)
            return True
        else:
            print('Failed to set BinningMode, did not understand keyword: ',binningMode)
            return False



    @QMethod
    def acquireSingleImage(self):
        if demo:
            return self.demodata
        if self.cam.AcquisitionMode.GetValue() == ps.AcquisitionMode_SingleFrame:
            self.cam.BeginAcquisition()
            try:
                image_result = self.cam.GetNextImage()
                if image_result.IsIncomplete():
                        print('Image incomplete with image status %d ...' % image_result.GetImageStatus())

                else:
                    if self.bit8:
                        data = np.array(image_result.GetData())
                        print('8 bit')
                    else:
                        #newimage = image_result.Convert(ps.PixelFormat_Mono16)
                        print('her')
                        newimage = image_result.Convert(ps.PixelFormat_Mono8)
                        data = np.array(newimage.GetData())
                        print('converted')
                    image_result.Release()

            except ps.SpinnakerException as ex:
                print('Error: %s' % ex)
                return False

            self.cam.EndAcquisition()
            return data
        else:
            return None

    @QMethod
    def beginAcquisition(self):
        if demo:
            print('Acquisition beginning')
            return None
        if self.cam.AcquisitionMode.GetValue() == ps.AcquisitionMode_Continuous:
            self.cam.BeginAcquisition()

    @QMethod
    def endAcquisition(self):
        if demo:
            print('Acquisition ending')
            return None
        if self.cam.AcquisitionMode.GetValue() == ps.AcquisitionMode_Continuous:
            self.cam.EndAcquisition()



    @QMethod
    def getImage(self):
        if demo:
            return self.demodata
        if self.cam.AcquisitionMode.GetValue() == ps.AcquisitionMode_Continuous:
            try:
                image_result = self.cam.GetNextImage()
                if image_result.IsIncomplete():
                    print('Image incomplete with image status %d ...' % image_result.GetImageStatus())
                    return None
                else:
                    if self.bit8:
                        #print(image_result.GetData())
                        data = image_result.GetData()
                        #print(max(data))
                        #print(len(data))
                    else:
                        #print('before:')
                        #print(image_result.GetData())
                        #print(len(image_result.GetData()))
                        #print(max(image_result.GetData()))
                        data = image_result.Convert(ps.PixelFormat_Mono16).GetData()
                        #print('after')
                        #print(max(data))
                        #print(len(data))
                    image_result.Release()       
            except ps.SpinnakerException as ex:
                print('Error: %s' % ex)
                return False
            return data
        else:
            return None                                 



    def onClosing(self):
        self.cam.DeInit()
        del self.cam
        self.system.ReleaseInstance()








if __name__ == "__main__":
    server = Server()
    server.run()



