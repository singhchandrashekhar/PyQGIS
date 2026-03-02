# -*- coding: utf-8 -*-
"""QGIS entry point for the OFC 1m Offset plugin."""


def classFactory(iface):
    from .ofc_offset_plugin import OfcOffsetPlugin

    return OfcOffsetPlugin(iface)
