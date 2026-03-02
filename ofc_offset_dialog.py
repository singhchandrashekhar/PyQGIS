# -*- coding: utf-8 -*-
from qgis.PyQt.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QVBoxLayout,
)
from qgis.core import QgsMapLayerType, QgsProject, QgsWkbTypes


class OfcOffsetDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("OFC 1m Offset")
        self.setMinimumWidth(440)

        self.description_label = QLabel(
            "Select input layers:\n"
            "• OFC: line layer\n"
            "• offset_pt: point layer or table (e.g. Excel) with fields start_X, start_Y, end_X, end_Y"
        )
        self.ofc_combo = QComboBox()
        self.offset_combo = QComboBox()

        form = QFormLayout()
        form.addRow("OFC layer", self.ofc_combo)
        form.addRow("offset_pt layer", self.offset_combo)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(self.description_label)
        layout.addLayout(form)
        layout.addWidget(self.button_box)
        self.setLayout(layout)

        self.populate_layers()

    def populate_layers(self):
        self.ofc_combo.clear()
        self.offset_combo.clear()

        for layer in QgsProject.instance().mapLayers().values():
            if layer.type() != QgsMapLayerType.VectorLayer:
                continue

            geometry_type = layer.geometryType()
            if geometry_type == QgsWkbTypes.LineGeometry:
                self.ofc_combo.addItem(layer.name(), layer.id())
            elif geometry_type in (QgsWkbTypes.PointGeometry, QgsWkbTypes.NullGeometry):
                self.offset_combo.addItem(layer.name(), layer.id())

        self._preselect_by_name(self.ofc_combo, "OFC")
        self._preselect_by_name(self.offset_combo, "offset_pt")

    @staticmethod
    def _preselect_by_name(combo: QComboBox, preferred_name: str):
        for idx in range(combo.count()):
            if combo.itemText(idx).strip().lower() == preferred_name.lower():
                combo.setCurrentIndex(idx)
                return

    @property
    def selected_ofc_layer_id(self):
        return self.ofc_combo.currentData()

    @property
    def selected_offset_layer_id(self):
        return self.offset_combo.currentData()
