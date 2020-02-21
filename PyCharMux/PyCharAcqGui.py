
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 19 10:26:32 2020

@author: Javier
"""

from __future__ import print_function
from PyQt5 import Qt
from qtpy.QtWidgets import (QHeaderView, QCheckBox, QSpinBox, QLineEdit,
                            QDoubleSpinBox, QTextEdit, QComboBox,
                            QTableWidget, QAction, QMessageBox, QFileDialog,
                            QInputDialog)

from qtpy import QtWidgets, uic
import numpy as np
import time
import os
import sys
import matplotlib.pyplot as plt
import PyGFETdb.PlotDataClass as PyFETpl
from pyqtgraph.parametertree import Parameter, ParameterTree

import PyqtTools.FileModule as FileMod
import PyqtTools.PlotModule as PltMod
import PyqtTools.SaveDictsModule as SaveDC
import PyqtTools.SweepsModule as SweepMod
import PyqtTools.StabDetector as StbDet

import PyCharAcqCore.PyCharAcqThread as AcqMod


###############################################################################
####
###############################################################################


class CharacLivePlot():

    DCPlotVars = ('Ids', 'Rds', 'Gm', 'Ig')
    BodePlotVars = ('GmPh', 'GmMag')
    PSDPlotVars = ('PSD',)
    PlotSwDC = None
    PlotSwAC = None
    DebugFig = None

    def __init__(self, SinglePoint=True, Bode=True, PSD=True, FFT=False):

        self.DebugFig, self.DebugAxs = plt.subplots()
        self.DebugAxs.ticklabel_format(axis='y', style='sci',
                                       scilimits=(-2, 2))
        plt.show()

        if not SinglePoint:
            self.PlotSwDC = PyFETpl.PyFETPlot()
            self.PlotSwDC.AddAxes(self.DCPlotVars)

        if Bode or PSD:
            PVAC = []
            if Bode:
                for var in self.BodePlotVars:
                    PVAC.append(var)
            if PSD:
                for var in self.PSDPlotVars:
                    PVAC.append(var)
            self.PlotSwAC = PyFETpl.PyFETPlot()
            self.PlotSwAC.AddAxes(PVAC)

        if FFT:
            self.FFTFig, self.FFTAxs = plt.subplots()
            self.FFTAxs.ticklabel_format(axis='y', style='sci',
                                         scilimits=(-2, 2))
            plt.show()

    def UpdateTimeViewPlot(self, Ids, Time, Dev):
        while self.DebugAxs.lines:
            self.DebugAxs.lines[0].remove()
        self.DebugAxs.plot(Time, Ids)
        self.DebugAxs.set_ylim(np.min(Ids), np.max(Ids))
        self.DebugAxs.set_xlim(np.min(Time), np.max(Time))
        self.DebugAxs.set_title(str(Dev))
        self.DebugFig.canvas.draw()

    def UpdateTimeAcViewPlot(self, Ids, Time):
        while self.DebugAxs.lines:
            self.DebugAxs.lines[0].remove()
        self.DebugAxs.plot(Time, Ids)
        self.DebugAxs.set_ylim(np.min(Ids), np.max(Ids))
        self.DebugAxs.set_xlim(np.min(Time), np.max(Time))
        self.DebugFig.canvas.draw()

    def UpdateSweepDcPlots(self, Dcdict):
        if self.PlotSwDC:
            self.PlotSwDC.ClearAxes()
            self.PlotSwDC.PlotDataCh(Dcdict)
            self.PlotSwDC.AddLegend()
            self.PlotSwDC.Fig.canvas.draw()

    def UpdateAcPlots(self, Acdict):
        if self.PlotSwAC:
            self.PlotSwAC.ClearAxes()
            self.PlotSwAC.PlotDataCh(Acdict)
            self.PlotSwAC.Fig.canvas.draw()

    def PlotFFT(self, FFT):
        self.FFTAxs.plot(np.abs(FFT))
        self.FFTFig.canvas.draw()

    def __del__(self):
        plt.close('all')


###############################################################################
####
###############################################################################


class MainWindow(Qt.QWidget):
    ''' Main Window '''

    PlotSweep = None

    def __init__(self):
        super(MainWindow, self).__init__()

        layout = Qt.QVBoxLayout(self)

        self.btnAcq = Qt.QPushButton("Start Char!")
        layout.addWidget(self.btnAcq)

        # Sampling Settings
        self.SamplingPar = AcqMod.SampSetParam(name='SampSettingConf')
        self.Parameters = Parameter.create(name='App Parameters',
                                           type='group',
                                           children=(self.SamplingPar,))

        self.SamplingPar.NewConf.connect(self.on_NewConf)

        # Sweep Config
        self.SweepParams = SweepMod.SweepsConfig(name='Sweeps Configuration')
        self.Parameters.addChild(self.SweepParams)

        # Sweep Saving
        self.SaveSwParams = SaveDC.SaveSweepParameters(QTparent=self,
                                                        name='Sweeps File')
        self.Parameters.addChild(self.SaveSwParams)

        # Plotting
        self.PlotParams = PltMod.PlotterParameters(name='Plot options')
        self.PlotParams.SetChannels(self.SamplingPar.GetChannelsNames())
        self.PlotParams.param('Fs').setValue(self.SamplingPar.FsxCh.value())

        self.Parameters.addChild(self.PlotParams)

        # Raw Plotting
        # self.RawPlotParams = PltMod.PlotterParameters(name='Raw Plot')
        # self.RawPlotParams.SetChannels(self.SamplingPar.GetRowNames())
        # self.RawPlotParams.param('Fs').setValue(self.SamplingPar.Fs.value())

        # self.Parameters.addChild(self.RawPlotParams)

        # PSD Plotting
        self.PSDParams = PltMod.PSDParameters(name='PSD Options')
        self.PSDParams.param('Fs').setValue(self.SamplingPar.FsxCh.value())
        self.Parameters.addChild(self.PSDParams)
        self.Parameters.sigTreeStateChanged.connect(self.on_pars_changed)

        # File Saving
        self.FileParameters = FileMod.SaveFileParameters(QTparent=self,
                                                         name='Record File')
        self.Parameters.addChild(self.FileParameters)

        # Config Saving
        self.ConfigParameters = FileMod.SaveSateParameters(QTparent=self,
                                                           name='Configuration File')
        self.Parameters.addChild(self.ConfigParameters)


        ##
        self.treepar = ParameterTree()
        self.treepar.setParameters(self.Parameters, showTop=False)
        self.treepar.setWindowTitle('pyqtgraph example: Parameter Tree')

        layout.addWidget(self.treepar)

        self.setGeometry(650, 20, 400, 800)
        self.setWindowTitle('MainWindow')

        self.btnAcq.clicked.connect(self.on_btnStart)
        self.threadAcq = None
        self.threadSave = None
        self.threadPlotter = None
        self.threadPlotterRaw = None

    # Changes Control
    def on_pars_changed(self, param, changes):
        print("tree changes:")
        for param, change, data in changes:
            path = self.Parameters.childPath(param)
            if path is not None:
                childName = '.'.join(path)
            else:
                childName = param.name()
        print('  parameter: %s' % childName)
        print('  change:    %s' % change)
        print('  data:      %s' % str(data))
        print('  ----------')

        if childName == 'SampSettingConf.Sampling Settings.FsxCh':
            self.PlotParams.param('Fs').setValue(data)
            self.PSDParams.param('Fs').setValue(data)

        if childName == 'SampSettingConf.Sampling Settings.Fs':
            self.RawPlotParams.param('Fs').setValue(data)

        if childName == 'Plot options.RefreshTime':
            if self.threadPlotter is not None:
                self.threadPlotter.SetRefreshTime(data)

        if childName == 'Plot options.ViewTime':
            if self.threadPlotter is not None:
                self.threadPlotter.SetViewTime(data)

        # if childName == 'Raw Plot.ViewTime':
        #     if self.threadPlotterRaw is not None:
        #         self.threadPlotterRaw.SetViewTime(data)

        # if childName == 'Raw Plot.RefreshTime':
        #     if self.threadPlotterRaw is not None:
        #         self.threadPlotterRaw.SetRefreshTime(data)

    def on_NewConf(self):
        self.Parameters.sigTreeStateChanged.disconnect()
        self.PlotParams.SetChannels(self.SamplingPar.GetChannelsNames())
        self.RawPlotParams.SetChannels(self.SamplingPar.GetRowNames())
        self.Parameters.sigTreeStateChanged.connect(self.on_pars_changed)

    def on_btnStart(self):
        if self.threadAcq is None:
            self.VdInd = 0
            self.VgInd = 0

            # Sweep Variables
            self.SweepsKwargs = self.SweepParams.GetSweepsParams()
            self.DCSaveKwargs = self.SaveSwParams.GetParams()
            self.SwEnable = self.SweepsKwargs['Enable']
            self.VdsSweepVals = self.SweepsKwargs['VdSweep']
            self.VgsSweepVals = self.SweepsKwargs['VgSweep']

            GenKwargs = self.SamplingPar.GetSampKwargs()
            GenKwargs['Vds'] = self.SweepsKwargs['VdSweep'][self.VdInd]
            GenKwargs['Vgs'] = self.SweepsKwargs['VgSweep'][self.VgInd]

            GenChanKwargs = self.SamplingPar.GetChannelsConfigKwargs()
            AvgIndex = self.SamplingPar.SampSet.param('nAvg').value()
            ChannelsNames = self.SamplingPar.GetChannelsNames()

            # Cycles
            # self.Cycles = self.SamplingPar.GetCycles()
            # self.initCy = self.Cycles['InitCy']
            # self.finalCy = self.Cycles['FinalCy']
            # if self.initCy > self.finalCy:
            #     print('Set correct Cycles')
            #     self.finalCy = self.initCy + 1
            #     self.SamplingPar.Cycles.param('FinalCy').setValue(self.finalCy)
            # self.SamplingPar.Cycles.param('CurrentCy').setValue(self.initCy)

            self.threadAcq = AcqMod.DataAcquisitionThread(ChannelsConfigKW=GenChanKwargs,
                                                          SampKw=GenKwargs,
                                                          AvgIndex=AvgIndex,
                                                          )
            # if not self.SinglePoint: TODO
            if self.PlotSweep:
                del self.PlotSweep
            self.PlotSweep = CharacLivePlot(SinglePoint=False,
                                            Bode=False,
                                            PSD=False)

            # def InitSweepChar(self):
            # Apply First Bias Point
            if self.SwEnable:
                self.threadStbDet = StbDet.StbDetThread(MaxSlope=self.SweepsKwargs['MaxSlope'],
                                                        TimeOut=self.SweepsKwargs['TimeOut'],
                                                        nChannels=len(ChannelsNames),
                                                        ChnName=ChannelsNames,
                                                        # PlotterDemodKwargs=,
                                                        PlotterDemodKwargs=self.PSDParams.GetParams(),
                                                        VdVals=self.VdsSweepVals,
                                                        VgVals=self.VgsSweepVals)
                
                self.threadStbDet.NextVg.connect(self.on_NextBias)
                self.threadStbDet.initTimer()  # TimerPara el primer Sweep
                self.threadStbDet.start()


            ##
            self.threadAcq.NewMuxData.connect(self.on_NewSample)
            self.threadAcq.start()

            PlotterKwargs = self.PlotParams.GetParams()

            FileName = self.FileParameters.FilePath()
            print('Filename', FileName)
            if FileName == '':
                print('No file')
            else:
                if os.path.isfile(FileName):
                    print('Remove File')
                    os.remove(FileName)
                MaxSize = self.FileParameters.param('MaxSize').value()
                self.threadSave = FileMod.DataSavingThread(FileName=FileName,
                                                           nChannels=PlotterKwargs['nChannels'],
                                                           MaxSize=MaxSize)
                self.threadSave.start()

            if self.PlotParams.param('PlotEnable').value():
                self.threadPlotter = PltMod.Plotter(**PlotterKwargs)
                self.threadPlotter.start()

            # if self.RawPlotParams.param('PlotEnable').value():
            #     RawPlotterKwargs = self.RawPlotParams.GetParams()
            #     self.threadPlotterRaw = PltMod.Plotter(ShowTime=False,
            #                                            **RawPlotterKwargs)
            #     self.threadPlotterRaw.start()
            # self.threadPSDPlotter = PltMod.PSDPlotter(ChannelConf=PlotterKwargs['ChannelConf'],
            #                                           nChannels=PlotterKwargs['nChannels'],
            #                                           **self.PSDParams.GetParams())
            # self.threadPSDPlotter.start()

            self.btnAcq.setText("Stop Gen")
            self.OldTime = time.time()
            self.Tss = []
        else:
            self.threadAcq.DaqInterface.Stop()
            self.threadAcq = None

            if self.threadSave is not None:
                self.threadSave.terminate()
                self.threadSave = None
            if self.PlotParams.param('PlotEnable').value():
                self.threadPlotter.terminate()
                self.threadPlotter = None

            self.btnAcq.setText("Start Gen")

    def on_NewSample(self):
        ''' Visualization of streaming data-WorkThread. '''
        Ts = time.time() - self.OldTime
        self.Tss.append(Ts)
        self.OldTime = time.time()
        # print(self.threadAcq.aiData.shape)

        if self.threadStbDet:
            self.threadStbDet.AddData(self.threadAcq.OutData.transpose())
        if self.threadSave is not None:
            self.threadSave.AddData(self.threadAcq.OutData.transpose())
        if self.PlotParams.param('PlotEnable').value():
            self.threadPlotter.AddData(self.threadAcq.OutData.transpose())
        # if self.RawPlotParams.param('PlotEnable').value():
        #     self.threadPlotterRaw.AddData(self.threadAcq.aiData.transpose())
        # self.threadPSDPlotter.AddData(self.threadAcq.OutData.transpose())
        print('Sample time', Ts, np.mean(self.Tss))

    # Next Bias
    def on_NextBias(self):
        print('NextBias')
        self.PlotSweep.UpdateSweepDcPlots(self.threadStbDet.SaveDCAC.DevDCVals)
        
        if self.VdInd < len(self.VdsSweepVals) - 1:
            self.VdInd += 1
        else:
            self.VdInd = 0
            if self.VgInd < len(self.VgsSweepVals) - 1:
                self.VgInd += 1
            else:
                self.VgInd = 0
                DCDict = self.threadStbDet.SaveDCAC.DevDCVals
                ACDict = self.threadStbDet.SaveDCAC.DevACVals
                print(self.DCSaveKwargs)
                self.threadStbDet.SaveDCAC.SaveDicts(DCDict,
                                                     ACDict,
                                                     **self.DCSaveKwargs)
                # self.NextCycle()
                self.StopMain()

        if self.threadAcq:

            self.threadStbDet.VgIndex = self.VgInd
            self.threadStbDet.VdIndex = self.VdInd
            self.ApplyBiasPoint()
            self.threadStbDet.initTimer()

        else:
            self.StopMain()
            
            # self.threadAcq.DaqInterface.Stop()
            # self.threadAcq = None
            # self.btnAcq.setText("Start Gen")
            # # self.StopThreads()
            # self.threadStbDet.Timer.stop()
            # self.threadStbDet.Timer.killTimer(self.threadStbDet.Id)
            # self.threadStbDet.NextVg.disconnect()
            # DCDict = self.threadStbDet.SaveDCAC.DevDCVals
            # ACDict = self.threadStbDet.SaveDCAC.DevACVals
            # self.threadStbDet.SaveDCAC.SaveDicts(DCDict,
            #                                      ACDict,
            #                                      **self.DcSaveKwargs)
            # self.threadStbDet.stop()

    # def NextCycle(self):
    #     if self.initCy < self.finalCy-1:
    #         self.initCy += 1
    #         self.SamplingPar.Cycles.param('CurrentCy').setValue(self.initCy)



    #         # SwVgsVals, SwVdsVals = self.SweepVariables()
    #         # self.Charac.InitSweep(VgsVals=SwVgsVals,
    #         #                       VdsVals=SwVdsVals,
    #         #                       PSD=self.CheckPSD,
    #         #                       Bode=self.CheckBode)
    #     else:
    #         if self.Charac.CharactRunning:
    #             self.initCy = 0
    #             self.ChannelsPar.Cycles.param('CurrentCy').setValue(self.initCy)
    #             self.Charac.SetBias(Vds=0, Vgs=0)
    #             self.StopSweep()

    def ApplyBiasPoint(self):
        print(self.VgsSweepVals)
        print(self.VgInd)
        self.threadAcq.DaqInterface.SetBias(Vgs=self.VgsSweepVals[self.VgInd],
                                            Vds=self.VdsSweepVals[self.VdInd])

# #############################STOP##############################
    def StopThreads(self):
        if self.threadSave is not None:
            self.threadSave.stop()
            self.threadSave = None

        if self.threadPlotter is not None:
            self.threadPlotter.stop()
            self.threadPlotter = None

        if self.threadPsdPlotter is not None:
            self.threadPsdPlotter.stop()
            self.threadPsdPlotter = None

    def StopMain(self): 
        if self.threadAcq:
            self.threadAcq.DaqInterface.Stop()
            self.threadAcq = None
        if self.threadStbDet:
            self.threadStbDet.Timer.stop()
            self.threadStbDet.Timer.killTimer(self.threadStbDet.Id)
            # self.threadStbDet.NextVg.disconnect()  
            # self.threadStbDet.stop()
        
        if self.threadSave is not None:
            self.threadSave.terminate()
            self.threadSave = None
        if self.threadPlotter:
            self.threadPlotter.stop()
            self.threadPlotter = None

        self.btnAcq.setText("Start Gen")



def main():
    import argparse
    import pkg_resources

    # Add version option
    __version__ = pkg_resources.require("PyCont")[0].version
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', action='version',
                        version='%(prog)s {version}'.format(
                            version=__version__))
    parser.parse_args()

    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
