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


# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'
from stat import S_ISLNK
from qgis import processing
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QCoreApplication,QVariant
from qgis.core import (QgsProcessing,QgsProcessingAlgorithm,
                       QgsField,
                       QgsFeatureSink,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterField,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterRasterDestination,
                        QgsProcessingUtils,QgsRasterLayer,QgsVectorLayer)
import os,time,sys
sys.path.append(os.path.dirname(__file__))
#from PIL import Image
from smk_geotools import feature2Layer,addFieldValue,clipRaster4
#from saastopuu import *



class cliprasterbyfeat(QgsProcessingAlgorithm):

    

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        #inputs
        self.addParameter(QgsProcessingParameterVectorLayer('vector', 'vector', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterLayer('raster', 'raster', defaultValue=None))
        self.addParameter(QgsProcessingParameterField('rastername', 'rastername', type=QgsProcessingParameterField.Any, parentLayerParameterName='vector', allowMultiple=False, defaultValue='fid'))
        self.addParameter(QgsProcessingParameterFile('outfolder', 'outfolder', behavior=QgsProcessingParameterFile.Folder, fileFilter='All files (*.*)', defaultValue='C:\\Users\\mjkesala\\pvenv\\aineistot\\rasterit'))
        self.addParameter(QgsProcessingParameterRasterDestination('outputraster', 'outputraster', createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        results = {}
        outputs = {}
        try:
 
            source = QgsProcessingUtils.mapLayerFromString(parameters['vector'],context)
            #source = self.parameterAsSource(parameters, self.INPUT, context)
            if source.featureCount() > 100:
                feedback.reportError("Input layer has too many features. 100 features is maximum. Process failed.")
                sys.exit()

            #feedback.pushInfo(str(parameters['INPUT']))
            source = processing.run("native:dissolve", {'INPUT':parameters['vector'],'FIELD':[],'OUTPUT':'TEMPORARY_OUTPUT'},context=context,feedback=feedback,is_child_algorithm=True)
            source = processing.run("native:multiparttosingleparts", {'INPUT':source['OUTPUT'],'OUTPUT':'TEMPORARY_OUTPUT'},context=context,feedback=feedback,is_child_algorithm=False)
            source = source['OUTPUT']
           
            
            # Compute the number of steps to display within the progress bar and
            #slayer = QgsVectorLayer(parameters['INPUT'],"slayer","ogr")
            # get features from source
            
            total = 100.0 / source.featureCount() if source.featureCount() else 0
            
            features = source.getFeatures()
            raster_list = []
            feedback.pushInfo(str(total))
            for current, feature in enumerate(features):
                #feedback.setProgressText("testia ja "+str(out))
                # Stop the algorithm if cancel button has been clicked
                if feedback.isCanceled():
                    break
                
                feedback.setProgressText("Rajataan aineistot")

                #leimFeat = feature.getFeatures()
                leimArea = [feature.geometry().area()/10000]
                out = feature2Layer(feature,100)
                #out1 = feature2Layer(feature,0)
                out.setCrs(source.crs())
                #out1.setCrs(source.crs())
                #leim = addFieldValue(out1,"leimikko",1)
                
                
                raster = QgsProcessingUtils.mapLayerFromString(parameters['raster'],context)
                raster = clipRaster4(raster,out,parameters['outfolder'],current)
                raster_list.append(raster)
                    
                    #out = outChm
                

     
            alg_params = {
                'ADD_ALPHA': False,
                'ASSIGN_CRS': None,
                'EXTRA': '',
                'INPUT': raster_list,
                'PROJ_DIFFERENCE': False,
                'RESAMPLING': 0,  # Nearest Neighbour
                'RESOLUTION': 0,  # Average
                'SEPARATE': False,
                'SRC_NODATA': '',
                'OUTPUT': parameters['outputraster']}
            
            outputs['BuildVirtualRaster'] = processing.run('gdal:buildvirtualraster', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
            
        except Exception as e:
                feedback.pushWarning(e)
   
        
        results['outputraster'] = outputs['BuildVirtualRaster']['OUTPUT']
        
        return results


    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'ClipRasterFeatByFeat'

    def icon(self):
        
        return QIcon('icon.jpg')

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
        return cliprasterbyfeat()