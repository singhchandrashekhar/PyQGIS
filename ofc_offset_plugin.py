# -*- coding: utf-8 -*-
import os

from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.core import (
    Qgis,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsFeature,
    QgsGeometry,
    QgsMapLayerType,
    QgsPointXY,
    QgsProject,
    QgsVectorFileWriter,
    QgsVectorLayer,
    QgsWkbTypes,
)

from .ofc_offset_dialog import OfcOffsetDialog


class OfcOffsetPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.action = None

    def initGui(self):
        self.action = QAction("OFC 1m Offset", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addPluginToMenu("&OFC Offset", self.action)
        self.iface.addToolBarIcon(self.action)

    def unload(self):
        if self.action:
            self.iface.removePluginMenu("&OFC Offset", self.action)
            self.iface.removeToolBarIcon(self.action)

    def run(self):
        dialog = OfcOffsetDialog(self.iface.mainWindow())
        if not dialog.exec_():
            return

        ofc_layer = QgsProject.instance().mapLayer(dialog.selected_ofc_layer_id)
        offset_layer = QgsProject.instance().mapLayer(dialog.selected_offset_layer_id)

        error = self._validate_layers(ofc_layer, offset_layer)
        if error:
            self._warn(error)
            return

        try:
            output_layer_path = self._create_offset_layer(ofc_layer, offset_layer)
        except Exception as ex:
            self._warn(f"Failed to create offset lines: {ex}")
            return

        output_layer = QgsVectorLayer(output_layer_path, "OFC_1m_offset", "ogr")
        if output_layer.isValid():
            QgsProject.instance().addMapLayer(output_layer)
            self.iface.messageBar().pushMessage(
                "OFC 1m Offset",
                f"Created: {output_layer_path}",
                level=Qgis.Success,
                duration=6,
            )
        else:
            self._warn(f"Output was written but could not be loaded: {output_layer_path}")

    def _validate_layers(self, ofc_layer, offset_layer):
        if not ofc_layer or ofc_layer.type() != QgsMapLayerType.VectorLayer:
            return "Please select a valid OFC vector layer."
        if ofc_layer.geometryType() != QgsWkbTypes.LineGeometry:
            return "OFC layer must be a line layer."

        if not offset_layer or offset_layer.type() != QgsMapLayerType.VectorLayer:
            return "Please select a valid offset_pt vector layer."
        if offset_layer.geometryType() not in (QgsWkbTypes.PointGeometry, QgsWkbTypes.NullGeometry):
            return "offset_pt layer must be a point layer or a table (for example, Excel sheet)."

        required_fields = {"start_X", "start_Y", "end_X", "end_Y"}
        actual_fields = {f.name() for f in offset_layer.fields()}
        missing = required_fields - actual_fields
        if missing:
            return f"offset_pt layer is missing required fields: {', '.join(sorted(missing))}"

        if ofc_layer.crs().authid() != "EPSG:4326":
            return "OFC layer CRS must be EPSG:4326."
        if offset_layer.crs().authid() != "EPSG:4326":
            return "offset_pt layer CRS must be EPSG:4326."

        return None

    def _create_offset_layer(self, ofc_layer, offset_layer):
        source_path = ofc_layer.source().split("|")[0]
        source_dir = os.path.dirname(source_path)
        base_name = "OFC_1m_offset"
        output_path = os.path.join(source_dir, f"{base_name}.shp")

        suffix = 1
        while os.path.exists(output_path):
            output_path = os.path.join(source_dir, f"{base_name}_{suffix}.shp")
            suffix += 1

        crs_4326 = QgsCoordinateReferenceSystem("EPSG:4326")
        crs_metric = QgsCoordinateReferenceSystem("EPSG:3857")
        transform_context = QgsProject.instance().transformContext()
        to_metric = QgsCoordinateTransform(crs_4326, crs_metric, transform_context)
        to_4326 = QgsCoordinateTransform(crs_metric, crs_4326, transform_context)

        writer = QgsVectorFileWriter(
            output_path,
            "UTF-8",
            ofc_layer.fields(),
            ofc_layer.wkbType(),
            crs_4326,
            "ESRI Shapefile",
        )
        if writer.hasError() != QgsVectorFileWriter.NoError:
            raise RuntimeError(writer.errorMessage())

        guidance_points = self._build_guidance_points(offset_layer)
        if not guidance_points:
            raise RuntimeError("offset_pt layer has no usable start/end coordinate rows.")

        for ofc_feature in ofc_layer.getFeatures():
            line_geom = ofc_feature.geometry()
            if line_geom.isEmpty():
                continue

            guidance_point = self._nearest_guidance_point(ofc_feature, guidance_points)
            side = self._calculate_side(line_geom, guidance_point, to_metric)

            metric_geom = QgsGeometry(line_geom)
            metric_geom.transform(to_metric)
            offset_metric = metric_geom.offsetCurve(1.0 * side, 8, Qgis.JoinStyle.Round, 2.0)
            if offset_metric.isEmpty():
                continue

            offset_metric.transform(to_4326)
            new_feature = QgsFeature(ofc_layer.fields())
            new_feature.setAttributes(ofc_feature.attributes())
            new_feature.setGeometry(offset_metric)
            writer.addFeature(new_feature)

        del writer
        return output_path

    def _build_guidance_points(self, offset_layer):
        guidance_points = []
        for feature in offset_layer.getFeatures():
            try:
                start_x = float(feature["start_X"])
                start_y = float(feature["start_Y"])
                end_x = float(feature["end_X"])
                end_y = float(feature["end_Y"])
            except (TypeError, ValueError):
                continue

            guidance_points.append(
                QgsPointXY((start_x + end_x) / 2.0, (start_y + end_y) / 2.0)
            )

        return guidance_points

    def _nearest_guidance_point(self, line_feature, guidance_points):
        line_geom = line_feature.geometry()
        line_center = line_geom.centroid().asPoint()

        closest = None
        best_distance = float("inf")
        for point in guidance_points:
            dist = (line_center.x() - point.x()) ** 2 + (line_center.y() - point.y()) ** 2
            if dist < best_distance:
                best_distance = dist
                closest = point

        return closest

    def _calculate_side(self, line_geom, guidance_point_4326, to_metric_transform):
        metric_line = QgsGeometry(line_geom)
        metric_line.transform(to_metric_transform)

        vertices = [v for v in metric_line.vertices()]
        if len(vertices) < 2:
            return 1.0

        p1, p2 = vertices[0], vertices[1]
        dx = p2.x() - p1.x()
        dy = p2.y() - p1.y()

        ref_pt_metric = to_metric_transform.transform(guidance_point_4326)

        cross = dx * (ref_pt_metric.y() - p1.y()) - dy * (ref_pt_metric.x() - p1.x())
        return 1.0 if cross >= 0 else -1.0

    def _warn(self, message):
        QMessageBox.warning(self.iface.mainWindow(), "OFC 1m Offset", message)
