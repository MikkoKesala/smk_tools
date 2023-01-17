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
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink)
from SuojavyohykeValinta import getWater,bufferzone,feature2layer
from PIL import Image
import processing
#from sys import exit

pluginPath = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        os.pardir))

class suojakaista_toolsAlgorithm(QgsProcessingAlgorithm):
    """
    This is an example algorithm that takes a vector layer and
    creates a new identical one.

    It is meant to be used as an example of how to create your own
    algorithms and explain methods and variables used to do it. An
    algorithm like this will be available in all elements, and there
    is not need for additional work.

    All Processing algorithms should extend the QgsProcessingAlgorithm
    class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    OUTPUT = 'OUTPUT'
    PINTAALA = 'PINTAALA'
    VAIKUTUS = 'VAIKUTUS'
    INPUT = 'INPUT'

    pnimet = ['suojakaista_taustarasterit','RUSLE','MassataseGISSUS','WB_Finland'] #taustarastereissa band1 = costdistance ; band2 = euclidean ; band3 = lsn


    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input vector features source. It can have any kind of
        # geometry.
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('Leimikko'),
                [QgsProcessing.TypeVectorPolygon]
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.VAIKUTUS,
                self.tr('Pidätyksen vaikutusprosentti (%)'),
                type=QgsProcessingParameterNumber.Integer,
                minValue=40,maxValue=95,defaultValue=70
            )
            )
        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Suojakaista-alue')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
        source = self.parameterAsSource(parameters, self.INPUT, context)
        if source.featureCount() > 20:
            feedback.reportError("Input layer has too many features. 20 dissolved features is maximum. Process failed.")
            sys.exit()

        #feedback.pushInfo(str(parameters['INPUT']))
        source = processing.run("native:dissolve", {'INPUT':parameters['INPUT'],'FIELD':[],'OUTPUT':'TEMPORARY_OUTPUT'})
        source = source['OUTPUT']
        #features = source.getFeatures()

        # Compute the number of steps to display within the progress bar and
        # get features from source
        total = 100.0 / source.featureCount() if source.featureCount() else 0
        
        features = source.getFeatures()
        vaik = self.parameterAsInt(parameters,self.VAIKUTUS,context)
        for current, feature in enumerate(features):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break
            rasterit = []
            for i in self.pnimet:
                #print (i)
                f = feature2layer(feature)
                rast = getWater(f,i)
                #rast = gdal.Open(rast)
                rasterit.append(rast)
                #exit

            out = [f]
            out = bufferzone(f,rasterit,vaik)
            
            # Add a feature in the sink
            if current == 0:
                (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT,
                context, out[0].fields(), out[0].wkbType(), out[0].sourceCrs())
            feedback.pushInfo(str(out[0].fields().names()))
            for outfeat in out[0].getFeatures():
                sink.addFeature(outfeat, QgsFeatureSink.FastInsert)
            g = Image.open(out[1])
            g.show()
            # Update the progress bar
            feedback.setProgress(int(current * total))

        # Return the results of the algorithm. In this case our only result is
        # the feature sink which contains the processed features, but some
        # algorithms may return multiple feature sinks, calculated numeric
        # statistics, etc. These should all be included in the returned
        # dictionary, with keys matching the feature corresponding parameter
        # or output names.
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
