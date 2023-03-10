# -*- coding: utf-8 -*-

"""
/***************************************************************************
 smk_tools
                                 A QGIS plugin
 Suomen metsäkeskuksen työkalut
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2022-10-04
        copyright            : (C) 2022 by Suomen metsäkeskus
        email                : mikko.kesala@metsakeskus.fi
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'Suomen metsäkeskus'
__date__ = '2022-10-04'
__copyright__ = '(C) 2022 by Suomen metsäkeskus'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os,sys
from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingUtils,
                       QgsProcessingParameterDefinition)
#from get feature2layer
from getInput import getWater,feature2layer
from bufferZone import getBufferzone
from waterLine import getWaterline
#from PIL import Image
import processing
#from sys import exit

pluginPath = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        os.pardir))

class suojakaista_toolsAlgorithm(QgsProcessingAlgorithm):
    """
    This is an algorithm that takes a vector layer and
    get background rasters via interface the vector area
    and creates a new buffer zone along the waterbody.
    Input layer should be near waterbody

    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    OUTPUT = 'OUTPUT'
    MINDIST = 'MINDIST'
    MEANDIST = 'MEANDIST'
    AREA = 'AREA'
    #COST = 'COST' not use the cost parameters before correct mass flux formula 
    #COSTB = 'COSTB'
    INPUT = 'INPUT'

    interface_name = ['suojakaista_taustarasterit','RUSLE','WB_Finland','DEM']
    #backgroud rasters: band1 = costdistance ; band2 = euclidean ; band3 = lsn


    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('Leimikko'),
                [QgsProcessing.TypeVectorPolygon]
            )
        )
        
        self.addParameter(
            QgsProcessingParameterNumber(
                self.MEANDIST,
                self.tr('Suojakaistan keskileveys'),
                type=QgsProcessingParameterNumber.Integer,
                minValue=5,maxValue=50,defaultValue=15
            )
            )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.MINDIST,
                self.tr('Suojakaistan minimileveys (m)'),
                type=QgsProcessingParameterNumber.Integer,
                minValue=5,maxValue=20,defaultValue=5
            )
            )
       
        """
        params = []
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.COSTB,
                self.tr('Pidätyksen vaikutusprosentti on ehtona'),defaultValue=False
            )
        )
    
        params.append(
            QgsProcessingParameterNumber(
                self.COST,
                self.tr('Pidätyksen vaikutusprosentti (%)'),
                minValue=60,maxValue=98,defaultValue=90,
            )
        )
        for p in params:
            p.setFlags(p.flags() | QgsProcessingParameterDefinition.FlagAdvanced) 
            self.addParameter(p)
        """

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Suojakaista-alue')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        

        source = self.parameterAsSource(parameters, self.INPUT, context)
        if source.featureCount() > 20:
            feedback.reportError("Input layer has too many features. 20 features is maximum. Process failed.")
            sys.exit()

        feedback.pushInfo("Aloitetaan suojakaistan luonti")
        source = processing.run("native:dissolve", {'INPUT':parameters['INPUT'],'FIELD':[],'OUTPUT':'TEMPORARY_OUTPUT'})
        source = source['OUTPUT']

        # Compute the number of steps to display within the progress bar and
        # get features from source
        total = 100.0 / source.featureCount() if source.featureCount() else 0
        count = source.featureCount() if source.featureCount() else 0

        features = source.getFeatures()
        #costb = self.parameterAsBoolean(parameters,self.COSTB,context)
        #cost = self.parameterAsInt(parameters,self.COST,context)
        #cost = (costb,cost)
        cost = (False,80) #change to above when massflux formula is correct
        mindist = self.parameterAsInt(parameters,self.MINDIST,context)
        meandist = self.parameterAsInt(parameters,self.MEANDIST,context)
        dist = (mindist,meandist)
        
        for current, feature in enumerate(features):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break
            feedback.pushInfo("kuvio "+ str(current+1) +"/"+ str(count))
            feedback.setProgress(int(current * total/4))
            
            rasterit = []
            for i in self.interface_name:
                #print (i)
                f = feature2layer(feature)
                rast = getWater(f,i)
                #rast = gdal.Open(rast)
                rasterit.append(rast)
                #exit

            feedback.pushInfo("Tausta-aineisto haettu rajapinnasta")
            feedback.setProgress(int(current * total/3))
            waterline = getWaterline(rasterit,f)
            feedback.pushInfo("Kuvion vesiraja on määritetty")
            feedback.setProgress(int(current * total/2))

            out = getBufferzone(rasterit,waterline[1],waterline[0],dist,cost)
            feedback.pushInfo("Suojakaista on luotu kohteelle "+str(current+1)+"/"+str(count))

            # Add a feature in the sink
            if current == 0:
                (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT,
                context, out.fields(), out.wkbType(), out.sourceCrs())
            
            for outfeat in out.getFeatures():
                sink.addFeature(outfeat, QgsFeatureSink.FastInsert)
            
            feedback.setProgress(int(current * total))

        # Return the results of the algorithm
        #style for layer
        style = os.path.join(os.path.dirname(__file__),"suojakaista_style1.qml")
        layer = QgsProcessingUtils.mapLayerFromString(dest_id,context)
        layer.loadNamedStyle(style)

        return {self.OUTPUT: dest_id}

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Luo suojakaistaehdotus'
    def icon(self):

        return QIcon(os.path.join(pluginPath, 'icon.jpg'))

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr(self.name())

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr(self.groupId())

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'SMK luontotieto'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return suojakaista_toolsAlgorithm()
