# -*- coding: utf-8 -*-

"""
/***************************************************************************
 RLERatioOfMap
                                 A QGIS plugin
 This plugin computes RLE compression ratio using layers
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2020-07-10
        copyright            : (C) 2020 by YSU
        email                : danillpot@yandex.ru
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

__author__ = 'YSU'
__date__ = '2020-07-10'
__copyright__ = '(C) 2020 by YSU'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os
import csv
import qgis

from PyQt5.QtCore import QCoreApplication
from qgis.core import (QgsProcessingAlgorithm,
                       QgsProcessingParameterExtent,
                       QgsProcessingParameterFileDestination,
                       QgsProcessingParameterFile,
                       QgsRectangle,
                       QgsProcessingParameterString,
                       QgsProcessingParameterNumber,
                       QgsProcessingException,
                       QgsMapSettings,
                       QgsMapRendererParallelJob)
from qgis.PyQt.QtCore import QSize
from qgis.PyQt.QtGui import QColor


# more imports
from mapanalyser.rle.rle_compression_ratio import get_ratio_with_abs_comparator, get_ratio_with_simple_comparator
from ..utils import tr, define_help_info, raise_exception, write_to_file


class RLERatioOfMapAlgorithm(QgsProcessingAlgorithm):
    """
    This is a class that calculates the RLE ratio of an map
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    OUTPUT = 'OUTPUT'
    INPUT = 'INPUT'
    EXTENT = 'EXTENT'
    CANVAS_NAME = 'CANVAS_NAME'
    WIDTH = 'WIDTH'
    HEIGHT = 'HEIGHT'
    HELP_FILE = 'rle_map_help.txt'

    def __init__(self):
        super().__init__()
        directory = os.path.dirname(__file__)
        file_name = os.path.join(directory, self.HELP_FILE)
        self._shortHelp = define_help_info(file_name)


    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """
        
        default_extent = qgis.utils.iface.mapCanvas().extent()
        default_extent_value = '{0},{1},{2},{3}'.format(default_extent.xMinimum(),
                                                        default_extent.xMaximum(),
                                                        default_extent.yMinimum(),
                                                        default_extent.yMaximum())

        self.addParameter(
            QgsProcessingParameterString(
                self.CANVAS_NAME,
                tr('Canvas name')))

        self.addParameter(
            QgsProcessingParameterExtent(
                self.EXTENT,
                tr('Minimum extent to render'),
                defaultValue=str(default_extent_value)))

        self.addParameter(
            QgsProcessingParameterNumber(
                self.WIDTH,
                tr('Output image width'),
                defaultValue=800))

        self.addParameter(
            QgsProcessingParameterNumber(
                self.HEIGHT,
                tr('Output image height'),
                defaultValue=600))

        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT,
                tr('Output file'),
                'csv(*.csv)',
            )
        )


    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        extent = self.parameterAsExtent(parameters, self.EXTENT, context)

        if not extent:
            raise_exception('can\'t read extent')

        feedback.setProgress(10)
        output_file = self.parameterAsFileOutput(
            parameters,
            self.OUTPUT,
            context)
        canvas_name = self.parameterAsString(
            parameters,
            self.CANVAS_NAME,
            context)

        if not canvas_name:
            if not output_file:
                raise_exception('empty output and canvas name')

            canvas_name = os.path.basename(output_file)

        image_width = self.parameterAsInt(parameters, self.WIDTH, context)

        if not image_width:
            image_width = 800

        image_height = self.parameterAsInt(parameters, self.HEIGHT, context)

        if not image_height:
            image_height = 600

        feedback.setProgress(20)
        output_dir = os.path.dirname(output_file)
        image_path = self.create_image(
            extent,
            image_width,
            image_height,
            canvas_name,
            output_dir)
        ratio = self.compress_from_image(image_path)
        row = [{
                'canvas': canvas_name,
                'compress ratio': ratio
            }]
        feedback.setProgress(80)

        if output_file:
            header = ['canvas', 'compress ratio']
            write_to_file(output_file, header, row, ';')

        return {'RLE compression ratio': ratio}


    def compress_from_image(self, image_path):
        '''
        This method computes RLE compress ratio

        :param image_path: Path to image
        '''

        if not image_path:
            raise_exception('image_path is empty')

        ratio = get_ratio_with_simple_comparator(image_path)

        return ratio


    def create_image(self, extent, width, height, canvas_name, output_dir):
        '''
        This method create an image

        :param extent: Extent
        :param width: Output image width
        :param height: Output image height
        :param canvas_name: Map name
        :param output_dir: Output directory for image
        '''

        if not extent:
            raise_exception('extent is empty')

        if not width:
            raise_exception('width is empty')

        if not height:
            raise_exception('height is empty')

        if not canvas_name:
            raise_exception('canvas name is empty')

        if not output_dir:
            raise_exception('output_dir is empty')

        file_name = '{0}/{1}.png'.format(output_dir, canvas_name)
        settings = QgsMapSettings()
        settings.setLayers(qgis.utils.iface.mapCanvas().layers())
        settings.setBackgroundColor(QColor(255, 255, 255))
        settings.setOutputSize(QSize(width, height))
        settings.setExtent(extent)
        render = QgsMapRendererParallelJob(settings)
        render.start()
        render.waitForFinished()
        image = render.renderedImage()
        image.save(file_name, "png")

        return file_name


    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Compute RLE ratio of map'



    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return tr(self.name())


    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return tr(self.groupId())


    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Map complexity'


    def shortHelpString(self):
        return self._shortHelp


    def createInstance(self):
        return RLERatioOfMapAlgorithm()
