try:
    from PySide6 import QtCore, QtGui, QtWidgets
    from shiboken6 import wrapInstance
except:
    from PySide2 import QtCore, QtGui, QtWidgets
    from shiboken2 import wrapInstance

import maya.cmds as cmds
import maya.OpenMayaUI as omui
import os
import random

# 🧩 Import utility module safely
try:
    from . import project_util as util
except ImportError:
    import project_util as util


def getMayaMainWindow():
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QWidget)


class GeoScatterToolUI(QtWidgets.QDialog):
    def __init__(self, parent=getMayaMainWindow()):
        super(GeoScatterToolUI, self).__init__(parent)
        self.setWindowTitle("GeoScatter Tool Pro 🐸")
        self.setMinimumWidth(450)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)

        self.scatteredObjects = []
        self.defaultValues = {}

        self.setupUI()
        self.storeDefaultValues()
        self.applyButtonStyles()
        self.applyTheme()

    # ---------------------- UI setup ----------------------
    def setupUI(self):
        layout = QtWidgets.QVBoxLayout(self)

        # Copies + Seed
        topLayout = QtWidgets.QHBoxLayout()
        self.numCopiesField = QtWidgets.QSpinBox()
        self.numCopiesField.setRange(1, 5000)
        self.numCopiesField.setValue(10)
        topLayout.addWidget(QtWidgets.QLabel("Copies:"))
        topLayout.addWidget(self.numCopiesField)

        self.seedField = QtWidgets.QSpinBox()
        self.seedField.setRange(0, 999999)
        topLayout.addWidget(QtWidgets.QLabel("Seed:"))
        topLayout.addWidget(self.seedField)
        layout.addLayout(topLayout)

        # Scatter mode + icon
        scatterModeLayout = QtWidgets.QHBoxLayout()
        iconLabel = QtWidgets.QLabel()
        iconPath = r"C:/Users/LENOVO01/Documents/maya/2024/scripts/scatter_tool/resources/icons/pepe.png"
        if os.path.exists(iconPath):
            iconPixmap = QtGui.QPixmap(iconPath)
            iconPixmap = iconPixmap.scaled(28, 28, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            iconLabel.setPixmap(iconPixmap)
        else:
            iconLabel.setText("🐸")
        iconLabel.setFixedSize(30, 30)
        iconLabel.setAlignment(QtCore.Qt.AlignCenter)
        iconLabel.setStyleSheet("border-radius: 15px; background-color: #2E2A33; padding: 2px;")
        scatterModeLayout.addWidget(iconLabel)

        scatterModeLayout.addWidget(QtWidgets.QLabel("Scatter Mode:"))
        self.scatterModeCombo = QtWidgets.QComboBox()
        self.scatterModeCombo.addItems(["Vertex", "Face"])
        scatterModeLayout.addWidget(self.scatterModeCombo)
        scatterModeLayout.addStretch()
        layout.addLayout(scatterModeLayout)

        # Align normal
        self.alignNormal = QtWidgets.QCheckBox("Align to surface normal")
        self.alignNormal.setChecked(True)
        layout.addWidget(self.alignNormal)

        # Rotation / Scale
        layout.addWidget(QtWidgets.QLabel("Random Rotation (deg):"))
        self.rotMinX, self.rotMaxX = self.makeRangeSpin(0, 360)
        self.rotMinY, self.rotMaxY = self.makeRangeSpin(0, 360)
        self.rotMinZ, self.rotMaxZ = self.makeRangeSpin(0, 360)
        layout.addLayout(self.makeFormLayout("X Rotation:", self.rotMinX, self.rotMaxX))
        layout.addLayout(self.makeFormLayout("Y Rotation:", self.rotMinY, self.rotMaxY))
        layout.addLayout(self.makeFormLayout("Z Rotation:", self.rotMinZ, self.rotMaxZ))

        layout.addWidget(QtWidgets.QLabel("Random Scale:"))
        self.scaleMin, self.scaleMax = self.makeRangeSpin(0.8, 1.2, 0.01, 100.0)
        layout.addLayout(self.makeFormLayout("Scale:", self.scaleMin, self.scaleMax))

        # Parent
        parentLayout = QtWidgets.QHBoxLayout()
        parentLayout.addWidget(QtWidgets.QLabel("Parent group:"))
        self.parentNameEdit = QtWidgets.QLineEdit()
        parentLayout.addWidget(self.parentNameEdit)
        layout.addLayout(parentLayout)

        self.useBoundingBox = QtWidgets.QCheckBox("Use Bounding Box Offset (avoid clipping)")
        self.useBoundingBox.setChecked(True)
        layout.addWidget(self.useBoundingBox)

        # Buttons
        btnRow = QtWidgets.QHBoxLayout()
        self.scatterBtn = QtWidgets.QPushButton("Scatter!")
        self.scatterBtn.clicked.connect(self.scatterObjects)
        btnRow.addWidget(self.scatterBtn)

        self.clearScatterBtn = QtWidgets.QPushButton("Clear Scatter")
        self.clearScatterBtn.clicked.connect(self.clearScatter)
        btnRow.addWidget(self.clearScatterBtn)
        layout.addLayout(btnRow)

        self.statusLabel = QtWidgets.QLabel("")
        layout.addWidget(self.statusLabel)

    # ---------------------- store defaults ----------------------
    def storeDefaultValues(self):
        self.defaultValues = {
            "numCopies": self.numCopiesField.value(),
            "seed": self.seedField.value(),
            "rotX": [self.rotMinX.value(), self.rotMaxX.value()],
            "rotY": [self.rotMinY.value(), self.rotMaxY.value()],
            "rotZ": [self.rotMinZ.value(), self.rotMaxZ.value()],
            "scale": [self.scaleMin.value(), self.scaleMax.value()],
            "alignNormal": self.alignNormal.isChecked(),
            "scatterMode": self.scatterModeCombo.currentText(),
            "parent": self.parentNameEdit.text()
        }

    # ---------------------- helpers ----------------------
    def makeRangeSpin(self, minVal, maxVal, step=0.1, bound=10000.0):
        minBox = QtWidgets.QDoubleSpinBox()
        minBox.setRange(-bound, bound)
        minBox.setSingleStep(step)
        minBox.setValue(minVal)
        maxBox = QtWidgets.QDoubleSpinBox()
        maxBox.setRange(-bound, bound)
        maxBox.setSingleStep(step)
        maxBox.setValue(maxVal)
        return minBox, maxBox

    def makeFormLayout(self, label, minBox, maxBox):
        layout = QtWidgets.QHBoxLayout()
        lbl = QtWidgets.QLabel(label)
        lbl.setFixedWidth(90)
        layout.addWidget(lbl)
        layout.addWidget(QtWidgets.QLabel("Min"))
        layout.addWidget(minBox)
        layout.addWidget(QtWidgets.QLabel("Max"))
        layout.addWidget(maxBox)
        return layout

    # ---------------------- styles ----------------------
    def applyButtonStyles(self):
        self.scatterBtn.setStyleSheet("""
            QPushButton {
                background-color: #84B082; color: white;
                border-radius: 6px; font-weight: bold;
            }
            QPushButton:hover { background-color: #4d804b; }
        """)
        self.scatterBtn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))

        self.clearScatterBtn.setStyleSheet("""
            QPushButton {
                background-color: #A30B37; color: white;
                border-radius: 6px; font-weight: bold;
            }
            QPushButton:hover { background-color: #B20E45; }
        """)
        self.clearScatterBtn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))

    def applyTheme(self):
        self.setStyleSheet("""
            QDialog { background-color: #4A424C; }
            QLabel { color: #FCFCFF; font-weight: bold; }
            QSpinBox, QDoubleSpinBox, QLineEdit, QComboBox {
                background-color: #353A47; color: white;
                border: 1px solid #C6C8EE; border-radius: 4px; padding: 2px;
            }
            QCheckBox { color: #FCFCFF; }
        """)

    # ---------------------- actions ----------------------
    def scatterObjects(self):
        selection = cmds.ls(selection=True)
        if len(selection) < 2:
            cmds.warning("Select: [target geometry] + [scatter source(s)]")
            return
        target, sources = selection[0], selection[1:]
        random.seed(self.seedField.value())
        created = util.scatterObjects(
            target, sources,
            num=self.numCopiesField.value(),
            scatterMode=self.scatterModeCombo.currentText(),
            alignNormal=self.alignNormal.isChecked(),
            useBoundingBox=self.useBoundingBox.isChecked(),
            rotRange=((self.rotMinX.value(), self.rotMaxX.value()),
                      (self.rotMinY.value(), self.rotMaxY.value()),
                      (self.rotMinZ.value(), self.rotMaxZ.value())),
            scaleRange=(self.scaleMin.value(), self.scaleMax.value()),
            parentName=self.parentNameEdit.text().strip()
        )
        self.scatteredObjects.extend(created)
        self.statusLabel.setText(f"Scattered: {len(created)} objects")

    def clearScatter(self):
        parentName = self.parentNameEdit.text().strip()
        removed = util.clearScatter(self.scatteredObjects, parentName)
        self.scatteredObjects = []
        self.parentNameEdit.setText("")
        self.statusLabel.setText(f"All scattered objects cleared ({removed} removed).")


def run():
    for w in QtWidgets.QApplication.allWidgets():
        if isinstance(w, GeoScatterToolUI):
            w.close()
    ui = GeoScatterToolUI()
    ui.show()
    return ui
