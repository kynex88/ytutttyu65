"""
================================================================================
MEF Converter Package
================================================================================
مكتبة تحويل ملفات IGI1, IGI2, MDL, SMD, OBJ إلى صيغ متعددة

Version: 2.1.0
Author: Tavrixender
License: © 2024 Tavrixender
"""

__version__ = "2.1.0"
__author__ = "Tavrixender"
__all__ = [
    'MEFConverter',
    'MefModelIGI1',
    'MefModelIGI2',
    'DirectXExporter',
    'AnimationExporter',
    'TextureAtlas',
    'PerformanceMonitor',
    'ParallelProcessor',
]

# Import main classes
from mef_converter.main import MEFConverter
from mef_converter.formats.mef_igi1_parser import MefModelIGI1
from mef_converter.formats.mef_igi2_parser import MefModelIGI2
from mef_converter.exporters.mef_igi2.export_directx import DirectXExporter
from mef_converter.animation.anim_exporter import AnimationExporter
from mef_converter.exporters.mef_igi2.export_atlas import TextureAtlas
from mef_converter.performance.monitor import PerformanceMonitor
from mef_converter.parallel.processor import ParallelProcessor
