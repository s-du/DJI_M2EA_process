""" Main entry point to the application. """

# define authorship information
__authors__ = ['Samuel Dubois']
__author__ = ','.join(__authors__)
__credits__ = []
__copyright__ = 'Copyright (c) Buildwise 2022'
__license__ = ''

from PyQt5 import QtWidgets, QtCore

import os

# Handle high resolution displays:
if hasattr(QtCore.Qt, 'AA_EnableHighDpiScaling'):
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
if hasattr(QtCore.Qt, 'AA_UseHighDpiPixmaps'):
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)



def main(argv=None):
    """
    Creates the main window for the application and begins the \
    QApplication if necessary.

    :param      argv | [, ..] || None

    :return      error code
    """

    # Define installation path
    install_folder = os.path.dirname(__file__)

    app = None

    # create the application if necessary
    if (not QtWidgets.QApplication.instance()):
        app = QtWidgets.QApplication(argv)
        app.setStyle('Breeze')

    # create the main window
    from gui.thermal_process import ThermalProcess
    window = ThermalProcess()
    window.setWindowTitle('Process DJI M2EA thermal images!')
    window.show()

    # run the application if necessary
    if (app):
        return app.exec_()

    # no errors since we're not running our own event loop
    return 0


if __name__ == '__main__':
    import sys

    sys.exit(main(sys.argv))