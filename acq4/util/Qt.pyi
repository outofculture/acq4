try:
    from PyQt5 import QtWidgets, QtCore, QtGui

    QtCore = QtCore
    QtGui = QtGui
    QtWidgets = QtWidgets
except ImportError:
    try:
        from PyQt6 import QtWidgets, QtCore, QtGui

        QtCore = QtCore
        QtGui = QtGui
        QtWidgets = QtWidgets
    except ImportError:
        try:
            from PySide2 import QtWidgets, QtCore, QtGui

            QtCore = QtCore
            QtGui = QtGui
            QtWidgets = QtWidgets
        except ImportError:
            try:
                from PySide6 import QtWidgets, QtCore, QtGui

                QtCore = QtCore
                QtGui = QtGui
                QtWidgets = QtWidgets
            except ImportError:
                raise Exception("No suitable qt binding found")

# TODO combine these into a single namespace?