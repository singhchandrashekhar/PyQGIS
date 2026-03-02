# PyQGIS

diff --git a/README.md b/README.md
index ab662d914154c87df01f2f670014458ade8c169b..fb845c090f27cae2dd974147ec1ab0690044d6d9 100644
--- a/README.md
+++ b/README.md
@@ -1 +1,28 @@
-# PyQGIS
\ No newline at end of file
+# PyQGIS - OFC 1m Offset Plugin
+
+This repository contains a QGIS plugin that:
+
+- lets a user pick two layers: `OFC` (line) and `offset_pt` (point or Excel-backed table),
+- reads `start_X`, `start_Y`, `end_X`, `end_Y` fields from `offset_pt` (including rows loaded from Excel),
+- creates a **1 meter** offset line for each OFC feature,
+- keeps output in **EPSG:4326**,
+- saves the output shapefile in the same folder as the original OFC layer.
+
+## Plugin folder
+
+- `ofc_offset_plugin/`
+
+## Install in QGIS (manual)
+
+1. Copy `ofc_offset_plugin` into your QGIS profile plugin directory:
+   - Linux: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
+   - Windows: `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\`
+2. Restart QGIS.
+3. Open **Plugins > Manage and Install Plugins** and enable **OFC 1m Offset**.
+
+## Usage
+
+1. Load your `OFC` layer and load `offset_pt` (point layer or Excel sheet as table) with fields `start_X`, `start_Y`, `end_X`, `end_Y`.
+2. Start plugin from menu **OFC Offset > OFC 1m Offset**.
+3. Confirm layers and click **OK**.
+4. Output is created in the OFC source folder as `OFC_1m_offset.shp` (or numbered variant).
