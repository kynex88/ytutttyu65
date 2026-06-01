"""
================================================================================
MEF Converter - Main Entry Point
================================================================================
نقطة الدخول الرئيسية لتطبيق تحويل ملفات MEF
Unified interface for all MEF conversion operations
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import all modules
from core.buffer import Buffer
from core.types import Vector3, Sphere, DateTime, Bone, XTRWEntry, TextureReference, MeshInfo, MefDebugParams
from core.constants import ModelType, SCALE, INV_SCALE
from core.utils import (
    detect_file_type,
    detect_mef_version,
    convert_to_json_serializable,
    set_global_debug_params,
    apply_all_fixes
)

from formats.mef_base import LoopFile, Chunk, ChunkHeader
from formats.mef_igi1_parser import MefModelIGI1, OptimizedMefModelIGI1
from formats.mef_igi2_parser import MefModelIGI2, OptimizedMefModelIGI2
from formats.mdl_parser import StudioHeader, MDLHeader, MdlModel
from formats.smd_parser import SMDExporter
from formats.obj_parser import OBJExporter

from exporters.mef_igi1.export_extra import add_directx_export_to_mef_model_igi1
from exporters.mef_igi2.export_extra import (
    add_directx_export_to_mef_model_igi2,
    batch_convert_smd_fixed,
    batch_convert_obj_fixed
)
from exporters.mef_igi2.export_directx import DirectXExporter
from exporters.mef_igi2.export_atlas import TextureAtlas, enable_atlas_for_all_formats

from animation.anim_exporter import AnimationExporter, AdvancedAnimation
from animation.txan_analyzer import AdvancedAnimationAnalyzer

from parallel.processor import ParallelProcessor
from parallel.cache import MefCache
from performance.monitor import PerformanceMonitor


class MEFConverter:
    """فئة رئيسية لتحويل ملفات MEF"""
    
    def __init__(self, enable_debug=False, enable_performance_monitor=False):
        """
        Initialize the MEF Converter
        
        Args:
            enable_debug: تفعيل وضع التصحيح
            enable_performance_monitor: مراقبة الأداء
        """
        self.debug = enable_debug
        self.monitor = PerformanceMonitor() if enable_performance_monitor else None
        self.cache = MefCache()
        self.processor = ParallelProcessor()
        
        if self.debug:
            set_global_debug_params(True, True, True)
    
    def convert_file(self, input_file: str, output_dir: str, output_format: str = "obj", 
                    enable_atlas: bool = False, enable_animation: bool = False) -> bool:
        """
        Convert a single MEF file to desired format
        
        Args:
            input_file: مسار الملف المدخل
            output_dir: مجلد المخرجات
            output_format: صيغة الإخراج (obj, gltf, directx, etc.)
            enable_atlas: تفعيل خريطة النسيج
            enable_animation: تفعيل تصدير الرسوم المتحركة
        
        Returns:
            True إذا نجح التحويل، False إذا فشل
        """
        try:
            if self.monitor:
                self.monitor.start()
            
            input_path = Path(input_file)
            if not input_path.exists():
                print(f"❌ Input file not found: {input_file}")
                return False
            
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Detect file type
            file_type = detect_file_type(input_file)
            mef_version = detect_mef_version(input_file) if file_type == "MEF" else None
            
            print(f"📂 File: {input_path.name}")
            print(f"   Type: {file_type}")
            if mef_version:
                print(f"   Version: {mef_version}")
            
            # Load model based on type
            model = None
            if file_type == "MEF":
                if mef_version == "IGI1":
                    model = MefModelIGI1(input_file)
                elif mef_version == "IGI2":
                    model = MefModelIGI2(input_file)
            elif file_type == "MDL":
                model = MdlModel(input_file)
            elif file_type == "SMD":
                model = SMDExporter(input_file)
            elif file_type == "OBJ":
                model = OBJExporter(input_file)
            
            if model is None:
                print(f"❌ Could not load model from {input_file}")
                return False
            
            # Apply fixes if needed
            if self.debug:
                apply_all_fixes(model)
            
            # Export to desired format
            output_file = output_path / f"{input_path.stem}.{output_format}"
            
            if output_format == "directx":
                dx_exporter = DirectXExporter(model)
                dx_exporter.export(str(output_file))
            elif output_format == "obj":
                if hasattr(model, 'export_to_obj'):
                    model.export_to_obj(str(output_file))
                else:
                    print(f"❌ OBJ export not supported for {file_type}")
                    return False
            elif output_format == "gltf":
                if hasattr(model, 'export_to_gltf'):
                    model.export_to_gltf(str(output_file))
                else:
                    print(f"❌ glTF export not supported for {file_type}")
                    return False
            
            # Add atlas if requested
            if enable_atlas:
                atlas = TextureAtlas(model)
                atlas.generate()
                atlas.apply()
            
            # Export animations if requested
            if enable_animation and hasattr(model, 'animations'):
                anim_exporter = AnimationExporter(model)
                anim_exporter.export(str(output_path / f"{input_path.stem}_anim"))
            
            print(f"✅ Successfully exported to: {output_file}")
            
            if self.monitor:
                self.monitor.stop()
                print(f"   ⏱️ Time: {self.monitor.get_elapsed_time():.2f}s")
            
            return True
        
        except Exception as e:
            print(f"❌ Error converting file: {e}")
            if self.debug:
                import traceback
                traceback.print_exc()
            return False
    
    def batch_convert(self, input_dir: str, output_dir: str, output_format: str = "obj",
                     recursive: bool = True, enable_atlas: bool = False) -> int:
        """
        تحويل مجموعة من الملفات
        
        Args:
            input_dir: مجلد المدخلات
            output_dir: مجلد المخرجات
            output_format: صيغة الإخراج
            recursive: البحث المتكرر في الأجلد الفرعية
            enable_atlas: تفعيل خريطة النسيج
        
        Returns:
            عدد الملفات المحولة بنجاح
        """
        input_path = Path(input_dir)
        if not input_path.exists():
            print(f"❌ Input directory not found: {input_dir}")
            return 0
        
        # Find all supported files
        patterns = ["*.mef", "*.mdl", "*.smd", "*.obj"]
        files = []
        for pattern in patterns:
            if recursive:
                files.extend(input_path.rglob(pattern))
            else:
                files.extend(input_path.glob(pattern))
        
        if not files:
            print(f"⚠️ No supported files found in {input_dir}")
            return 0
        
        print(f"🔄 Converting {len(files)} files...")
        success_count = 0
        
        for file in files:
            print(f"\n📄 Processing: {file.name}")
            rel_path = file.relative_to(input_path)
            out_subdir = Path(output_dir) / rel_path.parent
            
            if self.convert_file(str(file), str(out_subdir), output_format, enable_atlas):
                success_count += 1
        
        print(f"\n✅ Completed: {success_count}/{len(files)} files converted")
        return success_count


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='MEF Model Converter - Convert MEF/MDL/SMD/OBJ files to various formats'
    )
    
    parser.add_argument('-i', '--input', required=True,
                       help='Input file or directory')
    parser.add_argument('-o', '--output', required=True,
                       help='Output directory')
    parser.add_argument('-f', '--format', default='obj',
                       choices=['obj', 'gltf', 'directx', 'collada', 'json', 'txt'],
                       help='Output format (default: obj)')
    parser.add_argument('-r', '--recursive', action='store_true',
                       help='Recursive batch conversion')
    parser.add_argument('--atlas', action='store_true',
                       help='Enable texture atlas')
    parser.add_argument('--animation', action='store_true',
                       help='Export animations')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug mode')
    parser.add_argument('--monitor', action='store_true',
                       help='Enable performance monitoring')
    
    args = parser.parse_args()
    
    # Create converter
    converter = MEFConverter(
        enable_debug=args.debug,
        enable_performance_monitor=args.monitor
    )
    
    # Check if input is file or directory
    input_path = Path(args.input)
    
    if input_path.is_file():
        # Single file conversion
        success = converter.convert_file(
            args.input,
            args.output,
            args.format,
            enable_atlas=args.atlas,
            enable_animation=args.animation
        )
        return 0 if success else 1
    
    elif input_path.is_dir():
        # Batch conversion
        count = converter.batch_convert(
            args.input,
            args.output,
            args.format,
            recursive=args.recursive,
            enable_atlas=args.atlas
        )
        return 0 if count > 0 else 1
    
    else:
        print(f"❌ Invalid input path: {args.input}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
