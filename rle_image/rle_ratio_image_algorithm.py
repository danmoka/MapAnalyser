# -*- coding: utf-8 -*-

"""
/***************************************************************************
 RLERatioOfImage
                                 A QGIS plugin
 This plugin computes RLE compession ratio of image
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2020-07-10
        copyright            : (C) 2020 by YSU
        email                : daniilpot@yandex.ru
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

from PyQt5.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFileDestination,
                       QgsProcessingParameterFile,
                       QgsProcessingException)

# more imports
from ..rle.rle_compression_ratio import (get_ratio_with_abs_comparator, get_ratio_with_simple_comparator)


class RLERatioOfImageAlgorithm(QgsProcessingAlgorithm):
    """
    This is a class that calculates the RLE ratio of an image
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    OUTPUT = 'OUTPUT'
    INPUT = 'INPUT'

    def __init__(self):
        super().__init__()
        self._shortHelp = 'This algorithm calculates the RLE ratio of image.'

        self.define_help_info('rle_image_help.txt')

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        self.addParameter(
            QgsProcessingParameterFile(
                name=self.INPUT,
                description=self.tr('Input file'),
                extension='png',
            )
        )

        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT,
                self.tr('Output file'),
                'csv(*.csv)',
            )
        )


    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        
        image = self.parameterAsFile(parameters, self.INPUT, context)

        if not image:
            self.raise_exception('can\'t get an image path')

        feedback.setProgress(20)

        if feedback.isCanceled():
            return -1

        feedback.pushInfo(self.tr('The RLE algorithm is running'))
        ratio = self.compress_from_path(image)
        feedback.setProgress(80)

        if feedback.isCanceled():
            return -1

        output = self.parameterAsFileOutput(parameters, self.OUTPUT, context)

        if output:
            feedback.pushInfo(self.tr('Writing to file'))
            file_name = os.path.basename(image)
            file_name = os.path.splitext(file_name)[0]
            row = [{'image': file_name,
                   'compress ratio': ratio}]
            header = ['image', 'compress ratio']
            self.write_to_file(output, header, row, ';')

        return {'RLE compression ratio': ratio}


    def compress_from_path(self, path):
        '''
        This method computes RLE compress ratio

        :param path: Path to image
        '''

        if not path:
            self.raise_exception('image path is empty')

        return get_ratio_with_abs_comparator(path)


    def write_to_file(self, path, header, rows, delimiter):
        '''
        This method writes the result to a file

        :param path: Path to file
        :param header: Header of the csv file
        :param row: Csv rows
        :param delimiter: Csv delimiter
        '''

        if not path:
            self.raise_exception('output path is empty')
        if not header:
            self.raise_exception('header is empty')
        if not rows:
            self.raise_exception('rows is empty')
        if not delimiter:
            self.raise_exception('delimiter is empty')

        file_exists = os.path.isfile(path)

        try:
            output_file = open(path, 'a')
            cout = csv.DictWriter(output_file, header, delimiter = delimiter)

            if not file_exists:
                cout.writeheader()

            cout.writerows(rows)
            output_file.close()
        except Exception:
            self.raise_exception('error while writing to file')


    def raise_exception(self, message):
        raise QgsProcessingException(self.tr(message))


    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Calculate the RLE ratio of image'


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
        return 'Map complexity'


    def shortHelpString(self):
        return self._shortHelp


    def tr(self, string):
        return QCoreApplication.translate('Processing', string)


    def createInstance(self):
        return RLERatioOfImageAlgorithm()


    def define_help_info(self, help_file):
        """
        Sets the help text.

        :help_file: File name
        """

        directory = os.path.dirname(__file__)
        file_name = os.path.join(directory, help_file)

        try:
            with open(file_name, 'r') as f:
                text = f.read()
                self._shortHelp += text
        except Exception:
            pass
