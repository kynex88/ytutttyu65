#!/usr/bin/env python3
"""
السكربت الثالث والعشرين - قارئ وعارض نماذج MEF للعبتي IGI1 و IGI2
ونماذج MDL للعبة Half-Life (Counter-Strike 1.6)
نسخة محسنة بالكامل مع دعم جميع القطع والمواد المتعددة والتزين الكامل
"""

import os
import sys
import numpy as np
import math
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum
import struct
import argparse
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import List, Tuple, Optional, Dict

# ضمان الطباعة الآمنة على ويندوز عند وجود رموز Unicode (مثل emojis)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# أضف هذه الدوال في بداية السكربت (بعد import)
def fix_export_to_directx_in_main(input_path, output_subdir, file_type, model, export_formats):
    """دالة مساعدة لتصدير DirectX من main()"""
    if "directx" not in export_formats:
        return
    
    print(f"   DEBUG: DirectX export triggered for {file_type}")
    try:
        dx_path = os.path.join(output_subdir, f"{Path(input_path).stem}.x")
        
        if file_type == "MEF":
            # تحديد إصدار IGI
            if hasattr(model, 'txan_data') or hasattr(model, 'render_mesh_data'):
                version = "IGI2"
            else:
                version = "IGI1"
            export_to_directx(model, dx_path, "igi2" if version == "IGI2" else "igi1")
        elif file_type == "MDL":
            export_to_directx(model, dx_path, "auto")
        elif file_type == "SMD":
            export_to_directx(model, dx_path, "smd")
        elif file_type == "OBJ":
            export_to_directx(model, dx_path, "obj")
        else:
            print(f"   ⚠️ DirectX export not supported for {file_type}")
            return
        
        print(f"   ✅ DirectX export completed: {dx_path}")
    except Exception as e:
        print(f"   ⚠️ DirectX export failed: {e}")
        import traceback
        traceback.print_exc()


# أضف هذه الدوال إلى MefModelIGI2 (قبل export_all)
def add_directx_export_to_mef_model_igi2():
    """إضافة دالة export_to_directx إلى MefModelIGI2"""
    
    def export_to_directx(self, output_path: str):
        """تصدير النموذج إلى DirectX (.X)"""
        from mef_igi2_export import export_to_directx as dx_export
        return dx_export(self, output_path, "igi2", self.debug_params)
    
    MefModelIGI2.export_to_directx = export_to_directx


def add_directx_export_to_mef_model_igi1():
    """إضافة دالة export_to_directx إلى MefModelIGI1"""
    
    def export_to_directx(self, output_path: str):
        """تصدير النموذج إلى DirectX (.X)"""
        from mef_igi2_export import export_to_directx as dx_export
        return dx_export(self, output_path, "igi1", self.debug_params)
    
    MefModelIGI1.export_to_directx = export_to_directx


# أصلح دالة batch_convert_smd - اجعلها دالة عامة خارج الكلاس
def batch_convert_smd_fixed(input_dir: str, output_dir: str, export_formats: List[str] = None):
    """
    تحويل جميع ملفات SMD في مجلد إلى صيغ متعددة - نسخة مصلحة
    """
    if export_formats is None:
        export_formats = ["obj", "gltf", "json", "txt"]
    
    smd_files = []
    for ext in ['*.smd', '*.SMD']:
        smd_files.extend(Path(input_dir).glob(ext))
    
    if not smd_files:
        print(f"No SMD files found in '{input_dir}'")
        return False
    
    print(f"\nFound {len(smd_files)} SMD file(s):")
    for f in smd_files:
        print(f"  - {f.name}")
    
    successful = 0
    failed = 0
    
    for smd_file in smd_files:
        print(f"\n{'='*60}")
        print(f"Processing: {smd_file.name}")
        print(f"{'='*60}")
        
        output_subdir = os.path.join(output_dir, smd_file.stem)
        
        try:
            smd = SMDExporter.from_file(str(smd_file))
            base_name = smd_file.stem
            smd.export_all(output_subdir, base_name, export_formats)
            successful += 1
            print(f"✓ Successfully processed: {smd_file.name}")
        except Exception as e:
            failed += 1
            print(f"✗ Failed to process: {smd_file.name} - {e}")
    
    print("\n" + "="*60)
    print("SMD BATCH CONVERSION COMPLETE")
    print("="*60)
    print(f"Total files found : {len(smd_files)}")
    print(f"Successfully processed : {successful}")
    print(f"Failed : {failed}")
    print(f"Output folder : {output_dir}")
    print("="*60)
    
    return successful > 0


# أصلح دالة convert_smd_to_formats
def convert_smd_to_formats_fixed(input_smd: str, output_dir: str, export_formats: List[str] = None):
    """
    دالة مساعدة لتحويل ملف SMD واحد إلى صيغ متعددة - نسخة مصلحة
    """
    if export_formats is None:
        export_formats = ["obj", "gltf", "json", "txt"]
    
    if not os.path.exists(input_smd):
        print(f"Error: SMD file not found: {input_smd}")
        return False
    
    try:
        print(f"\nReading SMD file: {input_smd}")
        smd = SMDExporter.from_file(input_smd)
        base_name = os.path.splitext(os.path.basename(input_smd))[0]
        smd.export_all(output_dir, base_name, export_formats)
        return True
    except Exception as e:
        print(f"Error converting SMD: {e}")
        import traceback
        traceback.print_exc()
        return False


# أصلح دالة batch_convert_obj
def batch_convert_obj_fixed(input_dir: str, output_dir: str, export_formats: List[str] = None):
    """
    تحويل جميع ملفات OBJ في مجلد إلى صيغ متعددة - نسخة مصلحة
    """
    if export_formats is None:
        export_formats = ["obj", "gltf", "json", "txt", "smd", "mdl"]
    
    obj_files = []
    for ext in ['*.obj', '*.OBJ']:
        obj_files.extend(Path(input_dir).glob(ext))
    
    if not obj_files:
        print(f"No OBJ files found in '{input_dir}'")
        return False
    
    print(f"\nFound {len(obj_files)} OBJ file(s):")
    for f in obj_files:
        print(f"  - {f.name}")
    
    successful = 0
    failed = 0
    
    for obj_file in obj_files:
        print(f"\n{'='*60}")
        print(f"Processing: {obj_file.name}")
        print(f"{'='*60}")
        
        output_subdir = os.path.join(output_dir, obj_file.stem)
        
        try:
            obj = OBJExporter.from_file(str(obj_file))
            base_name = obj_file.stem
            obj.export_all(output_subdir, base_name, export_formats)
            successful += 1
            print(f"✓ Successfully processed: {obj_file.name}")
        except Exception as e:
            failed += 1
            print(f"✗ Failed to process: {obj_file.name} - {e}")
    
    print("\n" + "="*60)
    print("OBJ BATCH CONVERSION COMPLETE")
    print("="*60)
    print(f"Total files found : {len(obj_files)}")
    print(f"Successfully processed : {successful}")
    print(f"Failed : {failed}")
    print(f"Output folder : {output_dir}")
    print("="*60)
    
    return successful > 0


# أصلح دالة convert_obj_to_formats
def convert_obj_to_formats_fixed(input_obj: str, output_dir: str, export_formats: List[str] = None):
    """
    دالة مساعدة لتحويل ملف OBJ واحد إلى صيغ متعددة - نسخة مصلحة
    """
    if export_formats is None:
        export_formats = ["obj", "gltf", "json", "txt", "smd", "mdl"]
    
    if not os.path.exists(input_obj):
        print(f"Error: OBJ file not found: {input_obj}")
        return False
    
    try:
        print(f"\nReading OBJ file: {input_obj}")
        obj = OBJExporter.from_file(input_obj)
        base_name = os.path.splitext(os.path.basename(input_obj))[0]
        obj.export_all(output_dir, base_name, export_formats)
        return True
    except Exception as e:
        print(f"Error converting OBJ: {e}")
        import traceback
        traceback.print_exc()
        return False
        
# ------------------------------------------------------------
# دالة مساعدة لتحويل الكائنات إلى صيغة قابلة للتسلسل في JSON
# ------------------------------------------------------------
def convert_to_json_serializable(obj):
    """تحويل الكائنات إلى صيغة قابلة للتسلسل في JSON"""
    if isinstance(obj, np.float32):
        return float(obj)
    elif isinstance(obj, np.float64):
        return float(obj)
    elif isinstance(obj, np.int32):
        return int(obj)
    elif isinstance(obj, np.int64):
        return int(obj)
    elif isinstance(obj, np.uint16):
        return int(obj)
    elif isinstance(obj, np.uint32):
        return int(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: convert_to_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_to_json_serializable(item) for item in obj]
    return obj


# ------------------------------------------------------------
# استيراد مكتبات إضافية للصور والصيغ
# ------------------------------------------------------------
try:
    from PIL import Image
    import io
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("Warning: PIL not installed. Lightmap conversion to PNG will be disabled.")
    print("Install with: pip install Pillow")

try:
    import pygltflib
    GLTF_AVAILABLE = True
except ImportError:
    GLTF_AVAILABLE = False
    print("Warning: pygltflib not installed. glTF export will be disabled.")
    print("Install with: pip install pygltflib")

# ------------------------------------------------------------
# إعدادات سريعة
# ------------------------------------------------------------
ENABLE_TEXTURE_ATLAS = False
INPUT_DIR = "mef_igi2"
OUTPUT_DIR = "mdls_igi2"
# ========== إعدادات Texture Atlas للصيغ المختلفة ==========
ENABLE_TEXTURE_ATLAS_SMD = False   # تفعيل الأطلس لـ SMD
ENABLE_TEXTURE_ATLAS_OBJ = True   # تفعيل الأطلس لـ OBJ  
ENABLE_TEXTURE_ATLAS_MDL = True   # تفعيل الأطلس لـ MDL
# ========================================================

# ========== إعدادات وضع Texture Atlas ==========
# وضعيات الأطلس:
# - "preserve": الحفاظ على المواد الأصلية مع تغيير map_Kd فقط
# - "merge": دمج جميع المواد في مادة واحدة باسم atlas_material
ATLAS_MODE = "preserve"  # القيمة الافتراضية: preserve
# ====================================================
# ------------------------------------------------------------
# ثوابت Half-Life MDL
# ------------------------------------------------------------
MDL_ID = ord('I') | (ord('D') << 8) | (ord('S') << 16) | (ord('T') << 24)  # IDST
MDL_VERSION = 10

# Bone flags
BONE_HAS_POSITION = 0x0001
BONE_HAS_ROTATION = 0x0002
BONE_HAS_SCALE = 0x0004

# ------------------------------------------------------------
# تعريفات Buffer
# ------------------------------------------------------------
class Buffer:
    def __init__(self, data: bytes):
        self.data = data
        self.offset = 0

    def read(self, size: int = None) -> bytes:
        if size is None:
            size = len(self.data) - self.offset
        if self.offset + size > len(self.data):
            raise ValueError(f"Buffer overflow: trying to read {size} bytes at offset {self.offset}")
        d = self.data[self.offset:self.offset+size]
        self.offset += size
        return d

    def read_uint8(self) -> int:
        return struct.unpack('<B', self.read(1))[0]

    def read_int8(self) -> int:
        return struct.unpack('<b', self.read(1))[0]

    def read_uint16(self) -> int:
        return struct.unpack('<H', self.read(2))[0]

    def read_int16(self) -> int:
        return struct.unpack('<h', self.read(2))[0]

    def read_uint32(self) -> int:
        return struct.unpack('<I', self.read(4))[0]

    def read_int32(self) -> int:
        return struct.unpack('<i', self.read(4))[0]

    def read_float(self) -> float:
        return struct.unpack('<f', self.read(4))[0]

    def read_fmt(self, fmt: str):
        size = struct.calcsize('<' + fmt)
        data = self.read(size)
        return struct.unpack('<' + fmt, data)

    def read_ascii_string(self, length: int) -> str:
        data = self.read(length)
        return data.split(b'\x00')[0].decode('ascii', errors='ignore')

    def align(self, alignment: int):
        skip = (alignment - (self.offset % alignment)) % alignment
        self.offset += skip

    def size(self) -> int:
        return len(self.data) - self.offset

    def eof(self) -> bool:
        return self.offset >= len(self.data)


# ------------------------------------------------------------
# تعريفات هياكل MDL
# ------------------------------------------------------------
@dataclass
class MDLHeader:
    """رأس ملف MDL حسب وثائق Valve"""
    id: int                     # 'IDST'
    version: int                # إصدار الملف
    name: str                   # اسم النموذج (64 حرف)
    length: int                 # حجم الملف
    
    eyeposition: Tuple[float, float, float]
    min_corner: Tuple[float, float, float]
    max_corner: Tuple[float, float, float]
    bbmin: Tuple[float, float, float]
    bbmax: Tuple[float, float, float]
    
    flags: int
    
    numbones: int
    boneindex: int
    
    numbonecontrollers: int
    bonecontrollerindex: int
    
    numhitboxes: int
    hitboxindex: int
    
    numseq: int
    seqindex: int
    
    numseqgroups: int
    seqgroupindex: int
    
    numtextures: int
    textureindex: int
    texturedataindex: int
    
    numskinref: int
    numskinfamilies: int
    skinindex: int
    
    numbodyparts: int
    bodypartindex: int
    
    numattachments: int
    attachmentindex: int
    
    soundtable: int
    soundindex: int
    soundgroups: int
    soundgroupindex: int
    
    numtransitions: int
    transitionindex: int
    
    @classmethod
    def from_buffer(cls, buffer: Buffer):
        id_val = buffer.read_uint32()
        version = buffer.read_uint32()
        name = buffer.read_ascii_string(64)
        length = buffer.read_uint32()
        
        eyeposition = buffer.read_fmt("3f")
        min_corner = buffer.read_fmt("3f")
        max_corner = buffer.read_fmt("3f")
        bbmin = buffer.read_fmt("3f")
        bbmax = buffer.read_fmt("3f")
        
        flags = buffer.read_uint32()
        
        numbones = buffer.read_uint32()
        boneindex = buffer.read_uint32()
        
        numbonecontrollers = buffer.read_uint32()
        bonecontrollerindex = buffer.read_uint32()
        
        numhitboxes = buffer.read_uint32()
        hitboxindex = buffer.read_uint32()
        
        numseq = buffer.read_uint32()
        seqindex = buffer.read_uint32()
        
        numseqgroups = buffer.read_uint32()
        seqgroupindex = buffer.read_uint32()
        
        numtextures = buffer.read_uint32()
        textureindex = buffer.read_uint32()
        texturedataindex = buffer.read_uint32()
        
        numskinref = buffer.read_uint32()
        numskinfamilies = buffer.read_uint32()
        skinindex = buffer.read_uint32()
        
        numbodyparts = buffer.read_uint32()
        bodypartindex = buffer.read_uint32()
        
        numattachments = buffer.read_uint32()
        attachmentindex = buffer.read_uint32()
        
        soundtable = buffer.read_uint32()
        soundindex = buffer.read_uint32()
        soundgroups = buffer.read_uint32()
        soundgroupindex = buffer.read_uint32()
        
        numtransitions = buffer.read_uint32()
        transitionindex = buffer.read_uint32()
        
        return cls(
            id_val, version, name, length,
            eyeposition, min_corner, max_corner, bbmin, bbmax,
            flags,
            numbones, boneindex,
            numbonecontrollers, bonecontrollerindex,
            numhitboxes, hitboxindex,
            numseq, seqindex,
            numseqgroups, seqgroupindex,
            numtextures, textureindex, texturedataindex,
            numskinref, numskinfamilies, skinindex,
            numbodyparts, bodypartindex,
            numattachments, attachmentindex,
            soundtable, soundindex, soundgroups, soundgroupindex,
            numtransitions, transitionindex
        )


@dataclass
class StudioBone:
    """هيكل العظمة"""
    name: str
    parent: int
    flags: int
    bonecontroller: List[int]
    value: List[float]
    scale: List[float]
    
    @classmethod
    def from_buffer(cls, buffer: Buffer):
        name = buffer.read_ascii_string(32)
        parent = buffer.read_int32()
        flags = buffer.read_int32()
        bonecontroller = [buffer.read_int32() for _ in range(6)]
        value = [buffer.read_float() for _ in range(6)]
        scale = [buffer.read_float() for _ in range(6)]
        return cls(name, parent, flags, bonecontroller, value, scale)


@dataclass
class StudioBodyPart:
    """جزء من الجسم"""
    name: str
    nummodels: int
    base: int
    modelindex: int
    
    @classmethod
    def from_buffer(cls, buffer: Buffer):
        name = buffer.read_ascii_string(64)
        nummodels = buffer.read_uint32()
        base = buffer.read_uint32()
        modelindex = buffer.read_uint32()
        return cls(name, nummodels, base, modelindex)


@dataclass
class StudioModel:
    """نموذج فرعي"""
    name: str
    type: int
    boundingradius: float
    nummesh: int
    meshindex: int
    numverts: int
    vertinfoindex: int
    vertindex: int
    numnorms: int
    norminfoindex: int
    normindex: int
    numgroups: int
    groupindex: int
    
    @classmethod
    def from_buffer(cls, buffer: Buffer):
        name = buffer.read_ascii_string(64)
        type_val = buffer.read_uint32()
        boundingradius = buffer.read_float()
        nummesh = buffer.read_uint32()
        meshindex = buffer.read_uint32()
        numverts = buffer.read_uint32()
        vertinfoindex = buffer.read_uint32()
        vertindex = buffer.read_uint32()
        numnorms = buffer.read_uint32()
        norminfoindex = buffer.read_uint32()
        normindex = buffer.read_uint32()
        numgroups = buffer.read_uint32()
        groupindex = buffer.read_uint32()
        return cls(name, type_val, boundingradius, nummesh, meshindex,
                   numverts, vertinfoindex, vertindex, numnorms,
                   norminfoindex, normindex, numgroups, groupindex)


@dataclass
class StudioMesh:
    """شبكة"""
    numtris: int
    triindex: int
    skinref: int
    numnorms: int
    normindex: int
    
    @classmethod
    def from_buffer(cls, buffer: Buffer):
        numtris = buffer.read_uint32()
        triindex = buffer.read_uint32()
        skinref = buffer.read_uint32()
        numnorms = buffer.read_uint32()
        normindex = buffer.read_uint32()
        return cls(numtris, triindex, skinref, numnorms, normindex)


@dataclass
class StudioVertex:
    """رأس"""
    x: float
    y: float
    z: float
    
    @classmethod
    def from_buffer(cls, buffer: Buffer):
        return cls(buffer.read_float(), buffer.read_float(), buffer.read_float())


@dataclass
class StudioNormal:
    """طبيعية"""
    x: float
    y: float
    z: float
    
    @classmethod
    def from_buffer(cls, buffer: Buffer):
        return cls(buffer.read_float(), buffer.read_float(), buffer.read_float())


@dataclass
class StudioTriangle:
    """مثلث"""
    vertindex: List[int]  # 3 indices
    normindex: List[int]  # 3 indices
    s: int
    t: int
    
    @classmethod
    def from_buffer(cls, buffer: Buffer):
        vertindex = [buffer.read_int16() for _ in range(3)]
        normindex = [buffer.read_int16() for _ in range(3)]
        s = buffer.read_int16()
        t = buffer.read_int16()
        return cls(vertindex, normindex, s, t)

@dataclass
class StudioVertex:
    """رأس"""
    x: float
    y: float
    z: float
    
    @classmethod
    def from_buffer(cls, buffer: Buffer):
        return cls(buffer.read_float(), buffer.read_float(), buffer.read_float())


@dataclass
class StudioNormal:
    """طبيعية"""
    x: float
    y: float
    z: float
    
    @classmethod
    def from_buffer(cls, buffer: Buffer):
        return cls(buffer.read_float(), buffer.read_float(), buffer.read_float())


@dataclass
class StudioTriangle:
    """مثلث"""
    vertindex: List[int]
    normindex: List[int]
    s: int
    t: int
    
    @classmethod
    def from_buffer(cls, buffer: Buffer):
        vertindex = [buffer.read_int16() for _ in range(3)]
        normindex = [buffer.read_int16() for _ in range(3)]
        s = buffer.read_int16()
        t = buffer.read_int16()
        return cls(vertindex, normindex, s, t)


@dataclass
class StudioVertexInfo:
    """معلومات الرأس (مؤشرات إلى العظام والأوزان)"""
    bone_id: int
    bone_count: int
    
    @classmethod
    def from_buffer(cls, buffer: Buffer):
        bone_id = buffer.read_uint8()
        bone_count = buffer.read_uint8()
        buffer.read(2)  # padding
        return cls(bone_id, bone_count)


@dataclass
class StudioNormalInfo:
    """معلومات الطبيعية"""
    bone_id: int
    bone_count: int
    
    @classmethod
    def from_buffer(cls, buffer: Buffer):
        bone_id = buffer.read_uint8()
        bone_count = buffer.read_uint8()
        buffer.read(2)  # padding
        return cls(bone_id, bone_count)
                   

# ========== دعم صيغة SMD (StudioMDL) من Crowbar ==========

@dataclass
class SMDNode:
    """عقدة في هيكل SMD (عظمة)"""
    id: int
    name: str
    parent_id: int

@dataclass
class SMDVertex:
    """رأس في SMD"""
    bone_id: int      # مؤشر العظمة المرتبطة
    pos: Tuple[float, float, float]
    normal: Tuple[float, float, float]
    uv: Tuple[float, float]
    link_count: int = 1  # عدد العظام المرتبطة (1-4)
    links: List[Tuple[int, float]] = field(default_factory=list)  # (bone_id, weight)

@dataclass
class SMDFace:
    """وجه مثلث في SMD"""
    vertices: List[SMDVertex]  # 3 رؤوس

@dataclass
class SMDTriangle:
    """مثلث في SMD (صيغة Crowbar)"""
    parent_bone: int
    vertices: List[Tuple[float, float, float]]  # 3 رؤوس
    normals: List[Tuple[float, float, float]]   # 3 طبيعيات
    uvs: List[Tuple[float, float]]              # 3 UVs
    link_count: int = 1
    links: List[Tuple[int, float]] = field(default_factory=list)

class SMDExporter:
    """
    مصدر نماذج SMD (StudioMDL) - صيغة Crowbar
    يمكنه قراءة SMD وتصديره إلى صيغ أخرى
    """
    
    def __init__(self):
        self.nodes: List[SMDNode] = []      # العظام
        self.triangles: List[SMDTriangle] = []  # المثلثات
        self.vertices: List[SMDVertex] = []     # الرؤوس (للتزين)
        self.animations: Dict[str, any] = {}    # الرسوم المتحركة (اختياري)
        # ✅ المتغيرات الجديدة للمواد
        self.materials: List[str] = []           # أسماء المواد (القوام)
        self.material_triangle_indices: Dict[str, List[int]] = {}  # المادة -> قائمة مؤشرات المثلثات
        self.current_material: str = None        # المادة الحالية أثناء القراءة
        
    @classmethod
    def from_file(cls, filepath: str) -> 'SMDExporter':
        """قراءة ملف SMD من قرص"""
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        return cls.from_string(content)
    
    @classmethod
    def from_string(cls, content: str) -> 'SMDExporter':
        """قراءة SMD من نص - نسخة محسنة لـ Crowbar مع حفظ المواد"""
        exporter = cls()
        lines = content.strip().split('\n')
        
        i = 0
        current_material = None  # ✅ جديد: تتبع المادة الحالية
        material_faces = {}      # ✅ جديد: تخزين الوجوه لكل مادة
        
        while i < len(lines):
            line = lines[i].strip()
            
            if line == "nodes":
                # قراءة العظام
                i += 1
                while i < len(lines):
                    line = lines[i].strip()
                    if not line:
                        i += 1
                        continue
                    if line == "end":
                        break
                    
                    parts = line.split('"')
                    if len(parts) >= 3:
                        try:
                            node_id = int(parts[0].strip())
                            node_name = parts[1].strip()
                            parent_id = int(parts[2].strip())
                            exporter.nodes.append(SMDNode(node_id, node_name, parent_id))
                        except ValueError as e:
                            print(f"   Warning: Could not parse node line: {line}")
                    i += 1
                    
            elif line == "skeleton":
                # قراءة الهيكل العظمي (للتزين) - نتخطى مؤقتاً
                i += 1
                while i < len(lines):
                    line = lines[i].strip()
                    i += 1
                    if line == "end":
                        break
                        
            elif line == "triangles":
                # قراءة المثلثات (الشبكة)
                i += 1
                while i < len(lines):
                    line = lines[i].strip()
                    if not line:
                        i += 1
                        continue
                    if line == "end":
                        break
                    
                    # ✅ التصحيح: السطر الأول هو اسم المادة (القوام)
                    current_material = line.strip()
                    i += 1
                    
                    # ✅ تخزين الوجوه لهذه المادة
                    if current_material not in material_faces:
                        material_faces[current_material] = []
                    
                    vertices = []
                    normals = []
                    uvs = []
                    links = []
                    link_count = 1
                    
                    for v in range(3):
                        if i >= len(lines):
                            break
                        vert_line = lines[i].strip()
                        i += 1
                        
                        # تحليل الرأس: parent_bone pos_x pos_y pos_z norm_x norm_y norm_z u v [link_count [bone_id weight ...]]
                        vert_parts = vert_line.split()
                        if len(vert_parts) >= 9:
                            try:
                                parent_bone = int(vert_parts[0])
                                pos = (float(vert_parts[1]), float(vert_parts[2]), float(vert_parts[3]))
                                norm = (float(vert_parts[4]), float(vert_parts[5]), float(vert_parts[6]))
                                uv = (float(vert_parts[7]), float(vert_parts[8]))
                                
                                vertices.append(pos)
                                normals.append(norm)
                                uvs.append(uv)
                                
                                # قراءة الروابط (للتزين المتعدد)
                                if len(vert_parts) > 9:
                                    lcount = int(vert_parts[9])
                                    link_count = lcount
                                    vlinks = []
                                    for l in range(lcount):
                                        idx = 10 + l * 2
                                        if idx + 1 < len(vert_parts):
                                            bone_id = int(vert_parts[idx])
                                            weight = float(vert_parts[idx + 1])
                                            vlinks.append((bone_id, weight))
                                    links.append(vlinks)
                                else:
                                    links.append([(parent_bone, 1.0)])
                            except ValueError as e:
                                print(f"   Warning: Could not parse vertex line: {vert_line}")
                                continue
                    
                    if len(vertices) == 3:
                        triangle = SMDTriangle(parent_bone, vertices, normals, uvs, link_count, links)
                        exporter.triangles.append(triangle)
                        # ✅ تخزين المادة مع المثلث
                        material_faces[current_material].append(len(exporter.triangles) - 1)
                        
            elif line == "vertexanimation":
                # قراءة رسوم متحركة للرؤوس (اختياري)
                i += 1
                while i < len(lines):
                    line = lines[i].strip()
                    i += 1
                    if line == "end":
                        break
                        
            else:
                i += 1
        
        # ✅ حفظ المواد المستخرجة في كائن SMDExporter
        exporter.materials = list(material_faces.keys())
        exporter.material_triangle_indices = material_faces
        exporter.current_material = current_material
        
        print(f"   Parsed {len(exporter.nodes)} nodes, {len(exporter.triangles)} triangles")
        print(f"   Found materials: {exporter.materials}")
        return exporter
    
    def to_vertices_array(self) -> np.ndarray:
        """
        تحويل المثلثات إلى مصفوفة رؤوس موحدة
        """
        vertices = []
        faces = []
        vertex_counter = 0
        
        for tri in self.triangles:
            face_indices = []
            for v in range(3):
                pos = tri.vertices[v]
                norm = tri.normals[v]
                uv = tri.uvs[v]
                
                # استخدام أول رابط فقط إذا كان موجوداً
                bone_id = tri.links[v][0][0] if v < len(tri.links) and tri.links[v] else 0
                weight = tri.links[v][0][1] if v < len(tri.links) and tri.links[v] else 1.0
                
                vertices.append({
                    'px': pos[0], 'py': pos[1], 'pz': pos[2],
                    'nx': norm[0], 'ny': norm[1], 'nz': norm[2],
                    'u': uv[0], 'v': uv[1],
                    'bone_id': bone_id,
                    'weight': weight
                })
                face_indices.append(vertex_counter)
                vertex_counter += 1
            
            faces.append(face_indices)
        
        dtype_out = np.dtype([
            ("px", np.float32), ("py", np.float32), ("pz", np.float32),
            ("nx", np.float32), ("ny", np.float32), ("nz", np.float32),
            ("u", np.float32), ("v", np.float32),
            ("bone_id", np.uint16), ("weight", np.float32)
        ])
        
        verts_arr = np.array([(v['px'], v['py'], v['pz'],
                               v['nx'], v['ny'], v['nz'],
                               v['u'], v['v'],
                               v['bone_id'], v['weight']) 
                              for v in vertices], dtype=dtype_out)
        
        faces_arr = np.array(faces)
        
        return verts_arr, faces_arr
    
    def to_bones_list(self) -> List[Dict]:
        """تحويل العظام إلى قائمة"""
        bones = []
        for node in self.nodes:
            bones.append({
                'id': node.id,
                'name': node.name,
                'parent_id': node.parent_id
            })
        return bones
    
    def export_obj(self, output_path: str):
        """تصدير SMD إلى OBJ مع دعم المواد المتعددة من SMD"""
        vertices, faces = self.to_vertices_array()
        
        if len(vertices) == 0:
            print("No vertices to export")
            return
        
        base_name = os.path.splitext(output_path)[0]
        obj_path = f"{base_name}.obj"
        mtl_path = f"{base_name}.mtl"
        
        # ========== إعادة بناء المواد من بيانات SMD ==========
        # إذا كانت لدينا معلومات المواد من SMD
        material_names = []
        
        if hasattr(self, 'materials') and self.materials:
            # استخدام المواد المستخرجة من SMD
            material_names = self.materials
            print(f"   Using {len(material_names)} materials from SMD: {material_names}")
        else:
            # الحالة القديمة: مادة واحدة افتراضية
            material_names = ["smd_material"]
            print(f"   No materials found in SMD, using default material")
        
        # ========== إنشاء قاموس لتعيين كل وجه إلى مادته ==========
        face_to_material = {}
        
        if hasattr(self, 'material_triangle_indices') and self.material_triangle_indices:
            # بناء تعيين من مؤشر الوجه إلى اسم المادة
            for mat_name, tri_indices in self.material_triangle_indices.items():
                for tri_idx in tri_indices:
                    face_to_material[tri_idx] = mat_name
            print(f"   Mapped {len(face_to_material)} faces to materials")
        
        # ========== تجميع الوجوه حسب المادة ==========
        material_faces_map = {}
        for mat_name in material_names:
            material_faces_map[mat_name] = []
        
        # توزيع الوجوه على المواد
        if face_to_material:
            for face_idx, face in enumerate(faces):
                mat_name = face_to_material.get(face_idx, material_names[0])
                if mat_name not in material_faces_map:
                    material_faces_map[mat_name] = []
                material_faces_map[mat_name].append(face)
        else:
            # بدون معلومات المواد، كل الوجوه في مادة واحدة
            material_faces_map[material_names[0]] = faces
        
        # ========== كتابة ملف MTL (مواد متعددة) ==========
        with open(mtl_path, 'w', encoding='utf-8') as f:
            for mat_name in material_names:
                # تنظيف اسم المادة (إزالة المسارات وجعلها صالحة لاسم الملف)
                clean_mat_name = mat_name.replace('\\', '/').split('/')[-1]
                clean_mat_name = clean_mat_name.split('.')[0] if '.' in clean_mat_name else clean_mat_name
                clean_mat_name = clean_mat_name.replace(' ', '_').replace('-', '_')
                if not clean_mat_name:
                    clean_mat_name = f"material_{material_names.index(mat_name)}"
                
                # اسم ملف القوام
                tex_file = mat_name
                if not tex_file.endswith('.tga') and not tex_file.endswith('.png') and not tex_file.endswith('.bmp'):
                    tex_file = f"{clean_mat_name}.png"
                
                f.write(f"newmtl {clean_mat_name}\n")
                f.write("Ns 10.0000\n")
                f.write("Ka 1.0000 1.0000 1.0000\n")
                f.write("Kd 1.0000 1.0000 1.0000\n")
                f.write("Ks 0.0000 0.0000 0.0000\n")
                f.write(f"map_Kd {tex_file}\n")
                f.write("\n")
        
        # ========== كتابة ملف OBJ مع وجوه مادة تلو الأخرى ==========
        with open(obj_path, 'w', encoding='utf-8') as f:
            f.write(f"mtllib {os.path.basename(mtl_path)}\n")
            f.write(f"o {os.path.basename(base_name)}\n")
            
            # كتابة الرؤوس
            for v in vertices:
                f.write(f"v {v['px']:.6f} {v['py']:.6f} {v['pz']:.6f}\n")
            
            # كتابة إحداثيات النسيج (UV)
            for v in vertices:
                f.write(f"vt {v['u']:.6f} {1.0 - v['v']:.6f}\n")
            
            # كتابة الطبيعيات
            for v in vertices:
                f.write(f"vn {v['nx']:.6f} {v['ny']:.6f} {v['nz']:.6f}\n")
            
            # كتابة الوجوه حسب المادة
            total_faces_written = 0
            for mat_name, material_faces in material_faces_map.items():
                if not material_faces:
                    continue
                
                # تنظيف اسم المادة ليتوافق مع MTL
                clean_mat_name = mat_name.replace('\\', '/').split('/')[-1]
                clean_mat_name = clean_mat_name.split('.')[0] if '.' in clean_mat_name else clean_mat_name
                clean_mat_name = clean_mat_name.replace(' ', '_').replace('-', '_')
                if not clean_mat_name:
                    clean_mat_name = f"material_{material_names.index(mat_name)}"
                
                f.write(f"usemtl {clean_mat_name}\n")
                
                for face in material_faces:
                    a, b, c = face[0] + 1, face[1] + 1, face[2] + 1
                    f.write(f"f {a}/{a}/{a} {b}/{b}/{b} {c}/{c}/{c}\n")
                    total_faces_written += 1
            
            if total_faces_written == 0:
                # Fallback: كتابة كل الوجوه بمادة واحدة
                f.write(f"usemtl smd_material\n")
                for face in faces:
                    a, b, c = face[0] + 1, face[1] + 1, face[2] + 1
                    f.write(f"f {a}/{a}/{a} {b}/{b}/{b} {c}/{c}/{c}\n")
        
        print(f"   OBJ: {obj_path} (with {len(material_names)} materials)")
        print(f"   MTL: {mtl_path}")
    
    def get_material_for_triangle(self, triangle_index: int) -> str:
        """الحصول على اسم المادة لمثلث معين"""
        if hasattr(self, 'material_triangle_indices') and self.material_triangle_indices:
            for mat_name, tri_indices in self.material_triangle_indices.items():
                if triangle_index in tri_indices:
                    return mat_name
        return "default_material"
    
    def get_materials_list(self) -> List[str]:
        """الحصول على قائمة المواد الفريدة"""
        if hasattr(self, 'materials') and self.materials:
            return self.materials
        return ["default_material"]
        
    def export_gltf(self, output_path: str):
        """تصدير SMD إلى glTF"""
        if not GLTF_AVAILABLE:
            print("   pygltflib not available, skipping glTF export")
            return
        
        vertices, faces = self.to_vertices_array()
        
        if len(vertices) == 0:
            print("No vertices to export")
            return
        
        try:
            from pygltflib import GLTF2, Buffer, BufferView, Accessor, Mesh, Primitive, Attributes, Asset, Scene, Node, Skin
            
            gltf = GLTF2()
            gltf.asset = Asset(generator="SMD Exporter (Crowbar)", version="2.0")
            
            positions = []
            normals = []
            uvs = []
            weights = []
            joints = []
            
            for v in vertices:
                positions.extend([v['px'], v['py'], v['pz']])
                normals.extend([v['nx'], v['ny'], v['nz']])
                uvs.extend([v['u'], 1.0 - v['v']])
                weights.extend([v['weight'], 0.0, 0.0, 0.0])  # padding to 4
                joints.extend([v['bone_id'], 0, 0, 0])
            
            binary_data = bytearray()
            
            # Positions
            pos_bytes = np.array(positions, dtype=np.float32).tobytes()
            pos_bv = BufferView(buffer=0, byteOffset=len(binary_data), byteLength=len(pos_bytes), target=34962)
            gltf.bufferViews.append(pos_bv)
            binary_data.extend(pos_bytes)
            
            pos_acc = Accessor(bufferView=len(gltf.bufferViews)-1, componentType=5126,
                               count=len(vertices), type="VEC3")
            gltf.accessors.append(pos_acc)
            
            # Normals
            norm_bytes = np.array(normals, dtype=np.float32).tobytes()
            norm_bv = BufferView(buffer=0, byteOffset=len(binary_data), byteLength=len(norm_bytes), target=34962)
            gltf.bufferViews.append(norm_bv)
            binary_data.extend(norm_bytes)
            
            norm_acc = Accessor(bufferView=len(gltf.bufferViews)-1, componentType=5126,
                                count=len(vertices), type="VEC3")
            gltf.accessors.append(norm_acc)
            
            # UVs
            uv_bytes = np.array(uvs, dtype=np.float32).tobytes()
            uv_bv = BufferView(buffer=0, byteOffset=len(binary_data), byteLength=len(uv_bytes), target=34962)
            gltf.bufferViews.append(uv_bv)
            binary_data.extend(uv_bytes)
            
            uv_acc = Accessor(bufferView=len(gltf.bufferViews)-1, componentType=5126,
                              count=len(vertices), type="VEC2")
            gltf.accessors.append(uv_acc)
            
            # Weights
            weights_bytes = np.array(weights, dtype=np.float32).tobytes()
            weights_bv = BufferView(buffer=0, byteOffset=len(binary_data), byteLength=len(weights_bytes), target=34962)
            gltf.bufferViews.append(weights_bv)
            binary_data.extend(weights_bytes)
            
            weights_acc = Accessor(bufferView=len(gltf.bufferViews)-1, componentType=5126,
                                   count=len(vertices), type="VEC4")
            gltf.accessors.append(weights_acc)
            
            # Joints
            joints_bytes = np.array(joints, dtype=np.uint16).tobytes()
            joints_bv = BufferView(buffer=0, byteOffset=len(binary_data), byteLength=len(joints_bytes), target=34962)
            gltf.bufferViews.append(joints_bv)
            binary_data.extend(joints_bytes)
            
            joints_acc = Accessor(bufferView=len(gltf.bufferViews)-1, componentType=5123,
                                  count=len(vertices), type="VEC4")
            gltf.accessors.append(joints_acc)
            
            # Indices
            indices_list = []
            for face in faces:
                indices_list.extend([face[0], face[1], face[2]])
            
            indices_bytes = np.array(indices_list, dtype=np.uint32).tobytes()
            indices_bv = BufferView(buffer=0, byteOffset=len(binary_data), byteLength=len(indices_bytes), target=34963)
            gltf.bufferViews.append(indices_bv)
            binary_data.extend(indices_bytes)
            
            indices_acc = Accessor(bufferView=len(gltf.bufferViews)-1, componentType=5125,
                                   count=len(indices_list), type="SCALAR")
            gltf.accessors.append(indices_acc)
            
            # Buffer - استخدم اسم الملف الأساسي من output_path
            base_filename = os.path.splitext(os.path.basename(output_path))[0]
            gltf.buffers.append(Buffer(byteLength=len(binary_data), uri=f"{base_filename}.bin"))
            
            attributes = Attributes(POSITION=0, NORMAL=1, TEXCOORD_0=2, WEIGHTS_0=3, JOINTS_0=4)
            primitive = Primitive(attributes=attributes, indices=len(gltf.accessors)-1, material=0)
            mesh = Mesh(primitives=[primitive])
            gltf.meshes.append(mesh)
            
            # إضافة العظام إذا وجدت
            if self.nodes:
                bone_nodes = []
                for node in self.nodes:
                    gltf_node = Node(name=node.name)
                    gltf.nodes.append(gltf_node)
                    bone_nodes.append(len(gltf.nodes)-1)
                
                # بناء التسلسل الهرمي
                for i, node in enumerate(self.nodes):
                    if node.parent_id >= 0:
                        parent_idx = None
                        for j, n in enumerate(self.nodes):
                            if n.id == node.parent_id:
                                parent_idx = bone_nodes[j]
                                break
                        if parent_idx is not None:
                            if gltf.nodes[parent_idx].children is None:
                                gltf.nodes[parent_idx].children = []
                            gltf.nodes[parent_idx].children.append(bone_nodes[i])
                
                skin = Skin(joints=bone_nodes)
                gltf.skins.append(skin)
                
                node = Node(mesh=0, skin=len(gltf.skins)-1)
                gltf.nodes.append(node)
                scene = Scene(nodes=[len(gltf.nodes)-1])
            else:
                node = Node(mesh=0)
                gltf.nodes.append(node)
                scene = Scene(nodes=[0])
            
            gltf.scenes.append(scene)
            gltf.scene = 0
            
            # حفظ ملفات glTF
            gltf.save(f"{output_path}.gltf")
            with open(f"{os.path.splitext(output_path)[0]}.bin", 'wb') as f:
                f.write(binary_data)
            
            print(f"   glTF: {output_path}.gltf")
            print(f"   glTF binary: {os.path.splitext(output_path)[0]}.bin")
            
        except Exception as e:
            print(f"   Error exporting glTF: {e}")
            import traceback
            traceback.print_exc()
    
    def export_json(self, output_path: str):
        """تصدير بيانات SMD إلى JSON"""
        vertices, faces = self.to_vertices_array()
        
        data = {
            "format": "SMD (StudioMDL)",
            "nodes": [{"id": n.id, "name": n.name, "parent_id": n.parent_id} for n in self.nodes],
            "triangles_count": len(self.triangles),
            "vertices_count": len(vertices),
            "faces_count": len(faces),
            "vertices": [{"pos": [v['px'], v['py'], v['pz']],
                         "norm": [v['nx'], v['ny'], v['nz']],
                         "uv": [v['u'], v['v']],
                         "bone_id": v['bone_id'],
                         "weight": v['weight']} for v in vertices],
            "faces": [{"indices": list(f)} for f in faces]
        }
        
        data = convert_to_json_serializable(data)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        print(f"   JSON: {output_path}")
    
    def export_txt(self, output_path: str):
        """تصدير معلومات SMD إلى ملف نصي"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# SMD (StudioMDL) File Information\n")
            f.write(f"# Source: Crowbar decompile\n\n")
            
            f.write("=== NODES (Bones) ===\n")
            for node in self.nodes:
                f.write(f"  {node.id}: {node.name} (parent: {node.parent_id})\n")
            
            f.write(f"\n=== TRIANGLES ===\n")
            f.write(f"Total triangles: {len(self.triangles)}\n")
            
            vertices, faces = self.to_vertices_array()
            f.write(f"\n=== GEOMETRY ===\n")
            f.write(f"Total vertices: {len(vertices)}\n")
            f.write(f"Total faces: {len(faces)}\n")
            
            if self.animations:
                f.write(f"\n=== ANIMATIONS ===\n")
                for name, anim in self.animations.items():
                    f.write(f"  {name}: {anim}\n")
        
        print(f"   TXT: {output_path}")
    
    def export_all(self, output_dir: str, base_name: str, export_formats: List[str] = None):
        """تصدير SMD إلى جميع الصيغ المطلوبة"""
        if export_formats is None:
            export_formats = ["obj", "gltf", "json", "txt"]
        
        self.ensure_dir(output_dir)
        
        print(f"\nExporting SMD to {output_dir}")
        print("-" * 50)
        
        if "obj" in export_formats:
            self.export_obj(os.path.join(output_dir, base_name))
        
        if "gltf" in export_formats:
            self.export_gltf(os.path.join(output_dir, base_name))
        
        if "json" in export_formats:
            self.export_json(os.path.join(output_dir, f"{base_name}.json"))
        
        if "txt" in export_formats:
            self.export_txt(os.path.join(output_dir, f"{base_name}_info.txt"))
        
        print("-" * 50)
        print("Export completed successfully!")
    
    def ensure_dir(self, path):
        Path(path).mkdir(parents=True, exist_ok=True)


    def convert_smd_to_formats(input_smd: str, output_dir: str, export_formats: List[str] = None):
        """
        دالة مساعدة لتحويل ملف SMD واحد إلى صيغ متعددة
        """
        if export_formats is None:
            export_formats = ["obj", "gltf", "json", "txt"]
        
        if not os.path.exists(input_smd):
            print(f"Error: SMD file not found: {input_smd}")
            return False
        
        try:
            print(f"\nReading SMD file: {input_smd}")
            smd = SMDExporter.from_file(input_smd)
            
            base_name = os.path.splitext(os.path.basename(input_smd))[0]
            smd.export_all(output_dir, base_name, export_formats)
            
            return True
        except Exception as e:
            print(f"Error converting SMD: {e}")
            import traceback
            traceback.print_exc()
            return False


    def batch_convert_smd(input_dir: str, output_dir: str, export_formats: List[str] = None):
        """
        تحويل جميع ملفات SMD في مجلد إلى صيغ متعددة
        
        Args:
            input_dir: المجلد الذي يحتوي على ملفات SMD
            output_dir: مجلد الإخراج
            export_formats: قائمة الصيغ المطلوبة
        """
        if export_formats is None:
            export_formats = ["obj", "gltf", "json", "txt"]
        
        smd_files = []
        for ext in ['*.smd', '*.SMD']:
            smd_files.extend(Path(input_dir).glob(ext))
        
        if not smd_files:
            print(f"No SMD files found in '{input_dir}'")
            return False
        
        print(f"\nFound {len(smd_files)} SMD file(s):")
        for f in smd_files:
            print(f"  - {f.name}")
        
        successful = 0
        failed = 0
        
        for smd_file in smd_files:
            print(f"\n{'='*60}")
            print(f"Processing: {smd_file.name}")
            print(f"{'='*60}")
            
            output_subdir = os.path.join(output_dir, smd_file.stem)
            
            if convert_smd_to_formats(str(smd_file), output_subdir, export_formats):
                successful += 1
                print(f"✓ Successfully processed: {smd_file.name}")
            else:
                failed += 1
                print(f"✗ Failed to process: {smd_file.name}")
        
        print("\n" + "="*60)
        print("SMD BATCH CONVERSION COMPLETE")
        print("="*60)
        print(f"Total files found : {len(smd_files)}")
        print(f"Successfully processed : {successful}")
        print(f"Failed : {failed}")
        print(f"Output folder : {output_dir}")
        print("="*60)
        
        return successful > 0
    
    
def convert_smd_to_formats(input_smd: str, output_dir: str, export_formats: List[str] = None):
    """
    دالة مساعدة عامة لتحويل ملف SMD واحد إلى صيغ متعددة.
    (ممرّ آمن للدالة المعرّفة داخل SMDExporter)
    """
    return SMDExporter.convert_smd_to_formats(input_smd, output_dir, export_formats)


def batch_convert_smd(input_dir: str, output_dir: str, export_formats: List[str] = None):
    """
    دالة مساعدة عامة لتحويل جميع ملفات SMD في مجلد.
    (ممرّ آمن للدالة المعرّفة داخل SMDExporter)
    """
    return SMDExporter.batch_convert_smd(input_dir, output_dir, export_formats)


@dataclass    
class StudioHeader:
    """قارئ ملفات MDL حسب وثائق Valve الرسمية"""
    
    def __init__(self, buffer: Buffer):
        self.buffer = buffer
        self.header: MDLHeader = None
        self.bones: List[StudioBone] = []
        self.bodyparts: List[StudioBodyPart] = []
        self.models: List[StudioModel] = []
        self.meshes: List[StudioMesh] = []
        self.vertices: List[StudioVertex] = []
        self.normals: List[StudioNormal] = []
        self.triangles: List[StudioTriangle] = []
        
        self._parse()
    
    def _parse(self):
        """التحليل الكامل لملف MDL"""
        self.header = MDLHeader.from_buffer(self.buffer)
        print(f"MDL Header: {self.header.name}")
        print(f"  Version: {self.header.version}")
        print(f"  Bones: {self.header.numbones}")
        print(f"  Bodyparts: {self.header.numbodyparts}")
        print(f"  Textures: {self.header.numtextures}")
        print(f"  Sequences: {self.header.numseq}")
        
        # قراءة العظام
        if self.header.numbones > 0 and self.header.boneindex > 0:
            self.buffer.offset = self.header.boneindex
            for i in range(self.header.numbones):
                bone = StudioBone.from_buffer(self.buffer)
                self.bones.append(bone)
            print(f"  Parsed {len(self.bones)} bones")
        
        # قراءة أجزاء الجسم
        if self.header.numbodyparts > 0 and self.header.bodypartindex > 0:
            self.buffer.offset = self.header.bodypartindex
            for bp_idx in range(self.header.numbodyparts):
                bodypart = StudioBodyPart.from_buffer(self.buffer)
                self.bodyparts.append(bodypart)
                print(f"  Bodypart {bp_idx}: {bodypart.name}, models={bodypart.nummodels}")
                
                # قراءة النماذج
                if bodypart.nummodels > 0 and bodypart.modelindex > 0:
                    current_offset = self.buffer.offset
                    self.buffer.offset = bodypart.modelindex
                    
                    for m_idx in range(bodypart.nummodels):
                        model = StudioModel.from_buffer(self.buffer)
                        self.models.append(model)
                        print(f"    Model {m_idx}: {model.name}, meshes={model.nummesh}, verts={model.numverts}")
                        
                        # قراءة الشبكات
                        if model.nummesh > 0 and model.meshindex > 0:
                            mesh_offset_backup = self.buffer.offset
                            self.buffer.offset = model.meshindex
                            
                            for mesh_idx in range(model.nummesh):
                                mesh = StudioMesh.from_buffer(self.buffer)
                                self.meshes.append(mesh)
                                print(f"      Mesh {mesh_idx}: tris={mesh.numtris}")
                            
                            self.buffer.offset = mesh_offset_backup
                    
                    self.buffer.offset = current_offset
        
        # قراءة الرؤوس والمثلثات
        self._parse_geometry()
        
        print(f"  Total vertices: {len(self.vertices)}")
        print(f"  Total triangles: {len(self.triangles)}")
    
    def _parse_geometry(self):
        """قراءة الرؤوس والمثلثات من جميع النماذج مع دعم Triangle Strips/Fans"""
        
        # قوائم مؤقتة للرؤوس والطبيعيات والمثلثات
        all_vertices = []      # الرؤوس الفعلية (x,y,z)
        all_normals = []       # الطبيعيات الفعلية (nx,ny,nz)
        all_vertex_infos = []  # معلومات الرأس (العظام)
        all_normal_infos = []  # معلومات الطبيعية
        all_triangles = []     # المثلثات (مؤشرات إلى all_vertices)
        
        for model in self.models:
            if model.numverts == 0:
                continue
            
            # ========== 1. قراءة معلومات الرؤوس ==========
            if model.vertinfoindex > 0 and model.vertinfoindex <= len(self.buffer.data):
                self.buffer.offset = model.vertinfoindex
                for v in range(model.numverts):
                    vert_info = StudioVertexInfo.from_buffer(self.buffer)
                    all_vertex_infos.append(vert_info)
            
            # ========== 2. قراءة الرؤوس الفعلية ==========
            if model.vertindex > 0 and model.vertindex <= len(self.buffer.data):
                self.buffer.offset = model.vertindex
                for v in range(model.numverts):
                    vertex = StudioVertex.from_buffer(self.buffer)
                    all_vertices.append(vertex)
            
            # ========== 3. قراءة معلومات الطبيعيات ==========
            if model.norminfoindex > 0 and model.norminfoindex <= len(self.buffer.data):
                self.buffer.offset = model.norminfoindex
                for n in range(model.numnorms):
                    norm_info = StudioNormalInfo.from_buffer(self.buffer)
                    all_normal_infos.append(norm_info)
            
            # ========== 4. قراءة الطبيعيات الفعلية ==========
            if model.normindex > 0 and model.normindex <= len(self.buffer.data):
                self.buffer.offset = model.normindex
                for n in range(model.numnorms):
                    normal = StudioNormal.from_buffer(self.buffer)
                    all_normals.append(normal)
            
            # ========== 5. قراءة المثلثات من الشبكات باستخدام Triangle Commands ==========
            for mesh in self.meshes:
                if mesh.numtris == 0 or mesh.triindex == 0:
                    continue
                
                if mesh.triindex <= len(self.buffer.data):
                    self.buffer.offset = mesh.triindex
                    # قراءة المثلثات باستخدام طريقة Strip/Fan
                    self._parse_triangle_commands(all_triangles, mesh.skinref)
        
        # معالجة المثلثات وتحويل المؤشرات
        valid_vertices = []
        valid_normals = []
        valid_triangles = []
        
        for v in all_vertices:
            valid_vertices.append(v)
        
        for n in all_normals:
            valid_normals.append(n)
        
        # تحويل المثلثات: استخراج المؤشرات الصالحة
        for tri in all_triangles:
            if all(0 <= idx < len(valid_vertices) for idx in tri.vertindex):
                valid_triangles.append(tri)
        
        self.vertices = valid_vertices
        self.normals = valid_normals
        self.triangles = valid_triangles
        
        print(f"  Final vertices: {len(self.vertices)}")
        print(f"  Final normals: {len(self.normals)}")
        print(f"  Final triangles: {len(self.triangles)}")
        
        # تحقق أخير
        if self.triangles:
            max_idx = max([max(tri.vertindex) for tri in self.triangles])
            if max_idx >= len(self.vertices):
                print(f"  ⚠️ WARNING: Still have out-of-range indices! max={max_idx}, vertices={len(self.vertices)}")
    
    def _parse_triangle_commands(self, all_triangles: list, skinref: int):
        """
        قراءة Triangle Commands من MDL (Triangle Strips و Fans)
        هذه هي الطريقة الصحيحة التي تستخدمها لعبة Half-Life
        """
        vertex_cache = []  # لتخزين مؤشرات الرؤوس المؤقتة في Strips/Fans
        
        while True:
            # قراءة الأمر (short/int16)
            if self.buffer.offset + 2 > len(self.buffer.data):
                break
            
            command = self.buffer.read_int16()
            
            if command == 0:
                # نهاية قائمة المثلثات
                break
            
            if command > 0:
                # Triangle Strip
                num_vertices = command
                # قراءة الرؤوس
                vertices_in_strip = []
                for i in range(num_vertices):
                    if self.buffer.offset + 8 > len(self.buffer.data):  # 2+2+2+2=8 bytes
                        break
                    vert_idx = self.buffer.read_int16()
                    norm_idx = self.buffer.read_int16()
                    s = self.buffer.read_int16()
                    t = self.buffer.read_int16()
                    vertices_in_strip.append((vert_idx, norm_idx, s, t))
                
                # تحويل Strip إلى مثلثات
                # Strip: 0-1-2, 1-2-3, 2-3-4, ...
                for i in range(len(vertices_in_strip) - 2):
                    a = vertices_in_strip[i]
                    b = vertices_in_strip[i + 1]
                    c = vertices_in_strip[i + 2]
                    
                    # كل 3 رؤوس تشكل مثلثاً (مع تبديل الترتيب لـ Odd/Even)
                    if i % 2 == 0:
                        tri = StudioTriangle(
                            vertindex=[a[0], b[0], c[0]],
                            normindex=[a[1], b[1], c[1]],
                            s=a[2], t=a[3]
                        )
                    else:
                        tri = StudioTriangle(
                            vertindex=[b[0], a[0], c[0]],
                            normindex=[b[1], a[1], c[1]],
                            s=b[2], t=b[3]
                        )
                    all_triangles.append(tri)
                    
            elif command < 0:
                # Triangle Fan
                num_vertices = -command
                # قراءة الرؤوس
                vertices_in_fan = []
                for i in range(num_vertices):
                    if self.buffer.offset + 8 > len(self.buffer.data):
                        break
                    vert_idx = self.buffer.read_int16()
                    norm_idx = self.buffer.read_int16()
                    s = self.buffer.read_int16()
                    t = self.buffer.read_int16()
                    vertices_in_fan.append((vert_idx, norm_idx, s, t))
                
                # تحويل Fan إلى مثلثات
                # Fan: 0-1-2, 0-2-3, 0-3-4, ...
                if len(vertices_in_fan) >= 3:
                    first = vertices_in_fan[0]
                    for i in range(1, len(vertices_in_fan) - 1):
                        b = vertices_in_fan[i]
                        c = vertices_in_fan[i + 1]
                        tri = StudioTriangle(
                            vertindex=[first[0], b[0], c[0]],
                            normindex=[first[1], b[1], c[1]],
                            s=first[2], t=first[3]
                        )
                        all_triangles.append(tri)
    
    def extract_textures(self, output_dir: str):
        """استخراج القوام المدمجة من ملف MDL"""
        if self.header.numtextures == 0 or self.header.textureindex == 0:
            print("  No embedded textures found")
            return
        
        self.buffer.offset = self.header.textureindex
        texture_dir = os.path.join(output_dir, "textures")
        Path(texture_dir).mkdir(parents=True, exist_ok=True)
        
        for i in range(self.header.numtextures):
            # قراءة معلومات القوام
            name = self.buffer.read_ascii_string(64)
            flags = self.buffer.read_uint32()
            width = self.buffer.read_uint32()
            height = self.buffer.read_uint32()
            index = self.buffer.read_uint32()
            
            print(f"  Texture {i}: {name} ({width}x{height})")
            
            # قراءة بيانات القوام من texturedataindex
            if index > 0 and self.header.texturedataindex > 0:
                old_offset = self.buffer.offset
                self.buffer.offset = self.header.texturedataindex + index
                
                # حساب حجم البيانات (8-bit paletted في GoldSrc)
                data_size = width * height
                if data_size > 0 and data_size <= len(self.buffer.data) - self.buffer.offset:
                    # قراءة بيانات البكسل
                    pixel_data = self.buffer.read(data_size)
                    
                    # حفظ كملف TGA
                    tex_path = os.path.join(texture_dir, f"{name}.tga")
                    with open(tex_path, 'wb') as f:
                        # كتابة رأس TGA بسيط (RGB غير مضغوط)
                        # هذا رأس TGA أساسي - يمكن تحسينه
                        header = bytearray([
                            0,  # ID length
                            0,  # Color map type
                            2,  # Image type (RGB)
                            0, 0,  # Color map start
                            0, 0,  # Color map length
                            0,  # Color map bits
                            0, 0,  # X origin
                            0, 0,  # Y origin
                            width & 0xFF, (width >> 8) & 0xFF,  # Width
                            height & 0xFF, (height >> 8) & 0xFF,  # Height
                            24,  # Bits per pixel
                            0   # Image descriptor
                        ])
                        f.write(header)
                        f.write(pixel_data)
                    
                    print(f"    Saved: {tex_path}")
                
                self.buffer.offset = old_offset
    
    def debug_print_geometry(self):
        """طباعة معلومات تشخيصية عن الهندسة"""
        print(f"\n🔍 DEBUG: Total vertices: {len(self.vertices)}")
        print(f"🔍 DEBUG: Total normals: {len(self.normals)}")
        print(f"🔍 DEBUG: Total triangles: {len(self.triangles)}")
        
        if len(self.vertices) > 0:
            print(f"\n🔍 DEBUG: First 5 vertices (raw):")
            for i in range(min(5, len(self.vertices))):
                v = self.vertices[i]
                print(f"  v{i}: ({v.x:.2f}, {v.y:.2f}, {v.z:.2f})")
        
        if len(self.triangles) > 0:
            print(f"\n🔍 DEBUG: First 5 triangles (raw indices):")
            for i in range(min(5, len(self.triangles))):
                tri = self.triangles[i]
                print(f"  tri{i}: verts=({tri.vertindex[0]}, {tri.vertindex[1]}, {tri.vertindex[2]}), "
                      f"norms=({tri.normindex[0]}, {tri.normindex[1]}, {tri.normindex[2]}), "
                      f"uv=({tri.s}, {tri.t})")
        
        # التحقق من صحة المؤشرات
        if self.triangles:
            max_vert_idx = max([max(tri.vertindex) for tri in self.triangles])
            max_norm_idx = max([max(tri.normindex) for tri in self.triangles]) if self.triangles else -1
            print(f"\n🔍 DEBUG: Max vertex index used: {max_vert_idx} (total vertices: {len(self.vertices)})")
            print(f"🔍 DEBUG: Max normal index used: {max_norm_idx} (total normals: {len(self.normals)})")
            
            if max_vert_idx >= len(self.vertices):
                print(f"⚠️ WARNING: Vertex index {max_vert_idx} out of range!")
            if max_norm_idx >= len(self.normals) and len(self.normals) > 0:
                print(f"⚠️ WARNING: Normal index {max_norm_idx} out of range!")
    
    def export_obj_as_points(self, out_dir, base_name):
        """تصدير كل مثلث كثلاث رؤوس منفصلة (حل مؤقت للمؤشرات الخاطئة)"""
        if len(self.vertices) == 0 or len(self.triangles) == 0:
            print("No geometry to export")
            return
        
        obj_path = os.path.join(out_dir, f"{base_name}_points.obj")
        mtl_path = os.path.join(out_dir, f"{base_name}_points.mtl")
        
        with open(mtl_path, 'w', encoding='utf-8') as f:
            f.write(f"newmtl material\n")
            f.write("Ns 10.0000\n")
            f.write("Ka 1.0000 1.0000 1.0000\n")
            f.write("Kd 1.0000 1.0000 1.0000\n")
            f.write("Ks 0.0000 0.0000 0.0000\n")
        
        with open(obj_path, 'w', encoding='utf-8') as f:
            f.write(f"mtllib {base_name}_points.mtl\n")
            f.write(f"o {base_name}\n")
            
            # تجميع كل الرؤوس من المثلثات (بدون إعادة استخدام)
            all_points = []
            for tri in self.triangles:
                for idx in tri.vertindex:
                    if 0 <= idx < len(self.vertices):
                        v = self.vertices[idx]
                        # تحويل Y-up إلى Z-up
                        all_points.append((v.x, v.z, v.y))
                    else:
                        # نقطة وهمية للمؤشرات الخاطئة
                        all_points.append((0, 0, 0))
            
            # كتابة الرؤوس
            for p in all_points:
                f.write(f"v {p[0]:.6f} {p[1]:.6f} {p[2]:.6f}\n")
            
            # كتابة الوجوه (كل 3 رؤوس تشكل وجهاً)
            f.write(f"usemtl material\n")
            for i in range(0, len(all_points), 3):
                if i + 2 < len(all_points):
                    f.write(f"f {i+1} {i+2} {i+3}\n")
        
        print(f"   OBJ (points mode): {obj_path}")
    
    def export_obj(self, out_dir, base_name):
        """تصدير إلى OBJ"""
        self.debug_print_geometry()
        if len(self.vertices) == 0 or len(self.triangles) == 0:
            print("No geometry to export")
            return
        
        obj_path = os.path.join(out_dir, f"{base_name}.obj")
        mtl_path = os.path.join(out_dir, f"{base_name}.mtl")
        
        with open(mtl_path, 'w', encoding='utf-8') as f:
            f.write(f"newmtl {base_name}_material\n")
            f.write("Ns 10.0000\n")
            f.write("Ka 1.0000 1.0000 1.0000\n")
            f.write("Kd 1.0000 1.0000 1.0000\n")
            f.write("Ks 0.0000 0.0000 0.0000\n")
            if self.header.numtextures > 0:
                f.write("map_Kd texture.bmp\n")
        
        with open(obj_path, 'w', encoding='utf-8') as f:
            f.write(f"mtllib {base_name}.mtl\n")
            f.write(f"o {base_name}\n")
            
            # تجميع كل الرؤوس والطبيعيات و UVs
            all_vertices = []
            all_normals = []
            all_uvs = []
            
            for tri in self.triangles:
                for i in range(3):
                    vert_idx = tri.vertindex[i]
                    norm_idx = tri.normindex[i]
                    
                    if vert_idx >= 0 and vert_idx < len(self.vertices):
                        v = self.vertices[vert_idx]
                        # تحويل Y-up إلى Z-up
                        all_vertices.append((v.x, v.z, v.y))
                        
                        if norm_idx >= 0 and norm_idx < len(self.normals):
                            n = self.normals[norm_idx]
                            # تحويل Y-up إلى Z-up للطبيعيات
                            all_normals.append((n.x, n.z, n.y))
                        else:
                            all_normals.append((0, 0, 0))
                        
                        # UV من s,t (تطبيع)
                        u = tri.s / 32768.0 if tri.s != 0 else 0.0
                        vt = tri.t / 32768.0 if tri.t != 0 else 0.0
                        all_uvs.append((u, 1.0 - vt))
            
            if len(all_vertices) == 0:
                print("   No valid vertices to export")
                return
            
            # كتابة الرؤوس
            for v in all_vertices:
                f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
            
            # كتابة إحداثيات النسيج
            for uv in all_uvs:
                f.write(f"vt {uv[0]:.6f} {uv[1]:.6f}\n")
            
            # كتابة الطبيعيات
            for n in all_normals:
                f.write(f"vn {n[0]:.6f} {n[1]:.6f} {n[2]:.6f}\n")
            
            # كتابة الوجوه (كل 3 رؤوس تشكل وجهاً واحداً)
            f.write(f"usemtl {base_name}_material\n")
            
            for i in range(0, len(all_vertices), 3):
                a, b, c = i + 1, i + 2, i + 3
                f.write(f"f {a}/{a}/{a} {b}/{b}/{b} {c}/{c}/{c}\n")
        
        print(f"   OBJ: {obj_path}")
        print(f"   MTL: {mtl_path}")
    
    def export_gltf(self, out_dir, base_name):
        """تصدير إلى glTF مع دعم العظام"""
        if not GLTF_AVAILABLE:
            print("   pygltflib not available, skipping glTF export")
            return
        
        if len(self.vertices) == 0 or len(self.triangles) == 0:
            print("No geometry to export")
            return
        
        try:
            from pygltflib import GLTF2, Buffer, BufferView, Accessor, Mesh, Primitive, Attributes, Asset, Scene, Node, Skin
            
            gltf = GLTF2()
            gltf.asset = Asset(generator="HL MDL Reader (Valve spec)", version="2.0")
            
            positions = []
            for v in self.vertices:
                # تحويل Y-up إلى Z-up
                positions.extend([v.x, v.z, v.y])
            
            indices = []
            for tri in self.triangles:
                a, b, c = tri.vertindex[0], tri.vertindex[1], tri.vertindex[2]
                if a >= 0 and b >= 0 and c >= 0:
                    indices.extend([a, b, c])
            
            if len(indices) == 0:
                print("   No valid triangles to export")
                return
            
            binary_data = bytearray()
            
            # Positions
            pos_bytes = np.array(positions, dtype=np.float32).tobytes()
            pos_bv = BufferView(buffer=0, byteOffset=len(binary_data), byteLength=len(pos_bytes), target=34962)
            gltf.bufferViews.append(pos_bv)
            binary_data.extend(pos_bytes)
            
            pos_acc = Accessor(bufferView=len(gltf.bufferViews)-1, componentType=5126,
                               count=len(self.vertices), type="VEC3")
            gltf.accessors.append(pos_acc)
            
            # Indices
            idx_bytes = np.array(indices, dtype=np.uint32).tobytes()
            idx_bv = BufferView(buffer=0, byteOffset=len(binary_data), byteLength=len(idx_bytes), target=34963)
            gltf.bufferViews.append(idx_bv)
            binary_data.extend(idx_bytes)
            
            idx_acc = Accessor(bufferView=len(gltf.bufferViews)-1, componentType=5125,
                               count=len(indices), type="SCALAR")
            gltf.accessors.append(idx_acc)
            
            gltf.buffers.append(Buffer(byteLength=len(binary_data), uri=f"{base_name}.bin"))
            
            attributes = Attributes(POSITION=0)
            primitive = Primitive(attributes=attributes, indices=len(gltf.accessors)-1, material=0)
            mesh = Mesh(primitives=[primitive])
            gltf.meshes.append(mesh)
            
            # إضافة العظام إذا وجدت
            if len(self.bones) > 0:
                # إنشاء عقد للعظام
                bone_nodes = []
                for i, bone in enumerate(self.bones):
                    # تحويل موقع العظمة
                    bx, by, bz = bone.value[0], bone.value[1], bone.value[2]
                    # تحويل Y-up إلى Z-up
                    node = Node(name=bone.name, translation=[bx, bz, by])
                    gltf.nodes.append(node)
                    bone_nodes.append(len(gltf.nodes)-1)
                
                # بناء التسلسل الهرمي
                for i, bone in enumerate(self.bones):
                    if bone.parent >= 0 and bone.parent < len(bone_nodes):
                        if gltf.nodes[bone_nodes[bone.parent]].children is None:
                            gltf.nodes[bone_nodes[bone.parent]].children = []
                        gltf.nodes[bone_nodes[bone.parent]].children.append(bone_nodes[i])
                
                # إنشاء Skin
                skin = Skin(joints=bone_nodes)
                gltf.skins.append(skin)
                
                # ربط الـ skin بالـ mesh
                node = Node(mesh=0, skin=len(gltf.skins)-1)
                gltf.nodes.append(node)
                scene = Scene(nodes=[len(gltf.nodes)-1])
            else:
                node = Node(mesh=0)
                gltf.nodes.append(node)
                scene = Scene(nodes=[0])
            
            gltf.scenes.append(scene)
            gltf.scene = 0
            
            gltf.save(f"{out_dir}/{base_name}.gltf")
            
            with open(f"{out_dir}/{base_name}.bin", 'wb') as f:
                f.write(binary_data)
            
            print(f"   glTF: {out_dir}/{base_name}.gltf")
            print(f"   glTF binary: {out_dir}/{base_name}.bin")
            if len(self.bones) > 0:
                print(f"   Bones exported: {len(self.bones)}")
            
        except Exception as e:
            print(f"   Error exporting glTF: {e}")
    
    def export_json(self, out_dir, base_name):
        """تصدير بيانات النموذج إلى JSON"""
        data = {
            "header": {
                "name": self.header.name,
                "version": self.header.version,
                "flags": self.header.flags,
                "numbones": self.header.numbones,
                "numtextures": self.header.numtextures,
                "numbodyparts": self.header.numbodyparts,
                "numseq": self.header.numseq
            },
            "bones": [{"name": b.name, "parent": b.parent} for b in self.bones],
            "bodyparts": [{"name": bp.name, "nummodels": bp.nummodels} for bp in self.bodyparts],
            "num_vertices": len(self.vertices),
            "num_triangles": len(self.triangles)
        }
        
        data = convert_to_json_serializable(data)
        json_path = os.path.join(out_dir, f"{base_name}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   JSON: {json_path}")
    
    def export_txt(self, out_dir, base_name):
        """تصدير معلومات النموذج إلى ملف نصي"""
        txt_path = os.path.join(out_dir, f"{base_name}_info.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# Half-Life MDL Model Info (Valve specification)\n")
            f.write(f"File: {self.header.name}\n")
            f.write(f"Version: {self.header.version}\n")
            f.write(f"Flags: {self.header.flags}\n\n")
            
            f.write("Bounding Box:\n")
            f.write(f"  Min: ({self.header.min_corner[0]:.2f}, {self.header.min_corner[1]:.2f}, {self.header.min_corner[2]:.2f})\n")
            f.write(f"  Max: ({self.header.max_corner[0]:.2f}, {self.header.max_corner[1]:.2f}, {self.header.max_corner[2]:.2f})\n\n")
            
            f.write(f"Bones ({len(self.bones)}):\n")
            for i, bone in enumerate(self.bones):
                f.write(f"  {i}: {bone.name} (parent: {bone.parent})\n")
            f.write("\n")
            
            f.write(f"Bodyparts ({len(self.bodyparts)}):\n")
            for bp in self.bodyparts:
                f.write(f"  {bp.name}: {bp.nummodels} models\n")
            f.write("\n")
            
            f.write(f"Geometry:\n")
            f.write(f"  Vertices: {len(self.vertices)}\n")
            f.write(f"  Triangles: {len(self.triangles)}\n")
        
        print(f"   TXT: {txt_path}")
    
    def export_all(self, out_dir, export_formats=None):
        """تصدير كل شيء"""
        if export_formats is None:
            export_formats = ["obj"]
        
        base_name = os.path.basename(out_dir)
        self.ensure_dir(out_dir)
        
        # استخراج القوام المدمجة
        self.extract_textures(out_dir)
        
        print(f"\nExporting MDL to {out_dir}")
        print("-" * 50)
        
        # تشخيص
        self.debug_print_geometry()
        
        if "obj" in export_formats:
            # جرب الطريقة التشخيصية أولاً
            self.export_obj_as_points(out_dir, base_name)
            # ثم الطريقة العادية
            self.export_obj(out_dir, base_name)
        
        if "gltf" in export_formats and GLTF_AVAILABLE:
            self.export_gltf(out_dir, base_name)
        
        if "json" in export_formats:
            self.export_json(out_dir, base_name)
        
        if "txt" in export_formats:
            self.export_txt(out_dir, base_name)
        
        print("-" * 50)
        print("Export completed successfully!")
    
    def ensure_dir(self, path):
        Path(path).mkdir(parents=True, exist_ok=True)

# ========== دعم صيغة OBJ (Wavefront) ==========
# إضافة كاملة لدعم ملفات OBJ بجميع أشكالها وأنواعها

@dataclass
class OBJVertex:
    """رأس في OBJ (v)"""
    x: float
    y: float
    z: float

@dataclass
class OBJTextureVertex:
    """إحداثيات نسيج في OBJ (vt)"""
    u: float
    v: float
    w: float = 0.0  # اختياري للـ 3D textures

@dataclass
class OBJNormal:
    """طبيعية في OBJ (vn)"""
    x: float
    y: float
    z: float

@dataclass
class OBJFace:
    """وجه في OBJ (f) - يدعم جميع التنسيقات"""
    # يمكن أن تكون المؤشرات بأشكال متعددة:
    # v, v/vt, v/vt/vn, v//vn
    vertex_indices: List[int] = field(default_factory=list)
    texture_indices: List[int] = field(default_factory=list)
    normal_indices: List[int] = field(default_factory=list)
    material_name: str = "default"

@dataclass
class OBJMaterial:
    """مادة في OBJ (ملف MTL)"""
    name: str
    ambient: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    diffuse: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    specular: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    emissive: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    shininess: float = 10.0
    transparency: float = 1.0
    diffuse_texture: str = ""
    bump_texture: str = ""
    specular_texture: str = ""
    alpha_texture: str = ""

@dataclass
class OBJObject:
    """كائن (مجموعة) في OBJ (o أو g)"""
    name: str
    material_name: str = "default"
    vertices: List[OBJVertex] = field(default_factory=list)
    texture_vertices: List[OBJTextureVertex] = field(default_factory=list)
    normals: List[OBJNormal] = field(default_factory=list)
    faces: List[OBJFace] = field(default_factory=list)
    smoothing_groups: Dict[int, List[OBJFace]] = field(default_factory=dict)

class OBJExporter:
    """
    قارئ ومصدر لملفات OBJ (Wavefront)
    يدعم:
    - جميع أنواع الرؤوس (v, vt, vn, vp)
    - جميع تنسيقات الوجوه (f v, f v/vt, f v/vt/vn, f v//vn)
    - مجموعات الكائنات (o, g)
    - المواد (ملفات MTL)
    - مجموعات التنعيم (s)
    - القطع (l, p, usemtl, mtllib)
    """
    
    def __init__(self):
        self.objects: List[OBJObject] = []
        self.materials: Dict[str, OBJMaterial] = {}
        self.material_libs: List[str] = []
        self.current_object: OBJObject = None
        self.current_material: str = "default"
        self.current_smoothing: int = 0
        
        # بيانات عامة للتحليل
        self._all_vertices: List[OBJVertex] = []
        self._all_texture_vertices: List[OBJTextureVertex] = []
        self._all_normals: List[OBJNormal] = []
        
    @classmethod
    def from_file(cls, filepath: str, mtl_search_paths: List[str] = None) -> 'OBJExporter':
        """قراءة ملف OBJ من القرص مع دعم ملفات MTL"""
        exporter = cls()
        
        if mtl_search_paths is None:
            mtl_search_paths = [os.path.dirname(filepath), os.getcwd()]
        
        # قراءة ملف OBJ
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        exporter.parse_obj_content(content, filepath, mtl_search_paths)
        return exporter
    
    @classmethod
    def from_string(cls, content: str, base_path: str = "", mtl_search_paths: List[str] = None) -> 'OBJExporter':
        """قراءة OBJ من نص"""
        exporter = cls()
        if mtl_search_paths is None:
            mtl_search_paths = [os.getcwd()]
        exporter.parse_obj_content(content, base_path, mtl_search_paths)
        return exporter
    
    def parse_obj_content(self, content: str, base_path: str, mtl_search_paths: List[str]):
        """تحليل محتوى ملف OBJ"""
        lines = content.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            parts = line.split()
            cmd = parts[0].lower()
            
            if cmd == 'v':  # رأس
                self._parse_vertex(parts)
            elif cmd == 'vt':  # إحداثيات نسيج
                self._parse_texture_vertex(parts)
            elif cmd == 'vn':  # طبيعية
                self._parse_normal(parts)
            elif cmd == 'vp':  # رأس معلمي (نتخطى)
                pass
            elif cmd == 'f':  # وجه
                self._parse_face(parts)
            elif cmd == 'o':  # كائن جديد
                self._new_object(parts[1] if len(parts) > 1 else f"object_{len(self.objects)}")
            elif cmd == 'g':  # مجموعة (نفس o)
                if len(parts) > 1:
                    self._new_object(parts[1])
            elif cmd == 'usemtl':  # استخدام مادة
                if len(parts) > 1:
                    self.current_material = parts[1]
                    if self.current_object:
                        self.current_object.material_name = self.current_material
            elif cmd == 'mtllib':  # مكتبة مواد
                if len(parts) > 1:
                    mtl_file = parts[1]
                    self.material_libs.append(mtl_file)
                    self._load_mtl_file(mtl_file, base_path, mtl_search_paths)
            elif cmd == 's':  # مجموعة تنعيم
                if len(parts) > 1:
                    try:
                        self.current_smoothing = int(parts[1])
                    except:
                        self.current_smoothing = 0 if parts[1] == 'off' else 0
            elif cmd == 'l':  # خط (نتخطى)
                pass
            elif cmd == 'p':  # نقطة (نتخطى)
                pass
        
        # ✅ إنشاء كائن افتراضي إذا لم يكن هناك كائنات
        if not self.objects and (self._all_vertices or self._all_texture_vertices or self._all_normals):
            self._new_object("default")
        
        print(f"   OBJ Parsed: {len(self.objects)} objects, {len(self._all_vertices)} vertices, "
              f"{len(self._all_texture_vertices)} UVs, {len(self._all_normals)} normals, "
              f"{len(self.materials)} materials")
              
    def _new_object(self, name: str):
        """إنشاء كائن جديد"""
        obj = OBJObject(
            name=name,
            material_name=self.current_material,
            vertices=[],
            texture_vertices=[],
            normals=[],
            faces=[],
            smoothing_groups={}
        )
        self.objects.append(obj)
        self.current_object = obj
    
    def _parse_vertex(self, parts: List[str]):
        """تحليل رأس (v x y z [w])"""
        x = float(parts[1])
        y = float(parts[2])
        z = float(parts[3]) if len(parts) > 3 else 0.0
        
        vertex = OBJVertex(x, y, z)
        self._all_vertices.append(vertex)
        if self.current_object:
            self.current_object.vertices.append(vertex)
    
    def _parse_texture_vertex(self, parts: List[str]):
        """تحليل إحداثيات نسيج (vt u [v [w]])"""
        u = float(parts[1])
        v = float(parts[2]) if len(parts) > 2 else 0.0
        w = float(parts[3]) if len(parts) > 3 else 0.0
        
        tex_vert = OBJTextureVertex(u, v, w)
        self._all_texture_vertices.append(tex_vert)
        if self.current_object:
            self.current_object.texture_vertices.append(tex_vert)
    
    def _parse_normal(self, parts: List[str]):
        """تحليل طبيعية (vn x y z)"""
        x = float(parts[1])
        y = float(parts[2])
        z = float(parts[3]) if len(parts) > 3 else 0.0
        
        normal = OBJNormal(x, y, z)
        self._all_normals.append(normal)
        if self.current_object:
            self.current_object.normals.append(normal)
    
    def _parse_face(self, parts: List[str]):
        """
        تحليل وجه (f v1 v2 v3 ...)
        يدعم التنسيقات:
        - f v1 v2 v3
        - f v1/vt1 v2/vt2 v3/vt3
        - f v1/vt1/vn1 v2/vt2/vn2 v3/vt3/vn3
        - f v1//vn1 v2//vn2 v3//vn3
        """
        # ✅ التصحيح: إنشاء كائن افتراضي إذا لم يكن موجوداً
        if self.current_object is None:
            self._new_object("default")
        
        face = OBJFace(material_name=self.current_material)
        
        for i in range(1, len(parts)):
            token = parts[i]
            
            if '/' in token:
                # تنسيق مع مؤشرات إضافية
                indices = token.split('/')
                v_idx = int(indices[0]) if indices[0] else 0
                vt_idx = int(indices[1]) if len(indices) > 1 and indices[1] else 0
                vn_idx = int(indices[2]) if len(indices) > 2 and indices[2] else 0
                
                face.vertex_indices.append(v_idx)
                face.texture_indices.append(vt_idx)
                face.normal_indices.append(vn_idx)
            else:
                # تنسيق بسيط (فقط رؤوس)
                v_idx = int(token)
                face.vertex_indices.append(v_idx)
                # لا توجد مؤشرات نسيج أو طبيعيات
        
        if len(face.vertex_indices) >= 3:
            self.current_object.faces.append(face)
            
    def _load_mtl_file(self, mtl_filename: str, base_path: str, search_paths: List[str]):
        """تحميل ملف مواد MTL"""
        # البحث عن ملف MTL
        mtl_path = None
        for search_path in search_paths:
            candidate = os.path.join(search_path, mtl_filename)
            if os.path.exists(candidate):
                mtl_path = candidate
                break
            # جرب بدون مسار
            candidate = os.path.join(search_path, os.path.basename(mtl_filename))
            if os.path.exists(candidate):
                mtl_path = candidate
                break
        
        if not mtl_path:
            # جرب نسبة إلى ملف OBJ
            if base_path:
                candidate = os.path.join(os.path.dirname(base_path), mtl_filename)
                if os.path.exists(candidate):
                    mtl_path = candidate
        
        if not mtl_path:
            print(f"   Warning: MTL file not found: {mtl_filename}")
            return
        
        try:
            with open(mtl_path, 'r', encoding='utf-8', errors='ignore') as f:
                self._parse_mtl_content(f.read())
        except Exception as e:
            print(f"   Warning: Could not read MTL file {mtl_filename}: {e}")
    
    def _parse_mtl_content(self, content: str):
        """تحليل محتوى ملف MTL"""
        lines = content.strip().split('\n')
        current_material = None
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            parts = line.split()
            cmd = parts[0].lower()
            
            if cmd == 'newmtl':
                if len(parts) > 1:
                    current_material = OBJMaterial(name=parts[1])
                    self.materials[current_material.name] = current_material
            elif current_material:
                if cmd == 'ka':  # Ambient
                    vals = [float(p) for p in parts[1:]]
                    current_material.ambient = tuple(vals + [1.0, 1.0, 1.0])[:3]
                elif cmd == 'kd':  # Diffuse
                    vals = [float(p) for p in parts[1:]]
                    current_material.diffuse = tuple(vals + [1.0, 1.0, 1.0])[:3]
                elif cmd == 'ks':  # Specular
                    vals = [float(p) for p in parts[1:]]
                    current_material.specular = tuple(vals + [1.0, 1.0, 1.0])[:3]
                elif cmd == 'ke':  # Emissive
                    vals = [float(p) for p in parts[1:]]
                    current_material.emissive = tuple(vals + [1.0, 1.0, 1.0])[:3]
                elif cmd == 'ns':  # Shininess
                    current_material.shininess = float(parts[1])
                elif cmd == 'd' or cmd == 'tr':  # Transparency
                    current_material.transparency = float(parts[1])
                elif cmd == 'map_kd':  # Diffuse texture
                    current_material.diffuse_texture = ' '.join(parts[1:]).strip('"')
                elif cmd == 'map_bump' or cmd == 'bump':  # Bump texture
                    current_material.bump_texture = ' '.join(parts[1:]).strip('"')
                elif cmd == 'map_ks':  # Specular texture
                    current_material.specular_texture = ' '.join(parts[1:]).strip('"')
                elif cmd == 'map_d':  # Alpha texture
                    current_material.alpha_texture = ' '.join(parts[1:]).strip('"')
        
        print(f"   Loaded {len(self.materials)} materials from MTL")
    
    # ========== دوال التحويل إلى صيغ أخرى ==========
    
    def to_unified_vertices(self, apply_swizzle: bool = True, swizzle_mode: str = "XZY") -> np.ndarray:
        """
        تحويل جميع الوجوه إلى مصفوفة رؤوس موحدة مع طبيعيات و UVs
        
        Args:
            apply_swizzle: تطبيق تحويل المحاور
            swizzle_mode: نمط التحويل (XYZ, XZY, YXZ, etc.)
        """
        vertices = []
        faces = []
        vertex_counter = 0
        
        for obj in self.objects:
            for face in obj.faces:
                face_indices = []
                for i in range(len(face.vertex_indices)):
                    v_idx = face.vertex_indices[i] - 1  # OBJ تستخدم 1-indexed
                    
                    # الحصول على الرأس
                    if 0 <= v_idx < len(self._all_vertices):
                        v = self._all_vertices[v_idx]
                        px, py, pz = v.x, v.y, v.z
                    else:
                        px, py, pz = 0, 0, 0
                    
                    # الحصول على إحداثيات النسيج
                    vt_idx = face.texture_indices[i] - 1 if i < len(face.texture_indices) else -1
                    if 0 <= vt_idx < len(self._all_texture_vertices):
                        vt = self._all_texture_vertices[vt_idx]
                        u, vt_val = vt.u, vt.v
                    else:
                        u, vt_val = 0, 0
                    
                    # الحصول على الطبيعية
                    vn_idx = face.normal_indices[i] - 1 if i < len(face.normal_indices) else -1
                    if 0 <= vn_idx < len(self._all_normals):
                        n = self._all_normals[vn_idx]
                        nx, ny, nz = n.x, n.y, n.z
                    else:
                        nx, ny, nz = 0, 0, 0
                    
                    # تطبيق تحويل المحاور إذا لزم الأمر
                    if apply_swizzle:
                        mode = swizzle_mode.upper()
                        if mode == "XZY":
                            px, py, pz = px, pz, -py
                            nx, ny, nz = nx, nz, -ny
                        elif mode == "XYZ":
                            pass
                        elif mode == "YXZ":
                            px, py, pz = py, px, pz
                            nx, ny, nz = ny, nx, nz
                        elif mode == "ZXY":
                            px, py, pz = pz, px, py
                            nx, ny, nz = nz, nx, ny
                    
                    vertices.append({
                        'px': px, 'py': py, 'pz': pz,
                        'nx': nx, 'ny': ny, 'nz': nz,
                        'u': u, 'v': vt_val,
                        'material': face.material_name
                    })
                    face_indices.append(vertex_counter)
                    vertex_counter += 1
                
                if len(face_indices) >= 3:
                    faces.append(face_indices[:3])
        
        if not vertices:
            return np.array([]), np.array([])
        
        dtype_out = np.dtype([
            ("px", np.float32), ("py", np.float32), ("pz", np.float32),
            ("nx", np.float32), ("ny", np.float32), ("nz", np.float32),
            ("u", np.float32), ("v", np.float32),
            ("material", 'U64')
        ])
        
        verts_arr = np.array([(v['px'], v['py'], v['pz'],
                               v['nx'], v['ny'], v['nz'],
                               v['u'], v['v'],
                               v['material']) for v in vertices], dtype=dtype_out)
        
        faces_arr = np.array(faces)
        
        return verts_arr, faces_arr
    
    def to_smd(self) -> SMDExporter:
        """تحويل OBJ إلى SMD (StudioMDL)"""
        smd = SMDExporter()
        
        # إنشاء عظمة افتراضية واحدة
        smd.nodes = [SMDNode(id=0, name="root", parent_id=-1)]
        
        vertices, faces = self.to_unified_vertices(apply_swizzle=True)
        
        if len(vertices) == 0:
            return smd
        
        # تجميع الرؤوس حسب المادة
        material_vertices = {}
        for i, v in enumerate(vertices):
            mat = v['material']
            if mat not in material_vertices:
                material_vertices[mat] = []
            material_vertices[mat].append((i, v))
        
        # إنشاء مثلثات SMD لكل مادة
        face_idx = 0
        for mat, verts in material_vertices.items():
            # تجميع الرؤوس المتتالية
            vert_indices = [v[0] for v in verts]
            
            # البحث عن الوجوه التي تنتمي لهذه المادة
            material_faces = []
            for face in faces:
                if all(idx in vert_indices for idx in face):
                    material_faces.append(face)
            
            for face in material_faces:
                tri_vertices = []
                tri_normals = []
                tri_uvs = []
                tri_links = []
                
                for idx in face:
                    v = vertices[idx]
                    tri_vertices.append((v['px'], v['py'], v['pz']))
                    tri_normals.append((v['nx'], v['ny'], v['nz']))
                    tri_uvs.append((v['u'], 1.0 - v['v']))
                    tri_links.append([(0, 1.0)])
                
                triangle = SMDTriangle(
                    parent_bone=0,
                    vertices=tri_vertices,
                    normals=tri_normals,
                    uvs=tri_uvs,
                    link_count=1,
                    links=tri_links
                )
                smd.triangles.append(triangle)
                face_idx += 1
        
        print(f"   Converted OBJ to SMD: {len(smd.triangles)} triangles, {len(vertices)} vertices")
        return smd
    
    def to_mdl_format(self, model_name: str = "obj_model") -> StudioHeader:
        """
        تحويل OBJ إلى هيكل مشابه لـ MDL (بقدر الإمكان)
        """
        # إنشاء Buffer فارغ مؤقت (لن نستخدمه فعلياً)
        dummy_buffer = Buffer(b'')
        header = StudioHeader(dummy_buffer)
        
        vertices, faces = self.to_unified_vertices(apply_swizzle=True)
        
        if len(vertices) == 0:
            return header
        
        # تحويل الرؤوس إلى صيغة StudioVertex
        header.vertices = []
        for v in vertices:
            header.vertices.append(StudioVertex(v['px'], v['py'], v['pz']))
        
        # تحويل الطبيعيات
        header.normals = []
        for v in vertices:
            header.normals.append(StudioNormal(v['nx'], v['ny'], v['nz']))
        
        # تحويل الوجوه إلى مثلثات MDL
        header.triangles = []
        for face in faces:
            if len(face) == 3:
                tri = StudioTriangle(
                    vertindex=[face[0], face[1], face[2]],
                    normindex=[face[0], face[1], face[2]],
                    s=0, t=0
                )
                header.triangles.append(tri)
        
        # إنشاء هيكل عظمي افتراضي
        header.bones = [StudioBone(name="root", parent=-1, flags=0, 
                                    bonecontroller=[0]*6, value=[0]*6, scale=[1]*6)]
        
        # إنشاء BodyPart افتراضي
        header.bodyparts = [StudioBodyPart(name=model_name, nummodels=1, base=0, modelindex=0)]
        
        # إنشاء Model افتراضي
        header.models = [StudioModel(name=model_name, type=0, boundingradius=1.0,
                                      nummesh=1, meshindex=0,
                                      numverts=len(vertices), vertinfoindex=0, vertindex=0,
                                      numnorms=len(vertices), norminfoindex=0, normindex=0,
                                      numgroups=0, groupindex=0)]
        
        # إنشاء Mesh افتراضي
        header.meshes = [StudioMesh(numtris=len(header.triangles), triindex=0,
                                     skinref=0, numnorms=0, normindex=0)]
        
        print(f"   Converted OBJ to MDL-like format: {len(header.vertices)} vertices, {len(header.triangles)} triangles")
        return header
    
    def export_obj(self, output_path: str):
        """تصدير OBJ مع الحفاظ على البيانات الأصلية دون تغيير"""
        # بدلاً من استخدام to_unified_vertices، اكتب البيانات مباشرة من self._all_vertices
        
        base_name = os.path.splitext(output_path)[0]
        obj_path = f"{base_name}.obj"
        mtl_path = f"{base_name}.mtl"
        
        # كتابة ملف MTL
        with open(mtl_path, 'w', encoding='utf-8') as f:
            for name, mat in self.materials.items():
                f.write(f"newmtl {mat.name}\n")
                f.write(f"Ns {mat.shininess:.6f}\n")
                f.write(f"Ka {mat.ambient[0]:.6f} {mat.ambient[1]:.6f} {mat.ambient[2]:.6f}\n")
                f.write(f"Kd {mat.diffuse[0]:.6f} {mat.diffuse[1]:.6f} {mat.diffuse[2]:.6f}\n")
                f.write(f"Ks {mat.specular[0]:.6f} {mat.specular[1]:.6f} {mat.specular[2]:.6f}\n")
                if mat.diffuse_texture:
                    f.write(f"map_Kd {mat.diffuse_texture}\n")
                f.write("\n")
        
        # كتابة ملف OBJ مع الحفاظ على الترتيب الأصلي
        with open(obj_path, 'w', encoding='utf-8') as f:
            # كتابة مكتبة المواد
            if self.material_libs:
                for lib in self.material_libs:
                    f.write(f"mtllib {lib}\n")
            elif self.materials:
                f.write(f"mtllib {os.path.basename(mtl_path)}\n")
            
            # كتابة جميع الرؤوس بالترتيب الأصلي
            for v in self._all_vertices:
                f.write(f"v {v.x:.6f} {v.y:.6f} {v.z:.6f}\n")
            
            # كتابة إحداثيات النسيج بالترتيب الأصلي
            for vt in self._all_texture_vertices:
                if vt.w != 0.0:
                    f.write(f"vt {vt.u:.6f} {vt.v:.6f} {vt.w:.6f}\n")
                else:
                    f.write(f"vt {vt.u:.6f} {vt.v:.6f}\n")
            
            # كتابة الطبيعيات بالترتيب الأصلي
            for vn in self._all_normals:
                f.write(f"vn {vn.x:.6f} {vn.y:.6f} {vn.z:.6f}\n")
            
            # كتابة الكائنات والوجوه مع الحفاظ على المواد
            for obj in self.objects:
                if obj.name:
                    f.write(f"o {obj.name}\n")
                
                # كتابة usemtl إذا كانت المادة مختلفة
                current_mat = None
                for face in obj.faces:
                    if face.material_name != current_mat:
                        current_mat = face.material_name
                        f.write(f"usemtl {current_mat}\n")
                    
                    # كتابة الوجه مع الحفاظ على التنسيق الأصلي
                    f.write("f")
                    for i in range(len(face.vertex_indices)):
                        v_idx = face.vertex_indices[i]
                        vt_idx = face.texture_indices[i] if i < len(face.texture_indices) else 0
                        vn_idx = face.normal_indices[i] if i < len(face.normal_indices) else 0
                        
                        if vt_idx > 0 and vn_idx > 0:
                            f.write(f" {v_idx}/{vt_idx}/{vn_idx}")
                        elif vt_idx > 0:
                            f.write(f" {v_idx}/{vt_idx}")
                        elif vn_idx > 0:
                            f.write(f" {v_idx}//{vn_idx}")
                        else:
                            f.write(f" {v_idx}")
                    f.write("\n")
        
        print(f"   OBJ: {obj_path}")
        print(f"   MTL: {mtl_path}")
    
    def _get_original_vertices_for_gltf(self):
        """استخراج الرؤوس والوجوه من البيانات الأصلية مع الحفاظ على UVs"""
        vertices = []
        faces = []
        vertex_counter = 0
        vertex_map = {}  # لتجنب تكرار الرؤوس المتطابقة
        
        for obj in self.objects:
            for face in obj.faces:
                face_indices = []
                for i in range(len(face.vertex_indices)):
                    v_idx = face.vertex_indices[i] - 1
                    vt_idx = face.texture_indices[i] - 1 if i < len(face.texture_indices) else -1
                    vn_idx = face.normal_indices[i] - 1 if i < len(face.normal_indices) else -1
                    
                    # إنشاء مفتاح فريد للرأس (موقع + UV + طبيعية)
                    v = self._all_vertices[v_idx] if 0 <= v_idx < len(self._all_vertices) else OBJVertex(0,0,0)
                    vt = self._all_texture_vertices[vt_idx] if 0 <= vt_idx < len(self._all_texture_vertices) else OBJTextureVertex(0,0)
                    vn = self._all_normals[vn_idx] if 0 <= vn_idx < len(self._all_normals) else OBJNormal(0,0,0)
                    
                    key = (v_idx, vt_idx, vn_idx)
                    
                    if key not in vertex_map:
                        vertex_map[key] = vertex_counter
                        vertices.append({
                            'px': v.x, 'py': v.y, 'pz': v.z,
                            'nx': vn.x, 'ny': vn.y, 'nz': vn.z,
                            'u': vt.u, 'v': vt.v
                        })
                        vertex_counter += 1
                    
                    face_indices.append(vertex_map[key])
                
                if len(face_indices) == 3:
                    faces.append(face_indices)
                elif len(face_indices) > 3:
                    # تقسيم المضلع إلى مثلثات (تثليث بسيط)
                    for i in range(1, len(face_indices) - 1):
                        faces.append([face_indices[0], face_indices[i], face_indices[i+1]])
        
        return vertices, faces
        
    def export_gltf(self, output_path: str):
        """تصدير OBJ إلى glTF مع الحفاظ على البيانات الأصلية"""
        if not GLTF_AVAILABLE:
            print("   pygltflib not available, skipping glTF export")
            return
        
        # استخدم البيانات الأصلية بدلاً من تحويلها
        vertices, faces = self._get_original_vertices_for_gltf()
        
        if len(vertices) == 0:
            print("No vertices to export")
            return
        
        try:
            from pygltflib import GLTF2, Buffer, BufferView, Accessor, Mesh, Primitive, Attributes, Asset, Scene, Node
            
            gltf = GLTF2()
            gltf.asset = Asset(generator="OBJ Exporter (preserve UVs)", version="2.0")
            
            positions = []
            normals = []
            uvs = []
            
            for v in vertices:
                positions.extend([v['px'], v['py'], v['pz']])
                normals.extend([v['nx'], v['ny'], v['nz']])
                uvs.extend([v['u'], 1.0 - v['v']])  # Flip V for OpenGL
            
            binary_data = bytearray()
            
            # Positions
            pos_bytes = np.array(positions, dtype=np.float32).tobytes()
            pos_bv = BufferView(buffer=0, byteOffset=len(binary_data), byteLength=len(pos_bytes), target=34962)
            gltf.bufferViews.append(pos_bv)
            binary_data.extend(pos_bytes)
            
            pos_acc = Accessor(bufferView=len(gltf.bufferViews)-1, componentType=5126,
                               count=len(vertices), type="VEC3")
            gltf.accessors.append(pos_acc)
            
            # Normals
            norm_bytes = np.array(normals, dtype=np.float32).tobytes()
            norm_bv = BufferView(buffer=0, byteOffset=len(binary_data), byteLength=len(norm_bytes), target=34962)
            gltf.bufferViews.append(norm_bv)
            binary_data.extend(norm_bytes)
            
            norm_acc = Accessor(bufferView=len(gltf.bufferViews)-1, componentType=5126,
                                count=len(vertices), type="VEC3")
            gltf.accessors.append(norm_acc)
            
            # UVs
            uv_bytes = np.array(uvs, dtype=np.float32).tobytes()
            uv_bv = BufferView(buffer=0, byteOffset=len(binary_data), byteLength=len(uv_bytes), target=34962)
            gltf.bufferViews.append(uv_bv)
            binary_data.extend(uv_bytes)
            
            uv_acc = Accessor(bufferView=len(gltf.bufferViews)-1, componentType=5126,
                              count=len(vertices), type="VEC2")
            gltf.accessors.append(uv_acc)
            
            # Indices
            indices_list = []
            for face in faces:
                indices_list.extend([face[0], face[1], face[2]])
            
            indices_bytes = np.array(indices_list, dtype=np.uint32).tobytes()
            indices_bv = BufferView(buffer=0, byteOffset=len(binary_data), byteLength=len(indices_bytes), target=34963)
            gltf.bufferViews.append(indices_bv)
            binary_data.extend(indices_bytes)
            
            indices_acc = Accessor(bufferView=len(gltf.bufferViews)-1, componentType=5125,
                                   count=len(indices_list), type="SCALAR")
            gltf.accessors.append(indices_acc)
            
            base_filename = os.path.splitext(os.path.basename(output_path))[0]
            gltf.buffers.append(Buffer(byteLength=len(binary_data), uri=f"{base_filename}.bin"))
            
            attributes = Attributes(POSITION=0, NORMAL=1, TEXCOORD_0=2)
            primitive = Primitive(attributes=attributes, indices=len(gltf.accessors)-1, material=0)
            mesh = Mesh(primitives=[primitive])
            gltf.meshes.append(mesh)
            
            node = Node(mesh=0)
            gltf.nodes.append(node)
            scene = Scene(nodes=[0])
            gltf.scenes.append(scene)
            gltf.scene = 0
            
            gltf.save(f"{output_path}.gltf")
            with open(f"{os.path.splitext(output_path)[0]}.bin", 'wb') as f:
                f.write(binary_data)
            
            print(f"   glTF: {output_path}.gltf (UVs preserved)")
            
        except Exception as e:
            print(f"   Error exporting glTF: {e}")
            import traceback
            traceback.print_exc()
    
    def export_json(self, output_path: str):
        """تصدير بيانات OBJ إلى JSON"""
        vertices, faces = self.to_unified_vertices(apply_swizzle=False)
        
        data = {
            "format": "OBJ (Wavefront)",
            "objects": [],
            "materials": {name: {"diffuse": list(mat.diffuse), "diffuse_texture": mat.diffuse_texture}
                         for name, mat in self.materials.items()}
        }
        
        for obj in self.objects:
            obj_data = {
                "name": obj.name,
                "material": obj.material_name,
                "vertices_count": len(obj.vertices),
                "texture_vertices_count": len(obj.texture_vertices),
                "normals_count": len(obj.normals),
                "faces_count": len(obj.faces)
            }
            data["objects"].append(obj_data)
        
        data["total_vertices"] = len(self._all_vertices)
        data["total_texture_vertices"] = len(self._all_texture_vertices)
        data["total_normals"] = len(self._all_normals)
        data["total_faces"] = sum(len(obj.faces) for obj in self.objects)
        
        data = convert_to_json_serializable(data)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        print(f"   JSON: {output_path}")
    
    def export_txt(self, output_path: str):
        """تصدير معلومات OBJ إلى ملف نصي"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# OBJ (Wavefront) File Information\n\n")
            
            f.write("=== OBJECTS ===\n")
            for obj in self.objects:
                f.write(f"  {obj.name}: material={obj.material_name}, "
                       f"vertices={len(obj.vertices)}, UVs={len(obj.texture_vertices)}, "
                       f"normals={len(obj.normals)}, faces={len(obj.faces)}\n")
            
            f.write(f"\n=== MATERIALS ===\n")
            for name, mat in self.materials.items():
                f.write(f"  {name}: diffuse={mat.diffuse}, texture={mat.diffuse_texture}\n")
            
            f.write(f"\n=== STATISTICS ===\n")
            f.write(f"  Total vertices: {len(self._all_vertices)}\n")
            f.write(f"  Total texture vertices: {len(self._all_texture_vertices)}\n")
            f.write(f"  Total normals: {len(self._all_normals)}\n")
            f.write(f"  Total faces: {sum(len(obj.faces) for obj in self.objects)}\n")
            f.write(f"  Total objects: {len(self.objects)}\n")
            f.write(f"  Total materials: {len(self.materials)}\n")
        
        print(f"   TXT: {output_path}")
    
    def export_all(self, output_dir: str, base_name: str, export_formats: List[str] = None):
        """تصدير OBJ إلى جميع الصيغ المطلوبة مع الحفاظ على البيانات الأصلية"""
        if export_formats is None:
            export_formats = ["obj", "gltf", "json", "txt", "smd", "mdl"]
        
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        print(f"\nExporting OBJ to {output_dir}")
        print("-" * 50)
        
        if "obj" in export_formats:
            self.export_obj(os.path.join(output_dir, base_name))
        
        if "gltf" in export_formats:
            self.export_gltf(os.path.join(output_dir, base_name))
        
        if "json" in export_formats:
            self.export_json(os.path.join(output_dir, f"{base_name}.json"))
        
        if "txt" in export_formats:
            self.export_txt(os.path.join(output_dir, f"{base_name}_info.txt"))
        
        if "smd" in export_formats:
            # عند التصدير إلى SMD، استخدم البيانات المحولة (مع swizzle)
            vertices, faces = self.to_unified_vertices(apply_swizzle=True)
            if len(vertices) > 0:
                smd = self.to_smd()
                smd.export_all(output_dir, base_name, ["obj", "gltf", "json", "txt"])
        
        if "mdl" in export_formats:
            mdl = self.to_mdl_format(base_name)
            mdl.export_all(os.path.join(output_dir, f"{base_name}_mdl"), ["obj", "gltf", "json", "txt"])
        
        print("-" * 50)
        print("OBJ Export completed successfully!")


# ========== دوال مساعدة لمعالجة ملفات OBJ ==========

    def convert_obj_to_formats(input_obj: str, output_dir: str, export_formats: List[str] = None):
        """
        دالة مساعدة لتحويل ملف OBJ واحد إلى صيغ متعددة
        
        Args:
            input_obj: مسار ملف OBJ
            output_dir: مجلد الإخراج
            export_formats: قائمة الصيغ المطلوبة (obj, gltf, json, txt, smd, mdl)
        """
        if export_formats is None:
            export_formats = ["obj", "gltf", "json", "txt", "smd", "mdl"]
        
        if not os.path.exists(input_obj):
            print(f"Error: OBJ file not found: {input_obj}")
            return False
        
        try:
            print(f"\nReading OBJ file: {input_obj}")
            obj = OBJExporter.from_file(input_obj)
            
            base_name = os.path.splitext(os.path.basename(input_obj))[0]
            obj.export_all(output_dir, base_name, export_formats)
            
            return True
        except Exception as e:
            print(f"Error converting OBJ: {e}")
            import traceback
            traceback.print_exc()
            return False


    def batch_convert_obj(input_dir: str, output_dir: str, export_formats: List[str] = None):
        """
        تحويل جميع ملفات OBJ في مجلد إلى صيغ متعددة
        
        Args:
            input_dir: المجلد الذي يحتوي على ملفات OBJ
            output_dir: مجلد الإخراج
            export_formats: قائمة الصيغ المطلوبة
        """
        if export_formats is None:
            export_formats = ["obj", "gltf", "json", "txt", "smd", "mdl"]
        
        obj_files = []
        for ext in ['*.obj', '*.OBJ']:
            obj_files.extend(Path(input_dir).glob(ext))
        
        if not obj_files:
            print(f"No OBJ files found in '{input_dir}'")
            return False
        
        print(f"\nFound {len(obj_files)} OBJ file(s):")
        for f in obj_files:
            print(f"  - {f.name}")
        
        successful = 0
        failed = 0
        
        for obj_file in obj_files:
            print(f"\n{'='*60}")
            print(f"Processing: {obj_file.name}")
            print(f"{'='*60}")
            
            output_subdir = os.path.join(output_dir, obj_file.stem)
            
            if convert_obj_to_formats(str(obj_file), output_subdir, export_formats):
                successful += 1
                print(f"✓ Successfully processed: {obj_file.name}")
            else:
                failed += 1
                print(f"✗ Failed to process: {obj_file.name}")
        
        print("\n" + "="*60)
        print("OBJ BATCH CONVERSION COMPLETE")
        print("="*60)
        print(f"Total files found : {len(obj_files)}")
        print(f"Successfully processed : {successful}")
        print(f"Failed : {failed}")
        print(f"Output folder : {output_dir}")
        print("="*60)
        
        return successful > 0
                
def convert_obj_to_formats(input_obj: str, output_dir: str, export_formats: List[str] = None):
    """
    دالة مساعدة عامة لتحويل ملف OBJ واحد إلى صيغ متعددة.
    (ممرّ آمن للدالة المعرّفة داخل OBJExporter)
    """
    return OBJExporter.convert_obj_to_formats(input_obj, output_dir, export_formats)


def batch_convert_obj(input_dir: str, output_dir: str, export_formats: List[str] = None):
    """
    دالة مساعدة عامة لتحويل جميع ملفات OBJ في مجلد.
    (ممرّ آمن للدالة المعرّفة داخل OBJExporter)
    """
    return OBJExporter.batch_convert_obj(input_dir, output_dir, export_formats)


# ============================================================
# DirectX (.X) File Exporter - دعم كامل للعظام والحركة
# ============================================================

@dataclass
class DXFrame:
    """هيكل الإطار (Frame) في DirectX - يمثل عظمة"""
    name: str
    parent_name: str = ""
    parent_id: int = -1
    matrix: List[List[float]] = field(default_factory=lambda: [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]])
    position: Tuple[float, float, float] = (0, 0, 0)
    rotation: Tuple[float, float, float, float] = (0, 0, 0, 1)  # Quaternion
    scale: Tuple[float, float, float] = (1, 1, 1)
    mesh_name: str = ""
    vertices: List[Tuple[float, float, float]] = field(default_factory=list)
    normals: List[Tuple[float, float, float]] = field(default_factory=list)
    uvs: List[Tuple[float, float]] = field(default_factory=list)
    faces: List[Tuple[int, int, int]] = field(default_factory=list)
    materials: List[Dict] = field(default_factory=list)


@dataclass
class DXSkinWeight:
    """وزن عظمة (Skin Weight) في DirectX"""
    bone_name: str
    vertex_index: int
    weight: float


@dataclass
class DXAnimationKey:
    """إطار مفتاحي للحركة"""
    time: float
    matrix: List[List[float]]


@dataclass
class DXAnimation:
    """حركة كاملة في DirectX"""
    name: str
    frame_name: str
    keys: List[DXAnimationKey]


class DirectXExporter:
    """
    مصدر نماذج DirectX (.X) مع دعم كامل لـ:
    - العظام (Frame Hierarchy)
    - التزين (Skin Weights)
    - الرسوم المتحركة (Animations)
    - المواد والقوام (Materials & Textures)
    """
    
    def __init__(self):
        self.frames: List[DXFrame] = []
        self.skin_weights: List[DXSkinWeight] = []
        self.animations: List[DXAnimation] = []
        self.materials: List[Dict] = []
        self.textures: List[str] = []
        
    def fix_directx_bone_extraction():
        """تصحيح استخراج العظام من MEF لـ DirectXExporter"""
    
    def from_mef_model(self, model, debug_params: 'MefDebugParams' = None):
        """
        استخراج البيانات من نموذج MEF (IGI1/IGI2) - نسخة مصلحة
        """
        if debug_params is None:
            debug_params = MefDebugParams()
        
        # ========== 1. استخراج العظام ==========
        if hasattr(model, 'bones') and model.bones:
            for i, bone in enumerate(model.bones):
                # الحصول على اسم الأب
                parent_name = ""
                if hasattr(bone, 'parent_id') and bone.parent_id >= 0:
                    parent_name = model.bones[bone.parent_id].name if bone.parent_id < len(model.bones) else ""
                
                frame = DXFrame(
                    name=bone.name,
                    parent_id=bone.parent_id if hasattr(bone, 'parent_id') else -1,
                    parent_name=parent_name,
                    position=(bone.pos.x, bone.pos.y, bone.pos.z)
                )
                self.frames.append(frame)
            
            print(f"   🦴 Extracted {len(self.frames)} bones/frames")
        
        # ========== 2. استخراج بيانات التزين (Skin Weights) ==========
        if hasattr(model, 'render_mesh_data') and model.render_mesh_data:
            mesh_data = model.render_mesh_data
            
            if hasattr(mesh_data, 'vertices'):
                vertices = mesh_data.vertices
                
                # البحث عن الأوزان
                for i, v in enumerate(vertices):
                    bone_id = None
                    weight = None
                    
                    # محاولة استخراج bone_id بعدة طرق
                    if "bone_id" in v.dtype.names:
                        bid = v["bone_id"]
                        if isinstance(bid, np.ndarray):
                            bone_id = int(bid[0]) if len(bid) > 0 else None
                        else:
                            bone_id = int(bid) if bid is not None else None
                    
                    # محاولة استخراج weight
                    if "weight" in v.dtype.names:
                        w = v["weight"]
                        if isinstance(w, np.ndarray):
                            weight = float(w[0]) if len(w) > 0 else None
                        else:
                            weight = float(w) if w is not None else None
                    
                    if bone_id is not None and weight is not None and weight > 0:
                        if bone_id < len(model.bones):
                            self.skin_weights.append(DXSkinWeight(
                                bone_name=model.bones[bone_id].name,
                                vertex_index=i,
                                weight=weight
                            ))
                
                print(f"   🎨 Extracted {len(self.skin_weights)} skin weights")
        
        # ========== 3. استخراج الشبكة (Mesh) ==========
        self._extract_mesh_from_mef(model, debug_params)
        
        # ========== 4. استخراج المواد ==========
        self._extract_materials_from_mef(model)
        
        # ========== 5. استخراج الرسوم المتحركة ==========
        self._extract_animations_from_mef(model)
        
        return self
    
    def fix_directx_mdl_extraction():
        """تصحيح استخراج العظام من MDL لـ DirectXExporter"""
    
    def from_mdl_model(self, model):
        """
        استخراج البيانات من نموذج MDL (StudioHeader)
        """
        # ========== 1. استخراج العظام ==========
        if hasattr(model, 'bones') and model.bones:
            for i, bone in enumerate(model.bones):
                # استخدام parent وليس parent_id (التصحيح)
                parent_id = bone.parent if hasattr(bone, 'parent') else -1
                
                frame = DXFrame(
                    name=bone.name,
                    parent_id=parent_id,
                    parent_name=model.bones[parent_id].name if parent_id >= 0 and parent_id < len(model.bones) else "",
                    position=(bone.value[0] if len(bone.value) > 0 else 0,
                             bone.value[1] if len(bone.value) > 1 else 0,
                             bone.value[2] if len(bone.value) > 2 else 0)
                )
                self.frames.append(frame)
            
            # بناء التسلسل الهرمي
            for i, bone in enumerate(model.bones):
                parent_id = bone.parent if hasattr(bone, 'parent') else -1
                if parent_id >= 0 and parent_id < len(self.frames):
                    self.frames[i].parent_id = parent_id
            
            print(f"   🦴 Extracted {len(self.frames)} bones/frames from MDL")
        
        # ========== 2. استخراج الشبكة ==========
        self._extract_mesh_from_mdl(model)
        
        # ========== 3. استخراج المواد ==========
        if hasattr(model, 'header') and hasattr(model.header, 'numtextures') and model.header.numtextures > 0:
            for i in range(min(model.header.numtextures, 10)):
                self.materials.append({
                    "name": f"material_{i}",
                    "texture": f"texture_{i}.bmp"
                })
            print(f"   🎨 Extracted {len(self.materials)} materials from MDL")
        
        return self
    
    def _extract_mesh_from_mdl(self, model):
        """استخراج الشبكة من نموذج MDL"""
        if not hasattr(model, 'vertices') or not model.vertices:
            return
        
        # تحويل الرؤوس
        for i, v in enumerate(model.vertices):
            px, py, pz = v.x, v.z, v.y  # تحويل Y-up إلى Z-up
            self.frames[0].vertices.append((px, py, pz))
            self.frames[0].normals.append((0, 0, 0))
            self.frames[0].uvs.append((0, 0))
        
        # استخراج الوجوه
        for tri in model.triangles:
            if len(tri.vertindex) >= 3:
                self.frames[0].faces.append((tri.vertindex[0], tri.vertindex[1], tri.vertindex[2]))
        
        print(f"   📦 Extracted mesh from MDL: {len(self.frames[0].vertices)} vertices, {len(self.frames[0].faces)} faces")
    
    def from_smd_model(self, smd: SMDExporter):
        """
        استخراج البيانات من نموذج SMD
        """
        # ========== 1. استخراج العظام ==========
        for node in smd.nodes:
            frame = DXFrame(
                name=node.name,
                parent_id=node.parent_id,
                parent_name=self._find_parent_name(smd.nodes, node.parent_id),
                position=(0, 0, 0)
            )
            self.frames.append(frame)
        
        print(f"   🦴 Extracted {len(self.frames)} bones/frames from SMD")
        
        # ========== 2. استخراج الشبكة ==========
        self._extract_mesh_from_smd(smd)
        
        # ========== 3. استخراج المواد ==========
        if hasattr(smd, 'materials') and smd.materials:
            for mat_name in smd.materials:
                self.materials.append({
                    "name": mat_name,
                    "texture": mat_name
                })
            print(f"   🎨 Extracted {len(self.materials)} materials from SMD")
        
        return self
    
    def from_obj_model(self, obj: OBJExporter, base_name: str = "model"):
        """
        استخراج البيانات من نموذج OBJ
        """
        # ========== 1. إنشاء عظمة افتراضية ==========
        self.frames.append(DXFrame(name="root", parent_id=-1))
        
        # ========== 2. استخراج الشبكة ==========
        vertices, faces = obj.to_unified_vertices(apply_swizzle=True)
        
        for v in vertices:
            self.frames[0].vertices.append((v['px'], v['py'], v['pz']))
            self.frames[0].normals.append((v['nx'], v['ny'], v['nz']))
            self.frames[0].uvs.append((v['u'], v['v']))
        
        for face in faces:
            if len(face) == 3:
                self.frames[0].faces.append((face[0], face[1], face[2]))
        
        # ========== 3. استخراج المواد ==========
        for name, mat in obj.materials.items():
            self.materials.append({
                "name": name,
                "texture": mat.diffuse_texture,
                "ambient": mat.ambient,
                "diffuse": mat.diffuse,
                "specular": mat.specular
            })
        
        print(f"   📦 Extracted mesh: {len(self.frames[0].vertices)} vertices, {len(self.frames[0].faces)} faces")
        print(f"   🎨 Extracted {len(self.materials)} materials from OBJ")
        
        return self
    
    def fix_directx_mesh_extraction():
        """تصحيح استخراج الشبكة من MEF لـ DirectXExporter"""
    
    def _extract_mesh_from_mef(self, model, debug_params):
        """استخراج الشبكة من نموذج MEF - نسخة مصلحة"""
        if not hasattr(model, 'render_mesh_data') or not model.render_mesh_data:
            return
        
        mesh_data = model.render_mesh_data
        
        # تحويل الرؤوس
        if hasattr(mesh_data, 'vertices'):
            vertices = mesh_data.vertices
            
            for i, v in enumerate(vertices):
                # استخراج الموقع - التصحيح هنا
                if "pos" in v.dtype.names:
                    px, py, pz = float(v["pos"][0]), float(v["pos"][1]), float(v["pos"][2])
                elif "px" in v.dtype.names:
                    px, py, pz = float(v["px"]), float(v["py"]), float(v["pz"])
                else:
                    px, py, pz = 0.0, 0.0, 0.0
                
                # تطبيق swizzle
                px, py, pz = debug_params.swizzle(px, py, pz, debug_params.v_scale)
                
                # استخراج الطبيعية
                if "normal" in v.dtype.names:
                    normal = v["normal"]
                    nx, ny, nz = float(normal[0]), float(normal[1]), float(normal[2])
                elif "nx" in v.dtype.names:
                    nx, ny, nz = float(v["nx"]), float(v["ny"]), float(v["nz"])
                else:
                    nx, ny, nz = 0.0, 0.0, 0.0
                
                nx, ny, nz = debug_params.swizzle(nx, ny, nz, 1.0)
                
                # استخراج UV
                if "uv0" in v.dtype.names:
                    uv = v["uv0"]
                    u, vt = float(uv[0]), float(uv[1])
                elif "u" in v.dtype.names and "v" in v.dtype.names:
                    u, vt = float(v["u"]), float(v["v"])
                else:
                    u, vt = 0.0, 0.0
                
                # إضافة الرأس إلى الإطار المناسب
                frame_idx = 0
                if hasattr(v, 'bone_id') and self.frames:
                    bone_id_val = v["bone_id"]
                    if isinstance(bone_id_val, np.ndarray):
                        bone_id = int(bone_id_val[0]) if len(bone_id_val) > 0 else 0
                    else:
                        bone_id = int(bone_id_val)
                    if 0 <= bone_id < len(self.frames):
                        frame_idx = bone_id
                
                # التأكد من وجود الإطار
                while frame_idx >= len(self.frames):
                    self.frames.append(DXFrame(name=f"bone_{len(self.frames)}"))
                
                self.frames[frame_idx].vertices.append((px, py, pz))
                self.frames[frame_idx].normals.append((nx, ny, nz))
                self.frames[frame_idx].uvs.append((u, vt))
            
            # استخراج الوجوه
            if hasattr(mesh_data, 'faces'):
                for face in mesh_data.faces:
                    if len(face) >= 3:
                        self.frames[0].faces.append((int(face[0]), int(face[1]), int(face[2])))
            
            print(f"   📦 Extracted mesh: {len(self.frames[0].vertices)} vertices, {len(self.frames[0].faces)} faces")

    def _extract_mesh_from_smd(self, smd: SMDExporter):
        """استخراج الشبكة من نموذج SMD"""
        vertices, faces = smd.to_vertices_array()
        
        for i, v in enumerate(vertices):
            frame_idx = 0
            if hasattr(smd, 'nodes') and smd.nodes:
                bone_id = v['bone_id']
                if 0 <= bone_id < len(smd.nodes):
                    frame_idx = bone_id
            
            while frame_idx >= len(self.frames):
                self.frames.append(DXFrame(name=f"bone_{len(self.frames)}"))
            
            self.frames[frame_idx].vertices.append((v['px'], v['py'], v['pz']))
            self.frames[frame_idx].normals.append((v['nx'], v['ny'], v['nz']))
            self.frames[frame_idx].uvs.append((v['u'], v['v']))
        
        for face in faces:
            if len(face) == 3:
                self.frames[0].faces.append((face[0], face[1], face[2]))
        
        print(f"   📦 Extracted mesh from SMD: {len(self.frames[0].vertices)} vertices, {len(self.frames[0].faces)} faces")
    
    def _extract_materials_from_mef(self, model):
        """استخراج المواد من نموذج MEF"""
        if not hasattr(model, 'render_mesh_data') or not model.render_mesh_data:
            return
        
        if hasattr(model.render_mesh_data, 'primitives') and model.render_mesh_data.primitives:
            for i, prim in enumerate(model.render_mesh_data.primitives):
                texture_index = prim.diffuse_texture if hasattr(prim, 'diffuse_texture') else 0
                texture_name = get_texture_name(texture_index, "model", i, 
                                                getattr(model, 'texture_references', None))
                
                self.materials.append({
                    "name": f"material_{i}",
                    "texture": texture_name,
                    "transparency": prim.transparency if hasattr(prim, 'transparency') else 1.0,
                    "shininess": prim.shininess if hasattr(prim, 'shininess') else 10
                })
        
        print(f"   🎨 Extracted {len(self.materials)} materials from MEF")
    
    def _extract_animations_from_mef(self, model):
        """استخراج الرسوم المتحركة من نموذج MEF"""
        if not hasattr(model, 'txan_data') or not model.txan_data:
            return
        
        bone_count = len(self.frames) if self.frames else 0
        
        for txan_idx, txan in enumerate(model.txan_data):
            fields = txan.unknown_fields
            
            if len(fields) >= 28:
                frame_count = fields[1] if fields[1] < 1000 else 0
                duration_ms = fields[2] if fields[2] > 0 else 1000
                duration = duration_ms / 1000.0
                
                for frame in range(min(frame_count, 100)):
                    frame_time = frame / max(frame_count, 1) * duration
                    
                    for bone in range(min(bone_count, 10)):
                        idx = 4 + (frame * bone_count + bone) * 6
                        
                        if idx + 5 < len(fields):
                            # بناء مصفوفة التحويل من البيانات
                            matrix = [
                                [1, 0, 0, fields[idx] / 100.0],
                                [0, 1, 0, fields[idx+1] / 100.0],
                                [0, 0, 1, fields[idx+2] / 100.0],
                                [0, 0, 0, 1]
                            ]
                            
                            animation = DXAnimation(
                                name=f"anim_{txan_idx}",
                                frame_name=self.frames[bone].name if bone < len(self.frames) else f"bone_{bone}",
                                keys=[DXAnimationKey(time=frame_time, matrix=matrix)]
                            )
                            self.animations.append(animation)
        
        print(f"   🎬 Extracted {len(self.animations)} animations from TXAN")
    
    def _find_parent_name(self, nodes: List, parent_id: int) -> str:
        """العثور على اسم العظمة الأب"""
        for node in nodes:
            if node.id == parent_id:
                return node.name
        return ""
    
    def export_to_file(self, output_path: str):
        """تصدير كل البيانات إلى ملف DirectX (.X) - نسخة مصلحة"""
        with open(output_path, 'w', encoding='utf-8') as f:
            # رأس الملف
            f.write("xof 0303txt 0032\n")
            f.write("\n")
            
            # الرأس
            f.write("Header {\n")
            f.write("    1;\n")
            f.write("    0;\n")
            f.write("    1;\n")
            f.write("}\n")
            f.write("\n")
            
            # المواد
            self._write_materials(f)
            
            # الإطارات (العظام) - العقد الجذرية فقط
            root_frames = [f for f in self.frames if f.parent_id == -1]
            for frame in root_frames:
                self._write_frame_hierarchy(f, frame, 0)
            
            # أوزان التزين
            if self.skin_weights:
                self._write_skin_weights(f)
            
            # الرسوم المتحركة
            if self.animations:
                self._write_animations(f)

    def _write_frame_hierarchy(self, f, frame: DXFrame, level: int):
        """كتابة إطار وأبنائه بشكل هرمي"""
        indent = "    " * level
        
        f.write(f"{indent}Frame {frame.name} {{\n")
        
        # مصفوفة التحويل
        mat = frame.matrix
        f.write(f"{indent}    FrameTransformMatrix {{\n")
        f.write(f"{indent}        {mat[0][0]:.6f}, {mat[0][1]:.6f}, {mat[0][2]:.6f}, {mat[0][3]:.6f},\n")
        f.write(f"{indent}        {mat[1][0]:.6f}, {mat[1][1]:.6f}, {mat[1][2]:.6f}, {mat[1][3]:.6f},\n")
        f.write(f"{indent}        {mat[2][0]:.6f}, {mat[2][1]:.6f}, {mat[2][2]:.6f}, {mat[2][3]:.6f},\n")
        f.write(f"{indent}        {mat[3][0]:.6f}, {mat[3][1]:.6f}, {mat[3][2]:.6f}, {mat[3][3]:.6f};;\n")
        f.write(f"{indent}    }}\n")
        
        # الشبكة
        if frame.vertices and frame.faces:
            self._write_mesh(f, frame, id(frame), indent + "    ")
        
        # إطارات الأبناء
        children = [f for f in self.frames if f.parent_id == id(frame)]
        for child in children:
            self._write_frame_hierarchy(f, child, level + 1)
        
        f.write(f"{indent}}}\n")
        
    def _write_materials(self, f):
        """كتابة المواد إلى ملف DirectX"""
        if not self.materials:
            # مادة افتراضية
            f.write("Material default_material {\n")
            f.write("    0.8; 0.8; 0.8; 1.0;;\n")
            f.write("    10.0;\n")
            f.write("    0.0; 0.0; 0.0;;\n")
            f.write("    0.0; 0.0; 0.0;;\n")
            f.write("}\n")
            f.write("\n")
            return
        
        for i, mat in enumerate(self.materials):
            color = mat.get("diffuse", (1.0, 1.0, 1.0))
            shininess = mat.get("shininess", 10)
            texture = mat.get("texture", "")
            
            f.write(f"Material {mat['name']} {{\n")
            f.write(f"    {color[0]:.3f}; {color[1]:.3f}; {color[2]:.3f}; 1.0;;\n")
            f.write(f"    {shininess:.1f};\n")
            f.write(f"    0.0; 0.0; 0.0;;\n")
            f.write(f"    0.0; 0.0; 0.0;;\n")
            
            if texture:
                f.write(f"    TextureFilename {{\n")
                f.write(f"        \"{texture}\";\n")
                f.write(f"    }}\n")
            
            f.write("}\n")
            f.write("\n")
    
    def _write_frames(self, f):
        """كتابة الإطارات (العظام) إلى ملف DirectX"""
        for i, frame in enumerate(self.frames):
            f.write(f"Frame {frame.name} {{\n")
            
            # مصفوفة التحويل
            mat = frame.matrix
            f.write(f"    FrameTransformMatrix {{\n")
            f.write(f"        {mat[0][0]:.6f}, {mat[0][1]:.6f}, {mat[0][2]:.6f}, {mat[0][3]:.6f}, \n")
            f.write(f"        {mat[1][0]:.6f}, {mat[1][1]:.6f}, {mat[1][2]:.6f}, {mat[1][3]:.6f}, \n")
            f.write(f"        {mat[2][0]:.6f}, {mat[2][1]:.6f}, {mat[2][2]:.6f}, {mat[2][3]:.6f}, \n")
            f.write(f"        {mat[3][0]:.6f}, {mat[3][1]:.6f}, {mat[3][2]:.6f}, {mat[3][3]:.6f};;\n")
            f.write(f"    }}\n")
            
            # الشبكة (Mesh) إن وجدت
            if frame.vertices and frame.faces:
                self._write_mesh(f, frame, i)
            
            f.write("}\n")
            f.write("\n")
            
            # إطارات الأبناء
            children = [f for f in self.frames if f.parent_id == i]
            for child in children:
                self._write_child_frame(f, child)
    
    def _write_child_frame(self, f, frame: DXFrame, level: int = 1):
        """كتابة إطار ابن"""
        indent = "    " * level
        
        f.write(f"{indent}Frame {frame.name} {{\n")
        
        # مصفوفة التحويل
        mat = frame.matrix
        f.write(f"{indent}    FrameTransformMatrix {{\n")
        f.write(f"{indent}        {mat[0][0]:.6f}, {mat[0][1]:.6f}, {mat[0][2]:.6f}, {mat[0][3]:.6f}, \n")
        f.write(f"{indent}        {mat[1][0]:.6f}, {mat[1][1]:.6f}, {mat[1][2]:.6f}, {mat[1][3]:.6f}, \n")
        f.write(f"{indent}        {mat[2][0]:.6f}, {mat[2][1]:.6f}, {mat[2][2]:.6f}, {mat[2][3]:.6f}, \n")
        f.write(f"{indent}        {mat[3][0]:.6f}, {mat[3][1]:.6f}, {mat[3][2]:.6f}, {mat[3][3]:.6f};;\n")
        f.write(f"{indent}    }}\n")
        
        # الشبكة إن وجدت
        if frame.vertices and frame.faces:
            self._write_mesh(f, frame, id(frame), indent + "    ")
        
        f.write(f"{indent}}}\n")
    
    def _write_mesh(self, f, frame: DXFrame, mesh_id: int, indent: str = "    "):
        """كتابة الشبكة (Mesh) إلى ملف DirectX - نسخة مصلحة"""
        if not frame.vertices:
            return
        
        f.write(f"{indent}Mesh {frame.name}_mesh {{\n")
        
        # ========== الرؤوس ==========
        f.write(f"{indent}    {len(frame.vertices)};\n")
        for v in frame.vertices:
            # الصيغة الصحيحة: x; y; z;,
            f.write(f"{indent}    {v[0]:.6f}; {v[1]:.6f}; {v[2]:.6f};,\n")
        
        # ========== الوجوه ==========
        f.write(f"{indent}    {len(frame.faces)};\n")
        for face in frame.faces:
            # الصيغة الصحيحة: 3; a, b, c;;
            f.write(f"{indent}    3; {face[0]}, {face[1]}, {face[2]};;\n")
        
        # ========== الطبيعيات (Normals) ==========
        if frame.normals:
            f.write(f"{indent}    MeshNormals {{\n")
            f.write(f"{indent}        {len(frame.normals)};\n")
            for n in frame.normals:
                f.write(f"{indent}        {n[0]:.6f}; {n[1]:.6f}; {n[2]:.6f};,\n")
            f.write(f"{indent}        {len(frame.faces)};\n")
            for i, face in enumerate(frame.faces):
                # كل وجه له 3 طبيعيات (عادة نفس الفهرس)
                f.write(f"{indent}        3; {i}, {i}, {i};;\n")
            f.write(f"{indent}    }}\n")
        
        # ========== إحداثيات النسيج (UVs) ==========
        if frame.uvs:
            f.write(f"{indent}    MeshTextureCoords {{\n")
            f.write(f"{indent}        {len(frame.uvs)};\n")
            for uv in frame.uvs:
                f.write(f"{indent}        {uv[0]:.6f}; {1.0 - uv[1]:.6f};;\n")
            f.write(f"{indent}    }}\n")
        
        # ========== قائمة المواد (MeshMaterialList) ==========
        if self.materials:
            # حساب عدد الوجوه لكل مادة
            face_count = len(frame.faces)
            
            f.write(f"{indent}    MeshMaterialList {{\n")
            f.write(f"{indent}        {len(self.materials)};\n")  # عدد المواد
            f.write(f"{indent}        {face_count};\n")  # عدد الوجوه
            
            # توزيع الوجوه على المواد (هنا كل الوجوه للمادة 0 كمثال)
            for i in range(face_count):
                f.write(f"{indent}        {i % len(self.materials)},\n")
            
            # أسماء المواد
            for mat in self.materials:
                f.write(f"{indent}        {mat['name']};\n")
            
            f.write(f"{indent}    }}\n")
        
        f.write(f"{indent}}}\n")
    
    def _write_skin_weights(self, f):
        """كتابة أوزان التزين (Skin Weights) إلى ملف DirectX"""
        f.write("SkinWeights {\n")
        
        # تجميع الأوزان حسب العظمة
        weights_by_bone = {}
        for w in self.skin_weights:
            if w.bone_name not in weights_by_bone:
                weights_by_bone[w.bone_name] = []
            weights_by_bone[w.bone_name].append(w)
        
        for bone_name, weights in weights_by_bone.items():
            f.write(f"    \"{bone_name}\",\n")
            f.write(f"    {len(weights)};\n")
            
            # مؤشرات الرؤوس
            f.write("    ")
            for w in weights:
                f.write(f"{w.vertex_index}, ")
            f.write(";\n")
            
            # الأوزان
            f.write("    ")
            for w in weights:
                f.write(f"{w.weight:.6f}, ")
            f.write(";\n")
            
            # مصفوفة الإزاحة
            f.write("    1.0, 0.0, 0.0, 0.0,\n")
            f.write("    0.0, 1.0, 0.0, 0.0,\n")
            f.write("    0.0, 0.0, 1.0, 0.0,\n")
            f.write("    0.0, 0.0, 0.0, 1.0;;\n")
        
        f.write("}\n")
        f.write("\n")
    
    def _write_animations(self, f):
        """كتابة الرسوم المتحركة إلى ملف DirectX"""
        # تجميع الحركات حسب الإطار
        anims_by_frame = {}
        for anim in self.animations:
            if anim.frame_name not in anims_by_frame:
                anims_by_frame[anim.frame_name] = []
            anims_by_frame[anim.frame_name].append(anim)
        
        for frame_name, anims in anims_by_frame.items():
            f.write(f"Animation {{\n")
            f.write(f"    {{ {frame_name} }}\n")
            
            for anim in anims:
                f.write(f"    AnimationKey {{\n")
                f.write(f"        0;\n")  # 0 = Matrix key
                f.write(f"        {len(anim.keys)};\n")
                
                for key in anim.keys:
                    mat = key.matrix
                    f.write(f"        {key.time:.6f};")
                    f.write(f" {mat[0][0]:.6f}, {mat[0][1]:.6f}, {mat[0][2]:.6f}, {mat[0][3]:.6f},")
                    f.write(f" {mat[1][0]:.6f}, {mat[1][1]:.6f}, {mat[1][2]:.6f}, {mat[1][3]:.6f},")
                    f.write(f" {mat[2][0]:.6f}, {mat[2][1]:.6f}, {mat[2][2]:.6f}, {mat[2][3]:.6f},")
                    f.write(f" {mat[3][0]:.6f}, {mat[3][1]:.6f}, {mat[3][2]:.6f}, {mat[3][3]:.6f};;\n")
                
                f.write(f"    }}\n")
            
            f.write(f"    AnimationOptions {{\n")
            f.write(f"        0;\n")  # openclosed
            f.write(f"        0;\n")  # positionquality
            f.write(f"    }}\n")
            f.write(f"}}\n")
            f.write(f"\n")


# ============================================================
# دالة مساعدة لتصدير النموذج إلى DirectX
# ============================================================

def fix_export_to_directx():
    """تحديث export_to_directx لدعم جميع أنواع النماذج بشكل صحيح"""
    
    original_export_to_directx = export_to_directx
    
    def fixed_export_to_directx(model, output_path: str, model_type: str = "auto", debug_params: 'MefDebugParams' = None):
        """
        تصدير نموذج (MEF, SMD, OBJ, MDL) إلى ملف DirectX (.X) - نسخة مصلحة
        """
        print(f"   DEBUG: export_to_directx called with model_type={model_type}, output_path={output_path}")
        if debug_params is None:
            debug_params = MefDebugParams()
        
        exporter = DirectXExporter()
        
        # تحديد نوع النموذج
        if model_type == "auto":
            if hasattr(model, 'txan_data') or hasattr(model, 'render_mesh_data'):
                model_type = "igi2"
            elif hasattr(model, 'nodes') and hasattr(model, 'triangles'):
                model_type = "smd"
            elif hasattr(model, 'materials'):
                model_type = "obj"
            elif hasattr(model, 'bones'):
                model_type = "igi1"
            elif hasattr(model, 'header') and hasattr(model.header, 'numbones'):
                model_type = "mdl"
        
        # التصدير حسب النوع
        if model_type in ["igi1", "igi2"]:
            exporter.from_mef_model(model, debug_params)
        elif model_type == "smd":
            exporter.from_smd_model(model)
        elif model_type == "obj":
            exporter.from_obj_model(model)
        elif model_type == "mdl":
            # استخدام الدالة الجديدة لـ MDL
            if hasattr(exporter, 'from_mdl_model'):
                exporter.from_mdl_model(model)
            else:
                # طريقة بديلة
                for i, bone in enumerate(model.bones):
                    parent_id = bone.parent if hasattr(bone, 'parent') else -1
                    frame = DXFrame(
                        name=bone.name,
                        parent_id=parent_id,
                        position=(bone.value[0] if len(bone.value) > 0 else 0,
                                 bone.value[2] if len(bone.value) > 2 else 0,
                                 bone.value[1] if len(bone.value) > 1 else 0)
                    )
                    exporter.frames.append(frame)
                
                # استخراج الشبكة
                for v in model.vertices:
                    exporter.frames[0].vertices.append((v.x, v.z, v.y))
                for tri in model.triangles:
                    if len(tri.vertindex) >= 3:
                        exporter.frames[0].faces.append((tri.vertindex[0], tri.vertindex[1], tri.vertindex[2]))
                
                print(f"   📦 Extracted mesh from MDL: {len(exporter.frames[0].vertices)} vertices, {len(exporter.frames[0].faces)} faces")
                print(f"   🦴 Extracted {len(exporter.frames)} bones/frames from MDL")
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
        
        # حفظ الملف
        exporter.export_to_file(output_path)
        
        print(f"\n✅ Exported to DirectX: {output_path}")
        print(f"   📊 Frames: {len(exporter.frames)}")
        print(f"   🎨 Skin Weights: {len(exporter.skin_weights)}")
        print(f"   🎬 Animations: {len(exporter.animations)}")
        
        return True
    
    # استبدال الدالة
    globals()['export_to_directx'] = fixed_export_to_directx
    print("✅ Fixed export_to_directx function")


# ============================================================
# دوال إصلاح DirectX العامة (خارج الكلاس)
# ============================================================

def fix_directx_mesh_extraction():
    """تصحيح استخراج الشبكة من MEF لـ DirectXExporter"""
    
    def _extract_mesh_from_mef_fixed(self, model, debug_params):
        """استخراج الشبكة من نموذج MEF - نسخة مصلحة"""
        if not hasattr(model, 'render_mesh_data') or not model.render_mesh_data:
            return
        
        mesh_data = model.render_mesh_data
        
        if hasattr(mesh_data, 'vertices'):
            vertices = mesh_data.vertices
            
            for i, v in enumerate(vertices):
                # استخراج الموقع
                if "pos" in v.dtype.names:
                    px, py, pz = float(v["pos"][0]), float(v["pos"][1]), float(v["pos"][2])
                elif "px" in v.dtype.names:
                    px, py, pz = float(v["px"]), float(v["py"]), float(v["pz"])
                else:
                    px, py, pz = 0.0, 0.0, 0.0
                
                px, py, pz = debug_params.swizzle(px, py, pz, debug_params.v_scale)
                
                # استخراج الطبيعية
                if "normal" in v.dtype.names:
                    nx, ny, nz = float(v["normal"][0]), float(v["normal"][1]), float(v["normal"][2])
                elif "nx" in v.dtype.names:
                    nx, ny, nz = float(v["nx"]), float(v["ny"]), float(v["nz"])
                else:
                    nx, ny, nz = 0.0, 0.0, 0.0
                
                nx, ny, nz = debug_params.swizzle(nx, ny, nz, 1.0)
                
                # استخراج UV
                if "uv0" in v.dtype.names:
                    u, vt = float(v["uv0"][0]), float(v["uv0"][1])
                elif "u" in v.dtype.names and "v" in v.dtype.names:
                    u, vt = float(v["u"]), float(v["v"])
                else:
                    u, vt = 0.0, 0.0
                
                frame_idx = 0
                if hasattr(v, 'bone_id') and self.frames:
                    bone_id_val = v["bone_id"]
                    if isinstance(bone_id_val, np.ndarray):
                        bone_id = int(bone_id_val[0]) if len(bone_id_val) > 0 else 0
                    else:
                        bone_id = int(bone_id_val)
                    if 0 <= bone_id < len(self.frames):
                        frame_idx = bone_id
                
                while frame_idx >= len(self.frames):
                    self.frames.append(DXFrame(name=f"bone_{len(self.frames)}"))
                
                self.frames[frame_idx].vertices.append((px, py, pz))
                self.frames[frame_idx].normals.append((nx, ny, nz))
                self.frames[frame_idx].uvs.append((u, vt))
            
            if hasattr(mesh_data, 'faces'):
                for face in mesh_data.faces:
                    if len(face) >= 3:
                        self.frames[0].faces.append((int(face[0]), int(face[1]), int(face[2])))
            
            print(f"   📦 Extracted mesh: {len(self.frames[0].vertices)} vertices, {len(self.frames[0].faces)} faces")
    
    # تطبيق الدالة المُصححة
    DirectXExporter._extract_mesh_from_mef = _extract_mesh_from_mef_fixed
    print("✅ Fixed mesh extraction for DirectXExporter")


def fix_directx_bone_extraction():
    """تصحيح استخراج العظام من MEF لـ DirectXExporter"""
    
    def from_mef_model_fixed(self, model, debug_params: 'MefDebugParams' = None):
        if debug_params is None:
            debug_params = MefDebugParams()
        
        if hasattr(model, 'bones') and model.bones:
            for i, bone in enumerate(model.bones):
                parent_name = ""
                if hasattr(bone, 'parent_id') and bone.parent_id >= 0:
                    parent_name = model.bones[bone.parent_id].name if bone.parent_id < len(model.bones) else ""
                
                frame = DXFrame(
                    name=bone.name,
                    parent_id=bone.parent_id if hasattr(bone, 'parent_id') else -1,
                    parent_name=parent_name,
                    position=(bone.pos.x, bone.pos.y, bone.pos.z)
                )
                self.frames.append(frame)
            
            print(f"   🦴 Extracted {len(self.frames)} bones/frames")
        
        if hasattr(model, 'render_mesh_data') and model.render_mesh_data:
            mesh_data = model.render_mesh_data
            
            if hasattr(mesh_data, 'vertices'):
                vertices = mesh_data.vertices
                
                for i, v in enumerate(vertices):
                    bone_id = None
                    weight = None
                    
                    if "bone_id" in v.dtype.names:
                        bid = v["bone_id"]
                        if isinstance(bid, np.ndarray):
                            bone_id = int(bid[0]) if len(bid) > 0 else None
                        else:
                            bone_id = int(bid) if bid is not None else None
                    
                    if "weight" in v.dtype.names:
                        w = v["weight"]
                        if isinstance(w, np.ndarray):
                            weight = float(w[0]) if len(w) > 0 else None
                        else:
                            weight = float(w) if w is not None else None
                    
                    if bone_id is not None and weight is not None and weight > 0:
                        if bone_id < len(model.bones):
                            self.skin_weights.append(DXSkinWeight(
                                bone_name=model.bones[bone_id].name,
                                vertex_index=i,
                                weight=weight
                            ))
                
                print(f"   🎨 Extracted {len(self.skin_weights)} skin weights")
        
        self._extract_mesh_from_mef(model, debug_params)
        self._extract_materials_from_mef(model)
        self._extract_animations_from_mef(model)
        
        return self
    
    DirectXExporter.from_mef_model = from_mef_model_fixed
    print("✅ Fixed bone extraction for DirectXExporter")


def fix_directx_mdl_extraction():
    """تصحيح استخراج العظام من MDL لـ DirectXExporter"""
    
    def from_mdl_model_fixed(self, model):
        if hasattr(model, 'bones') and model.bones:
            for i, bone in enumerate(model.bones):
                parent_id = bone.parent if hasattr(bone, 'parent') else -1
                
                frame = DXFrame(
                    name=bone.name,
                    parent_id=parent_id,
                    parent_name=model.bones[parent_id].name if parent_id >= 0 and parent_id < len(model.bones) else "",
                    position=(bone.value[0] if len(bone.value) > 0 else 0,
                             bone.value[1] if len(bone.value) > 1 else 0,
                             bone.value[2] if len(bone.value) > 2 else 0)
                )
                self.frames.append(frame)
            
            for i, bone in enumerate(model.bones):
                parent_id = bone.parent if hasattr(bone, 'parent') else -1
                if parent_id >= 0 and parent_id < len(self.frames):
                    self.frames[i].parent_id = parent_id
            
            print(f"   🦴 Extracted {len(self.frames)} bones/frames from MDL")
        
        if hasattr(model, 'header') and hasattr(model.header, 'numtextures') and model.header.numtextures > 0:
            for i in range(min(model.header.numtextures, 10)):
                self.materials.append({
                    "name": f"material_{i}",
                    "texture": f"texture_{i}.bmp"
                })
            print(f"   🎨 Extracted {len(self.materials)} materials from MDL")
        
        return self
    
    def _extract_mesh_from_mdl_fixed(self, model):
        if not hasattr(model, 'vertices') or not model.vertices:
            return
        
        for i, v in enumerate(model.vertices):
            px, py, pz = v.x, v.z, v.y
            self.frames[0].vertices.append((px, py, pz))
            self.frames[0].normals.append((0, 0, 0))
            self.frames[0].uvs.append((0, 0))
        
        for tri in model.triangles:
            if len(tri.vertindex) >= 3:
                self.frames[0].faces.append((tri.vertindex[0], tri.vertindex[1], tri.vertindex[2]))
        
        print(f"   📦 Extracted mesh from MDL: {len(self.frames[0].vertices)} vertices, {len(self.frames[0].faces)} faces")
    
    DirectXExporter.from_mdl_model = from_mdl_model_fixed
    DirectXExporter._extract_mesh_from_mdl = _extract_mesh_from_mdl_fixed
    print("✅ Added MDL support to DirectXExporter")


def fix_export_to_directx():
    """تحديث export_to_directx لدعم جميع أنواع النماذج بشكل صحيح"""
    
    def fixed_export_to_directx(model, output_path: str, model_type: str = "auto", debug_params: 'MefDebugParams' = None):
        print(f"   DEBUG: export_to_directx called with model_type={model_type}, output_path={output_path}")
        if debug_params is None:
            debug_params = MefDebugParams()
        
        exporter = DirectXExporter()
        
        if model_type == "auto":
            if hasattr(model, 'txan_data') or hasattr(model, 'render_mesh_data'):
                model_type = "igi2"
            elif hasattr(model, 'nodes') and hasattr(model, 'triangles'):
                model_type = "smd"
            elif hasattr(model, 'materials'):
                model_type = "obj"
            elif hasattr(model, 'bones'):
                model_type = "igi1"
            elif hasattr(model, 'header') and hasattr(model.header, 'numbones'):
                model_type = "mdl"
        
        if model_type in ["igi1", "igi2"]:
            exporter.from_mef_model(model, debug_params)
        elif model_type == "smd":
            exporter.from_smd_model(model)
        elif model_type == "obj":
            exporter.from_obj_model(model)
        elif model_type == "mdl":
            if hasattr(exporter, 'from_mdl_model'):
                exporter.from_mdl_model(model)
            else:
                for i, bone in enumerate(model.bones):
                    parent_id = bone.parent if hasattr(bone, 'parent') else -1
                    frame = DXFrame(
                        name=bone.name,
                        parent_id=parent_id,
                        position=(bone.value[0] if len(bone.value) > 0 else 0,
                                 bone.value[2] if len(bone.value) > 2 else 0,
                                 bone.value[1] if len(bone.value) > 1 else 0)
                    )
                    exporter.frames.append(frame)
                
                for v in model.vertices:
                    exporter.frames[0].vertices.append((v.x, v.z, v.y))
                for tri in model.triangles:
                    if len(tri.vertindex) >= 3:
                        exporter.frames[0].faces.append((tri.vertindex[0], tri.vertindex[1], tri.vertindex[2]))
                
                print(f"   📦 Extracted mesh from MDL: {len(exporter.frames[0].vertices)} vertices, {len(exporter.frames[0].faces)} faces")
                print(f"   🦴 Extracted {len(exporter.frames)} bones/frames from MDL")
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
        
        exporter.export_to_file(output_path)
        
        print(f"\n✅ Exported to DirectX: {output_path}")
        print(f"   📊 Frames: {len(exporter.frames)}")
        print(f"   🎨 Skin Weights: {len(exporter.skin_weights)}")
        print(f"   🎬 Animations: {len(exporter.animations)}")
        
        return True
    
    globals()['export_to_directx'] = fixed_export_to_directx
    print("✅ Fixed export_to_directx function")
    
    
# ============================================================
# تطبيق جميع الإصلاحات
# ============================================================

def apply_all_directx_fixes():
    """تطبيق جميع إصلاحات DirectX"""
    print("\n🔧 Applying DirectX fixes...")
    fix_directx_mesh_extraction()
    fix_directx_bone_extraction()
    fix_directx_mdl_extraction()
    fix_export_to_directx()
    print("✅ All DirectX fixes applied successfully")


# تنفيذ الإصلاحات
apply_all_directx_fixes()


# ============================================================
# إضافة دعم DirectX (.X) إلى السكربت الرئيسي
# ============================================================

def convert_to_directx(input_path: str, output_path: str = None, 
                       debug_params: 'MefDebugParams' = None) -> bool:
    """
    تحويل ملف MEF أو SMD أو OBJ إلى DirectX (.X)
    
    Args:
        input_path: مسار ملف الإدخال
        output_path: مسار ملف الإخراج (اختياري)
        debug_params: معاملات التصحيح
    
    Returns:
        True إذا نجح التحويل، False إذا فشل
    """
    if debug_params is None:
        debug_params = MefDebugParams()
    
    if output_path is None:
        output_path = Path(input_path).with_suffix('.x')
    
    try:
        with open(input_path, "rb") as f:
            data = f.read()
        
        buffer = Buffer(data)
        file_type = detect_file_type(buffer, input_path)
        
        if file_type == "MEF":
            version = detect_mef_version(buffer)
            if version == "IGI2":
                model = MefModelIGI2(buffer, export_mode="multi")
            else:
                model = MefModelIGI1(buffer, export_mode="multi")
            
            export_to_directx(model, str(output_path), 
                            "igi2" if version == "IGI2" else "igi1", 
                            debug_params)
        
        elif file_type == "SMD":
            with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            model = SMDExporter.from_string(content)
            
            export_to_directx(model, str(output_path), "smd", debug_params)
        
        elif file_type == "OBJ":
            model = OBJExporter.from_file(input_path)
            
            export_to_directx(model, str(output_path), "obj", debug_params)
        
        else:
            print(f"❌ Unsupported file type: {file_type}")
            return False
        
        print(f"✅ Successfully converted to DirectX: {output_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error converting to DirectX: {e}")
        import traceback
        traceback.print_exc()
        return False


def batch_convert_to_directx(input_dir: str, output_dir: str = None,
                             debug_params: 'MefDebugParams' = None) -> dict:
    """
    تحويل جميع ملفات MEF و SMD و OBJ في مجلد إلى DirectX (.X)
    
    Args:
        input_dir: مجلد الإدخال
        output_dir: مجلد الإخراج (اختياري)
        debug_params: معاملات التصحيح
    
    Returns:
        قاموس بنتائج التحويل
    """
    if debug_params is None:
        debug_params = MefDebugParams()
    
    if output_dir is None:
        output_dir = input_dir + "_directx"
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # البحث عن الملفات
    extensions = ['*.mef', '*.MEF', '*.mdl', '*.MDL', '*.smd', '*.SMD', '*.obj', '*.OBJ']
    files = []
    for ext in extensions:
        files.extend(Path(input_dir).glob(ext))
    
    if not files:
        print(f"No supported files found in {input_dir}")
        return {"total": 0, "successful": 0, "failed": 0}
    
    print(f"\n📁 Found {len(files)} files to convert to DirectX")
    print("=" * 60)
    
    successful = 0
    failed = 0
    
    for file_path in files:
        output_path = Path(output_dir) / f"{file_path.stem}.x"
        
        print(f"\n🔄 Converting: {file_path.name}")
        
        if convert_to_directx(str(file_path), str(output_path), debug_params):
            successful += 1
            print(f"   ✅ Output: {output_path}")
        else:
            failed += 1
    
    print("\n" + "=" * 60)
    print("📊 DIRECTX BATCH CONVERSION REPORT")
    print("=" * 60)
    print(f"   Total files    : {len(files)}")
    print(f"   Successful     : {successful}")
    print(f"   Failed         : {failed}")
    print(f"   Output folder  : {output_dir}")
    print("=" * 60)
    
    return {"total": len(files), "successful": successful, "failed": failed}

    
# ------------------------------------------------------------
# كلاس MdlModel (الفئة الرئيسية لنماذج Half-Life)
# ------------------------------------------------------------
class MdlModel:
    def __init__(self, buffer: Buffer):
        self.buffer = buffer
        self.header: MDLHeader = None
        self.bones: List[MDLBone] = []
        self.textures: List[MDLTexture] = []
        self.bodyparts: List[MDLBodyPart] = []
        self.models: List[MDLModel] = []
        self.meshes: List[MDLMesh] = []
        self.vertices: List[MDLVertex] = []
        self.triangles: List[MDLTriangle] = []
        
        self._parse_header()
        self._parse_bones()
        self._parse_textures()
        self._parse_bodyparts()
        self._parse_vertices_and_triangles()
        
    def _parse_header(self):
        """قراءة رأس الملف"""
        self.header = MDLHeader.from_buffer(self.buffer)
        print(f"MDL Header: {self.header.name}")
        print(f"  Version: {self.header.version}")
        print(f"  Bones: {self.header.num_bones}")
        print(f"  Bodyparts: {self.header.num_bodyparts}")
        print(f"  Textures: {self.header.num_textures}")
        print(f"  Sequences: {self.header.num_seq}")
        
    def _parse_bones(self):
        """قراءة العظام"""
        if self.header.num_bones == 0 or self.header.bone_offset == 0:
            return
        
        self.buffer.offset = self.header.bone_offset
        for i in range(self.header.num_bones):
            bone = MDLBone.from_buffer(self.buffer)
            self.bones.append(bone)
        print(f"  Parsed {len(self.bones)} bones")
        
    def _parse_textures(self):
        """قراءة القوام"""
        if self.header.num_textures == 0 or self.header.texture_offset == 0:
            return
        
        self.buffer.offset = self.header.texture_offset
        for i in range(self.header.num_textures):
            texture = MDLTexture.from_buffer(self.buffer)
            self.textures.append(texture)
        print(f"  Parsed {len(self.textures)} textures")
        
    def _parse_bodyparts(self):
        """قراءة أجزاء الجسم والنماذج والشبكات"""
        if self.header.num_bodyparts == 0 or self.header.bodypart_offset == 0:
            return
        
        self.buffer.offset = self.header.bodypart_offset
        
        for bp_idx in range(self.header.num_bodyparts):
            bodypart = MDLBodyPart.from_buffer(self.buffer)
            self.bodyparts.append(bodypart)
            
            # قراءة النماذج في هذا الجزء
            if bodypart.num_models > 0:
                current_offset = self.buffer.offset
                self.buffer.offset = bodypart.model_offset
                
                for m_idx in range(bodypart.num_models):
                    model = MDLModel.from_buffer(self.buffer)
                    self.models.append(model)
                    
                    # قراءة الشبكات في هذا النموذج
                    if model.num_meshes > 0:
                        mesh_offset_backup = self.buffer.offset
                        self.buffer.offset = model.mesh_offset
                        
                        for mesh_idx in range(model.num_meshes):
                            mesh = MDLMesh.from_buffer(self.buffer)
                            self.meshes.append(mesh)
                        
                        self.buffer.offset = mesh_offset_backup
                
                self.buffer.offset = current_offset
        
        print(f"  Parsed {len(self.bodyparts)} bodyparts, {len(self.models)} models, {len(self.meshes)} meshes")
        
    def _parse_vertices_and_triangles(self):
        """قراءة الرؤوس والمثلثات من جميع النماذج"""
        for model in self.models:
            if model.num_verts == 0:
                continue
            
            # قراءة الرؤوس
            self.buffer.offset = model.vert_offset
            for v_idx in range(model.num_verts):
                vertex = MDLVertex.from_buffer(self.buffer)
                self.vertices.append(vertex)
            
            # قراءة المثلثات
            for mesh in self.meshes:
                if mesh.num_tris == 0:
                    continue
                
                self.buffer.offset = mesh.tri_offset
                for t_idx in range(mesh.num_tris):
                    tri = MDLTriangle.from_buffer(self.buffer)
                    self.triangles.append(tri)
        
        print(f"  Parsed {len(self.vertices)} vertices, {len(self.triangles)} triangles")
    
    # ========== دوال التصدير ==========
    def ensure_dir(self, path):
        Path(path).mkdir(parents=True, exist_ok=True)
    
    def export_obj(self, out_dir, base_name, export_formats=None):
        """تصدير النموذج إلى OBJ"""
        if export_formats is None:
            export_formats = ["obj"]
        
        if len(self.vertices) == 0 or len(self.triangles) == 0:
            print("No vertices or triangles to export")
            return
        
        # تحويل الرؤوس إلى صيغة موحدة
        dtype_out = np.dtype([
            ("px", np.float32), ("py", np.float32), ("pz", np.float32),
            ("nx", np.float32), ("ny", np.float32), ("nz", np.float32),
            ("u", np.float32), ("v", np.float32)
        ])
        
        # تطبيق تحويل المحاور (Half-Life تستخدم Y-up، نحول إلى Z-up)
        verts_arr = []
        for v in self.vertices:
            # تحويل: Y-up -> Z-up (نبدل Y و Z)
            verts_arr.append((
                v.x,      # X
                v.z,      # Z (كان Y)
                v.y,      # Y (كان Z)
                0, 0, 0,  # Normals (مؤقتة)
                v.u, 1.0 - v.v  # UV (نقلب V)
            ))
        
        vertices_transformed = np.array(verts_arr, dtype=dtype_out)
        
        # تجميع المثلثات
        faces_arr = []
        for tri in self.triangles:
            faces_arr.append([tri.indices[0], tri.indices[1], tri.indices[2]])
        faces_array = np.array(faces_arr)
        
        if "obj" in export_formats:
            obj_path = os.path.join(out_dir, f"{base_name}.obj")
            mtl_path = os.path.join(out_dir, f"{base_name}.mtl")
            
            # كتابة ملف MTL
            with open(mtl_path, "w", encoding="utf-8") as f:
                f.write(f"newmtl {base_name}_material\n")
                f.write("Ns 10.0000\n")
                f.write("Ka 1.0000 1.0000 1.0000\n")
                f.write("Kd 1.0000 1.0000 1.0000\n")
                f.write("Ks 0.0000 0.0000 0.0000\n")
                if self.textures:
                    tex_name = self.textures[0].name
                    if not tex_name.endswith('.bmp') and not tex_name.endswith('.png'):
                        tex_name += ".bmp"
                    f.write(f"map_Kd {tex_name}\n")
            
            # كتابة ملف OBJ
            with open(obj_path, "w", encoding="utf-8") as f:
                f.write(f"mtllib {base_name}.mtl\n")
                f.write(f"o {base_name}\n")
                
                # كتابة الرؤوس
                for v in vertices_transformed:
                    f.write(f"v {v['px']:.6f} {v['py']:.6f} {v['pz']:.6f}\n")
                
                # كتابة إحداثيات النسيج
                for v in vertices_transformed:
                    f.write(f"vt {v['u']:.6f} {v['v']:.6f}\n")
                
                f.write(f"usemtl {base_name}_material\n")
                
                # كتابة الوجوه
                for face in faces_array:
                    a, b, c = face[0] + 1, face[1] + 1, face[2] + 1
                    f.write(f"f {a}/{a} {b}/{b} {c}/{c}\n")
            
            print(f"   OBJ: {obj_path}")
            print(f"   MTL: {mtl_path}")
        
        # تصدير glTF
        if "gltf" in export_formats and GLTF_AVAILABLE:
            self._export_gltf(out_dir, base_name, vertices_transformed, faces_array)
        
        # تصدير DAE
        if "dae" in export_formats:
            self._export_collada(out_dir, base_name, vertices_transformed, faces_array)
        
        # تصدير JSON
        if "json" in export_formats:
            self._export_json(out_dir, base_name)
        
        # تصدير TXT
        if "txt" in export_formats:
            self._export_txt(out_dir, base_name)
    
    def _export_gltf(self, out_dir, base_name, vertices, faces):
        """تصدير إلى glTF"""
        try:
            from pygltflib import GLTF2, Buffer, BufferView, Accessor, Mesh, Primitive, Attributes, Asset, Scene, Node
            
            gltf = GLTF2()
            gltf.asset = Asset(generator="HL MDL Exporter", version="2.0")
            
            positions = []
            uvs = []
            for v in vertices:
                positions.extend([v['px'], v['py'], v['pz']])
                uvs.extend([v['u'], v['v']])
            
            binary_data = bytearray()
            
            # Positions
            pos_bytes = np.array(positions, dtype=np.float32).tobytes()
            pos_bv = BufferView(buffer=0, byteOffset=len(binary_data), byteLength=len(pos_bytes), target=34962)
            gltf.bufferViews.append(pos_bv)
            binary_data.extend(pos_bytes)
            
            pos_acc = Accessor(bufferView=len(gltf.bufferViews)-1, componentType=5126,
                               count=len(vertices), type="VEC3")
            gltf.accessors.append(pos_acc)
            
            # UVs
            uv_bytes = np.array(uvs, dtype=np.float32).tobytes()
            uv_bv = BufferView(buffer=0, byteOffset=len(binary_data), byteLength=len(uv_bytes), target=34962)
            gltf.bufferViews.append(uv_bv)
            binary_data.extend(uv_bytes)
            
            uv_acc = Accessor(bufferView=len(gltf.bufferViews)-1, componentType=5126,
                              count=len(vertices), type="VEC2")
            gltf.accessors.append(uv_acc)
            
            # Indices
            indices_list = []
            for face in faces:
                indices_list.extend([face[0], face[1], face[2]])
            
            indices_bytes = np.array(indices_list, dtype=np.uint32).tobytes()
            indices_bv = BufferView(buffer=0, byteOffset=len(binary_data), byteLength=len(indices_bytes), target=34963)
            gltf.bufferViews.append(indices_bv)
            binary_data.extend(indices_bytes)
            
            indices_acc = Accessor(bufferView=len(gltf.bufferViews)-1, componentType=5125,
                                   count=len(indices_list), type="SCALAR")
            gltf.accessors.append(indices_acc)
            
            gltf.buffers.append(Buffer(byteLength=len(binary_data), uri=f"{base_name}.bin"))
            
            attributes = Attributes(POSITION=0, TEXCOORD_0=1)
            primitive = Primitive(attributes=attributes, indices=len(gltf.accessors)-1, material=0)
            mesh = Mesh(primitives=[primitive])
            gltf.meshes.append(mesh)
            
            node = Node(mesh=0)
            gltf.nodes.append(node)
            scene = Scene(nodes=[0])
            gltf.scenes.append(scene)
            gltf.scene = 0
            
            gltf.save(f"{out_dir}/{base_name}.gltf")
            
            with open(f"{out_dir}/{base_name}.bin", 'wb') as f:
                f.write(binary_data)
            
            print(f"   glTF: {out_dir}/{base_name}.gltf")
            print(f"   glTF binary: {out_dir}/{base_name}.bin")
            
        except Exception as e:
            print(f"   Error exporting glTF: {e}")
    
    def _export_collada(self, out_dir, base_name, vertices, faces):
        """تصدير إلى Collada DAE"""
        try:
            root = ET.Element("COLLADA", xmlns="http://www.collada.org/2005/11/COLLADASchema", version="1.4.1")
            
            asset = ET.SubElement(root, "asset")
            contrib = ET.SubElement(asset, "contributor")
            ET.SubElement(contrib, "authoring_tool").text = "HL MDL Exporter"
            ET.SubElement(asset, "created").text = datetime.now().isoformat()
            ET.SubElement(asset, "modified").text = datetime.now().isoformat()
            ET.SubElement(asset, "unit", name="meter", meter="1")
            ET.SubElement(asset, "up_axis").text = "Y_UP"
            
            lib_geo = ET.SubElement(root, "library_geometries")
            geometry = ET.SubElement(lib_geo, "geometry", id=f"{base_name}-mesh", name=base_name)
            mesh = ET.SubElement(geometry, "mesh")
            
            source_pos = ET.SubElement(mesh, "source", id=f"{base_name}-mesh-positions")
            float_array_pos = ET.SubElement(source_pos, "float_array", id=f"{base_name}-mesh-positions-array",
                                           count=str(len(vertices) * 3))
            pos_str = " ".join([f"{v['px']} {v['py']} {v['pz']}" for v in vertices])
            float_array_pos.text = pos_str
            technique_common_pos = ET.SubElement(source_pos, "technique_common")
            accessor_pos = ET.SubElement(technique_common_pos, "accessor",
                                        source=f"#{base_name}-mesh-positions-array",
                                        count=str(len(vertices)), stride="3")
            ET.SubElement(accessor_pos, "param", name="X", type="float")
            ET.SubElement(accessor_pos, "param", name="Y", type="float")
            ET.SubElement(accessor_pos, "param", name="Z", type="float")
            
            source_uv = ET.SubElement(mesh, "source", id=f"{base_name}-mesh-uvs")
            float_array_uv = ET.SubElement(source_uv, "float_array", id=f"{base_name}-mesh-uvs-array",
                                          count=str(len(vertices) * 2))
            uv_str = " ".join([f"{v['u']} {1.0 - v['v']}" for v in vertices])
            float_array_uv.text = uv_str
            technique_common_uv = ET.SubElement(source_uv, "technique_common")
            accessor_uv = ET.SubElement(technique_common_uv, "accessor",
                                       source=f"#{base_name}-mesh-uvs-array",
                                       count=str(len(vertices)), stride="2")
            ET.SubElement(accessor_uv, "param", name="S", type="float")
            ET.SubElement(accessor_uv, "param", name="T", type="float")
            
            vertices_elem = ET.SubElement(mesh, "vertices", id=f"{base_name}-mesh-vertices")
            ET.SubElement(vertices_elem, "input", semantic="POSITION", source=f"#{base_name}-mesh-positions")
            
            triangles = ET.SubElement(mesh, "triangles", count=str(len(faces)))
            ET.SubElement(triangles, "input", semantic="VERTEX", source=f"#{base_name}-mesh-vertices", offset="0")
            ET.SubElement(triangles, "input", semantic="TEXCOORD", source=f"#{base_name}-mesh-uvs", offset="1")
            
            p = ET.SubElement(triangles, "p")
            indices = []
            for face in faces:
                a, b, c = face[0], face[1], face[2]
                indices.extend([a, a, b, b, c, c])
            p.text = " ".join(str(i) for i in indices)
            
            lib_vis = ET.SubElement(root, "library_visual_scenes")
            vis_scene = ET.SubElement(lib_vis, "visual_scene", id="Scene", name="Scene")
            node = ET.SubElement(vis_scene, "node", id=base_name, name=base_name)
            ET.SubElement(node, "instance_geometry", url=f"#{base_name}-mesh")
            
            scene = ET.SubElement(root, "scene")
            ET.SubElement(scene, "instance_visual_scene", url="#Scene")
            
            xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
            dae_path = os.path.join(out_dir, f"{base_name}.dae")
            with open(dae_path, 'w', encoding='utf-8') as f:
                f.write(xml_str)
            
            print(f"   DAE: {dae_path}")
            
        except Exception as e:
            print(f"   Error exporting Collada: {e}")
    
    def _export_json(self, out_dir, base_name):
        """تصدير بيانات النموذج إلى JSON"""
        data = {
            "header": {
                "name": self.header.name,
                "version": self.header.version,
                "checksum": self.header.checksum,
                "num_bones": self.header.num_bones,
                "num_textures": self.header.num_textures,
                "num_bodyparts": self.header.num_bodyparts,
                "num_seq": self.header.num_seq
            },
            "bones": [{"name": b.name, "parent": b.parent} for b in self.bones],
            "textures": [{"name": t.name, "width": t.width, "height": t.height} for t in self.textures],
            "bodyparts": [{"name": bp.name, "num_models": bp.num_models} for bp in self.bodyparts],
            "num_vertices": len(self.vertices),
            "num_triangles": len(self.triangles)
        }
        
        data = convert_to_json_serializable(data)
        json_path = os.path.join(out_dir, f"{base_name}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   JSON: {json_path}")
    
    def _export_txt(self, out_dir, base_name):
        """تصدير معلومات النموذج إلى ملف نصي"""
        txt_path = os.path.join(out_dir, f"{base_name}_info.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# Half-Life MDL Model Info\n")
            f.write(f"File: {self.header.name}\n")
            f.write(f"Version: {self.header.version}\n")
            f.write(f"Checksum: {self.header.checksum}\n\n")
            
            f.write("Bounding Box:\n")
            f.write(f"  Min: ({self.header.min[0]:.2f}, {self.header.min[1]:.2f}, {self.header.min[2]:.2f})\n")
            f.write(f"  Max: ({self.header.max[0]:.2f}, {self.header.max[1]:.2f}, {self.header.max[2]:.2f})\n\n")
            
            f.write(f"Bones ({len(self.bones)}):\n")
            for i, bone in enumerate(self.bones):
                f.write(f"  {i}: {bone.name} (parent: {bone.parent})\n")
            f.write("\n")
            
            f.write(f"Textures ({len(self.textures)}):\n")
            for tex in self.textures:
                f.write(f"  {tex.name}: {tex.width}x{tex.height}\n")
            f.write("\n")
            
            f.write(f"Bodyparts ({len(self.bodyparts)}):\n")
            for bp in self.bodyparts:
                f.write(f"  {bp.name}: {bp.num_models} models\n")
            f.write("\n")
            
            f.write(f"Geometry:\n")
            f.write(f"  Vertices: {len(self.vertices)}\n")
            f.write(f"  Triangles: {len(self.triangles)}\n")
        
        print(f"   TXT: {txt_path}")
    
    def export_all(self, out_dir, export_formats=None):
        """تصدير كل شيء"""
        if export_formats is None:
            export_formats = ["obj"]
        
        base_name = os.path.splitext(os.path.basename(out_dir))[0]
        if not base_name:
            base_name = "model"
        
        self.ensure_dir(out_dir)
        
        print(f"\nExporting MDL to {out_dir}")
        print("-" * 50)
        
        self.export_obj(out_dir, base_name, export_formats)
        
        print("-" * 50)
        print("Export completed successfully!")


# ------------------------------------------------------------
# كشف نوع الملف (MEF أو MDL)
# ------------------------------------------------------------
def detect_file_type(buffer: Buffer, filename: str = "") -> str:
    """تحديد نوع الملف: MEF, MDL, SMD, أو OBJ"""
    saved_pos = buffer.offset
    buffer.offset = 0
    
    try:
        # التحقق من توقيع MDL (IDST)
        magic = buffer.read(4)
        buffer.offset = saved_pos
        
        if magic == b'IDST':
            return "MDL"
        elif magic == b'ILFF':
            return "MEF"
        else:
            # التحقق من SMD بناءً على الامتداد أو أول سطر
            if filename.lower().endswith('.smd'):
                return "SMD"
            
            # ✅ أضف هذا الجزء الجديد لـ OBJ
            if filename.lower().endswith('.obj'):
                return "OBJ"
            
            # محاولة قراءة أول سطر للتحقق من صيغة OBJ
            try:
                first_line = buffer.data[:200].decode('ascii', errors='ignore')
                if first_line.startswith('v ') or first_line.startswith('vt ') or first_line.startswith('vn ') or first_line.startswith('f ') or first_line.startswith('o ') or first_line.startswith('g '):
                    return "OBJ"
            except:
                pass
            
            # محاولة قراءة أول سطر للتحقق من صيغة SMD
            try:
                first_line = buffer.data[:200].decode('ascii', errors='ignore')
                if 'version' in first_line and 'nodes' in first_line and 'triangles' in first_line:
                    return "SMD"
            except:
                pass
            
            return "UNKNOWN"
    except:
        buffer.offset = saved_pos
        return "UNKNOWN"

# ------------------------------------------------------------
# دالة الكشف عن إصدار MEF (من السكربت الأصلي)
# ------------------------------------------------------------
def detect_mef_version(buffer: Buffer, debug_params=None) -> str:
    """تحديد إصدار MEF (IGI1 أو IGI2)"""
    saved_pos = buffer.offset
    buffer.offset = 0
    
    try:
        signature = buffer.read(4)
        if signature != b'ILFF':
            raise ValueError("Not an ILFF file")
        
        file_size = buffer.read_uint32()
        align = buffer.read_uint32()
        offset = buffer.read_uint32()
        formatsig = buffer.read(4)
        
        ident = buffer.read(4)
        data_size = buffer.read_uint32()
        
        buffer.offset = saved_pos
        
        if data_size == 156 or data_size == 172:
            return "IGI1"
        elif data_size == 212:
            return "IGI2"
        
        return "IGI2"  # افتراضي
    except:
        buffer.offset = saved_pos
        return "IGI2"


# ------------------------------------------------------------
# استيراد الفئات من السكربت الأصلي (MEF)
# ------------------------------------------------------------
# ------------------------------------------------------------
# أنواع numpy للبيانات الكبيرة (IGI2)
# ------------------------------------------------------------
CollisionSphereDtype = np.dtype([
    ("pos", np.float32, (3,)),
    ("radius", np.float32, (1,)),
    ("type", np.int16, (1,)),
    ("count", np.uint16, (1,)),
    ("vertex_a", np.uint16, (1,)),
    ("vertex_b", np.uint16, (1,)),
])

CollisionVertexDtype = np.dtype([
    ("pos", np.float32, (3,)),
    ("uv", np.float32, (2,))
])

CollisionFaceDtype = np.dtype([
    ("face", np.uint16, (3,)),
    ("mat_id", np.uint16, (1,)),
    ("lightmap_id", np.uint16, (1,)),
    ("unknown", np.uint16, (1,))
])

ShadowFaceDtype = np.dtype([
    ("face", np.uint32, (3,)),
    ("edge_flags", np.uint32, (1,)),
    ("normal", np.float32, (3,)),
])

MorphVertexDtype = np.dtype([
    ("index", np.uint32, (1,)),
    ("pos", np.float32, (3,)),
])

LightmapUVData = np.dtype([
    ("uv", np.float32, (2,))
])

# ------------------------------------------------------------
# أنواع numpy للبيانات الكبيرة (IGI1)
# ------------------------------------------------------------
CollisionVertexDtypeIGI1 = np.dtype([
    ("f0", np.float32), ("f1", np.float32), ("f2", np.float32), ("f3", np.float32)
])

CollisionFaceDtypeIGI1 = np.dtype([
    ("a", np.uint16), ("b", np.uint16), ("c", np.uint16), ("mat", np.uint16)
])

CollisionMaterialDtypeIGI1 = np.dtype([
    ("f0", np.int16), ("f1", np.int16), ("f2", np.int16),
    ("f3", np.int16), ("f4", np.int16), ("f5", np.int16)
])

CollisionSphereDtypeIGI1 = np.dtype([
    ("f0", np.float32), ("f1", np.float32), ("f2", np.float32), ("f3", np.float32),
    ("s0", np.int16), ("s1", np.int16), ("s2", np.int16), ("s3", np.int16)
])

# ------------------------------------------------------------
# إعدادات سريعة - غيرها بضغطة زر واحدة
# ------------------------------------------------------------
# 🔘 زر إيقاف دمج القوام مؤقتاً
# غير القيمة إلى False لإيقاف الميزة، وإلى True لتشغيلها

# ملاحظة: هذا الزر يتحكم بميزة دمج القوام فقط. باقي السكربت يعمل بشكل طبيعي.
# ------------------------------------------------------------

# ------------------------------------------------------------
# تعريف مسارات الإدخال والإخراج (يمكن تغييرها عبر وسائط سطر الأوامر)
# ------------------------------------------------------------
# ------------------------------------------------------------
# ثوابت إضافية من وثائق Tav EndeR
# ------------------------------------------------------------
# Scale: IGI world units → normalised viewer units
SCALE: float = 0.01
INV_SCALE: float = 100.0

# Per-model-type vertex stride (bytes)
XTRV_STRIDE: dict = {0: 32, 1: 40, 2: 44, 3: 28}

# Byte offset of the position vector inside one XTRV vertex record
XTRV_POS_OFF: dict = {0: 0, 1: 0, 2: 0, 3: 0}

# Byte offset of the normal vector inside one XTRV vertex record
XTRV_NORM_OFF: dict = {0: 12, 1: 12, 2: 20, 3: 20}

# Byte offset of the primary UV pair inside one XTRV vertex record
XTRV_UV1_OFF: dict = {0: 24, 1: 24, 2: 32, 3: 12}

# Per-model-type DNER (part-descriptor) record stride (bytes)
DNER_STRIDE: dict = {0: 32, 1: 32, 2: 32, 3: 28}

# Shadow model specifics
SEMS_STRIDE: int = 28
XTVS_STRIDE: int = 12
CAFS_STRIDE: int = 28
EGDE_STRIDE: int = 8

# Human-readable names for each model type (مطابقة للوثائق)
MODEL_TYPE_NAMES_EXT: dict = {
    0: "Standard (Rigid)",
    1: "Extended (Bone/Dynamic)",
    2: "Extended UV2 (Lightmap)",
    3: "Compact (Shadow)",
}

# Magic constant for ILFF files
MAGIC_ILFF: bytes = b"ILFF"

# New chunk tags from documentation
NEW_CHUNK_TAGS: list = [b"XTXM", b"TCST", b"XTRN", b"NHSA", b"LLUN"]

# متغير عام للتحكم في معاملات التصحيح (يتم تعيينه من سطر الأوامر)
global_debug_params: Optional['MefDebugParams'] = None

# ------------------------------------------------------------
# تعريف Buffer و LoopFile (كما هي)
# ------------------------------------------------------------
class ChunkHeader:
    def __init__(self, ident: bytes, data_size: int, align: int, offset: int):
        self.ident = ident
        self.data_size = data_size
        self.align = align
        self.offset = offset


class Chunk:
    def __init__(self, header: ChunkHeader, buffer: Buffer):
        self.header = header
        self.buffer = buffer
        self.data = buffer.data  # ✅ احتفظ بنسخة من البيانات الأصلية


class LoopFile:
    def __init__(self, buffer: Buffer, flip_ident: bool = False):
        self.buffer = buffer
        self.flip_ident = flip_ident
        self.chunks = []
        self.index = 0
        self._parse_header()

    def _parse_header(self):
        signature = self.buffer.read(4)
        if signature != b'ILFF':
            raise ValueError(f"Not an ILFF file: {signature}")
        self.file_size = self.buffer.read_uint32()
        align = self.buffer.read_uint32()
        offset = self.buffer.read_uint32()
        formatsig = self.buffer.read(4)
        if formatsig != b'OCEM':
            raise ValueError(f"Expected OCEM, got {formatsig}")
        
        chunk_count = 0
        while not self.buffer.eof():
            ident = self.buffer.read(4)
            data_size = self.buffer.read_uint32()
            chunk_align = self.buffer.read_uint32()
            chunk_offset = self.buffer.read_uint32()
            header = ChunkHeader(ident, data_size, chunk_align, chunk_offset)
            
            # ✅ تحقق من أن data_size معقول
            if data_size > self.buffer.size():
                print(f"   WARNING: Chunk {ident} claims size {data_size} but only {self.buffer.size()} bytes left")
                break
                
            data = self.buffer.read(data_size)
            print(f"   DEBUG: Read chunk {ident} with {len(data)} bytes")  # ✅ طباعة تشخيصية
            
            self.buffer.align(4)
            chunk_buffer = Buffer(data)
            self.chunks.append(Chunk(header, chunk_buffer))
            chunk_count += 1
        
        print(f"Found {chunk_count} chunks in file")

    def next_chunk(self) -> Chunk:
        if self.index >= len(self.chunks):
            return None
        chunk = self.chunks[self.index]
        self.index += 1
        if self.flip_ident:
            chunk.header.ident = chunk.header.ident[::-1]
        return chunk

    def expect_chunk(self, ident: str) -> Chunk:
        ident_bytes = ident.encode('ascii')
        if self.flip_ident:
            ident_bytes = ident_bytes[::-1]
        for i in range(self.index, len(self.chunks)):
            if self.chunks[i].header.ident == ident_bytes:
                chunk = self.chunks[i]
                self.index = i + 1
                return chunk
        raise ValueError(f"Expected chunk {ident} not found")

    def has_chunk(self, ident: str) -> bool:
        ident_bytes = ident.encode('ascii')
        if self.flip_ident:
            ident_bytes = ident_bytes[::-1]
        for i in range(self.index, len(self.chunks)):
            if self.chunks[i].header.ident == ident_bytes:
                return True
        return False

    def print_all_chunks(self):
        print("\nAll chunks in file:")
        for i, chunk in enumerate(self.chunks):
            ident = chunk.header.ident
            if self.flip_ident:
                ident = ident[::-1]
            try:
                ident_str = ident.decode('ascii')
            except:
                ident_str = str(ident)
            print(f"  [{i}] {ident_str}: size={chunk.header.data_size}")

    def __bool__(self):
        return self.index < len(self.chunks)


# ------------------------------------------------------------
# تعريفات البيانات المشتركة
# ------------------------------------------------------------
class ModelType(IntEnum):
    StaticModel = 0
    SkinnedModel = 1
    MODEL2 = 2
    LightmappedModel = 3


class DateTime(datetime):
    @classmethod
    def from_buffer(cls, buffer: Buffer):
        return cls(
            buffer.read_uint32(), buffer.read_uint32(), buffer.read_uint32(),
            buffer.read_uint32(), buffer.read_uint32(), buffer.read_uint32(),
            buffer.read_uint32(),
        )


@dataclass(slots=True)
class Vector3:
    x: float
    y: float
    z: float

    @classmethod
    def from_buffer(cls, buffer: Buffer):
        return cls(buffer.read_float(), buffer.read_float(), buffer.read_float())

    def to_list(self):
        return [self.x, self.y, self.z]

    def to_array(self):
        return np.array([self.x, self.y, self.z], dtype=np.float32)


@dataclass(slots=True)
class Sphere:
    pos: Vector3
    radius: float

    @classmethod
    def from_buffer(cls, buffer: Buffer):
        return cls(Vector3.from_buffer(buffer), buffer.read_float())


@dataclass
class MeshInfo:
    face_count: int
    vertex_count: int
    buffer_size: int

    @classmethod
    def from_buffer(cls, buffer: Buffer):
        return cls(buffer.read_uint32(), buffer.read_uint32(), buffer.read_uint32())


# ------------------------------------------------------------
# تعريفات البيانات لـ IGI2 - الجزء 1 (يجب أن تأتي قبل RenderMeshDataIGI2)
# ------------------------------------------------------------
@dataclass(slots=True)
class RenderMeshHeader:
    header_size: int
    dword0: int
    lightmap_count: int
    face_count: int
    face_group_count: int
    bone_related_0: int
    bone_related_1: int
    vertex_count: int
    dword14: int
    dword18: int
    dword1c: int
    dword20: int
    dword24: int
    dword28: int

    @classmethod
    def from_buffer(cls, buffer: Buffer):
        size = buffer.size()
        if size == 44:
            return cls(44,
                       buffer.read_uint32(), buffer.read_uint32(), buffer.read_uint32(),
                       buffer.read_uint32(), 0, 0,
                       buffer.read_uint32(), buffer.read_uint32(), buffer.read_uint32(),
                       buffer.read_uint32(), buffer.read_uint32(), buffer.read_uint32(),
                       buffer.read_uint32())
        elif size == 40:
            return cls(40,
                       0, buffer.read_uint32(), buffer.read_uint32(), buffer.read_uint32(),
                       buffer.read_uint32(), buffer.read_uint32(), buffer.read_uint32(),
                       buffer.read_uint32(), buffer.read_uint32(), buffer.read_uint32(),
                       buffer.read_uint32(), 0, 0)
        elif size == 36:
            return cls(36,
                       buffer.read_uint32(), 0, buffer.read_uint32(), buffer.read_uint32(),
                       0, 0, buffer.read_uint32(),
                       buffer.read_uint32(), buffer.read_uint32(), buffer.read_uint32(),
                       buffer.read_uint32(), 0, 0)
        else:
            raise ValueError(f"Unknown RenderMeshHeader size {size}")


@dataclass(slots=True)
class CollisionMeshSubHeader:
    face_count: int
    vertex_count: int
    material_count: int
    sphere_count: int
    face_ptr: int
    vertex_ptr: int
    materials_ptr: int
    sphere_ptr: int


@dataclass(slots=True)
class CollisionMeshHeader:
    mesh0: CollisionMeshSubHeader
    mesh1: CollisionMeshSubHeader

    @classmethod
    def from_buffer(cls, buffer: Buffer):
        return cls(
            CollisionMeshSubHeader(*buffer.read_fmt("8I")),
            CollisionMeshSubHeader(*buffer.read_fmt("8I"))
        )


@dataclass(slots=True)
class ShadowMeshHeader:
    face_offset: int
    vertex_offset: int
    edge_offset: int
    face_count: int
    vertex_count: int
    edge_count: int
    bone_index: int

    @classmethod
    def from_buffer(cls, buffer: Buffer):
        try:
            return cls(*buffer.read_fmt("7I"))
        except:
            data = buffer.read_fmt("6I")
            return cls(data[0], data[1], data[2], data[3], data[4], data[5], 0)


# ------------------------------------------------------------
# تعريفات البيانات لـ IGI2 - الجزء 2
# ------------------------------------------------------------
@dataclass(slots=True)
class ModelInfoIGI2:
    version: float
    creation_type: DateTime
    model_type: ModelType
    unknown1: int
    unknown2: int
    unknown3: int
    bounding_sphere1: Sphere
    bounding_sphere2: Sphere
    bounding_sphere3: Sphere
    render_mesh_info: MeshInfo
    collision_mesh_info: MeshInfo
    something_radius: float
    field_80: int
    attachment_count: int
    magic_vertex_count: int
    portal_count: int
    glow_count: int
    bone_count: int
    field_8C: int
    field_90: int
    field_94: int
    field_98: int
    field_9C: int
    field_A0: int
    field_A4: int
    field_A8: int
    field_AC: int
    field_B0: int

    @classmethod
    def from_buffer(cls, buffer: Buffer):
        version = buffer.read_float()
        creation = DateTime.from_buffer(buffer)
        model_type = ModelType(buffer.read_uint32())
        unk1, unk2, unk3 = buffer.read_fmt("3i")
        sphere1 = Sphere.from_buffer(buffer)
        sphere2 = Sphere.from_buffer(buffer)
        sphere3 = Sphere.from_buffer(buffer)
        render_info = MeshInfo.from_buffer(buffer)
        collision_info = MeshInfo.from_buffer(buffer)
        something_radius = buffer.read_float()
        field_80 = buffer.read_uint16()
        attachment_count = buffer.read_uint16()
        magic_vertex_count = buffer.read_uint16()
        portal_count = buffer.read_uint16()
        glow_count = buffer.read_uint16()
        bone_count = buffer.read_uint16()
        field_8C = buffer.read_uint32()
        field_90 = buffer.read_uint32()
        field_94 = buffer.read_uint32()
        field_98 = buffer.read_uint32()
        field_9C = buffer.read_uint32()
        field_A0 = buffer.read_uint32()
        field_A4 = buffer.read_uint32()
        field_A8 = buffer.read_uint32()
        field_AC = buffer.read_uint32()
        field_B0 = buffer.read_uint32()
        return cls(version, creation, model_type,
                   unk1, unk2, unk3,
                   sphere1, sphere2, sphere3,
                   render_info, collision_info,
                   something_radius, field_80, attachment_count,
                   magic_vertex_count, portal_count, glow_count, bone_count,
                   field_8C, field_90, field_94, field_98,
                   field_9C, field_A0, field_A4, field_A8, field_AC, field_B0)


# ------------------------------------------------------------
# تعريفات البيانات لـ IGI1
# ------------------------------------------------------------
@dataclass(slots=True)
class ModelInfoIGI1:
    version: float
    creation_type: DateTime
    model_type: ModelType
    unknown1: int
    unknown2: int
    unknown3: int
    floats: list[float]  # 12 floats f0-fb
    unknown4: list[int]   # 6 uint32 _4-_9
    something_radius: float  # fc
    field_80: int
    attachment_count: int
    magic_vertex_count: int
    portal_count: int
    glow_count: int
    bone_count: int
    reserved: bytes

    @classmethod
    def from_buffer(cls, buffer: Buffer):
        version = buffer.read_float()  # _0
        creation = DateTime.from_buffer(buffer)
        model_type = ModelType(buffer.read_uint32())
        unk1, unk2, unk3 = buffer.read_fmt("3i")
        # قراءة 12 float
        floats = list(buffer.read_fmt("12f"))
        # قراءة 6 uint32
        unk4 = list(buffer.read_fmt("6I"))
        something_radius = buffer.read_float()  # fc
        field_80 = buffer.read_uint16()
        attachment_count = buffer.read_uint16()
        magic_vertex_count = buffer.read_uint16()
        portal_count = buffer.read_uint16()
        glow_count = buffer.read_uint16()
        bone_count = buffer.read_uint16()
        reserved = buffer.read(20)  # rs[20]
        return cls(version, creation, model_type,
                   unk1, unk2, unk3,
                   floats, unk4,
                   something_radius, field_80, attachment_count,
                   magic_vertex_count, portal_count, glow_count, bone_count,
                   reserved)


@dataclass(slots=True)
class RenderMeshHeaderIGI1:
    model_type: int
    dword0: int
    face_count: int
    mesh_count: int
    vertex_count: int
    extra: list[int]

    @classmethod
    def from_buffer(cls, buffer: Buffer, model_type: int):
        dword0 = buffer.read_uint32()  # usually 4
        if model_type == 0:  # rigid
            face_count = buffer.read_uint32()
            mesh_count = buffer.read_uint32()
            vertex_count = buffer.read_uint32()
            extra = list(buffer.read_fmt("8I"))  # rs[8]
            return cls(model_type, dword0, face_count, mesh_count, vertex_count, extra)
        elif model_type == 1:  # skinned
            face_count = buffer.read_uint32()
            mesh_count = buffer.read_uint32()
            v0 = buffer.read_uint32()
            v1 = buffer.read_uint32()
            vertex_count = buffer.read_uint32()
            extra = list(buffer.read_fmt("8I"))
            return cls(model_type, dword0, face_count, mesh_count, vertex_count, extra)
        elif model_type == 3:  # lightmapped
            lightmap_count = buffer.read_uint32()
            face_count = buffer.read_uint32()
            mesh_count = buffer.read_uint32()
            vertex_count = buffer.read_uint32()
            _5 = buffer.read_uint32()
            _6 = buffer.read_uint32()
            extra = list(buffer.read_fmt("7I"))
            return cls(model_type, dword0, face_count, mesh_count, vertex_count, extra)
        else:
            raise ValueError(f"Unknown model type for IGI1: {model_type}")


# ------------------------------------------------------------
# تعريفات الفئات الأخرى (FaceGroup, Bone, Attachment, ...)
# ------------------------------------------------------------
@dataclass(slots=True)
class FaceGroup:
    transparency: int
    shininess: int
    specular: int
    opacity: int
    material_origin: Vector3
    index_offset: int
    face_count: int
    vertex_offset: int
    vertex_count: int

    @classmethod
    def from_buffer(cls, buffer: Buffer, model_type: ModelType):
        if model_type in (ModelType.StaticModel, ModelType.SkinnedModel):
            return SkinnedFaceGroup.from_buffer(buffer)
        elif model_type == ModelType.LightmappedModel:
            return LightmapFaceGroup.from_buffer(buffer)
        else:
            raise NotImplementedError(f"Unsupported model type: {model_type}")


@dataclass(slots=True)
class SkinnedFaceGroup(FaceGroup):
    diffuse_texture: int
    bump_texture: int
    reflection_texture: int
    reflection_scale: int
    bump_scale: int

    @classmethod
    def from_buffer(cls, buffer: Buffer):
        transparency = buffer.read_uint8()
        shininess = buffer.read_uint8()
        specular = buffer.read_uint8()
        opacity = buffer.read_uint8()
        material_origin = Vector3.from_buffer(buffer)
        index_offset = buffer.read_uint16()
        face_count = buffer.read_uint16()
        vertex_offset = buffer.read_uint16()
        vertex_count = buffer.read_uint16()
        diffuse = buffer.read_int16()
        bump = buffer.read_int16()
        reflection = buffer.read_int16()
        ref_scale = buffer.read_uint8()
        bump_scale = buffer.read_uint8()
        return cls(transparency, shininess, specular, opacity, material_origin,
                   index_offset, face_count, vertex_offset, vertex_count,
                   diffuse, bump, reflection, ref_scale, bump_scale)


@dataclass(slots=True)
class LightmapFaceGroup(FaceGroup):
    diffuse_texture: int
    bump_texture: int
    lightmap_id: int = -1

    @classmethod
    def from_buffer(cls, buffer: Buffer):
        transparency = buffer.read_uint8()
        shininess = buffer.read_uint8()
        specular = buffer.read_uint8()
        opacity = buffer.read_uint8()
        material_origin = Vector3.from_buffer(buffer)
        index_offset = buffer.read_uint16()
        face_count = buffer.read_uint16()
        vertex_offset = buffer.read_uint16()
        vertex_count = buffer.read_uint16()
        diffuse = buffer.read_int16()
        bump = buffer.read_int16()
        return cls(transparency, shininess, specular, opacity, material_origin,
                   index_offset, face_count, vertex_offset, vertex_count,
                   diffuse, bump)


@dataclass(slots=True)
class Bone:
    name: str
    pos: Vector3
    parent_id: int


@dataclass(slots=True)
class Attachment:
    name: str
    pos: Vector3
    rotMat: list[float]
    unk: int
    bone_id: int

    @classmethod
    def from_buffer(cls, buffer: Buffer):
        name = buffer.read_ascii_string(16)
        pos = Vector3.from_buffer(buffer)
        rotMat = list(buffer.read_fmt("9f"))
        unk = buffer.read_uint32()
        bone_id = buffer.read_uint32()
        return cls(name, pos, rotMat, unk, bone_id)


@dataclass(slots=True)
class AttachmentIGI1:
    name: str
    pos: Vector3
    rotMat: list[float]
    unk: int

    @classmethod
    def from_buffer(cls, buffer: Buffer):
        name = buffer.read_ascii_string(16)
        pos = Vector3.from_buffer(buffer)
        rotMat = list(buffer.read_fmt("9f"))
        unk = buffer.read_uint32()
        return cls(name, pos, rotMat, unk)


@dataclass(slots=True)
class MagicVertex:
    pos: Vector3
    type: int

    @classmethod
    def from_buffer(cls, buffer: Buffer):
        pos = Vector3.from_buffer(buffer)
        typ = buffer.read_uint32()
        return cls(pos, typ)


@dataclass(slots=True)
class Portal:
    start_vertex: int
    num_vertices: int
    start_face: int
    num_faces: int
    portal_id: int

    @classmethod
    def from_buffer(cls, buffer: Buffer):
        return cls(*buffer.read_fmt("5I"))


@dataclass(slots=True)
class PortalVertex:
    pos: Vector3

    @classmethod
    def from_buffer(cls, buffer: Buffer):
        return cls(Vector3.from_buffer(buffer))


@dataclass(slots=True)
class PortalFace:
    a: int
    b: int
    c: int

    @classmethod
    def from_buffer(cls, buffer: Buffer):
        return cls(*buffer.read_fmt("3I"))


@dataclass(slots=True)
class GlowSprite:
    pos: Vector3
    radius: float
    color_r: float
    color_g: float
    color_b: float
    unk: int

    @classmethod
    def from_buffer(cls, buffer: Buffer):
        pos = Vector3.from_buffer(buffer)
        radius = buffer.read_float()
        r, g, b = buffer.read_fmt("3f")
        unk = buffer.read_uint32()
        return cls(pos, radius, r, g, b, unk)


@dataclass(slots=True)
class CollisionMaterialIGI2:
    opacity: int           # uint32
    portal_id: int         # uint16
    texture_id: int        # uint16
    unknown1: int          # uint32
    game_material_id: int  # uint16
    unknown2: int          # uint16

    @classmethod
    def from_buffer(cls, buffer: Buffer):
        opacity = buffer.read_uint32()
        portal_id = buffer.read_uint16()
        texture_id = buffer.read_uint16()
        unknown1 = buffer.read_uint32()
        game_material_id = buffer.read_uint16()
        unknown2 = buffer.read_uint16()
        return cls(opacity, portal_id, texture_id, unknown1, game_material_id, unknown2)


@dataclass(slots=True)
class CollisionMaterialIGI1:
    fields: list[int]  # 6 int16

    @classmethod
    def from_buffer(cls, buffer: Buffer):
        fields = list(buffer.read_fmt("6h"))
        return cls(fields)


@dataclass(slots=True)
class LightmapData:
    width: int
    height: int
    format: int
    data: bytes


@dataclass(slots=True)
class TXANData:
    unknown_fields: list[int]

    @classmethod
    def from_buffer(cls, buffer: Buffer):
        fields = list(buffer.read_fmt("28I"))
        return cls(fields)


# ------------------------------------------------------------
# تعريفات بيانات النماذج (يجب أن تأتي بعد RenderMeshHeader)
# ------------------------------------------------------------
@dataclass(slots=True)
class RenderMeshDataIGI1:
    mesh_header: RenderMeshHeaderIGI1
    materials: list  # قائمة المواد (كل مادة تحتوي على بيانات ووجوه)
    vertices: np.ndarray


@dataclass(slots=True)
class RenderMeshDataIGI2:
    mesh_header: RenderMeshHeader
    faces: np.ndarray = field(repr=False)
    vertices: np.ndarray = field(repr=False)
    primitives: list = field(default_factory=list)
    lightmap_uvs: np.ndarray = None


@dataclass(slots=True)
class CollisionMeshDataIGI2:
    mesh_header: CollisionMeshHeader
    spheres: np.ndarray
    faces: np.ndarray
    vertices: np.ndarray
    materials: list = field(default_factory=list)


@dataclass(slots=True)
class ShadowMeshDataIGI2:
    mesh_header: ShadowMeshHeader
    faces: np.ndarray
    vertices: np.ndarray
    edges: np.ndarray


# ------------------------------------------------------------
# تعريفات جديدة من وثائق Tav EndeR
# ------------------------------------------------------------
@dataclass(slots=True)
class HSEMInfo:
    """هيكل HSEM المعاد هيكلته حسب المواصفات الرسمية لـ IGI2"""
    version: float
    model_type: int
    bound_min: Vector3
    bound_max: Vector3
    radius: float

    @classmethod
    def from_buffer(cls, buffer: Buffer):
        """قراءة صحيحة حسب ترتيب البايتات الفعلي في IGI2"""
        # الترتيب الصحيح (من الوثائق + اختبار على الملفات):
        version = buffer.read_float()           # أول float = version
        model_type = buffer.read_uint32()       # model_type
        bound_min = Vector3.from_buffer(buffer)
        bound_max = Vector3.from_buffer(buffer)
        radius = buffer.read_float()

        # باقي البايتات (padding أو حقول إضافية) يتم تجاهلها تلقائياً
        return cls(version, model_type, bound_min, bound_max, radius)


@dataclass
class XTRWEntry:
    """مفردة وزن عظم (Vertex weight) من قطعة XTRW"""
    vertex_id: int
    bone_id: int
    weight: float

    @classmethod
    def from_buffer(cls, buffer: Buffer):
        vertex_id = buffer.read_uint32()
        bone_id = buffer.read_uint32()
        weight = buffer.read_float()
        return cls(vertex_id, bone_id, weight)


@dataclass
class TextureReference:
    """مرجع قوام من قطعة XTXM"""
    index: int
    name: str

    @classmethod
    def from_buffer(cls, buffer: Buffer):
        # الصيغة تعتمد على التطبيق الفعلي، هذه صيغة تقريبية
        index = buffer.read_uint32()
        name = buffer.read_ascii_string(32)
        return cls(index, name)


@dataclass
class TextureCoordinateSet:
    """مجموعة إحداثيات نسيج من قطعة TCST"""
    index: int
    uvs: List[Tuple[float, float]] = field(default_factory=list)

    @classmethod
    def from_buffer(cls, buffer: Buffer, count: int):
        uvs = []
        for _ in range(count):
            u = buffer.read_float()
            v = buffer.read_float()
            uvs.append((u, v))
        return cls(0, uvs)


# ------------------------------------------------------------
# كلاس MefDebugParams من وثائق Tav EndeR
# ------------------------------------------------------------
@dataclass
class MefDebugParams:
    """Dynamic parameters for coordinate and scale experiments."""
    v_scale: float = SCALE           # Multiplier for raw vertex floats
    b_scale: float = SCALE           # Multiplier for raw bone floats
    swizzle_mode: str = "XZY"        # Axis mapping (e.g. "XYZ", "XZY", "YXZ", etc.)
    bone_mode: str = "REL"           # "REL" (to parent), "ABS" (ignore hierarchy), "ROOT" (to bone 0)
    bone_id_bias: int = 0            # Offset applied to b_id (0, -1, 1)
    flip_x: bool = False
    flip_y: bool = False
    flip_z: bool = False

    def swizzle(self, x: float, y: float, z: float, scale: float = None) -> tuple:
        """Apply dynamic axis mapping and scaling."""
        if scale is None:
            scale = self.v_scale
        
        tx, ty, tz = x, y, z
        if self.flip_x: tx = -tx
        if self.flip_y: ty = -ty
        if self.flip_z: tz = -tz
        
        mode = self.swizzle_mode.upper()
        if mode == "XZY":  # Standard IGI->GL (X->X, Z->Y, Y->Z)
            return tx * scale, tz * scale, ty * scale
        elif mode == "XYZ":  # No mapping
            return tx * scale, ty * scale, tz * scale
        elif mode == "YXZ":  # Swap X/Y
            return ty * scale, tx * scale, tz * scale
        elif mode == "ZXY":
            return tz * scale, tx * scale, ty * scale
        elif mode == "YZX":
            return ty * scale, tz * scale, tx * scale
        elif mode == "ZYX":
            return tz * scale, ty * scale, tx * scale
        return tx * scale, ty * scale, tz * scale


# ------------------------------------------------------------
# الدوال المساعدة (محسنة للأداء)
# ------------------------------------------------------------
def make_translation_matrix(x, y, z):
    m = np.identity(4, dtype=np.float32)
    m[0, 3] = x
    m[1, 3] = y
    m[2, 3] = z
    return m


def build_parent_indices(child_counts):
    bone_count = len(child_counts)
    parents = [-1] * bone_count
    if bone_count == 0:
        return parents
    
    stack = [(0, int(child_counts[0]))]
    for i in range(1, bone_count):
        while stack and stack[-1][1] == 0:
            stack.pop()
        if not stack:
            break
        parent = stack[-1][0]
        parents[i] = parent
        stack[-1] = (stack[-1][0], stack[-1][1] - 1)
        stack.append((i, int(child_counts[i])))
    return parents


def build_bone_matrices(bone_positions, child_counts):
    bone_count = len(bone_positions)
    if bone_count == 0:
        return [], [], []
    
    parents = build_parent_indices(child_counts)
    bind_local = np.array([make_translation_matrix(p.x, p.y, p.z) for p in bone_positions])
    bind_global = np.zeros((bone_count, 4, 4), dtype=np.float32)
    
    for i in range(bone_count):
        parent = parents[i] if i < len(parents) else -1
        if parent == -1:
            bind_global[i] = bind_local[i]
        else:
            bind_global[i] = bind_global[parent] @ bind_local[i]
    
    inverse_bind = np.array([np.linalg.inv(m) for m in bind_global])
    return bind_global, inverse_bind, parents


def bake_skinning_improved(vertices, bone_global, inverse_bind, root_inv=None, 
                           debug_params: Optional['MefDebugParams'] = None,
                           extra_weights: Optional[List['XTRWEntry']] = None):
    """
    تحسين التزين مع دعم XTRW و bone_id_bias و bone_mode
    """
    if root_inv is None and len(bone_global) > 0:
        root_inv = np.linalg.inv(bone_global[0])
    
    if debug_params is None:
        debug_params = MefDebugParams()
    
    has_weight = "weight" in vertices.dtype.names
    has_bone_id = "bone_id" in vertices.dtype.names
    
    # بناء قاموس للأوزان الإضافية من XTRW
    xtrw_weights = {}
    if extra_weights:
        for ew in extra_weights:
            xtrw_weights[ew.vertex_id] = (ew.bone_id, ew.weight)
    
    vertex_count = len(vertices)
    result = np.zeros(vertex_count, dtype=[
        ("px", np.float32), ("py", np.float32), ("pz", np.float32),
        ("nx", np.float32), ("ny", np.float32), ("nz", np.float32),
        ("u", np.float32), ("v", np.float32),
        ("weight", np.float32), ("bone_id", np.uint16)
    ])
    
    for i in range(vertex_count):
        v = vertices[i]
        
        # استخراج الموقع
        if "pos" in v.dtype.names:
            pos = v["pos"]
            px, py, pz = float(pos[0]), float(pos[1]), float(pos[2])
        else:
            px = float(v["px"]) if "px" in v.dtype.names else 0.0
            py = float(v["py"]) if "py" in v.dtype.names else 0.0
            pz = float(v["pz"]) if "pz" in v.dtype.names else 0.0
        
        # استخراج الطبيعية
        if "normal" in v.dtype.names:
            normal = v["normal"]
            nx, ny, nz = float(normal[0]), float(normal[1]), float(normal[2])
        else:
            nx = float(v["nx"]) if "nx" in v.dtype.names else 0.0
            ny = float(v["ny"]) if "ny" in v.dtype.names else 0.0
            nz = float(v["nz"]) if "nz" in v.dtype.names else 0.0
        
        # استخراج UV
        if "uv0" in v.dtype.names:
            uv = v["uv0"]
            u, vt = float(uv[0]), float(uv[1])
        else:
            u = float(v["u"]) if "u" in v.dtype.names else 0.0
            vt = float(v["v"]) if "v" in v.dtype.names else 0.0
        
        # استخراج بيانات التزين (مع دعم XTRW و bone_id_bias)
        weight_val = 1.0
        bone_id_val = 0
        
        # أولاً: استخدام أوزان XTRW إذا كانت متوفرة
        if i in xtrw_weights:
            bone_id_val, weight_val = xtrw_weights[i]
        # ثانياً: استخدام الأوزان المضمنة في الرأس
        elif has_weight and has_bone_id:
            w = v["weight"]
            if isinstance(w, np.ndarray):
                weight_val = float(w[0]) if len(w) > 0 else 1.0
            else:
                weight_val = float(w)
            
            b = v["bone_id"]
            if isinstance(b, np.ndarray):
                bone_id_val = int(b[0]) if len(b) > 0 else 0
            else:
                bone_id_val = int(b)
        elif has_bone_id:
            b = v["bone_id"]
            if isinstance(b, np.ndarray):
                bone_id_val = int(b[0]) if len(b) > 0 else 0
            else:
                bone_id_val = int(b)
        
        # تطبيق bone_id_bias
        bone_id_val += debug_params.bone_id_bias
        
        # تطبيق التحويل حسب bone_mode
        pos_vec = np.array([px, py, pz, 1.0])
        
        if bone_id_val >= 0 and bone_id_val < len(bone_global) and weight_val > 0:
            G = bone_global[bone_id_val]
            pos_world = G @ pos_vec
            
            if debug_params.bone_mode == "ROOT" and len(bone_global) > 0:
                # تطبيق تحويل العظمة الجذرية
                root_matrix = bone_global[0]
                pos_model = np.linalg.inv(root_matrix) @ pos_world
            elif debug_params.bone_mode == "ABS":
                # تجاهل التسلسل الهرمي
                pos_model = pos_world
            else:  # "REL" أو الوضع الافتراضي
                pos_model = root_inv @ pos_world if root_inv is not None else pos_world
        else:
            pos_model = pos_vec[:3]
        
        # تطبيق swizzle على الإحداثيات
        px_out, py_out, pz_out = debug_params.swizzle(pos_model[0], pos_model[1], pos_model[2], debug_params.v_scale)
        nx_out, ny_out, nz_out = debug_params.swizzle(nx, ny, nz, 1.0)
        
        result[i]["px"] = px_out
        result[i]["py"] = py_out
        result[i]["pz"] = pz_out
        result[i]["nx"] = nx_out
        result[i]["ny"] = ny_out
        result[i]["nz"] = nz_out
        result[i]["u"] = u
        result[i]["v"] = vt
        result[i]["weight"] = weight_val
        result[i]["bone_id"] = bone_id_val if bone_id_val >= 0 else 0
    
    return result


# ------------------------------------------------------------
# دالة تحويل الإحداثيات (Swizzle) حسب وثائق Tav EndeR
# ------------------------------------------------------------
def apply_igi_swizzle(x: float, y: float, z: float, scale: float = SCALE) -> tuple:
    """
    تحويل الإحداثيات من صيغة IGI2 إلى الصيغة القياسية (Unity/Blender)
    الصيغة: (x, z, -y) * scale
    """
    return (x * scale, z * scale, -y * scale)


def apply_igi_swizzle_to_vector3(vec: Vector3, scale: float = SCALE) -> Vector3:
    """تطبيق التحويل على كائن Vector3"""
    x, y, z = apply_igi_swizzle(vec.x, vec.y, vec.z, scale)
    return Vector3(x, y, z)


# ------------------------------------------------------------
# دوال التصدير إلى صيغ إضافية
# ------------------------------------------------------------
def save_lightmap_as_png(lightmap_data, output_path):
    if not PIL_AVAILABLE:
        return False
    
    try:
        width = lightmap_data.width
        height = lightmap_data.height
        data = lightmap_data.data
        
        if len(data) == width * height * 3:
            img = Image.frombytes('RGB', (width, height), data)
        elif len(data) == width * height * 4:
            img = Image.frombytes('RGBA', (width, height), data)
        elif len(data) == width * height:
            img = Image.frombytes('L', (width, height), data)
        else:
            print(f"      Unknown lightmap format, size: {len(data)} bytes")
            return False
        
        img.save(output_path, 'PNG')
        return True
    except Exception as e:
        print(f"      Error converting to PNG: {e}")
        return False


def save_lightmap_as_dds(lightmap_data, output_path):
    try:
        with open(output_path, 'wb') as f:
            f.write(lightmap_data.data)
        return True
    except Exception as e:
        print(f"      Error saving DDS: {e}")
        return False


# ------------------------------------------------------------
# تعديل: تحديث export_to_collada لاستخدام global_debug_params
# ------------------------------------------------------------
def export_to_collada(model, output_path, base_name, vertices, faces, has_normals=True, has_uv=True):
    """تصدير Collada مع دعم معاملات التصحيح العامة"""
    # استخدام المعاملات العامة إذا كانت متوفرة
    debug_params = global_debug_params
    
    try:
        root = ET.Element("COLLADA", xmlns="http://www.collada.org/2005/11/COLLADASchema", version="1.4.1")
        
        asset = ET.SubElement(root, "asset")
        contrib = ET.SubElement(asset, "contributor")
        ET.SubElement(contrib, "authoring_tool").text = "IGI1/IGI2 MEF Exporter"
        if debug_params:
            ET.SubElement(contrib, "comments").text = f"Debug params: scale={debug_params.v_scale}, swizzle={debug_params.swizzle_mode}"
        ET.SubElement(asset, "created").text = datetime.now().isoformat()
        ET.SubElement(asset, "modified").text = datetime.now().isoformat()
        ET.SubElement(asset, "unit", name="meter", meter="1")
        ET.SubElement(asset, "up_axis").text = "Y_UP"
        
        lib_geo = ET.SubElement(root, "library_geometries")
        geometry = ET.SubElement(lib_geo, "geometry", id=f"{base_name}-mesh", name=base_name)
        mesh = ET.SubElement(geometry, "mesh")
        
        source_pos = ET.SubElement(mesh, "source", id=f"{base_name}-mesh-positions")
        float_array_pos = ET.SubElement(source_pos, "float_array", id=f"{base_name}-mesh-positions-array", 
                                       count=str(len(vertices) * 3))
        pos_str = " ".join([f"{v['px']} {v['py']} {v['pz']}" for v in vertices])
        float_array_pos.text = pos_str
        technique_common_pos = ET.SubElement(source_pos, "technique_common")
        accessor_pos = ET.SubElement(technique_common_pos, "accessor", 
                                    source=f"#{base_name}-mesh-positions-array",
                                    count=str(len(vertices)), stride="3")
        ET.SubElement(accessor_pos, "param", name="X", type="float")
        ET.SubElement(accessor_pos, "param", name="Y", type="float")
        ET.SubElement(accessor_pos, "param", name="Z", type="float")
        
        if has_normals:
            source_norm = ET.SubElement(mesh, "source", id=f"{base_name}-mesh-normals")
            float_array_norm = ET.SubElement(source_norm, "float_array", id=f"{base_name}-mesh-normals-array",
                                            count=str(len(vertices) * 3))
            norm_str = " ".join([f"{v['nx']} {v['ny']} {v['nz']}" for v in vertices])
            float_array_norm.text = norm_str
            technique_common_norm = ET.SubElement(source_norm, "technique_common")
            accessor_norm = ET.SubElement(technique_common_norm, "accessor",
                                         source=f"#{base_name}-mesh-normals-array",
                                         count=str(len(vertices)), stride="3")
            ET.SubElement(accessor_norm, "param", name="X", type="float")
            ET.SubElement(accessor_norm, "param", name="Y", type="float")
            ET.SubElement(accessor_norm, "param", name="Z", type="float")
        
        if has_uv:
            source_uv = ET.SubElement(mesh, "source", id=f"{base_name}-mesh-uvs")
            float_array_uv = ET.SubElement(source_uv, "float_array", id=f"{base_name}-mesh-uvs-array",
                                          count=str(len(vertices) * 2))
            uv_str = " ".join([f"{v['u']} {1.0 - v['v']}" for v in vertices])
            float_array_uv.text = uv_str
            technique_common_uv = ET.SubElement(source_uv, "technique_common")
            accessor_uv = ET.SubElement(technique_common_uv, "accessor",
                                       source=f"#{base_name}-mesh-uvs-array",
                                       count=str(len(vertices)), stride="2")
            ET.SubElement(accessor_uv, "param", name="S", type="float")
            ET.SubElement(accessor_uv, "param", name="T", type="float")
        
        vertices_elem = ET.SubElement(mesh, "vertices", id=f"{base_name}-mesh-vertices")
        ET.SubElement(vertices_elem, "input", semantic="POSITION", source=f"#{base_name}-mesh-positions")
        
        triangles = ET.SubElement(mesh, "triangles", count=str(len(faces)))
        ET.SubElement(triangles, "input", semantic="VERTEX", source=f"#{base_name}-mesh-vertices", offset="0")
        if has_normals:
            ET.SubElement(triangles, "input", semantic="NORMAL", source=f"#{base_name}-mesh-normals", offset="1")
        if has_uv:
            ET.SubElement(triangles, "input", semantic="TEXCOORD", source=f"#{base_name}-mesh-uvs", offset="2")
        
        p = ET.SubElement(triangles, "p")
        indices = []
        for face in faces:
            a, b, c = face[0], face[1], face[2]
            if has_normals and has_uv:
                indices.extend([a, a, a, b, b, b, c, c, c])
            elif has_normals:
                indices.extend([a, a, b, b, c, c])
            elif has_uv:
                indices.extend([a, a, b, b, c, c])
            else:
                indices.extend([a, b, c])
        p.text = " ".join(str(i) for i in indices)
        
        lib_vis = ET.SubElement(root, "library_visual_scenes")
        vis_scene = ET.SubElement(lib_vis, "visual_scene", id="Scene", name="Scene")
        node = ET.SubElement(vis_scene, "node", id=base_name, name=base_name)
        ET.SubElement(node, "instance_geometry", url=f"#{base_name}-mesh")
        
        scene = ET.SubElement(root, "scene")
        ET.SubElement(scene, "instance_visual_scene", url="#Scene")
        
        xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(xml_str)
        
        return True
    except Exception as e:
        print(f"      Error exporting to Collada: {e}")
        return False


# ------------------------------------------------------------
# تعديل: تحديث export_to_gltf لاستخدام global_debug_params
# ------------------------------------------------------------
def export_to_gltf(model, output_path, base_name, vertices, faces, has_normals=True, has_uv=True):
    """تصدير glTF مع دعم معاملات التصحيح العامة"""
    if not GLTF_AVAILABLE:
        return False
    
    # استخدام المعاملات العامة إذا كانت متوفرة
    debug_params = global_debug_params
    
    try:
        from pygltflib import GLTF2, Buffer, BufferView, Accessor, Mesh, Primitive, Attributes, Asset, Scene, Node
        
        gltf = GLTF2()
        gltf.asset = Asset(generator="IGI1/IGI2 MEF Exporter", version="2.0")
        
        positions = []
        normals = []
        uvs = []
        for v in vertices:
            positions.extend([v['px'], v['py'], v['pz']])
            if has_normals:
                normals.extend([v['nx'], v['ny'], v['nz']])
            if has_uv:
                uvs.extend([v['u'], 1.0 - v['v']])
        
        # إذا كانت معاملات التصحيح متوفرة، يمكن تطبيق تحويل إضافي
        if debug_params:
            # يمكن إضافة معالجة إضافية حسب الحاجة
            pass
        
        binary_data = bytearray()
        
        positions_bytes = np.array(positions, dtype=np.float32).tobytes()
        positions_buffer_view = BufferView(
            buffer=0,
            byteOffset=len(binary_data),
            byteLength=len(positions_bytes),
            target=34962
        )
        gltf.bufferViews.append(positions_buffer_view)
        binary_data.extend(positions_bytes)
        
        positions_accessor = Accessor(
            bufferView=len(gltf.bufferViews) - 1,
            componentType=5126,
            count=len(vertices),
            type="VEC3",
            min=[float(np.min(positions[0::3])), float(np.min(positions[1::3])), float(np.min(positions[2::3]))],
            max=[float(np.max(positions[0::3])), float(np.max(positions[1::3])), float(np.max(positions[2::3]))]
        )
        gltf.accessors.append(positions_accessor)
        
        if has_normals:
            normals_bytes = np.array(normals, dtype=np.float32).tobytes()
            normals_buffer_view = BufferView(
                buffer=0,
                byteOffset=len(binary_data),
                byteLength=len(normals_bytes),
                target=34962
            )
            gltf.bufferViews.append(normals_buffer_view)
            binary_data.extend(normals_bytes)
            
            normals_accessor = Accessor(
                bufferView=len(gltf.bufferViews) - 1,
                componentType=5126,
                count=len(vertices),
                type="VEC3"
            )
            gltf.accessors.append(normals_accessor)
        
        if has_uv:
            uvs_bytes = np.array(uvs, dtype=np.float32).tobytes()
            uvs_buffer_view = BufferView(
                buffer=0,
                byteOffset=len(binary_data),
                byteLength=len(uvs_bytes),
                target=34962
            )
            gltf.bufferViews.append(uvs_buffer_view)
            binary_data.extend(uvs_bytes)
            
            uvs_accessor = Accessor(
                bufferView=len(gltf.bufferViews) - 1,
                componentType=5126,
                count=len(vertices),
                type="VEC2"
            )
            gltf.accessors.append(uvs_accessor)
        
        indices = []
        for face in faces:
            indices.extend([face[0], face[1], face[2]])
        
        indices_bytes = np.array(indices, dtype=np.uint32).tobytes()
        indices_buffer_view = BufferView(
            buffer=0,
            byteOffset=len(binary_data),
            byteLength=len(indices_bytes),
            target=34963
        )
        gltf.bufferViews.append(indices_buffer_view)
        binary_data.extend(indices_bytes)
        
        indices_accessor = Accessor(
            bufferView=len(gltf.bufferViews) - 1,
            componentType=5125,
            count=len(indices),
            type="SCALAR"
        )
        gltf.accessors.append(indices_accessor)
        
        gltf.buffers.append(Buffer(byteLength=len(binary_data), uri=f"{base_name}.bin"))
        
        attributes = Attributes(POSITION=0)
        if has_normals:
            attributes.NORMAL = 1
        if has_uv:
            attributes.TEXCOORD_0 = 2
        
        primitive = Primitive(
            attributes=attributes,
            indices=len(gltf.accessors) - 1,
            material=0
        )
        
        mesh = Mesh(primitives=[primitive])
        gltf.meshes.append(mesh)
        
        node = Node(mesh=0)
        gltf.nodes.append(node)
        scene = Scene(nodes=[0])
        gltf.scenes.append(scene)
        gltf.scene = 0
        
        gltf.save(f"{output_path}.gltf")
        
        with open(f"{os.path.splitext(output_path)[0]}.bin", 'wb') as f:
            f.write(binary_data)
        
        print(f"   Exported glTF with debug_params={debug_params is not None}")
        return True
    except Exception as e:
        print(f"      Error exporting to glTF: {e}")
        return False

# ========== دالة glTF كاملة مع العظام والأوزان (مضافة حديثاً) ==========
def export_to_gltf_full(model, output_path, base_name, vertices, faces, has_normals=True, has_uv=True, has_skinning=False, bones=None):                     
    debug_params = get_global_debug_params()
    
    # استخدام debug_params إذا كانت متوفرة
    if debug_params:
        print(f"   Exporting glTF with debug scale: {debug_params.v_scale}")
        # يمكن تطبيق تحويل إضافي على الرؤوس إذا لزم الأمر
        # مثلاً: إذا أردت تطبيق swizzle إضافي على البيانات قبل التصدير
        # vertices = apply_additional_transform(vertices, debug_params)
        
    if not GLTF_AVAILABLE:
        return False
    
    try:
        from pygltflib import GLTF2, Buffer, BufferView, Accessor, Mesh, Primitive, Attributes, Asset, Scene, Node, Skin
        
        gltf = GLTF2()
        gltf.asset = Asset(generator="IGI1/IGI2 MEF Exporter", version="2.0")
        
        # تجميع البيانات
        positions = []
        normals = []
        uvs = []
        weights = []
        joints = []
        
        for i, v in enumerate(vertices):
            positions.extend([v['px'], v['py'], v['pz']])
            if has_normals:
                normals.extend([v['nx'], v['ny'], v['nz']])
            if has_uv:
                uvs.extend([v['u'], 1.0 - v['v']])
            
            # جمع بيانات التزين (إذا وجدت)
            if has_skinning:
                # padding إلى 4 قيم (أقصى 4 عظام لكل رأس)
                w = [0.0, 0.0, 0.0, 0.0]
                j = [0, 0, 0, 0]
                
                if 'weight' in v.dtype.names:
                    w_val = v['weight']
                    if isinstance(w_val, np.ndarray):
                        w[0] = float(w_val[0]) if len(w_val) > 0 else 0.0
                    else:
                        w[0] = float(w_val)
                
                if 'bone_id' in v.dtype.names:
                    j_val = v['bone_id']
                    if isinstance(j_val, np.ndarray):
                        j[0] = int(j_val[0]) if len(j_val) > 0 else 0
                    else:
                        j[0] = int(j_val)
                
                weights.extend(w)
                joints.extend(j)
        
        binary_data = bytearray()
        
        # Positions
        pos_bytes = np.array(positions, dtype=np.float32).tobytes()
        pos_bv = BufferView(buffer=0, byteOffset=len(binary_data), byteLength=len(pos_bytes), target=34962)
        gltf.bufferViews.append(pos_bv)
        binary_data.extend(pos_bytes)
        
        pos_acc = Accessor(bufferView=len(gltf.bufferViews)-1, componentType=5126, 
                           count=len(vertices), type="VEC3",
                           min=[float(np.min(positions[0::3])), float(np.min(positions[1::3])), float(np.min(positions[2::3]))],
                           max=[float(np.max(positions[0::3])), float(np.max(positions[1::3])), float(np.max(positions[2::3]))])
        gltf.accessors.append(pos_acc)
        
        # Normals
        if has_normals and normals:
            norm_bytes = np.array(normals, dtype=np.float32).tobytes()
            norm_bv = BufferView(buffer=0, byteOffset=len(binary_data), byteLength=len(norm_bytes), target=34962)
            gltf.bufferViews.append(norm_bv)
            binary_data.extend(norm_bytes)
            
            norm_acc = Accessor(bufferView=len(gltf.bufferViews)-1, componentType=5126, 
                                count=len(vertices), type="VEC3")
            gltf.accessors.append(norm_acc)
        
        # UVs
        if has_uv and uvs:
            uv_bytes = np.array(uvs, dtype=np.float32).tobytes()
            uv_bv = BufferView(buffer=0, byteOffset=len(binary_data), byteLength=len(uv_bytes), target=34962)
            gltf.bufferViews.append(uv_bv)
            binary_data.extend(uv_bytes)
            
            uv_acc = Accessor(bufferView=len(gltf.bufferViews)-1, componentType=5126, 
                              count=len(vertices), type="VEC2")
            gltf.accessors.append(uv_acc)
        
        # Weights & Joints (للعظام)
        if has_skinning and weights and joints:
            weights_bytes = np.array(weights, dtype=np.float32).tobytes()
            weights_bv = BufferView(buffer=0, byteOffset=len(binary_data), byteLength=len(weights_bytes), target=34962)
            gltf.bufferViews.append(weights_bv)
            binary_data.extend(weights_bytes)
            
            weights_acc = Accessor(bufferView=len(gltf.bufferViews)-1, componentType=5126, 
                                   count=len(vertices), type="VEC4")
            gltf.accessors.append(weights_acc)
            
            joints_bytes = np.array(joints, dtype=np.uint16).tobytes()
            joints_bv = BufferView(buffer=0, byteOffset=len(binary_data), byteLength=len(joints_bytes), target=34962)
            gltf.bufferViews.append(joints_bv)
            binary_data.extend(joints_bytes)
            
            joints_acc = Accessor(bufferView=len(gltf.bufferViews)-1, componentType=5123, 
                                  count=len(vertices), type="VEC4")
            gltf.accessors.append(joints_acc)
        
        # Indices
        indices_list = []
        for face in faces:
            indices_list.extend([face[0], face[1], face[2]])
        
        indices_bytes = np.array(indices_list, dtype=np.uint32).tobytes()
        indices_bv = BufferView(buffer=0, byteOffset=len(binary_data), byteLength=len(indices_bytes), target=34963)
        gltf.bufferViews.append(indices_bv)
        binary_data.extend(indices_bytes)
        
        indices_acc = Accessor(bufferView=len(gltf.bufferViews)-1, componentType=5125, 
                               count=len(indices_list), type="SCALAR")
        gltf.accessors.append(indices_acc)
        
        # Buffer
        gltf.buffers.append(Buffer(byteLength=len(binary_data), uri=f"{base_name}.bin"))
        
        # Primitive - بناء السمات حسب المتوفرة
        attribute_offset = 0
        attributes = Attributes(POSITION=attribute_offset)
        attribute_offset += 1
        
        if has_normals and normals:
            attributes.NORMAL = attribute_offset
            attribute_offset += 1
        if has_uv and uvs:
            attributes.TEXCOORD_0 = attribute_offset
            attribute_offset += 1
        if has_skinning and weights and joints:
            attributes.WEIGHTS_0 = attribute_offset
            attribute_offset += 1
            attributes.JOINTS_0 = attribute_offset
            attribute_offset += 1
        
        primitive = Primitive(attributes=attributes, indices=len(gltf.accessors)-1, material=0)
        mesh = Mesh(primitives=[primitive])
        gltf.meshes.append(mesh)
        
        # عظام
        if has_skinning and bones:
            # إضافة العظام كـ nodes
            bone_nodes = []
            for bone in bones:
                node = Node(name=bone.name if hasattr(bone, 'name') else f'bone_{len(bone_nodes)}')
                gltf.nodes.append(node)
                bone_nodes.append(len(gltf.nodes)-1)
            
            # إنشاء الهيكل الهرمي
            for i, bone in enumerate(bones):
                parent_id = bone.parent_id if hasattr(bone, 'parent_id') else -1
                if parent_id >= 0 and parent_id < len(bone_nodes):
                    if gltf.nodes[bone_nodes[i]].children is None:
                        gltf.nodes[bone_nodes[i]].children = []
                    gltf.nodes[bone_nodes[i]].children.append(bone_nodes[parent_id])
            
            # Skin
            skin = Skin(joints=bone_nodes)
            gltf.skins.append(skin)
            
            # ربط الـ skin بالـ mesh
            node = Node(mesh=0, skin=len(gltf.skins)-1)
            gltf.nodes.append(node)
            scene = Scene(nodes=[len(gltf.nodes)-1])
        else:
            node = Node(mesh=0)
            gltf.nodes.append(node)
            scene = Scene(nodes=[0])
        
        gltf.scenes.append(scene)
        gltf.scene = 0
        
        # حفظ
        gltf.save(f"{output_path}.gltf")
        with open(f"{os.path.splitext(output_path)[0]}.bin", 'wb') as f:
            f.write(binary_data)
        
        print(f"   Exported glTF with full data (skinning: {has_skinning}, vertices: {len(vertices)}, weights: {len(weights) > 0})")
        return True
        
    except Exception as e:
        print(f"      Error exporting to glTF: {e}")
        import traceback
        traceback.print_exc()
        return False


# ------------------------------------------------------------
# دالة مساعدة لتحويل مؤشرات القوام إلى أسماء ملفات (محدثة لدعم TextureReference)
# ------------------------------------------------------------
def get_texture_name(texture_index: int, base_name: str, material_index: int, 
                     texture_references: Optional[List[TextureReference]] = None) -> str:
    """
    تحويل مؤشر القوام إلى اسم ملف.
    يدعم الآن TextureReference من قطعة XTXM.
    """
    # أولاً: البحث في texture_references إذا كانت متوفرة
    if texture_references:
        for ref in texture_references:
            if ref.index == texture_index:
                # استخراج اسم الملف من المسار إذا لزم الأمر
                ref_name = ref.name
                if ref_name.endswith('.tga') or ref_name.endswith('.dds') or ref_name.endswith('.png'):
                    return ref_name
                else:
                    return f"{ref_name}.tga"
    
    # ثانياً: الأسماء الافتراضية
    if texture_index == 0:
        return f"{base_name}.tga"
    elif texture_index == 1:
        return f"{base_name}_bump.tga"
    elif texture_index == 2:
        return f"{base_name}_reflection.tga"
    else:
        return f"{base_name}_mat{material_index}.tga"


# ------------------------------------------------------------
# تعديل: إضافة دوال للتحكم في global_debug_params
# ------------------------------------------------------------

def set_global_debug_params(debug_params: 'MefDebugParams'):
    """تعيين معاملات التصحيح العامة للاستخدام في جميع أنحاء السكربت"""
    global global_debug_params
    global_debug_params = debug_params
    print(f"✅ Global debug parameters set: scale={debug_params.v_scale}, swizzle={debug_params.swizzle_mode}")


def get_global_debug_params() -> Optional[MefDebugParams]:
    """الحصول على معاملات التصحيح العامة"""
    return global_debug_params


def reset_global_debug_params():
    """إعادة تعيين المعاملات العامة إلى القيم الافتراضية"""
    global global_debug_params
    global_debug_params = MefDebugParams()
    print("✅ Global debug parameters reset to defaults")
    
    
# ------------------------------------------------------------
# تعديل: تحديث detect_mef_version لاستخدام global_debug_params
# ------------------------------------------------------------
def detect_mef_version(buffer: Buffer, debug_params: Optional[MefDebugParams] = None) -> str:
    """تحديد إصدار MEF (IGI1 أو IGI2) مع دعم القطع الجديدة ومعاملات التصحيح"""
    if debug_params is None:
        debug_params = global_debug_params
    
    saved_pos = buffer.offset
    buffer.offset = 0
    
    try:
        signature = buffer.read(4)
        if signature != b'ILFF':
            raise ValueError("Not an ILFF file")
        
        file_size = buffer.read_uint32()
        align = buffer.read_uint32()
        offset = buffer.read_uint32()
        formatsig = buffer.read(4)
        
        ident = buffer.read(4)
        data_size = buffer.read_uint32()
        
        buffer.offset = saved_pos
        
        # IGI1: HSEM حجم 156 (بدون الهيدر) أو 172 (مع الهيدر)
        # IGI2: HSEM حجم 212 (مع الهيدر)
        if data_size == 156 or data_size == 172:
            return "IGI1"
        elif data_size == 212:
            return "IGI2"
        
        # طريقة احتياطية: البحث عن قطع مميزة
        temp_buffer = Buffer(buffer.data)
        loop_file = LoopFile(temp_buffer, flip_ident=True)
        if loop_file.has_chunk("FACE"):
            return "IGI2"
        elif loop_file.has_chunk("RD3D"):
            return "IGI1"
        # قطع جديدة للكشف عن IGI2
        elif loop_file.has_chunk("XTRW") or loop_file.has_chunk("XTXM") or loop_file.has_chunk("TCST"):
            return "IGI2"
        else:
            raise ValueError("Unknown MEF version")
    except:
        buffer.offset = saved_pos
        raise


# ------------------------------------------------------------
# كلاس مساعد لدمج القوام في أطلس واحد
# ------------------------------------------------------------
class TextureAtlas:
    """يدمج عدة صور في صورة واحدة كبيرة (Texture Atlas) مع تتبع مواقعها"""
    
    def __init__(self, texture_dir: str, max_size: int = 8192):
        """
        Args:
            texture_dir: المجلد الذي يحتوي على ملفات القوام
            max_size: الحد الأقصى لأبعاد الأطلس (عرض وارتفاع)
        """
        self.texture_dir = texture_dir
        self.max_size = max_size
        self.texture_paths = []  # مسارات ملفات القوام
        self.texture_names = []  # أسماء الملفات (للمطابقة)
        self.positions = []      # مواقع القوام في الأطلس (x, y, width, height)
        self.atlas_image = None
        self.atlas_size = (0, 0)
        self.texture_indices = {}  # اسم القوام -> الرقم التسلسلي
        
    def _next_power_of_two(self, n: int) -> int:
        """تقريب الرقم إلى أقرب قوة للعدد 2"""
        return 1 << (n - 1).bit_length()    
    
    def find_texture_file(self, texture_name: str) -> str:
        """البحث عن ملف القوام في texture_dir بالصيغ المدعومة"""
        # قائمة الصيغ المدعومة
        extensions = ['.png', '.PNG', '.tga', '.TGA', '.jpg', '.JPG', '.jpeg', '.JPEG', '.bmp', '.BMP']
        
        # إذا كان الملف موجوداً بالاسم الكامل
        full_path = os.path.join(self.texture_dir, texture_name)
        if os.path.exists(full_path):
            return full_path
        
        # جرب إضافة صيغ مختلفة
        base_name = os.path.splitext(texture_name)[0]
        for ext in extensions:
            test_path = os.path.join(self.texture_dir, base_name + ext)
            if os.path.exists(test_path):
                return test_path
        
        return None
    
    def add_texture(self, texture_name: str) -> bool:
        """إضافة قوام إلى قائمة الانتظار للدمج"""
        file_path = self.find_texture_file(texture_name)
        if file_path:
            self.texture_paths.append(file_path)
            self.texture_names.append(texture_name)
            self.texture_indices[texture_name] = len(self.texture_paths) - 1
            return True
        else:
            print(f"   Warning: Texture '{texture_name}' not found in {self.texture_dir}")
            return False
    
    def pack_textures(self) -> bool:
        """ترتيب القوام في شبكة ودمجها في صورة واحدة"""
        if not self.texture_paths:
            return False
        
        # تحميل جميع الصور
        images = []
        widths = []
        heights = []
        
        for path in self.texture_paths:
            if not os.path.exists(path):
                print(f"   Error: Texture file not found: {path}")
                return False
            try:
                img = Image.open(path)
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                images.append(img)
                widths.append(img.width)
                heights.append(img.height)
            except Exception as e:
                print(f"   Error loading {path}: {e}")
                return False
        
        # حالة صورة واحدة فقط
        if len(images) == 1:
            self.atlas_image = images[0]
            self.positions = [(0, 0, images[0].width, images[0].height)]
            self.atlas_size = (images[0].width, images[0].height)
            return True
        
        # حساب أفضل ترتيب (بسيط: ترتيب تنازلي حسب المساحة)
        indices = list(range(len(images)))
        indices.sort(key=lambda i: -widths[i] * heights[i])
        
        # محاولة الترتيب في شبكة
        # أولاً: جرب ترتيباً أفقياً
        total_width = sum(widths[i] for i in indices)
        max_height = max(heights[i] for i in indices)
        
        if total_width <= self.max_size and max_height <= self.max_size:
            # ترتيب أفقي
            atlas_width = self._next_power_of_two(total_width)
            atlas_height = self._next_power_of_two(max_height)
            
            self.atlas_image = Image.new('RGBA', (atlas_width, atlas_height), (0, 0, 0, 0))
            
            x = 0
            positions = [None] * len(images)
            for idx in indices:
                img = images[idx]
                self.atlas_image.paste(img, (x, 0))
                positions[idx] = (x, 0, img.width, img.height)
                x += img.width
            
            self.positions = positions
            self.atlas_size = (atlas_width, atlas_height)
            return True
        
        # ثانياً: ترتيب في شبكة (تقدير عدد الأعمدة)
        import math
        num_images = len(images)
        cols = int(math.ceil(math.sqrt(num_images)))
        rows = int(math.ceil(num_images / cols))
        
        # حساب أبعاد الخلايا (نأخذ أكبر عرض وارتفاع)
        cell_width = max(widths)
        cell_height = max(heights)
        
        atlas_width = cols * cell_width
        atlas_height = rows * cell_height
        
        # تقريب الأبعاد إلى أقرب قوة للعدد 2
        atlas_width = self._next_power_of_two(atlas_width)
        atlas_height = self._next_power_of_two(atlas_height)
        
        if atlas_width <= self.max_size and atlas_height <= self.max_size:
            self.atlas_image = Image.new('RGBA', (atlas_width, atlas_height), (0, 0, 0, 0))
            
            positions = [None] * len(images)
            for i, idx in enumerate(indices):
                col = i % cols
                row = i // cols
                x = col * cell_width
                y = row * cell_height
                
                img = images[idx]
                # توسيط الصورة في الخلية
                x_offset = (cell_width - img.width) // 2
                y_offset = (cell_height - img.height) // 2
                
                self.atlas_image.paste(img, (x + x_offset, y + y_offset))
                positions[idx] = (x + x_offset, y + y_offset, img.width, img.height)
            
            self.positions = positions
            self.atlas_size = (atlas_width, atlas_height)
            return True
        
        print(f"   Warning: Could not pack textures within {self.max_size}x{self.max_size}")
        return False
    
    def get_uv_transform(self, texture_name: str, original_uvs: np.ndarray) -> np.ndarray:
        """
        تحويل إحداثيات UV من مساحة القوام الأصلي إلى مساحة الأطلس
        """
        import math
        
        if texture_name not in self.texture_indices:
            return original_uvs
        
        idx = self.texture_indices[texture_name]
        if idx >= len(self.positions):
            return original_uvs
        
        x, y, w, h = self.positions[idx]
        atlas_w, atlas_h = self.atlas_size
        
        # ========== التصحيح: تطبيع UVs إلى النطاق [0, 1] ==========
        # إذا كانت UVs خارج النطاق [0,1]، نقوم بتطبيعها باستخدام modulo
        # هذا يحافظ على التكرار (tiling) الصحيح للقوام
        normalized_uvs = original_uvs.copy()
        
        # تطبيع U: نأخذ الجزء الكسري فقط
        # هذا يحافظ على سلوك التكرار (wrap) للقوام عند تجاوز الحدود
        normalized_uvs[:, 0] = normalized_uvs[:, 0] - np.floor(normalized_uvs[:, 0])
        # تطبيع V: نفس الشيء
        normalized_uvs[:, 1] = normalized_uvs[:, 1] - np.floor(normalized_uvs[:, 1])
        
        # أو بدلاً من ذلك، استخدام modulo:
        # normalized_uvs[:, 0] = normalized_uvs[:, 0] % 1.0
        # normalized_uvs[:, 1] = normalized_uvs[:, 1] % 1.0
        # =========================================================
        
        # تحويل الإحداثيات المطبعة
        u_min = x / atlas_w
        v_min = y / atlas_h
        u_max = (x + w) / atlas_w
        v_max = (y + h) / atlas_h
        
        # تطبيق التحويل على كل نقطة مع استخدام UVs المطبعة
        transformed = np.zeros_like(normalized_uvs)
        transformed[:, 0] = u_min + normalized_uvs[:, 0] * (u_max - u_min)
        transformed[:, 1] = v_min + normalized_uvs[:, 1] * (v_max - v_min)
        
        return transformed
    
    def get_texture_index(self, texture_name: str) -> int:
        """الحصول على الرقم التسلسلي للقوام"""
        return self.texture_indices.get(texture_name, -1)
    
    def save_atlas(self, output_path: str, format: str = 'PNG') -> bool:
        """حفظ صورة الأطلس"""
        if self.atlas_image:
            self.atlas_image.save(output_path, format)
            return True
        return False
    
    def has_multiple_textures(self) -> bool:
        """هل هناك أكثر من قوام واحد؟"""
        return len(self.texture_paths) > 1

# ========== إضافة دعم Texture Atlas لـ SMD و OBJ و MDL ==========
# متغير عام للتحكم في ميزة دمج القوام (يمكن تغييره من سطر الأوامر)
ENABLE_TEXTURE_ATLAS_SMD = False   # تفعيل الأطلس لـ SMD
ENABLE_TEXTURE_ATLAS_OBJ = True   # تفعيل الأطلس لـ OBJ
ENABLE_TEXTURE_ATLAS_MDL = True   # تفعيل الأطلس لـ MDL

def enable_texture_atlas_for_all(enable: bool = True):
    """تفعيل أو إيقاف ميزة دمج القوام لجميع الصيغ"""
    global ENABLE_TEXTURE_ATLAS_SMD, ENABLE_TEXTURE_ATLAS_OBJ, ENABLE_TEXTURE_ATLAS_MDL
    ENABLE_TEXTURE_ATLAS_SMD = enable
    ENABLE_TEXTURE_ATLAS_OBJ = enable
    ENABLE_TEXTURE_ATLAS_MDL = enable
    print(f"✅ Texture Atlas for all formats: {'ENABLED' if enable else 'DISABLED'}")

# ========== دوال مساعدة للأطلس لجميع الصيغ ==========

def collect_textures_from_materials(materials: List[Dict], base_name: str) -> List[str]:
    """
    جمع أسماء ملفات القوام من قائمة المواد
    
    Args:
        materials: قائمة المواد (كل مادة تحتوي على texture_name أو texture_index)
        base_name: الاسم الأساسي للنموذج
    
    Returns:
        قائمة بأسماء ملفات القوام الفريدة
    """
    texture_names = set()
    
    for i, mat in enumerate(materials):
        # محاولة استخراج اسم القوام بطرق مختلفة
        tex_name = None
        
        if isinstance(mat, dict):
            tex_name = mat.get('texture_name')
            if not tex_name and 'diffuse_texture' in mat:
                tex_name = mat.get('diffuse_texture')
            if not tex_name and 'texture_index' in mat:
                tex_idx = mat.get('texture_index', 0)
                tex_name = get_texture_name(tex_idx, base_name, i, None)
        
        if tex_name:
            # تنظيف اسم الملف
            tex_name = os.path.basename(tex_name)
            # إزالة المسار إذا وجد
            tex_name = tex_name.replace('\\', '/').split('/')[-1]
            texture_names.add(tex_name)
    
    # إذا لم يتم العثور على أي قوام، نضيف افتراضياً
    if not texture_names:
        texture_names.add(f"{base_name}.tga")
    
    return list(texture_names)


def create_atlas_for_model(model_obj, texture_dir: str, base_name: str, 
                           texture_names: List[str] = None) -> Optional[TextureAtlas]:
    """
    إنشاء أطلس قوام لنموذج معين
    
    Args:
        model_obj: كائن النموذج (SMDExporter, OBJExporter, StudioHeader, أو MdlModel)
        texture_dir: المجلد الذي يحتوي على ملفات القوام
        base_name: الاسم الأساسي للنموذج
        texture_names: قائمة بأسماء القوام (إذا كانت None، سيتم جمعها تلقائياً)
    
    Returns:
        كائن TextureAtlas أو None إذا فشل الإنشاء
    """
    if not PIL_AVAILABLE:
        print("   ⚠️ PIL not available, cannot create texture atlas")
        return None
    
    # جمع أسماء القوام
    if texture_names is None:
        if hasattr(model_obj, 'get_texture_names'):
            texture_names = model_obj.get_texture_names()
        elif hasattr(model_obj, 'materials'):
            texture_names = collect_textures_from_materials(model_obj.materials, base_name)
        else:
            # محاولة استخراج من خصائص مختلفة
            texture_names = []
            if hasattr(model_obj, 'textures'):
                for tex in model_obj.textures:
                    if hasattr(tex, 'name'):
                        texture_names.append(tex.name)
    
    if not texture_names:
        print("   ⚠️ No textures found for atlas creation")
        return None
    
    # إذا كان هناك قوام واحد فقط، لا حاجة للأطلس
    if len(texture_names) == 1:
        print(f"   ℹ️ Single texture only, skipping atlas creation")
        return None
    
    # البحث عن مجلد القوام
    texture_dirs = [
        texture_dir,
        os.path.join(texture_dir, "textures"),
        os.path.join(os.path.dirname(texture_dir), "textures"),
        os.getcwd(),
        os.path.join(os.getcwd(), "textures")
    ]
    
    atlas = None
    for tex_dir in texture_dirs:
        if os.path.exists(tex_dir):
            atlas = TextureAtlas(tex_dir)
            break
    
    if atlas is None:
        atlas = TextureAtlas(texture_dir)
    
    # إضافة القوام إلى الأطلس
    for tex_name in texture_names:
        atlas.add_texture(tex_name)
    
    # دمج القوام
    if atlas.has_multiple_textures():
        if atlas.pack_textures():
            atlas_path = os.path.join(texture_dir, f"{base_name}_atlas.png")
            atlas.save_atlas(atlas_path, 'PNG')
            print(f"   ✅ Created texture atlas: {atlas_path} ({atlas.atlas_size[0]}x{atlas.atlas_size[1]})")
            print(f"      Textures merged: {len(atlas.texture_paths)} → 1")
            return atlas
    
    return None


def update_uvs_with_atlas(uvs: np.ndarray, atlas: TextureAtlas, texture_name: str) -> np.ndarray:
    """
    تحديث إحداثيات UV لاستخدام الأطلس
    
    Args:
        uvs: مصفوفة الإحداثيات الأصلية (N, 2)
        atlas: كائن TextureAtlas
        texture_name: اسم القوام الأصلي
    
    Returns:
        مصفوفة الإحداثيات الجديدة
    """
    if atlas is None or not atlas.has_multiple_textures():
        return uvs
    
    if texture_name not in atlas.texture_indices:
        return uvs
    
    return atlas.get_uv_transform(texture_name, uvs)


def update_mtl_to_use_atlas(mtl_path: str, atlas_name: str):
    """
    تحديث ملف MTL لاستخدام الأطلس بدلاً من القوام الفردية
    """
    if not os.path.exists(mtl_path):
        return
    
    with open(mtl_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # استبدال جميع map_Kd و map_Ke بالإشارة إلى الأطلس
    lines = content.split('\n')
    new_lines = []
    
    for line in lines:
        if line.startswith('map_Kd ') or line.startswith('map_Ke '):
            new_lines.append(f"map_Kd {atlas_name}")
        else:
            new_lines.append(line)
    
    with open(mtl_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    
    print(f"   Updated MTL to use atlas: {mtl_path}")


# ========== تحديث SMDExporter لدعم Texture Atlas ==========

def add_atlas_support_to_smd():
    """إضافة دوال دعم الأطلس إلى SMDExporter"""
    
    # حفظ المراجع الأصلية
    original_export_obj = SMDExporter.export_obj
    original_export_gltf = SMDExporter.export_gltf
    original_export_all = SMDExporter.export_all
    
    def get_texture_names_from_smd(self) -> List[str]:
        """استخراج أسماء القوام من SMD"""
        # SMD لا يحتوي على معلومات مباشرة عن القوام، نستخدم اسم افتراضي
        return ["texture.png"]
    
    def export_obj_with_atlas(self, output_path: str):
        """تصدير SMD إلى OBJ مع دعم المواد المتعددة - نسخة محسنة"""
        vertices, faces = self.to_vertices_array()
        
        if len(vertices) == 0:
            print("No vertices to export")
            return
        
        base_name = os.path.splitext(output_path)[0]
        obj_path = f"{base_name}.obj"
        mtl_path = f"{base_name}.mtl"
        
        # ========== استخدام المواد المستخرجة من SMD ==========
        material_names = []
        face_to_material = {}
        
        if hasattr(self, 'materials') and self.materials:
            material_names = self.materials
            print(f"   Using {len(material_names)} materials from SMD: {material_names}")
            
            # بناء تعيين من مؤشر الوجه إلى اسم المادة
            if hasattr(self, 'material_triangle_indices') and self.material_triangle_indices:
                for mat_name, tri_indices in self.material_triangle_indices.items():
                    for tri_idx in tri_indices:
                        face_to_material[tri_idx] = mat_name
                print(f"   Mapped {len(face_to_material)} faces to materials")
        else:
            material_names = ["smd_material"]
            print(f"   No materials found in SMD, using default material")
        
        # ========== تجميع الوجوه حسب المادة ==========
        material_faces_map = {}
        for mat_name in material_names:
            material_faces_map[mat_name] = []
        
        if face_to_material:
            for face_idx, face in enumerate(faces):
                mat_name = face_to_material.get(face_idx, material_names[0])
                if mat_name not in material_faces_map:
                    material_faces_map[mat_name] = []
                material_faces_map[mat_name].append(face)
        else:
            material_faces_map[material_names[0]] = faces
        
        # ========== التحقق من تفعيل الأطلس ==========
        use_atlas = ENABLE_TEXTURE_ATLAS_SMD and PIL_AVAILABLE
        atlas = None
        
        if use_atlas and len(material_names) > 1:
            texture_dir = os.path.dirname(output_path)
            atlas = create_atlas_for_model(self, texture_dir, os.path.basename(base_name), material_names)
            use_atlas = atlas and atlas.has_multiple_textures()
        
        # ========== كتابة ملف MTL ==========
        with open(mtl_path, 'w', encoding='utf-8') as f:
            for mat_name in material_names:
                # تنظيف اسم المادة
                clean_mat_name = mat_name.replace('\\', '/').split('/')[-1]
                clean_mat_name = clean_mat_name.split('.')[0] if '.' in clean_mat_name else clean_mat_name
                clean_mat_name = clean_mat_name.replace(' ', '_').replace('-', '_')
                if not clean_mat_name:
                    clean_mat_name = f"material_{material_names.index(mat_name)}"
                
                # اسم ملف القوام
                if use_atlas and atlas:
                    tex_file = f"{os.path.basename(base_name)}_atlas.png"
                else:
                    tex_file = mat_name
                    if not tex_file.endswith('.tga') and not tex_file.endswith('.png') and not tex_file.endswith('.bmp'):
                        tex_file = f"{clean_mat_name}.png"
                
                f.write(f"newmtl {clean_mat_name}\n")
                f.write("Ns 10.0000\n")
                f.write("Ka 1.0000 1.0000 1.0000\n")
                f.write("Kd 1.0000 1.0000 1.0000\n")
                f.write("Ks 0.0000 0.0000 0.0000\n")
                f.write(f"map_Kd {tex_file}\n")
                f.write("\n")
        
        # ========== تحديث UVs إذا كان الأطلس مفعلاً ==========
        if use_atlas and atlas:
            print(f"\n   🔧 Updating SMD UVs for atlas...")
            all_uvs = np.array([[v['u'], v['v']] for v in vertices])
            # استخدام أول مادة للأطلس
            first_texture = list(material_names)[0] if material_names else "texture.png"
            new_uvs = atlas.get_uv_transform(first_texture, all_uvs)
            for i, v in enumerate(vertices):
                v['u'] = new_uvs[i, 0]
                v['v'] = new_uvs[i, 1]
            print(f"   ✅ Updated {len(vertices)} vertices UVs")
        
        # ========== كتابة ملف OBJ ==========
        with open(obj_path, 'w', encoding='utf-8') as f:
            f.write(f"mtllib {os.path.basename(mtl_path)}\n")
            f.write(f"o {os.path.basename(base_name)}\n")
            
            # كتابة الرؤوس
            for v in vertices:
                f.write(f"v {v['px']:.6f} {v['py']:.6f} {v['pz']:.6f}\n")
            
            # كتابة إحداثيات النسيج
            for v in vertices:
                f.write(f"vt {v['u']:.6f} {1.0 - v['v']:.6f}\n")
            
            # كتابة الطبيعيات
            for v in vertices:
                f.write(f"vn {v['nx']:.6f} {v['ny']:.6f} {v['nz']:.6f}\n")
            
            # كتابة الوجوه حسب المادة
            total_faces_written = 0
            for mat_name, material_faces in material_faces_map.items():
                if not material_faces:
                    continue
                
                # تنظيف اسم المادة
                clean_mat_name = mat_name.replace('\\', '/').split('/')[-1]
                clean_mat_name = clean_mat_name.split('.')[0] if '.' in clean_mat_name else clean_mat_name
                clean_mat_name = clean_mat_name.replace(' ', '_').replace('-', '_')
                if not clean_mat_name:
                    clean_mat_name = f"material_{material_names.index(mat_name)}"
                
                f.write(f"usemtl {clean_mat_name}\n")
                
                for face in material_faces:
                    a, b, c = face[0] + 1, face[1] + 1, face[2] + 1
                    f.write(f"f {a}/{a}/{a} {b}/{b}/{b} {c}/{c}/{c}\n")
                    total_faces_written += 1
            
            # Fallback إذا لم يتم كتابة أي وجه
            if total_faces_written == 0:
                f.write(f"usemtl smd_material\n")
                for face in faces:
                    a, b, c = face[0] + 1, face[1] + 1, face[2] + 1
                    f.write(f"f {a}/{a}/{a} {b}/{b}/{b} {c}/{c}/{c}\n")
        
        print(f"   OBJ: {obj_path} (with {len(material_names)} materials)")
        print(f"   MTL: {mtl_path} (with {len(material_names)} materials)")
        
        # طباعة ملخص المواد للتحقق
        print(f"\n   📋 Materials summary:")
        for mat_name in material_names:
            face_count = len(material_faces_map.get(mat_name, []))
            print(f"      - {mat_name}: {face_count} faces")
    
    def export_gltf_with_atlas(self, output_path: str):
        """تصدير SMD إلى glTF مع دعم الأطلس"""
        if not GLTF_AVAILABLE:
            print("   pygltflib not available, skipping glTF export")
            return
        
        vertices, faces = self.to_vertices_array()
        
        if len(vertices) == 0:
            print("No vertices to export")
            return
        
        base_name = os.path.splitext(output_path)[0]
        
        # التحقق من تفعيل الأطلس
        use_atlas = ENABLE_TEXTURE_ATLAS_SMD and PIL_AVAILABLE
        atlas = None
        
        if use_atlas:
            texture_dir = os.path.dirname(output_path)
            atlas = create_atlas_for_model(self, texture_dir, os.path.basename(base_name))
            use_atlas = atlas and atlas.has_multiple_textures()
            
            if use_atlas and atlas:
                # ========== 🔴 تحديث UVs مباشرة في مصفوفة vertices ==========
                print(f"\n   🔧 Updating SMD UVs for atlas (glTF)...")
                all_uvs = np.array([[v['u'], v['v']] for v in vertices])
                first_texture = list(atlas.texture_names)[0] if atlas.texture_names else "texture.png"
                new_uvs = atlas.get_uv_transform(first_texture, all_uvs)
                for i, v in enumerate(vertices):
                    v['u'] = new_uvs[i, 0]
                    v['v'] = new_uvs[i, 1]
                print(f"   ✅ Updated {len(vertices)} vertices UVs")
        
        try:
            from pygltflib import GLTF2, Buffer, BufferView, Accessor, Mesh, Primitive, Attributes, Asset, Scene, Node, Skin
            
            gltf = GLTF2()
            gltf.asset = Asset(generator="SMD Exporter (Crowbar)", version="2.0")
            
            positions = []
            normals = []
            uvs = []
            weights = []
            joints = []
            
            for v in vertices:
                positions.extend([v['px'], v['py'], v['pz']])
                normals.extend([v['nx'], v['ny'], v['nz']])
                uvs.extend([v['u'], 1.0 - v['v']])
                weights.extend([v['weight'], 0.0, 0.0, 0.0])
                joints.extend([v['bone_id'], 0, 0, 0])
            
            binary_data = bytearray()
            
            # Positions
            pos_bytes = np.array(positions, dtype=np.float32).tobytes()
            pos_bv = BufferView(buffer=0, byteOffset=len(binary_data), byteLength=len(pos_bytes), target=34962)
            gltf.bufferViews.append(pos_bv)
            binary_data.extend(pos_bytes)
            
            pos_acc = Accessor(bufferView=len(gltf.bufferViews)-1, componentType=5126,
                               count=len(vertices), type="VEC3")
            gltf.accessors.append(pos_acc)
            
            # Normals
            norm_bytes = np.array(normals, dtype=np.float32).tobytes()
            norm_bv = BufferView(buffer=0, byteOffset=len(binary_data), byteLength=len(norm_bytes), target=34962)
            gltf.bufferViews.append(norm_bv)
            binary_data.extend(norm_bytes)
            
            norm_acc = Accessor(bufferView=len(gltf.bufferViews)-1, componentType=5126,
                                count=len(vertices), type="VEC3")
            gltf.accessors.append(norm_acc)
            
            # UVs
            uv_bytes = np.array(uvs, dtype=np.float32).tobytes()
            uv_bv = BufferView(buffer=0, byteOffset=len(binary_data), byteLength=len(uv_bytes), target=34962)
            gltf.bufferViews.append(uv_bv)
            binary_data.extend(uv_bytes)
            
            uv_acc = Accessor(bufferView=len(gltf.bufferViews)-1, componentType=5126,
                              count=len(vertices), type="VEC2")
            gltf.accessors.append(uv_acc)
            
            # Weights
            weights_bytes = np.array(weights, dtype=np.float32).tobytes()
            weights_bv = BufferView(buffer=0, byteOffset=len(binary_data), byteLength=len(weights_bytes), target=34962)
            gltf.bufferViews.append(weights_bv)
            binary_data.extend(weights_bytes)
            
            weights_acc = Accessor(bufferView=len(gltf.bufferViews)-1, componentType=5126,
                                   count=len(vertices), type="VEC4")
            gltf.accessors.append(weights_acc)
            
            # Joints
            joints_bytes = np.array(joints, dtype=np.uint16).tobytes()
            joints_bv = BufferView(buffer=0, byteOffset=len(binary_data), byteLength=len(joints_bytes), target=34962)
            gltf.bufferViews.append(joints_bv)
            binary_data.extend(joints_bytes)
            
            joints_acc = Accessor(bufferView=len(gltf.bufferViews)-1, componentType=5123,
                                  count=len(vertices), type="VEC4")
            gltf.accessors.append(joints_acc)
            
            # Indices
            indices_list = []
            for face in faces:
                indices_list.extend([face[0], face[1], face[2]])
            
            indices_bytes = np.array(indices_list, dtype=np.uint32).tobytes()
            indices_bv = BufferView(buffer=0, byteOffset=len(binary_data), byteLength=len(indices_bytes), target=34963)
            gltf.bufferViews.append(indices_bv)
            binary_data.extend(indices_bytes)
            
            indices_acc = Accessor(bufferView=len(gltf.bufferViews)-1, componentType=5125,
                                   count=len(indices_list), type="SCALAR")
            gltf.accessors.append(indices_acc)
            
            # Buffer
            base_filename = os.path.splitext(os.path.basename(output_path))[0]
            gltf.buffers.append(Buffer(byteLength=len(binary_data), uri=f"{base_filename}.bin"))
            
            attributes = Attributes(POSITION=0, NORMAL=1, TEXCOORD_0=2, WEIGHTS_0=3, JOINTS_0=4)
            primitive = Primitive(attributes=attributes, indices=len(gltf.accessors)-1, material=0)
            mesh = Mesh(primitives=[primitive])
            gltf.meshes.append(mesh)
            
            # العظام
            if self.nodes:
                bone_nodes = []
                for node in self.nodes:
                    gltf_node = Node(name=node.name)
                    gltf.nodes.append(gltf_node)
                    bone_nodes.append(len(gltf.nodes)-1)
                
                for i, node in enumerate(self.nodes):
                    if node.parent_id >= 0:
                        parent_idx = None
                        for j, n in enumerate(self.nodes):
                            if n.id == node.parent_id:
                                parent_idx = bone_nodes[j]
                                break
                        if parent_idx is not None:
                            if gltf.nodes[parent_idx].children is None:
                                gltf.nodes[parent_idx].children = []
                            gltf.nodes[parent_idx].children.append(bone_nodes[i])
                
                skin = Skin(joints=bone_nodes)
                gltf.skins.append(skin)
                
                node = Node(mesh=0, skin=len(gltf.skins)-1)
                gltf.nodes.append(node)
                scene = Scene(nodes=[len(gltf.nodes)-1])
            else:
                node = Node(mesh=0)
                gltf.nodes.append(node)
                scene = Scene(nodes=[0])
            
            gltf.scenes.append(scene)
            gltf.scene = 0
            
            gltf.save(f"{output_path}.gltf")
            with open(f"{os.path.splitext(output_path)[0]}.bin", 'wb') as f:
                f.write(binary_data)
            
            if use_atlas:
                print(f"   glTF: {output_path}.gltf (using texture atlas)")
            else:
                print(f"   glTF: {output_path}.gltf")
            print(f"   glTF binary: {os.path.splitext(output_path)[0]}.bin")
            
        except Exception as e:
            print(f"   Error exporting glTF: {e}")
            import traceback
            traceback.print_exc()
    
    def export_all_with_atlas(self, output_dir: str, base_name: str, export_formats: List[str] = None):
        """تصدير SMD إلى جميع الصيغ مع دعم الأطلس"""
        if export_formats is None:
            export_formats = ["obj", "gltf", "json", "txt"]
        
        self.ensure_dir(output_dir)
        
        print(f"\nExporting SMD to {output_dir}")
        print("-" * 50)
        
        if "obj" in export_formats:
            export_obj_with_atlas(self, os.path.join(output_dir, base_name))
        
        if "gltf" in export_formats:
            export_gltf_with_atlas(self, os.path.join(output_dir, base_name))
        
        if "json" in export_formats:
            self.export_json(os.path.join(output_dir, f"{base_name}.json"))
        
        if "txt" in export_formats:
            self.export_txt(os.path.join(output_dir, f"{base_name}_info.txt"))
        
        print("-" * 50)
        print("Export completed successfully!")
    
    # تطبيق الدوال الجديدة
    SMDExporter.export_obj = export_obj_with_atlas
    SMDExporter.export_gltf = export_gltf_with_atlas
    SMDExporter.export_all = export_all_with_atlas
    SMDExporter.get_texture_names = get_texture_names_from_smd


# ========== تحديث OBJExporter لدعم Texture Atlas ==========

def add_atlas_support_to_obj():
    """إضافة دوال دعم الأطلس إلى OBJExporter"""
    
    # حفظ المراجع الأصلية
    original_export_obj = OBJExporter.export_obj
    original_export_gltf = OBJExporter.export_gltf
    original_export_all = OBJExporter.export_all
    
    def get_texture_names_from_obj(self) -> List[str]:
        texture_names = []
        # الحفاظ على الترتيب كما هو في المواد
        for mat in self.materials.values():
            if mat.diffuse_texture:
                tex_name = os.path.basename(mat.diffuse_texture)
                tex_name = tex_name.replace('\\', '/').split('/')[-1]
                if tex_name not in texture_names:
                    texture_names.append(tex_name)
        if not texture_names:
            texture_names.append("texture.png")
        return texture_names  # يحافظ على الترتيب الأصلي
    
    def debug_uv_transform(self, atlas: TextureAtlas, material_name: str, vt_indices: List[int], orig_texture: str):
        """دالة تشخيصية لطباعة UVs قبل وبعد التحويل"""
        print(f"\n   🔍 DEBUG: Material '{material_name}' (texture: {orig_texture})")
        for vt_idx in vt_indices[:5]:
            if 0 <= vt_idx < len(self._all_texture_vertices):
                vt = self._all_texture_vertices[vt_idx]
                print(f"     VT {vt_idx}: original=({vt.u:.4f}, {vt.v:.4f})")
                
                # تطبيق التحويل
                uvs_array = np.array([[vt.u, vt.v]])
                new_uvs = atlas.get_uv_transform(orig_texture, uvs_array)
                print(f"       after atlas=({new_uvs[0,0]:.4f}, {new_uvs[0,1]:.4f})")

    def export_obj_with_atlas(self, output_path: str):
        """تصدير OBJ مع دعم الأطلس - مع تحديث UVs بشكل صحيح"""
        base_name = os.path.splitext(output_path)[0]
        obj_path = f"{base_name}.obj"
        mtl_path = f"{base_name}.mtl"
        
        # التحقق من تفعيل الأطلس ووضعه
        use_atlas = ENABLE_TEXTURE_ATLAS_OBJ and PIL_AVAILABLE
        atlas_mode = ATLAS_MODE  # استخدام الوضع العام
        atlas = None
        updated_texture_vertices = None
        
        if use_atlas:
            texture_dir = os.path.dirname(output_path)
            texture_names = self.get_texture_names()
            atlas = create_atlas_for_model(self, texture_dir, os.path.basename(base_name), texture_names)
            use_atlas = atlas and atlas.has_multiple_textures()
            
            if use_atlas:
                # ========== 🔴 التصحيح: بناء قائمة vt محدثة ==========
                print(f"\n   🔧 Building updated UV coordinates for atlas... (mode: {atlas_mode})")
                updated_texture_vertices = []
                
                # إنشاء cache لتحويلات UV لكل VT ومادة
                vt_transform_cache = {}  # (vt_index, material_name) -> (new_u, new_v)
                
                # أولاً: تجميع كل الوجوه لمعرفة أي VT يستخدم مع أي مادة
                for obj in self.objects:
                    for face in obj.faces:
                        mat_name = face.material_name
                        for i in range(len(face.texture_indices)):
                            vt_idx = face.texture_indices[i] - 1 if i < len(face.texture_indices) else -1
                            if vt_idx >= 0:
                                key = (vt_idx, mat_name)
                                if key not in vt_transform_cache:
                                    # الحصول على القوام الأصلي للمادة
                                    orig_texture = "texture.png"
                                    if mat_name in self.materials and self.materials[mat_name].diffuse_texture:
                                        orig_texture = os.path.basename(self.materials[mat_name].diffuse_texture)
                                        orig_texture = orig_texture.replace('\\', '/').split('/')[-1]
                                    
                                    # الحصول على UV الأصلي
                                    if 0 <= vt_idx < len(self._all_texture_vertices):
                                        vt = self._all_texture_vertices[vt_idx]
                                        u_orig, v_orig = vt.u, vt.v
                                        
                                        # تطبيع UVs إلى النطاق [0, 1]
                                        import math
                                        u_orig = u_orig - math.floor(u_orig)
                                        v_orig = v_orig - math.floor(v_orig)
                                    else:
                                        u_orig, v_orig = 0, 0
                                    
                                    # تطبيق تحويل الأطلس
                                    if orig_texture in atlas.texture_indices:
                                        uvs_array = np.array([[u_orig, v_orig]])
                                        new_uvs = atlas.get_uv_transform(orig_texture, uvs_array)
                                        vt_transform_cache[key] = (new_uvs[0, 0], new_uvs[0, 1])
                                    else:
                                        vt_transform_cache[key] = (u_orig, v_orig)
                
                # بناء قائمة vt المحدثة (نحافظ على نفس الترتيب)
                for vt_idx, vt in enumerate(self._all_texture_vertices):
                    # نأخذ أول مادة تستخدم هذا vt (افتراضي)
                    new_u, new_v = vt.u, vt.v
                    
                    # البحث عن تحويل لهذا vt
                    for (cached_vt_idx, mat_name), (u_new, v_new) in vt_transform_cache.items():
                        if cached_vt_idx == vt_idx:
                            new_u, new_v = u_new, v_new
                            break
                    
                    # الحفاظ على w إذا كانت موجودة
                    if vt.w != 0.0:
                        updated_texture_vertices.append(OBJTextureVertex(new_u, new_v, vt.w))
                    else:
                        updated_texture_vertices.append(OBJTextureVertex(new_u, new_v))
                
                print(f"   ✅ Built {len(updated_texture_vertices)} updated UV coordinates")
        
         # كتابة ملف MTL حسب الوضع المختار
        with open(mtl_path, 'w', encoding='utf-8') as f:
            if use_atlas and atlas:
                atlas_name = f"{os.path.basename(base_name)}_atlas.png"
                
                if atlas_mode == "merge":
                    # ========== وضع الدمج: مادة واحدة ==========
                    f.write(f"newmtl atlas_material\n")
                    f.write("Ns 10.0000\n")
                    f.write("Ka 1.0000 1.0000 1.0000\n")
                    f.write("Kd 1.0000 1.0000 1.0000\n")
                    f.write("Ks 0.0000 0.0000 0.0000\n")
                    f.write(f"map_Kd {atlas_name}\n")
                    print(f"   ✅ MTL mode: MERGE (single 'atlas_material')")
                    
                else:  # atlas_mode == "preserve"
                    # ========== وضع الحفاظ على المواد ==========
                    for name, mat in self.materials.items():
                        f.write(f"newmtl {mat.name}\n")
                        f.write(f"Ns {mat.shininess:.6f}\n")
                        f.write(f"Ka {mat.ambient[0]:.6f} {mat.ambient[1]:.6f} {mat.ambient[2]:.6f}\n")
                        f.write(f"Kd {mat.diffuse[0]:.6f} {mat.diffuse[1]:.6f} {mat.diffuse[2]:.6f}\n")
                        f.write(f"Ks {mat.specular[0]:.6f} {mat.specular[1]:.6f} {mat.specular[2]:.6f}\n")
                        f.write(f"map_Kd {atlas_name}\n")  # فقط تغيير مسار الصورة
                        f.write("\n")
                    print(f"   ✅ MTL mode: PRESERVE (keeping {len(self.materials)} materials, using atlas)")
            else:
                # مواد متعددة بدون أطلس
                for name, mat in self.materials.items():
                    f.write(f"newmtl {mat.name}\n")
                    f.write(f"Ns {mat.shininess:.6f}\n")
                    f.write(f"Ka {mat.ambient[0]:.6f} {mat.ambient[1]:.6f} {mat.ambient[2]:.6f}\n")
                    f.write(f"Kd {mat.diffuse[0]:.6f} {mat.diffuse[1]:.6f} {mat.diffuse[2]:.6f}\n")
                    f.write(f"Ks {mat.specular[0]:.6f} {mat.specular[1]:.6f} {mat.specular[2]:.6f}\n")
                    if mat.diffuse_texture:
                        f.write(f"map_Kd {mat.diffuse_texture}\n")
                    f.write("\n")
        
        # كتابة ملف OBJ
        with open(obj_path, 'w', encoding='utf-8') as f:
            if self.material_libs:
                for lib in self.material_libs:
                    f.write(f"mtllib {lib}\n")
            elif self.materials:
                f.write(f"mtllib {os.path.basename(mtl_path)}\n")
            
            # كتابة الرؤوس (بدون تغيير)
            for v in self._all_vertices:
                f.write(f"v {v.x:.6f} {v.y:.6f} {v.z:.6f}\n")
            
            # ========== 🔴 كتابة إحداثيات النسيج المحدثة ==========
            if use_atlas and atlas and updated_texture_vertices:
                for vt in updated_texture_vertices:
                    if vt.w != 0.0:
                        f.write(f"vt {vt.u:.6f} {vt.v:.6f} {vt.w:.6f}\n")
                    else:
                        f.write(f"vt {vt.u:.6f} {vt.v:.6f}\n")
            else:
                # الوضع العادي
                for vt in self._all_texture_vertices:
                    if vt.w != 0.0:
                        f.write(f"vt {vt.u:.6f} {vt.v:.6f} {vt.w:.6f}\n")
                    else:
                        f.write(f"vt {vt.u:.6f} {vt.v:.6f}\n")
            
            # كتابة الطبيعيات (بدون تغيير)
            for vn in self._all_normals:
                f.write(f"vn {vn.x:.6f} {vn.y:.6f} {vn.z:.6f}\n")
            
            # كتابة الكائنات والوجوه
            if use_atlas and atlas and atlas_mode == "merge":
                # ========== وضع الدمج: usemtl واحد فقط ==========
                f.write(f"usemtl atlas_material\n")
                for obj in self.objects:
                    if obj.name:
                        f.write(f"o {obj.name}\n")
                    for face in obj.faces:
                        f.write("f")
                        for i in range(len(face.vertex_indices)):
                            v_idx = face.vertex_indices[i]
                            vt_idx = face.texture_indices[i] if i < len(face.texture_indices) else 0
                            vn_idx = face.normal_indices[i] if i < len(face.normal_indices) else 0
                            
                            if vt_idx > 0 and vn_idx > 0:
                                f.write(f" {v_idx}/{vt_idx}/{vn_idx}")
                            elif vt_idx > 0:
                                f.write(f" {v_idx}/{vt_idx}")
                            elif vn_idx > 0:
                                f.write(f" {v_idx}//{vn_idx}")
                            else:
                                f.write(f" {v_idx}")
                        f.write("\n")
            else:
                # ========== الوضع العادي أو وضع الحفاظ ==========
                for obj in self.objects:
                    if obj.name:
                        f.write(f"o {obj.name}\n")
                    
                    current_mat = None
                    for face in obj.faces:
                        if use_atlas and atlas:
                            # في وضع الحفاظ، نستخدم اسم المادة الأصلي
                            mat_name = face.material_name
                        else:
                            mat_name = face.material_name
                        
                        if mat_name != current_mat:
                            current_mat = mat_name
                            f.write(f"usemtl {current_mat}\n")
                        
                        f.write("f")
                        for i in range(len(face.vertex_indices)):
                            v_idx = face.vertex_indices[i]
                            vt_idx = face.texture_indices[i] if i < len(face.texture_indices) else 0
                            vn_idx = face.normal_indices[i] if i < len(face.normal_indices) else 0
                            
                            if vt_idx > 0 and vn_idx > 0:
                                f.write(f" {v_idx}/{vt_idx}/{vn_idx}")
                            elif vt_idx > 0:
                                f.write(f" {v_idx}/{vt_idx}")
                            elif vn_idx > 0:
                                f.write(f" {v_idx}//{vn_idx}")
                            else:
                                f.write(f" {v_idx}")
                        f.write("\n")
        
        if use_atlas:
            print(f"   OBJ (with atlas, UVs updated): {obj_path}")
        else:
            print(f"   OBJ: {obj_path}")
        print(f"   MTL: {mtl_path}")
    
    def export_gltf_with_atlas(self, output_path: str):
        """تصدير OBJ إلى glTF مع دعم الأطلس - نسخة محسنة مع تتبع VT"""
        if not GLTF_AVAILABLE:
            print("   pygltflib not available, skipping glTF export")
            return
        
        base_name = os.path.splitext(output_path)[0]
        
        # التحقق من تفعيل الأطلس
        use_atlas = ENABLE_TEXTURE_ATLAS_OBJ and PIL_AVAILABLE
        atlas = None
        
        # جمع أسماء القوام (بحاجة للتشخيص)
        texture_names = self.get_texture_names()
        print(f"   Found textures: {texture_names}")
        
        if use_atlas and len(texture_names) > 1:
            texture_dir = os.path.dirname(output_path)
            atlas = create_atlas_for_model(self, texture_dir, os.path.basename(base_name), texture_names)
            use_atlas = atlas and atlas.has_multiple_textures()
            
            if use_atlas and atlas:
                print(f"\n   📊 ATLAS DIAGNOSTIC:")
                print(f"   Atlas size: {atlas.atlas_size[0]}x{atlas.atlas_size[1]}")
                print(f"   Atlas positions: {atlas.positions}")
                print(f"   Texture indices: {atlas.texture_indices}")
                print(f"\n   📍 Texture regions in atlas:")
                for tex_name, idx in atlas.texture_indices.items():
                    x, y, w, h = atlas.positions[idx]
                    u_min = x / atlas.atlas_size[0]
                    u_max = (x + w) / atlas.atlas_size[0]
                    v_min = y / atlas.atlas_size[1]
                    v_max = (y + h) / atlas.atlas_size[1]
                    print(f"     {tex_name}: pos=({x},{y}), size=({w},{h})")
                    print(f"       -> UV range: u=[{u_min:.3f}-{u_max:.3f}], v=[{v_min:.3f}-{v_max:.3f}]")
        
        # ========== بناء cache لتحويلات VT ==========
        vt_transform_cache = {}  # (vt_idx, material_name) -> (new_u, new_v)
        material_vt_map = {}     # material_name -> list of vt_idx (للتشخيص)
        
        for obj in self.objects:
            for face in obj.faces:
                mat_name = face.material_name
                
                # اسم القوام الأصلي للمادة
                orig_texture = "texture.png"
                if mat_name in self.materials and self.materials[mat_name].diffuse_texture:
                    orig_texture = os.path.basename(self.materials[mat_name].diffuse_texture)
                    orig_texture = orig_texture.replace('\\', '/').split('/')[-1]
                
                for i in range(len(face.texture_indices)):
                    vt_idx = face.texture_indices[i] - 1 if i < len(face.texture_indices) else -1
                    if vt_idx >= 0:
                        # تجميع VT لكل مادة للتشخيص
                        if mat_name not in material_vt_map:
                            material_vt_map[mat_name] = []
                        if vt_idx not in material_vt_map[mat_name]:
                            material_vt_map[mat_name].append(vt_idx)
                        
                        key = (vt_idx, mat_name)
                        if key not in vt_transform_cache:
                            # الحصول على UV الأصلي
                            if 0 <= vt_idx < len(self._all_texture_vertices):
                                vt = self._all_texture_vertices[vt_idx]
                                u_orig, v_orig = vt.u, vt.v
                                
                                # ========== تصحيح: تطبيع UVs إلى النطاق [0, 1] ==========
                                import math
                                u_orig = u_orig - math.floor(u_orig)
                                v_orig = v_orig - math.floor(v_orig)
                            else:
                                u_orig, v_orig = 0, 0
                            
                            # تطبيق تحويل الأطلس
                            if use_atlas and atlas and orig_texture in atlas.texture_indices:
                                uvs_array = np.array([[u_orig, v_orig]])
                                new_uvs = atlas.get_uv_transform(orig_texture, uvs_array)
                                vt_transform_cache[key] = (new_uvs[0, 0], new_uvs[0, 1])
                            else:
                                vt_transform_cache[key] = (u_orig, v_orig)
        
        # تشخيص: طباعة تحويلات UVs (اختياري، يمكن تعطيله)
        if use_atlas and atlas and False:  # set to True for debugging
            print(f"\n   🔬 UV TRANSFORM DIAGNOSTIC:")
            for mat_name, vt_list in material_vt_map.items():
                orig_texture = "texture.png"
                if mat_name in self.materials and self.materials[mat_name].diffuse_texture:
                    orig_texture = os.path.basename(self.materials[mat_name].diffuse_texture)
                    orig_texture = orig_texture.replace('\\', '/').split('/')[-1]
                
                print(f"\n     Material '{mat_name}' (texture: {orig_texture})")
                for vt_idx in vt_list[:5]:
                    if 0 <= vt_idx < len(self._all_texture_vertices):
                        vt = self._all_texture_vertices[vt_idx]
                        key = (vt_idx, mat_name)
                        if key in vt_transform_cache:
                            new_u, new_v = vt_transform_cache[key]
                            orig_u, orig_v = vt.u, vt.v
                            import math
                            norm_u = orig_u - math.floor(orig_u)
                            norm_v = orig_v - math.floor(orig_v)
                            print(f"       VT {vt_idx}: original=({orig_u:.4f}, {orig_v:.4f}) -> normalized=({norm_u:.4f}, {norm_v:.4f}) -> atlas=({new_u:.4f}, {new_v:.4f})")
        
        print(f"   Cached transforms for {len(vt_transform_cache)} unique (vt, material) pairs")
        
        # ========== بناء بيانات glTF باستخدام cache ==========
        positions = []
        normals = []
        uvs = []
        indices = []
        
        vertex_map = {}  # (v_idx, vt_idx, vn_idx, mat_name) -> vertex_index
        vertex_counter = 0
        
        for obj in self.objects:
            for face in obj.faces:
                mat_name = face.material_name
                
                face_indices = []
                for i in range(len(face.vertex_indices)):
                    v_idx = face.vertex_indices[i] - 1
                    vt_idx = face.texture_indices[i] - 1 if i < len(face.texture_indices) else -1
                    vn_idx = face.normal_indices[i] - 1 if i < len(face.normal_indices) else -1
                    
                    key = (v_idx, vt_idx, vn_idx, mat_name)
                    
                    if key not in vertex_map:
                        vertex_map[key] = vertex_counter
                        
                        # الرأس
                        if 0 <= v_idx < len(self._all_vertices):
                            v = self._all_vertices[v_idx]
                            positions.extend([v.x, v.y, v.z])
                        else:
                            positions.extend([0, 0, 0])
                        
                        # الطبيعية
                        if 0 <= vn_idx < len(self._all_normals):
                            n = self._all_normals[vn_idx]
                            normals.extend([n.x, n.y, n.z])
                        else:
                            normals.extend([0, 0, 0])
                        
                        # UV (من cache)
                        cache_key = (vt_idx, mat_name)
                        if cache_key in vt_transform_cache:
                            u_final, v_final = vt_transform_cache[cache_key]
                        else:
                            u_final, v_final = 0, 0
                        
                        # التأكد من أن القيم في النطاق [0, 1]
                        u_final = max(0.0, min(1.0, u_final))
                        v_final = max(0.0, min(1.0, v_final))
                        
                        uvs.extend([u_final, 1.0 - v_final])  # Flip V for OpenGL
                        
                        vertex_counter += 1
                    
                    face_indices.append(vertex_map[key])
                
                # إضافة الوجه (تثليث المضلعات)
                if len(face_indices) == 3:
                    indices.extend(face_indices)
                elif len(face_indices) == 4:
                    indices.extend([face_indices[0], face_indices[1], face_indices[2]])
                    indices.extend([face_indices[0], face_indices[2], face_indices[3]])
                elif len(face_indices) > 3:
                    for j in range(1, len(face_indices) - 1):
                        indices.extend([face_indices[0], face_indices[j], face_indices[j+1]])
        
        if len(positions) == 0:
            print("No vertices to export")
            return
        
        print(f"   Built: {len(positions)//3} vertices, {len(indices)//3} triangles")
        
        try:
            from pygltflib import GLTF2, Buffer, BufferView, Accessor, Mesh, Primitive, Attributes, Asset, Scene, Node
            
            gltf = GLTF2()
            gltf.asset = Asset(generator="OBJ Exporter (VT-accurate atlas)", version="2.0")
            
            binary_data = bytearray()
            
            # Positions
            pos_bytes = np.array(positions, dtype=np.float32).tobytes()
            pos_bv = BufferView(buffer=0, byteOffset=len(binary_data), byteLength=len(pos_bytes), target=34962)
            gltf.bufferViews.append(pos_bv)
            binary_data.extend(pos_bytes)
            
            pos_acc = Accessor(bufferView=len(gltf.bufferViews)-1, componentType=5126,
                               count=len(positions)//3, type="VEC3")
            gltf.accessors.append(pos_acc)
            
            # Normals
            norm_bytes = np.array(normals, dtype=np.float32).tobytes()
            norm_bv = BufferView(buffer=0, byteOffset=len(binary_data), byteLength=len(norm_bytes), target=34962)
            gltf.bufferViews.append(norm_bv)
            binary_data.extend(norm_bytes)
            
            norm_acc = Accessor(bufferView=len(gltf.bufferViews)-1, componentType=5126,
                                count=len(normals)//3, type="VEC3")
            gltf.accessors.append(norm_acc)
            
            # UVs
            uv_bytes = np.array(uvs, dtype=np.float32).tobytes()
            uv_bv = BufferView(buffer=0, byteOffset=len(binary_data), byteLength=len(uv_bytes), target=34962)
            gltf.bufferViews.append(uv_bv)
            binary_data.extend(uv_bytes)
            
            uv_acc = Accessor(bufferView=len(gltf.bufferViews)-1, componentType=5126,
                              count=len(uvs)//2, type="VEC2")
            gltf.accessors.append(uv_acc)
            
            # Indices
            idx_bytes = np.array(indices, dtype=np.uint32).tobytes()
            idx_bv = BufferView(buffer=0, byteOffset=len(binary_data), byteLength=len(idx_bytes), target=34963)
            gltf.bufferViews.append(idx_bv)
            binary_data.extend(idx_bytes)
            
            idx_acc = Accessor(bufferView=len(gltf.bufferViews)-1, componentType=5125,
                               count=len(indices), type="SCALAR")
            gltf.accessors.append(idx_acc)
            
            base_filename = os.path.splitext(os.path.basename(output_path))[0]
            gltf.buffers.append(Buffer(byteLength=len(binary_data), uri=f"{base_filename}.bin"))
            
            attributes = Attributes(POSITION=0, NORMAL=1, TEXCOORD_0=2)
            primitive = Primitive(attributes=attributes, indices=len(gltf.accessors)-1, material=0)
            mesh = Mesh(primitives=[primitive])
            gltf.meshes.append(mesh)
            
            node = Node(mesh=0)
            gltf.nodes.append(node)
            scene = Scene(nodes=[0])
            gltf.scenes.append(scene)
            gltf.scene = 0
            
            gltf.save(f"{output_path}.gltf")
            with open(f"{os.path.splitext(output_path)[0]}.bin", 'wb') as f:
                f.write(binary_data)
            
            if use_atlas:
                print(f"   glTF: {output_path}.gltf (using texture atlas with VT-accurate mapping)")
            else:
                print(f"   glTF: {output_path}.gltf")
            
        except Exception as e:
            print(f"   Error exporting glTF: {e}")
            import traceback
            traceback.print_exc()
        
    def export_all_with_atlas(self, output_dir: str, base_name: str, export_formats: List[str] = None):
        """تصدير OBJ إلى جميع الصيغ مع دعم الأطلس"""
        if export_formats is None:
            export_formats = ["obj", "gltf", "json", "txt", "smd", "mdl"]
        
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        print(f"\nExporting OBJ to {output_dir}")
        print("-" * 50)
        
        if "obj" in export_formats:
            export_obj_with_atlas(self, os.path.join(output_dir, base_name))
        
        if "gltf" in export_formats:
            export_gltf_with_atlas(self, os.path.join(output_dir, base_name))
        
        if "json" in export_formats:
            self.export_json(os.path.join(output_dir, f"{base_name}.json"))
        
        if "txt" in export_formats:
            self.export_txt(os.path.join(output_dir, f"{base_name}_info.txt"))
        
        if "smd" in export_formats:
            vertices, faces = self.to_unified_vertices(apply_swizzle=True)
            if len(vertices) > 0:
                smd = self.to_smd()
                smd.export_all(output_dir, base_name, ["obj", "gltf", "json", "txt"])
        
        if "mdl" in export_formats:
            mdl = self.to_mdl_format(base_name)
            mdl.export_all(os.path.join(output_dir, f"{base_name}_mdl"), ["obj", "gltf", "json", "txt"])
        
        print("-" * 50)
        print("OBJ Export completed successfully!")
    
    # تطبيق الدوال الجديدة
    OBJExporter.export_obj = export_obj_with_atlas
    OBJExporter.export_gltf = export_gltf_with_atlas
    OBJExporter.export_all = export_all_with_atlas
    OBJExporter.get_texture_names = get_texture_names_from_obj


# ========== تحديث StudioHeader (MDL) لدعم Texture Atlas ==========

def add_atlas_support_to_mdl():
    """إضافة دوال دعم الأطلس إلى StudioHeader (MDL)"""
    
    # حفظ المراجع الأصلية
    original_export_obj = StudioHeader.export_obj
    original_export_gltf = StudioHeader.export_gltf
    original_export_all = StudioHeader.export_all
    
    def get_texture_names_from_mdl(self) -> List[str]:
        """استخراج أسماء القوام من MDL"""
        texture_names = []
        if hasattr(self.header, 'numtextures') and self.header.numtextures > 0:
            # إضافة أسماء افتراضية للقوام
            for i in range(min(self.header.numtextures, 10)):
                texture_names.append(f"texture_{i}.bmp")
        if not texture_names:
            texture_names.append("texture.bmp")
        return texture_names
    
    def export_obj_with_atlas(self, out_dir, base_name):
        """تصدير MDL إلى OBJ مع دعم الأطلس - مع تحديث UVs بشكل صحيح"""
        self.debug_print_geometry()
        if len(self.vertices) == 0 or len(self.triangles) == 0:
            print("No geometry to export")
            return
        
        obj_path = os.path.join(out_dir, f"{base_name}.obj")
        mtl_path = os.path.join(out_dir, f"{base_name}.mtl")
        
        # التحقق من تفعيل الأطلس
        use_atlas = ENABLE_TEXTURE_ATLAS_MDL and PIL_AVAILABLE
        atlas = None
        
        if use_atlas:
            texture_dir = out_dir
            texture_names = self.get_texture_names()
            atlas = create_atlas_for_model(self, texture_dir, base_name, texture_names)
            use_atlas = atlas and atlas.has_multiple_textures()
        
        # تجميع الرؤوس والطبيعيات و UVs
        all_vertices = []
        all_normals = []
        all_uvs = []
        
        for tri in self.triangles:
            for i in range(3):
                vert_idx = tri.vertindex[i]
                norm_idx = tri.normindex[i]
                
                if vert_idx >= 0 and vert_idx < len(self.vertices):
                    v = self.vertices[vert_idx]
                    all_vertices.append((v.x, v.z, v.y))
                    
                    if norm_idx >= 0 and norm_idx < len(self.normals):
                        n = self.normals[norm_idx]
                        all_normals.append((n.x, n.z, n.y))
                    else:
                        all_normals.append((0, 0, 0))
                    
                    u = tri.s / 32768.0 if tri.s != 0 else 0.0
                    vt = tri.t / 32768.0 if tri.t != 0 else 0.0
                    all_uvs.append((u, 1.0 - vt))
        
        if len(all_vertices) == 0:
            print("   No valid vertices to export")
            return
        
        # ========== 🔴 تحديث UVs إذا كان الأطلس مفعلاً ==========
        if use_atlas and atlas:
            print(f"\n   🔧 Updating MDL UVs for atlas...")
            uvs_array = np.array(all_uvs)
            first_texture = list(atlas.texture_names)[0] if atlas.texture_names else "texture.bmp"
            new_uvs = atlas.get_uv_transform(first_texture, uvs_array)
            all_uvs = [(new_uvs[i, 0], new_uvs[i, 1]) for i in range(len(new_uvs))]
            print(f"   ✅ Updated {len(all_uvs)} UV coordinates")
        
        # كتابة ملف MTL
        with open(mtl_path, 'w', encoding='utf-8') as f:
            if use_atlas and atlas:
                atlas_name = f"{base_name}_atlas.png"
                f.write(f"newmtl {base_name}_material\n")
                f.write("Ns 10.0000\n")
                f.write("Ka 1.0000 1.0000 1.0000\n")
                f.write("Kd 1.0000 1.0000 1.0000\n")
                f.write("Ks 0.0000 0.0000 0.0000\n")
                f.write(f"map_Kd {atlas_name}\n")
            else:
                f.write(f"newmtl {base_name}_material\n")
                f.write("Ns 10.0000\n")
                f.write("Ka 1.0000 1.0000 1.0000\n")
                f.write("Kd 1.0000 1.0000 1.0000\n")
                f.write("Ks 0.0000 0.0000 0.0000\n")
                if self.header.numtextures > 0:
                    f.write("map_Kd texture.bmp\n")
        
        # كتابة ملف OBJ مع UVs المحدّثة
        with open(obj_path, 'w', encoding='utf-8') as f:
            f.write(f"mtllib {base_name}.mtl\n")
            f.write(f"o {base_name}\n")
            
            for v in all_vertices:
                f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
            
            for uv in all_uvs:
                f.write(f"vt {uv[0]:.6f} {uv[1]:.6f}\n")
            
            for n in all_normals:
                f.write(f"vn {n[0]:.6f} {n[1]:.6f} {n[2]:.6f}\n")
            
            f.write(f"usemtl {base_name}_material\n")
            
            for i in range(0, len(all_vertices), 3):
                a, b, c = i + 1, i + 2, i + 3
                f.write(f"f {a}/{a}/{a} {b}/{b}/{b} {c}/{c}/{c}\n")
        
        if use_atlas:
            print(f"   OBJ (with atlas, UVs updated): {obj_path}")
        else:
            print(f"   OBJ: {obj_path}")
        print(f"   MTL: {mtl_path}")
    
    def export_gltf_with_atlas(self, out_dir, base_name):
        """تصدير MDL إلى glTF مع دعم الأطلس"""
        if not GLTF_AVAILABLE:
            print("   pygltflib not available, skipping glTF export")
            return
        
        if len(self.vertices) == 0 or len(self.triangles) == 0:
            print("No geometry to export")
            return
        
        # التحقق من تفعيل الأطلس
        use_atlas = ENABLE_TEXTURE_ATLAS_MDL and PIL_AVAILABLE
        atlas = None
        
        if use_atlas:
            texture_dir = out_dir
            texture_names = self.get_texture_names()
            atlas = create_atlas_for_model(self, texture_dir, base_name, texture_names)
            use_atlas = atlas and atlas.has_multiple_textures()
        
        try:
            from pygltflib import GLTF2, Buffer, BufferView, Accessor, Mesh, Primitive, Attributes, Asset, Scene, Node, Skin
            
            gltf = GLTF2()
            gltf.asset = Asset(generator="HL MDL Reader (Valve spec)", version="2.0")
            
            positions = []
            indices = []
            
            # تجميع UVs
            all_uvs = []
            for tri in self.triangles:
                a, b, c = tri.vertindex[0], tri.vertindex[1], tri.vertindex[2]
                if a >= 0 and b >= 0 and c >= 0:
                    indices.extend([a, b, c])
                    u = tri.s / 32768.0 if tri.s != 0 else 0.0
                    vt = tri.t / 32768.0 if tri.t != 0 else 0.0
                    all_uvs.append((u, 1.0 - vt))
                    all_uvs.append((u, 1.0 - vt))
                    all_uvs.append((u, 1.0 - vt))
            
            for v in self.vertices:
                positions.extend([v.x, v.z, v.y])
            
            if len(indices) == 0:
                print("   No valid triangles to export")
                return
            
            # ========== 🔴 تحديث UVs إذا كان الأطلس مفعلاً ==========
            if use_atlas and atlas:
                print(f"\n   🔧 Updating MDL UVs for atlas (glTF)...")
                uvs_array = np.array(all_uvs)
                first_texture = list(atlas.texture_names)[0] if atlas.texture_names else "texture.bmp"
                new_uvs = atlas.get_uv_transform(first_texture, uvs_array)
                all_uvs = [(new_uvs[i, 0], new_uvs[i, 1]) for i in range(len(new_uvs))]
                print(f"   ✅ Updated {len(all_uvs)} UV coordinates")
            
            binary_data = bytearray()
            
            # Positions
            pos_bytes = np.array(positions, dtype=np.float32).tobytes()
            pos_bv = BufferView(buffer=0, byteOffset=len(binary_data), byteLength=len(pos_bytes), target=34962)
            gltf.bufferViews.append(pos_bv)
            binary_data.extend(pos_bytes)
            
            pos_acc = Accessor(bufferView=len(gltf.bufferViews)-1, componentType=5126,
                               count=len(self.vertices), type="VEC3")
            gltf.accessors.append(pos_acc)
            
            # UVs
            uv_flat = []
            for uv in all_uvs:
                uv_flat.extend([uv[0], uv[1]])
            uv_bytes = np.array(uv_flat, dtype=np.float32).tobytes()
            uv_bv = BufferView(buffer=0, byteOffset=len(binary_data), byteLength=len(uv_bytes), target=34962)
            gltf.bufferViews.append(uv_bv)
            binary_data.extend(uv_bytes)
            
            uv_acc = Accessor(bufferView=len(gltf.bufferViews)-1, componentType=5126,
                               count=len(all_uvs), type="VEC2")
            gltf.accessors.append(uv_acc)
            
            # Indices
            idx_bytes = np.array(indices, dtype=np.uint32).tobytes()
            idx_bv = BufferView(buffer=0, byteOffset=len(binary_data), byteLength=len(idx_bytes), target=34963)
            gltf.bufferViews.append(idx_bv)
            binary_data.extend(idx_bytes)
            
            idx_acc = Accessor(bufferView=len(gltf.bufferViews)-1, componentType=5125,
                               count=len(indices), type="SCALAR")
            gltf.accessors.append(idx_acc)
            
            gltf.buffers.append(Buffer(byteLength=len(binary_data), uri=f"{base_name}.bin"))
            
            attributes = Attributes(POSITION=0, TEXCOORD_0=1)
            primitive = Primitive(attributes=attributes, indices=len(gltf.accessors)-1, material=0)
            mesh = Mesh(primitives=[primitive])
            gltf.meshes.append(mesh)
            
            # العظام
            if len(self.bones) > 0:
                bone_nodes = []
                for i, bone in enumerate(self.bones):
                    bx, by, bz = bone.value[0], bone.value[1], bone.value[2]
                    node = Node(name=bone.name, translation=[bx, bz, by])
                    gltf.nodes.append(node)
                    bone_nodes.append(len(gltf.nodes)-1)
                
                for i, bone in enumerate(self.bones):
                    if bone.parent >= 0 and bone.parent < len(bone_nodes):
                        if gltf.nodes[bone_nodes[bone.parent]].children is None:
                            gltf.nodes[bone_nodes[bone.parent]].children = []
                        gltf.nodes[bone_nodes[bone.parent]].children.append(bone_nodes[i])
                
                skin = Skin(joints=bone_nodes)
                gltf.skins.append(skin)
                
                node = Node(mesh=0, skin=len(gltf.skins)-1)
                gltf.nodes.append(node)
                scene = Scene(nodes=[len(gltf.nodes)-1])
            else:
                node = Node(mesh=0)
                gltf.nodes.append(node)
                scene = Scene(nodes=[0])
            
            gltf.scenes.append(scene)
            gltf.scene = 0
            
            gltf.save(f"{out_dir}/{base_name}.gltf")
            
            with open(f"{out_dir}/{base_name}.bin", 'wb') as f:
                f.write(binary_data)
            
            if use_atlas:
                print(f"   glTF: {out_dir}/{base_name}.gltf (using texture atlas)")
            else:
                print(f"   glTF: {out_dir}/{base_name}.gltf")
            print(f"   glTF binary: {out_dir}/{base_name}.bin")
            if len(self.bones) > 0:
                print(f"   Bones exported: {len(self.bones)}")
            
        except Exception as e:
            print(f"   Error exporting glTF: {e}")
    
    def export_all_with_atlas(self, out_dir, export_formats=None):
        """تصدير MDL إلى جميع الصيغ مع دعم الأطلس"""
        if export_formats is None:
            export_formats = ["obj"]
        
        base_name = os.path.basename(out_dir)
        self.ensure_dir(out_dir)
        
        print(f"\nExporting MDL to {out_dir}")
        print("-" * 50)
        
        self.debug_print_geometry()
        
        if "obj" in export_formats:
            self.export_obj_as_points(out_dir, base_name)
            export_obj_with_atlas(self, out_dir, base_name)
        
        if "gltf" in export_formats and GLTF_AVAILABLE:
            export_gltf_with_atlas(self, out_dir, base_name)
        
        if "json" in export_formats:
            self.export_json(out_dir, base_name)
        
        if "txt" in export_formats:
            self.export_txt(out_dir, base_name)
        
        print("-" * 50)
        print("Export completed successfully!")
    
    # تطبيق الدوال الجديدة
    StudioHeader.export_obj = export_obj_with_atlas
    StudioHeader.export_gltf = export_gltf_with_atlas
    StudioHeader.export_all = export_all_with_atlas
    StudioHeader.get_texture_names = get_texture_names_from_mdl


# ========== تحديث MdlModel (نموذج MDL القديم) لدعم Texture Atlas ==========

def add_atlas_support_to_mdl_model():
    """إضافة دوال دعم الأطلس إلى MdlModel"""
    
    # حفظ المراجع الأصلية
    original_export_obj = MdlModel.export_obj
    
    def get_texture_names_from_mdl_model(self) -> List[str]:
        """استخراج أسماء القوام من MdlModel"""
        texture_names = []
        if hasattr(self, 'textures') and self.textures:
            for tex in self.textures:
                if hasattr(tex, 'name'):
                    texture_names.append(tex.name)
        if not texture_names:
            texture_names.append("texture.bmp")
        return texture_names
    
    def export_obj_with_atlas(self, out_dir, base_name, export_formats=None):
        """تصدير MdlModel إلى OBJ مع دعم الأطلس - مع تحديث UVs بشكل صحيح"""
        if export_formats is None:
            export_formats = ["obj"]
        
        if len(self.vertices) == 0 or len(self.triangles) == 0:
            print("No vertices or triangles to export")
            return
        
        # التحقق من تفعيل الأطلس
        use_atlas = ENABLE_TEXTURE_ATLAS_MDL and PIL_AVAILABLE
        atlas = None
        
        if use_atlas:
            texture_dir = out_dir
            texture_names = self.get_texture_names()
            atlas = create_atlas_for_model(self, texture_dir, base_name, texture_names)
            use_atlas = atlas and atlas.has_multiple_textures()
        
        dtype_out = np.dtype([
            ("px", np.float32), ("py", np.float32), ("pz", np.float32),
            ("nx", np.float32), ("ny", np.float32), ("nz", np.float32),
            ("u", np.float32), ("v", np.float32)
        ])
        
        verts_arr = []
        for v in self.vertices:
            verts_arr.append((
                v.x, v.z, v.y,
                0, 0, 0,
                v.u, 1.0 - v.v
            ))
        
        vertices_transformed = np.array(verts_arr, dtype=dtype_out)
        
        faces_arr = []
        for tri in self.triangles:
            faces_arr.append([tri.indices[0], tri.indices[1], tri.indices[2]])
        faces_array = np.array(faces_arr)
        
        # ========== 🔴 تحديث UVs إذا كان الأطلس مفعلاً ==========
        if use_atlas and atlas:
            print(f"\n   🔧 Updating MdlModel UVs for atlas...")
            uvs_array = np.array([[v['u'], v['v']] for v in vertices_transformed])
            first_texture = list(atlas.texture_names)[0] if atlas.texture_names else "texture.bmp"
            new_uvs = atlas.get_uv_transform(first_texture, uvs_array)
            for i in range(len(vertices_transformed)):
                vertices_transformed[i]['u'] = new_uvs[i, 0]
                vertices_transformed[i]['v'] = new_uvs[i, 1]
            print(f"   ✅ Updated {len(vertices_transformed)} UV coordinates")
        
        if "obj" in export_formats:
            obj_path = os.path.join(out_dir, f"{base_name}.obj")
            mtl_path = os.path.join(out_dir, f"{base_name}.mtl")
            
            with open(mtl_path, "w", encoding="utf-8") as f:
                if use_atlas and atlas:
                    atlas_name = f"{base_name}_atlas.png"
                    f.write(f"newmtl {base_name}_material\n")
                    f.write("Ns 10.0000\n")
                    f.write("Ka 1.0000 1.0000 1.0000\n")
                    f.write("Kd 1.0000 1.0000 1.0000\n")
                    f.write("Ks 0.0000 0.0000 0.0000\n")
                    f.write(f"map_Kd {atlas_name}\n")
                else:
                    f.write(f"newmtl {base_name}_material\n")
                    f.write("Ns 10.0000\n")
                    f.write("Ka 1.0000 1.0000 1.0000\n")
                    f.write("Kd 1.0000 1.0000 1.0000\n")
                    f.write("Ks 0.0000 0.0000 0.0000\n")
                    if self.textures:
                        tex_name = self.textures[0].name
                        if not tex_name.endswith('.bmp') and not tex_name.endswith('.png'):
                            tex_name += ".bmp"
                        f.write(f"map_Kd {tex_name}\n")
            
            with open(obj_path, "w", encoding="utf-8") as f:
                f.write(f"mtllib {base_name}.mtl\n")
                f.write(f"o {base_name}\n")
                
                for v in vertices_transformed:
                    f.write(f"v {v['px']:.6f} {v['py']:.6f} {v['pz']:.6f}\n")
                
                for v in vertices_transformed:
                    f.write(f"vt {v['u']:.6f} {v['v']:.6f}\n")
                
                f.write(f"usemtl {base_name}_material\n")
                
                for face in faces_array:
                    a, b, c = face[0] + 1, face[1] + 1, face[2] + 1
                    f.write(f"f {a}/{a} {b}/{b} {c}/{c}\n")
            
            if use_atlas:
                print(f"   OBJ (with atlas, UVs updated): {obj_path}")
            else:
                print(f"   OBJ: {obj_path}")
            print(f"   MTL: {mtl_path}")
        
        if "gltf" in export_formats and GLTF_AVAILABLE:
            self._export_gltf(out_dir, base_name, vertices_transformed, faces_array)
        
        if "dae" in export_formats:
            self._export_collada(out_dir, base_name, vertices_transformed, faces_array)
        
        if "json" in export_formats:
            self._export_json(out_dir, base_name)
        
        if "txt" in export_formats:
            self._export_txt(out_dir, base_name)

# ========== تفعيل دعم الأطلس لجميع الصيغ ==========

def enable_atlas_for_all_formats():
    """تفعيل دعم Texture Atlas لجميع الصيغ المدعومة"""
    add_atlas_support_to_smd()
    add_atlas_support_to_obj()
    add_atlas_support_to_mdl()
    add_atlas_support_to_mdl_model()
    print("✅ Texture Atlas support enabled for SMD, OBJ, and MDL formats")


# تفعيل الدعم تلقائياً عند استيراد السكربت
enable_atlas_for_all_formats()

# ------------------------------------------------------------
# تعديل: تحديث quick_validate لاستخدام global_debug_params
# ------------------------------------------------------------
def quick_validate(filepath: str, debug_params: Optional[MefDebugParams] = None) -> bool:
    """التحقق السريع من صحة ملف MEF مع دعم معاملات التصحيح"""
    if debug_params is None:
        debug_params = global_debug_params
    
    try:
        with open(filepath, "rb") as f:
            result = f.read(4) == b'ILFF'
            if debug_params:
                print(f"   Quick validate: {filepath} -> {'valid' if result else 'invalid'} (debug mode)")
            return result
    except:
        return False


# ------------------------------------------------------------
# الفئة الرئيسية للنموذج IGI2 (مأخوذة من السكربت السادس عشر)
# ------------------------------------------------------------
class MefModelIGI2EnhancedPatch:
    def __init__(self, buffer: Buffer, export_mode: str = "simple", debug_params: Optional[MefDebugParams] = None):
        self.debug_params = debug_params or MefDebugParams()
        loop_file = LoopFile(buffer, flip_ident=True)
        loop_file.print_all_chunks()

        self.model_info: ModelInfoIGI2 = None
        self.render_mesh_data: RenderMeshDataIGI2 = None
        self.collision_mesh_data: CollisionMeshDataIGI2 = None
        self.collision_mesh_data2: CollisionMeshDataIGI2 = None
        self.shadow_mesh_data: ShadowMeshDataIGI2 = None
        self.bones: list[Bone] = []
        self.attachments: list[Attachment] = []
        self.magic_vertices: list[MagicVertex] = []
        self.portals: list[Portal] = []
        self.portal_vertices: list[PortalVertex] = []
        self.portal_faces: list[PortalFace] = []
        self.glow_sprites: list[GlowSprite] = []
        self.morph_channels: dict[int, np.ndarray] = {}
        self.lightmaps: list[LightmapData] = []
        self.collision_materials: list[CollisionMaterialIGI2] = []
        self.txan_data: list[TXANData] = []
        
        # بيانات جديدة من وثائق Tav EndeR
        self.hsem_info: HSEMInfo = None
        self.vertex_weights: list[XTRWEntry] = []  # من قطعة XTRW
        self.texture_references: list[TextureReference] = []  # من قطعة XTXM
        self.extra_uv_sets: list[TextureCoordinateSet] = []  # من قطعة TCST
        
        self.export_mode = export_mode

        # ✅ استخدام هذه المتغيرات لتخزين بيانات العظام المؤقتة
        self._child_counts = None  # سيتم ملؤها من قطعة HIER
        self._bone_positions = None  # سيتم ملؤها من قطعة HIER
        
        # ========== 🟢 أضف هذه المتغيرات الجديدة هنا ==========
        self.bone_extra_params = []           # من قطعة HPRM
        self.external_refs = []               # من قطعة XTRN
        self.skeleton_hints = []              # من قطعة NHSA
        self.shadow_faces_detailed = []       # من قطعة SFAC (CAFS)
        self.shadow_edges_raw = None          # من قطعة EGDE
        self.hsem_raw_data = None             # البيانات الخام لـ HSEM
        self.collision_materials_mesh1 = []   # مواد التصادم للمجموعة الثانية
        # ====================================================
        
        loop_file.index = 0
        
        while True:
            chunk = loop_file.next_chunk()
            if chunk is None:
                break
            ident = chunk.header.ident.decode('ascii')
            
            if ident == "MESH":
                self.model_info = ModelInfoIGI2.from_buffer(chunk.buffer)
                print(f"Model type: {self.model_info.model_type.name}")
                print(f"  Attachments: {self.model_info.attachment_count}, Magic vertices: {self.model_info.magic_vertex_count}")
                print(f"  Portals: {self.model_info.portal_count}, Glow: {self.model_info.glow_count}, Bones: {self.model_info.bone_count}")
            elif ident == "HIER":
                self._process_hierarchy(chunk, loop_file)
            elif ident == "BNAM":
                pass
            elif ident == "ATTA":
                for _ in range(self.model_info.attachment_count):
                    self.attachments.append(Attachment.from_buffer(chunk.buffer))
                print(f"Processed {len(self.attachments)} attachments")
            elif ident == "MVTX":
                self._process_magic_vertices(chunk)
            elif ident == "PORT":
                self._process_portal(chunk)
            elif ident == "PTVX":
                self._process_portal_vertices(chunk)
            elif ident == "PTFC":
                self._process_portal_faces(chunk)
            elif ident == "GLOW":
                self._process_glow(chunk)
            elif ident == "RD3D":
                self._process_render_mesh(chunk, loop_file)
            elif ident == "CMSH":
                self._process_collision_mesh(chunk, loop_file)
            elif ident == "CMAT":
                self._process_collision_materials(chunk)
            elif ident == "SMES":
                print("Found SMES chunk, processing shadow mesh...")
                self._process_shadow_mesh(chunk, loop_file)
            elif ident == "MRPH":
                self._process_morph(chunk)
            elif ident == "LTMP":
                self._process_lightmap(chunk)
            elif ident == "TXAN":
                self._process_txan(chunk)
            # قطع جديدة من وثائق Tav EndeR
            elif ident == "XTRW":
                self._process_xtrw(chunk)
            elif ident == "XTXM":
                self._process_xtxm(chunk)
            elif ident == "TCST":
                self._process_tcst(chunk)
            elif ident == "HPRM":
                self._process_hprm(chunk)
            elif ident == "XTRN":
                self._process_xtrn(chunk)
            elif ident == "NHSA":
                self._process_nhsa(chunk)
            elif ident == "LLUN":
                self._process_llun(chunk)
            else:
                if chunk.header.data_size > 0:
                    print(f"Unhandled chunk: {ident} (size: {chunk.header.data_size})")

    def _process_magic_vertices(self, chunk):
        buffer = chunk.buffer
        count = self.model_info.magic_vertex_count if self.model_info else 0
        if count == 0:
            count = buffer.size() // 16
        for _ in range(count):
            if buffer.eof():
                break
            mv = MagicVertex.from_buffer(buffer)
            # ✅ تم إزالة swizzle من هنا - سيتم تطبيقه عند التصدير فقط
            self.magic_vertices.append(mv)
        print(f"Processed {len(self.magic_vertices)} magic vertices")

    def _process_portal(self, chunk):
        buffer = chunk.buffer
        count = self.model_info.portal_count if self.model_info else 0
        if count == 0:
            count = buffer.size() // 20
        for _ in range(count):
            if buffer.eof():
                break
            p = Portal.from_buffer(buffer)
            self.portals.append(p)
        print(f"Processed {len(self.portals)} portals")

    def _process_portal_vertices(self, chunk):
        buffer = chunk.buffer
        count = buffer.size() // 12
        for _ in range(count):
            if buffer.eof():
                break
            pv = PortalVertex.from_buffer(buffer)
            # ✅ تم إزالة swizzle من هنا - سيتم تطبيقه عند التصدير فقط
            self.portal_vertices.append(pv)
        print(f"Processed {len(self.portal_vertices)} portal vertices")

    def _process_portal_faces(self, chunk):
        buffer = chunk.buffer
        count = buffer.size() // 12
        for _ in range(count):
            if buffer.eof():
                break
            pf = PortalFace.from_buffer(buffer)
            self.portal_faces.append(pf)
        print(f"Processed {len(self.portal_faces)} portal faces")

    def _process_glow(self, chunk):
        buffer = chunk.buffer
        count = self.model_info.glow_count if self.model_info else 0
        if count == 0:
            count = buffer.size() // 32
        for _ in range(count):
            if buffer.eof():
                break
            g = GlowSprite.from_buffer(buffer)
            # ✅ تم إزالة swizzle من هنا - سيتم تطبيقه عند التصدير فقط
            self.glow_sprites.append(g)
        print(f"Processed {len(self.glow_sprites)} glow sprites")

    def _process_collision_materials(self, chunk):
        buffer = chunk.buffer
        data_size = buffer.size()
        material_size = 16
        count = data_size // material_size
        remainder = data_size % material_size
        
        print(f"   CMAT chunk: {data_size} bytes, expecting {count} materials, remainder {remainder} bytes")
        
        # قراءة المواد الكاملة
        for i in range(count):
            if buffer.eof():
                break
            try:
                mat = CollisionMaterialIGI2.from_buffer(buffer)
                self.collision_materials.append(mat)
                print(f"     Material {len(self.collision_materials)-1}: opacity={mat.opacity:.3f}, portal_id={mat.portal_id}, "
                      f"texture_id={mat.texture_id}, game_material_id={mat.game_material_id}")
            except Exception as e:
                print(f"   Error reading material {i}: {e}")
                break
        
        # معالجة البيانات الجزئية - ✅ يجب إضافتها كمواد
        if remainder > 0 and not buffer.eof():
            print(f"   Found partial material data: {remainder} bytes")
            
            # محاولة قراءة البيانات المتبقية كمواد جزئية
            remaining_data = buffer.read(remainder)
            
            # إذا كان الباقي 16 بايت، يمكن أن تكون opacity + portal_id + texture_id
            if remainder >= 16:
                temp_buffer = Buffer(remaining_data)
                try:
                    opacity = temp_buffer.read_float()
                    portal_id = temp_buffer.read_uint32()
                    texture_id = temp_buffer.read_uint32()
                    unknown1 = 0
                    game_material_id = 0
                    unknown2 = 0
                    
                    # إنشاء كائن مادة بالقيم المقروءة
                    partial_mat = CollisionMaterialIGI2(
                        opacity=opacity,
                        portal_id=portal_id,
                        texture_id=texture_id,
                        unknown1=unknown1,
                        game_material_id=game_material_id,
                        unknown2=unknown2
                    )
                    self.collision_materials.append(partial_mat)
                    print(f"     Added partial material: opacity={opacity:.3f}, portal_id={portal_id}, texture_id={texture_id}")
                except:
                    pass
            elif remainder == 12:
                # opacity + portal_id
                temp_buffer = Buffer(remaining_data)
                try:
                    opacity = temp_buffer.read_float()
                    portal_id = temp_buffer.read_uint32()
                    texture_id = 0
                    
                    partial_mat = CollisionMaterialIGI2(
                        opacity=opacity,
                        portal_id=portal_id,
                        texture_id=texture_id,
                        unknown1=0,
                        game_material_id=0,
                        unknown2=0
                    )
                    self.collision_materials.append(partial_mat)
                    print(f"     Added partial material (12 bytes): opacity={opacity:.3f}, portal_id={portal_id}")
                except:
                    pass
        
        print(f"   Processed {len(self.collision_materials)} collision materials")
    
    def _process_collision_materials_mesh1(self, chunk):
        """معالجة CMAT للمجموعة الثانية (mesh1) من التصادم"""
        buffer = chunk.buffer
        data_size = buffer.size()
        material_size = 16
        count = data_size // material_size
        remainder = data_size % material_size
        
        print(f"   mesh1 CMAT chunk: {data_size} bytes, expecting {count} materials, remainder {remainder} bytes")
        
        # التأكد من وجود قائمة للمواد
        if not hasattr(self, 'collision_materials_mesh1'):
            self.collision_materials_mesh1 = []
        
        # قراءة المواد الكاملة
        for i in range(count):
            if buffer.eof():
                break
            try:
                mat = CollisionMaterialIGI2.from_buffer(buffer)
                self.collision_materials_mesh1.append(mat)
                print(f"     Material {len(self.collision_materials_mesh1)-1}: opacity={mat.opacity:.3f}, portal_id={mat.portal_id}, "
                      f"texture_id={mat.texture_id}, game_material_id={mat.game_material_id}")
            except Exception as e:
                print(f"   Error reading material {i}: {e}")
                break
        
        # معالجة البيانات الجزئية
        if remainder > 0 and not buffer.eof():
            print(f"   Found partial material data in mesh1: {remainder} bytes")
            remaining_data = buffer.read(remainder)
            
            if remainder >= 16:
                temp_buffer = Buffer(remaining_data)
                try:
                    opacity = temp_buffer.read_float()
                    portal_id = temp_buffer.read_uint32()
                    texture_id = temp_buffer.read_uint32()
                    unknown1 = 0
                    game_material_id = 0
                    unknown2 = 0
                    
                    partial_mat = CollisionMaterialIGI2(
                        opacity=opacity,
                        portal_id=portal_id,
                        texture_id=texture_id,
                        unknown1=unknown1,
                        game_material_id=game_material_id,
                        unknown2=unknown2
                    )
                    self.collision_materials_mesh1.append(partial_mat)
                    print(f"     Added partial material (mesh1): opacity={opacity:.3f}, portal_id={portal_id}, texture_id={texture_id}")
                except:
                    pass
            elif remainder == 12:
                temp_buffer = Buffer(remaining_data)
                try:
                    opacity = temp_buffer.read_float()
                    portal_id = temp_buffer.read_uint32()
                    texture_id = 0
                    
                    partial_mat = CollisionMaterialIGI2(
                        opacity=opacity,
                        portal_id=portal_id,
                        texture_id=texture_id,
                        unknown1=0,
                        game_material_id=0,
                        unknown2=0
                    )
                    self.collision_materials_mesh1.append(partial_mat)
                    print(f"     Added partial material (mesh1, 12 bytes): opacity={opacity:.3f}, portal_id={portal_id}")
                except:
                    pass
        
        print(f"   Processed {len(self.collision_materials_mesh1)} collision materials for mesh1")
    
    def _process_hierarchy(self, chunk, loop_file):
        # تخزين بيانات العظام المؤقتة للاستخدام لاحقاً
        self._child_counts = [chunk.buffer.read_uint8() for _ in range(self.model_info.bone_count)]
        chunk.buffer.align(4)
        self._bone_positions = [Vector3.from_buffer(chunk.buffer) for _ in range(self.model_info.bone_count)]
        
        name_chunk = loop_file.expect_chunk("BNAM")
        bone_names = [name_chunk.buffer.read_ascii_string(16) for _ in range(self.model_info.bone_count)]

        # استخدام البيانات المخزنة
        child_counts = self._child_counts.copy()
        bone_positions = self._bone_positions.copy()
        
        bone_queue = []
        def create_bone(parent_id: int, name: str, position: Vector3, child_count: int):
            # ✅ تم إزالة swizzle من العظام - سيتم تطبيقه عند التزين فقط
            bone = Bone(name, position, parent_id)
            next_parent_id = len(self.bones)
            self.bones.append(bone)
            for _ in range(child_count):
                if not bone_queue and not (child_counts and bone_names and bone_positions):
                    break
                cnt = child_counts.pop(0) if child_counts else 0
                nm = bone_names.pop(0) if bone_names else ""
                pos_raw = bone_positions.pop(0) if bone_positions else Vector3(0, 0, 0)
                bone_queue.append((next_parent_id, nm, pos_raw, cnt))

        if bone_names and bone_positions and child_counts:
            bone_queue.append((-1, bone_names.pop(0), bone_positions.pop(0), child_counts.pop(0) if child_counts else 0))
        
        while bone_queue:
            create_bone(*bone_queue.pop(0))
        
        print(f"Processed {len(self.bones)} bones")
        print(f"  Stored {len(self._child_counts)} child counts and {len(self._bone_positions)} bone positions for later use")

    def _process_render_mesh(self, chunk, loop_file):
        assert self.render_mesh_data is None, "Render mesh already exists"
        render_mesh_info = RenderMeshHeader.from_buffer(chunk.buffer)
        
        face_chunk = loop_file.expect_chunk("FACE")
        faces_data = face_chunk.buffer.read(face_chunk.buffer.size())
        faces = np.frombuffer(faces_data, np.uint16).reshape(-1, 3)
        
        rend_chunk = loop_file.expect_chunk("REND")
        render_info = []
        for _ in range(render_mesh_info.face_group_count):
            render_info.append(FaceGroup.from_buffer(rend_chunk.buffer, self.model_info.model_type))
        
        vert_chunk = loop_file.expect_chunk("VRTX")
        model_type = self.model_info.model_type
        
        if model_type == ModelType.StaticModel:
            dtype = np.dtype([
                ("pos", np.float32, (3,)),
                ("normal", np.float32, (3,)),
                ("uv0", np.float32, (2,))
            ])
        elif model_type == ModelType.SkinnedModel:
            dtype = np.dtype([
                ("pos", np.float32, (3,)),
                ("normal", np.float32, (3,)),
                ("uv0", np.float32, (2,)),
                ("weight", np.float32, (1,)),
                ("index", np.ushort, (1,)),
                ("bone_id", np.ushort, (1,))
            ])
        elif model_type == ModelType.LightmappedModel:
            dtype = np.dtype([
                ("pos", np.float32, (3,)),
                ("uv0", np.float32, (2,)),
                ("uv1", np.float32, (2,))
            ])
        else:
            dtype = np.dtype([
                ("pos", np.float32, (3,)),
                ("normal", np.float32, (3,)),
                ("uv0", np.float32, (2,))
            ])
            print(f"Unknown model type {model_type}, using StaticModel dtype")
        
        vert_data = vert_chunk.buffer.read(vert_chunk.buffer.size())
        vertices = np.frombuffer(vert_data, dtype)
        
        lightmap_uvs = None
        if loop_file.has_chunk("LTMP"):
            try:
                lightmap_chunk = loop_file.expect_chunk("LTMP")
                lightmap_data = lightmap_chunk.buffer.read(lightmap_chunk.buffer.size())
                if lightmap_chunk.buffer.size() > 1000:
                    pass
                else:
                    uv_count = len(lightmap_data) // 8
                    if uv_count > 0:
                        lightmap_uvs = np.frombuffer(lightmap_data, np.float32).reshape(-1, 2)
                        print(f"   Found lightmap UVs: {len(lightmap_uvs)}")
            except Exception as e:
                print(f"   Error reading lightmap UVs: {e}")
        
        self.render_mesh_data = RenderMeshDataIGI2(render_mesh_info, faces, vertices, render_info, lightmap_uvs)
        print(f"Render mesh: {len(vertices)} vertices, {len(faces)} faces, {len(render_info)} material groups")

    def _process_collision_mesh(self, chunk, loop_file):
        collision_mesh_info = CollisionMeshHeader.from_buffer(chunk.buffer)
        
        # ========== المجموعة الأولى (mesh0) ==========
        # قراءة CVTX للمجموعة الأولى
        vertices_chunk = loop_file.expect_chunk("CVTX")
        vertices_data = vertices_chunk.buffer.read(vertices_chunk.buffer.size())
        
        # قراءة CFCE للمجموعة الأولى
        faces_chunk = loop_file.expect_chunk("CFCE")
        faces_data = faces_chunk.buffer.read(faces_chunk.buffer.size())
        
        # قراءة CMAT للمجموعة الأولى إذا كانت موجودة
        try:
            materials_chunk = loop_file.expect_chunk("CMAT")
            print(f"DEBUG: Found CMAT for mesh0! size={materials_chunk.header.data_size}")
            self._process_collision_materials(materials_chunk)
            materials0 = self.collision_materials.copy()
        except ValueError:
            print("   No CMAT chunk found for mesh0")
            materials0 = []
        
        # قراءة CSPH للمجموعة الأولى
        spheres_chunk = loop_file.expect_chunk("CSPH")
        spheres_data = spheres_chunk.buffer.read(spheres_chunk.buffer.size())
        
        # تحويل البيانات إلى مصفوفات (مع عمل copy للتعديل)
        vertices0 = np.frombuffer(vertices_data, CollisionVertexDtype).copy()
        faces0 = np.frombuffer(faces_data, CollisionFaceDtype)
        spheres0 = np.frombuffer(spheres_data, CollisionSphereDtype).copy()
        
        # ✅ تم إزالة swizzle من رؤوس وكرات التصادم - سيتم تطبيقه عند التصدير فقط
        
        # إنشاء كائن المجموعة الأولى
        self.collision_mesh_data = CollisionMeshDataIGI2(
            collision_mesh_info, spheres0, faces0, vertices0, materials0
        )
        print(f"Collision mesh 0: {len(vertices0)} vertices, {len(faces0)} faces, {len(materials0)} materials")
        
        # ========== المجموعة الثانية (mesh1) - إذا كانت موجودة ==========
        if collision_mesh_info.mesh1.face_count > 0:
            print(f"\n   📦 Found second collision mesh (mesh1) with {collision_mesh_info.mesh1.face_count} faces")
            
            # إعادة تعيين قائمة المواد للمجموعة الثانية
            self.collision_materials_mesh1 = []
            
            # قراءة CVTX للمجموعة الثانية (إذا كانت موجودة)
            try:
                vertices_chunk2 = loop_file.expect_chunk("CVTX")
                vertices_data2 = vertices_chunk2.buffer.read(vertices_chunk2.buffer.size())
                vertices1 = np.frombuffer(vertices_data2, CollisionVertexDtype).copy()
                # ✅ تم إزالة swizzle - سيتم تطبيقه عند التصدير فقط
                print(f"   mesh1: Found CVTX with {len(vertices1)} vertices")
            except ValueError:
                print("   mesh1: No CVTX chunk found")
                vertices1 = np.array([], dtype=CollisionVertexDtype)
            
            # قراءة CFCE للمجموعة الثانية (إذا كانت موجودة)
            try:
                faces_chunk2 = loop_file.expect_chunk("CFCE")
                faces_data2 = faces_chunk2.buffer.read(faces_chunk2.buffer.size())
                faces1 = np.frombuffer(faces_data2, CollisionFaceDtype)
                print(f"   mesh1: Found CFCE with {len(faces1)} faces")
            except ValueError:
                print("   mesh1: No CFCE chunk found")
                faces1 = np.array([], dtype=CollisionFaceDtype)
            
            # قراءة CMAT للمجموعة الثانية (إذا كانت موجودة)
            try:
                materials_chunk2 = loop_file.expect_chunk("CMAT")
                print(f"   mesh1: Found CMAT! size={materials_chunk2.header.data_size}")
                self._process_collision_materials_mesh1(materials_chunk2)
                materials1 = self.collision_materials_mesh1.copy()
                print(f"   mesh1: Processed {len(materials1)} materials")
            except ValueError:
                print("   mesh1: No CMAT chunk found")
                materials1 = []
            
            # قراءة CSPH للمجموعة الثانية (إذا كانت موجودة)
            try:
                spheres_chunk2 = loop_file.expect_chunk("CSPH")
                spheres_data2 = spheres_chunk2.buffer.read(spheres_chunk2.buffer.size())
                spheres1 = np.frombuffer(spheres_data2, CollisionSphereDtype).copy()
                # ✅ تم إزالة swizzle - سيتم تطبيقه عند التصدير فقط
                print(f"   mesh1: Found CSPH with {len(spheres1)} spheres")
            except ValueError:
                print("   mesh1: No CSPH chunk found")
                spheres1 = np.array([], dtype=CollisionSphereDtype)
            
            # إنشاء كائن المجموعة الثانية إذا كانت تحتوي على بيانات
            if len(vertices1) > 0 and len(faces1) > 0:
                self.collision_mesh_data2 = CollisionMeshDataIGI2(
                    collision_mesh_info, spheres1, faces1, vertices1, materials1
                )
                print(f"   ✅ Collision mesh 1 created: {len(vertices1)} vertices, {len(faces1)} faces, {len(materials1)} materials")
            else:
                print("   ⚠️ Second collision mesh has no vertices or faces, skipping")
                self.collision_mesh_data2 = None
            
    def _process_shadow_mesh(self, chunk, loop_file):
        try:
            shadow_header = ShadowMeshHeader.from_buffer(chunk.buffer)
            print(f"Shadow header: faces={shadow_header.face_count}, vertices={shadow_header.vertex_count}, edges={shadow_header.edge_count}, bone={shadow_header.bone_index}")
        except Exception as e:
            print(f"Error reading shadow header: {e}")
            return
        
        vertices = None
        faces = None
        edges = None
        
        if loop_file.has_chunk("SVTX"):
            try:
                vertex_chunk = loop_file.expect_chunk("SVTX")
                vertex_data = vertex_chunk.buffer.read(vertex_chunk.buffer.size())
                vertices = np.frombuffer(vertex_data, np.float32)
                if len(vertices) == shadow_header.vertex_count * 3:
                    vertices = vertices.reshape(-1, 3)
                else:
                    print(f"   Warning: Shadow vertex count mismatch. Expected {shadow_header.vertex_count*3}, got {len(vertices)}")
                    vertices = vertices.reshape(-1, 3) if len(vertices) % 3 == 0 else np.array([])
                # ✅ تم إزالة swizzle من رؤوس الظل - سيتم تطبيقه عند التصدير فقط
                print(f"   Found shadow vertices: {len(vertices)}")
            except Exception as e:
                print(f"   Error reading shadow vertices: {e}")
        
        if loop_file.has_chunk("SFAC"):
            try:
                face_chunk = loop_file.expect_chunk("SFAC")
                face_data = face_chunk.buffer.read(face_chunk.buffer.size())
                if len(face_data) > 0:
                    try:
                        faces = np.frombuffer(face_data, ShadowFaceDtype)
                        # ✅ تم إزالة swizzle من الطبيعيات - سيتم تطبيقه عند التصدير فقط
                        print(f"   Found shadow faces (with normals): {len(faces)}")
                    except:
                        faces = np.frombuffer(face_data, np.uint32).reshape(-1, 3)
                        print(f"   Found shadow faces (simple indices): {len(faces)}")
            except Exception as e:
                print(f"   Error reading shadow faces: {e}")
        
        if loop_file.has_chunk("EDGE"):
            try:
                edge_chunk = loop_file.expect_chunk("EDGE")
                edge_data = edge_chunk.buffer.read(edge_chunk.buffer.size())
                if len(edge_data) > 0:
                    edges = np.frombuffer(edge_data, np.uint32).reshape(-1, 2)
                    print(f"   Found shadow edges: {len(edges)}")
            except Exception as e:
                print(f"   Error reading shadow edges: {e}")
        
        if vertices is not None and len(vertices) > 0:
            self.shadow_mesh_data = ShadowMeshDataIGI2(shadow_header, faces, vertices, edges)
            print(f"Shadow mesh loaded: {len(vertices)} vertices")
        else:
            print("No shadow vertices found")

    def _process_morph(self, chunk):
        buffer = chunk.buffer
        counts = [buffer.read_uint32() for _ in range(16)]
        for channel, count in enumerate(counts):
            if count > 0:
                morph_data = buffer.read(MorphVertexDtype.itemsize * count)
                vertices = np.frombuffer(morph_data, MorphVertexDtype).copy()
                # ✅ تم إزالة swizzle من رؤوس التشكل - سيتم تطبيقه عند التصدير فقط
                self.morph_channels[channel] = vertices
                print(f"Found morph channel {channel} with {count} vertices")

    def _process_lightmap(self, chunk):
        try:
            buffer = chunk.buffer
            width = buffer.read_uint32()
            height = buffer.read_uint32()
            format_type = buffer.read_uint32()
            data_size = buffer.size()
            data = buffer.read(data_size)
            
            lightmap = LightmapData(width, height, format_type, data)
            self.lightmaps.append(lightmap)
            print(f"   Found lightmap: {width}x{height}, format={format_type}, size={data_size} bytes")
        except Exception as e:
            print(f"   Error processing lightmap: {e}")

    def _process_txan(self, chunk):
        try:
            buffer = chunk.buffer
            txan = TXANData.from_buffer(buffer)
            self.txan_data.append(txan)
            print(f"   Found TXAN chunk with {len(txan.unknown_fields)} fields")
        except Exception as e:
            print(f"   Error processing TXAN: {e}")

    # ========== دوال جديدة من وثائق Tav EndeR==========
    def _process_xtrw(self, chunk):
        """معالجة قطعة XTRW (أوزان العظام المنفصلة)"""
        buffer = chunk.buffer
        count = buffer.size() // 12
        for i in range(count):
            entry = XTRWEntry.from_buffer(buffer)
            self.vertex_weights.append(entry)
        print(f"   Processed {len(self.vertex_weights)} XTRW weight entries")

    def _process_xtxm(self, chunk):
        """معالجة قطعة XTXM (مراجع القوام)"""
        buffer = chunk.buffer
        count = buffer.size() // 36  # تقريباً 32+4
        for i in range(count):
            if buffer.eof():
                break
            ref = TextureReference.from_buffer(buffer)
            self.texture_references.append(ref)
        print(f"   Processed {len(self.texture_references)} texture references")

    def _process_tcst(self, chunk):
        """معالجة قطعة TCST (مجموعات إحداثيات نسيج إضافية)"""
        buffer = chunk.buffer
        uv_count = buffer.size() // 8
        uv_set = TextureCoordinateSet.from_buffer(buffer, uv_count)
        uv_set.index = len(self.extra_uv_sets)
        self.extra_uv_sets.append(uv_set)
        print(f"   Processed TCST with {uv_count} UV coordinates")

    def _process_hprm(self, chunk):
        """معالجة قطعة HPRM (معاملات العظام الإضافية) - مثل محاور إضافية للعظام"""
        buffer = chunk.buffer
        bone_param_count = buffer.size() // 12  # 3 floats لكل عظمة (12 بايت)
        print(f"   Found HPRM chunk with {bone_param_count} bone parameter sets")
        
        # تخزين معاملات HPRM الإضافية
        if not hasattr(self, 'hprm_data'):
            self.hprm_data = []
        
        for i in range(bone_param_count):
            # قراءة 3 floats (قد تكون محاور إضافية أو إزاحات)
            param_x = buffer.read_float()
            param_y = buffer.read_float()
            param_z = buffer.read_float()
            
            self.hprm_data.append({
                "bone_index": i if i < len(self.bones) else -1,
                "params": (param_x, param_y, param_z)
            })
            
            # إذا كان لدينا عظام، نطبق التحويل على العظمة المقابلة
            if i < len(self.bones) and hasattr(self, 'bones'):
                # ✅ تم إزالة swizzle من المعاملات - سيتم تطبيقه عند الحاجة
                # يمكن إضافة هذه المعاملات إلى العظمة كبيانات إضافية
                if not hasattr(self.bones[i], 'hprm_params'):
                    self.bones[i].hprm_params = []
                self.bones[i].hprm_params.append((param_x, param_y, param_z))
        
        print(f"   Processed {len(self.hprm_data)} HPRM bone parameter sets")
        
        # تصدير HPRM كملف JSON
        if hasattr(self, 'hprm_data') and self.hprm_data:
            # سيتم التصدير في export_all
            pass

    def _process_xtrn(self, chunk):
        """معالجة قطعة XTRN (مرجع خارجي)"""
        buffer = chunk.buffer
        ref_name = buffer.read_ascii_string(32) if buffer.size() >= 32 else ""
        print(f"   Found XTRN external reference: {ref_name}")

    def _process_nhsa(self, chunk):
        """معالجة قطعة NHSA (تلميح هيكل عظمي للحركة)"""
        buffer = chunk.buffer
        hint_data = buffer.read(min(16, buffer.size()))
        print(f"   Found NHSA skeleton hint: {hint_data.hex()[:32]}...")

    def _process_llun(self, chunk):
        """معالجة قطعة LLUN (Null terminator)"""
        print(f"   Found LLUN null chunk (size: {chunk.header.data_size})")
        # عادةً ما تكون فارغة أو تحتوي على بيانات صفرية

    # ========== دوال تصدير القطع الجديدة ==========
    def export_xtrw_info(self, out_dir: str, base_name: str):
        """تصدير أوزان العظام المنفصلة (XTRW)"""
        if not self.vertex_weights:
            return
        
        # JSON
        json_path = os.path.join(out_dir, f"{base_name}_xtrw.json")
        data = convert_to_json_serializable([{"vertex_id": w.vertex_id, "bone_id": w.bone_id, "weight": w.weight} 
                for w in self.vertex_weights])
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   XTRW (JSON): {json_path}")
        
        # TXT
        txt_path = os.path.join(out_dir, f"{base_name}_xtrw.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# XTRW (Separate Bone Weights)\n")
            f.write("# Format: vertex_id, bone_id, weight\n\n")
            for w in self.vertex_weights:
                f.write(f"{w.vertex_id:6d}, {w.bone_id:3d}, {w.weight:.6f}\n")
        print(f"   XTRW (TXT): {txt_path}")
        
        # CSV
        csv_path = os.path.join(out_dir, f"{base_name}_xtrw.csv")
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write("vertex_id,bone_id,weight\n")
            for w in self.vertex_weights:
                f.write(f"{w.vertex_id},{w.bone_id},{w.weight:.6f}\n")
        print(f"   XTRW (CSV): {csv_path}")

    def export_xtxm_info(self, out_dir: str, base_name: str):
        """تصدير مراجع القوام (XTXM)"""
        if not self.texture_references:
            return
        
        # JSON
        json_path = os.path.join(out_dir, f"{base_name}_xtxm.json")
        data = convert_to_json_serializable([{"index": ref.index, "name": ref.name} for ref in self.texture_references])
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   XTXM (JSON): {json_path}")
        
        # TXT
        txt_path = os.path.join(out_dir, f"{base_name}_xtxm.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# XTXM (Texture References)\n")
            f.write("# Format: index, name\n\n")
            for ref in self.texture_references:
                f.write(f"{ref.index:4d}: {ref.name}\n")
        print(f"   XTXM (TXT): {txt_path}")

    def export_tcst_info(self, out_dir: str, base_name: str):
        """تصدير مجموعات UV الإضافية (TCST)"""
        if not self.extra_uv_sets:
            return
        
        # JSON
        json_path = os.path.join(out_dir, f"{base_name}_tcst.json")
        data = convert_to_json_serializable([{"index": uv_set.index, "uv_count": len(uv_set.uvs), "uvs": uv_set.uvs} 
                for uv_set in self.extra_uv_sets])
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   TCST (JSON): {json_path}")
        
        # TXT
        txt_path = os.path.join(out_dir, f"{base_name}_tcst.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# TCST (Texture Coordinate Sets)\n")
            f.write("# Format: set_index, uv_index, u, v\n\n")
            for uv_set in self.extra_uv_sets:
                f.write(f"Set {uv_set.index}:\n")
                for i, (u, v) in enumerate(uv_set.uvs):
                    f.write(f"  [{i:4d}]: u={u:.6f}, v={v:.6f}\n")
                f.write("\n")
        print(f"   TCST (TXT): {txt_path}")

    def export_hprm_info(self, out_dir: str, base_name: str):
        """تصدير معاملات العظام الإضافية (HPRM)"""
        if not hasattr(self, 'hprm_data') or not self.hprm_data:
            return
        
        # JSON
        json_path = os.path.join(out_dir, f"{base_name}_hprm.json")
        data = convert_to_json_serializable(self.hprm_data)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   HPRM (JSON): {json_path}")
        
        # TXT
        txt_path = os.path.join(out_dir, f"{base_name}_hprm.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# HPRM (Additional Bone Parameters)\n")
            f.write("# Format: bone_index, param_x, param_y, param_z\n\n")
            for data in self.hprm_data:
                bone_name = self.bones[data["bone_index"]].name if data["bone_index"] >= 0 and data["bone_index"] < len(self.bones) else "unknown"
                px, py, pz = data["params"]
                f.write(f"Bone {data['bone_index']:3d} ({bone_name}): ({px:.6f}, {py:.6f}, {pz:.6f})\n")
        print(f"   HPRM (TXT): {txt_path}")
        
        # CSV
        csv_path = os.path.join(out_dir, f"{base_name}_hprm.csv")
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write("bone_index,bone_name,param_x,param_y,param_z\n")
            for data in self.hprm_data:
                bone_name = self.bones[data["bone_index"]].name if data["bone_index"] >= 0 and data["bone_index"] < len(self.bones) else "unknown"
                px, py, pz = data["params"]
                f.write(f"{data['bone_index']},{bone_name},{px:.6f},{py:.6f},{pz:.6f}\n")
        print(f"   HPRM (CSV): {csv_path}")
        
    # دوال التصدير (مشتركة)
    def ensure_dir(self, path):
        Path(path).mkdir(parents=True, exist_ok=True)

    def export_mtl(self, out_dir, base_name, suffix, texture_name=None, has_lightmap=False, material_index=0):
        if material_index > 0:
            mtl_filename = f"{base_name}{suffix}_{material_index}.mtl"
            mat_name = f"Mat_{base_name}{suffix}_{material_index}"
        else:
            mtl_filename = f"{base_name}{suffix}.mtl"
            mat_name = f"Mat_{base_name}{suffix}"
        
        mtl_path = os.path.join(out_dir, mtl_filename)
        
        if texture_name is None:
            texture_name = f"{base_name}.tga"
        
        with open(mtl_path, "w", encoding="utf-8") as f:
            f.write(f"newmtl {mat_name}\n")
            f.write("Ns 10.0000\n")
            f.write("Ka 1.0000 1.0000 1.0000\n")
            f.write("Kd 1.0000 1.0000 1.0000\n")
            f.write("Ks 0.0000 0.0000 0.0000\n")
            f.write(f"map_Kd {texture_name}\n")
            
            if has_lightmap:
                lightmap_name = f"{base_name}_lightmap_{material_index}.png"
                f.write(f"map_Ke {lightmap_name}\n")
                
        print(f"   MTL: {mtl_filename}")
        return mtl_filename, mat_name

    def export_obj(self, out_dir, base_name, suffix, faces, vertices, 
                   has_normals=True, has_uv2=False, lightmap_uvs=None, mtl_filename=None):
        obj_path = os.path.join(out_dir, f"{base_name}{suffix}.obj")
        
        # تحديد اسم ملف MTL واسم المادة
        if mtl_filename is None:
            mtl_file, mat_name = self.export_mtl(out_dir, base_name, suffix, 
                                                 f"{base_name}.tga", 
                                                 has_lightmap=(lightmap_uvs is not None))
            # حالة مادة واحدة
            using_multi_material = False
            default_mat_name = mat_name
        else:
            mtl_file = mtl_filename
            using_multi_material = True
            default_mat_name = f"Mat_{base_name}{suffix}_0"  # اسم افتراضي
        
        with open(obj_path, "w", encoding="utf-8") as f:
            f.write(f"mtllib {mtl_file}\n")
            f.write(f"o {base_name}{suffix}\n")
            
            # كتابة الرؤوس (تم تطبيق swizzle مسبقاً)
            for v in vertices:
                f.write(f"v {v['px']:.6f} {v['py']:.6f} {v['pz']:.6f}\n")
            
            # كتابة إحداثيات النسيج
            if "u" in vertices.dtype.names and "v" in vertices.dtype.names:
                for v in vertices:
                    f.write(f"vt {v['u']:.6f} {1.0 - v['v']:.6f}\n")
            
            if lightmap_uvs is not None:
                for uv in lightmap_uvs:
                    f.write(f"vt {uv[0]:.6f} {1.0 - uv[1]:.6f}\n")
            elif has_uv2 and "u1" in vertices.dtype.names and "v1" in vertices.dtype.names:
                for v in vertices:
                    f.write(f"vt {v['u1']:.6f} {1.0 - v['v1']:.6f}\n")
            
            # كتابة الطبيعيات (تم تطبيق swizzle مسبقاً)
            if has_normals and "nx" in vertices.dtype.names:
                for v in vertices:
                    f.write(f"vn {v['nx']:.6f} {v['ny']:.6f} {v['nz']:.6f}\n")
            
            # كتابة الوجوه
            if faces is not None and len(faces) > 0:
                if not using_multi_material or not hasattr(self.render_mesh_data, 'primitives') or not self.render_mesh_data.primitives:
                    # حالة مادة واحدة - استخدم usemtl واحد لكل الوجوه
                    f.write(f"usemtl {default_mat_name}\n")
                    for face in faces:
                        if len(face) >= 3:
                            a, b, c = face[0], face[1], face[2]
                            a1 = a + 1
                            b1 = b + 1
                            c1 = c + 1
                            
                            if has_normals:
                                f.write(f"f {a1}/{a1}/{a1} {b1}/{b1}/{b1} {c1}/{c1}/{c1}\n")
                            else:
                                f.write(f"f {a1}/{a1} {b1}/{b1} {c1}/{c1}\n")
                else:
                    # مواد متعددة - نكتب usemtl قبل كل مجموعة وجوه مع الحفاظ على ترتيب faces
                    primitives = self.render_mesh_data.primitives
                    current_face_index = 0
                    
                    for i, prim in enumerate(primitives):
                        face_count = prim.face_count
                        if face_count > 0:
                            mat_name = f"Mat_{base_name}{suffix}_{i}"
                            f.write(f"usemtl {mat_name}\n")
                            
                            # نكتب الوجوه من current_face_index إلى current_face_index + face_count
                            for j in range(face_count):
                                if current_face_index + j < len(faces):
                                    face = faces[current_face_index + j]
                                    if len(face) >= 3:
                                        a, b, c = face[0], face[1], face[2]
                                        a1 = a + 1
                                        b1 = b + 1
                                        c1 = c + 1
                                        
                                        if has_normals:
                                            f.write(f"f {a1}/{a1}/{a1} {b1}/{b1}/{b1} {c1}/{c1}/{c1}\n")
                                        else:
                                            f.write(f"f {a1}/{a1} {b1}/{b1} {c1}/{c1}\n")
                            
                            current_face_index += face_count
            else:
                f.write("# No faces in this mesh\n")
                
        print(f"   OBJ: {obj_path}")

    def export_obj_material_group(self, out_dir, base_name, suffix, 
                                  faces_subset, vertices, 
                                  material_index, face_offset,
                                  has_normals=True, has_uv2=False, lightmap_uvs=None):
        obj_filename = f"{base_name}{suffix}_{material_index}.obj"
        obj_path = os.path.join(out_dir, obj_filename)
        mtl_file, mat_name = self.export_mtl(out_dir, base_name, suffix, 
                                             f"{base_name}_{material_index}.tga", 
                                             has_lightmap=(lightmap_uvs is not None),
                                             material_index=material_index)
        
        with open(obj_path, "w", encoding="utf-8") as f:
            f.write(f"mtllib {mtl_file}\n")
            f.write(f"o {base_name}{suffix}_{material_index}\n")
            
            for v in vertices:
                f.write(f"v {v['px']:.6f} {v['py']:.6f} {v['pz']:.6f}\n")
            
            if "u" in vertices.dtype.names and "v" in vertices.dtype.names:
                for v in vertices:
                    f.write(f"vt {v['u']:.6f} {1.0 - v['v']:.6f}\n")
            
            if has_normals and "nx" in vertices.dtype.names:
                for v in vertices:
                    f.write(f"vn {v['nx']:.6f} {v['ny']:.6f} {v['nz']:.6f}\n")
            
            f.write(f"usemtl {mat_name}\n")
            
            if faces_subset is not None and len(faces_subset) > 0:
                for face in faces_subset:
                    if len(face) >= 3:
                        a, b, c = face[0], face[1], face[2]
                        a1 = a + 1
                        b1 = b + 1
                        c1 = c + 1
                        
                        if has_normals:
                            f.write(f"f {a1}/{a1}/{a1} {b1}/{b1}/{b1} {c1}/{c1}/{c1}\n")
                        else:
                            f.write(f"f {a1}/{a1} {b1}/{b1} {c1}/{c1}\n")
        
        print(f"   OBJ material group {material_index}: {obj_path}")
        return obj_path

    def export_render_mesh_simple(self, out_dir, base_name, export_formats=None):
        if export_formats is None:
            export_formats = ["obj"]
        
        if self.render_mesh_data is None:
            print("No render mesh data")
            return
        
        vertices = self.render_mesh_data.vertices
        faces = self.render_mesh_data.faces
        primitives = self.render_mesh_data.primitives
        model_type = self.model_info.model_type
        lightmap_uvs = self.render_mesh_data.lightmap_uvs
        
        # كود مؤقت لطباعة أول 10 رؤوس
        print("First 10 vertices raw data:")
        for i in range(min(10, len(vertices))):
            v = vertices[i]
            # تحويل الرأس إلى قاموس للوصول السهل
            v_dict = {}
            for name in v.dtype.names:
                v_dict[name] = v[name]
            
            # طباعة الحقول المتوفرة
            if model_type == ModelType.SkinnedModel:
                weight_val = v_dict['weight']
                if isinstance(weight_val, np.ndarray):
                    weight_str = f"{weight_val[0]:.2f}" if len(weight_val) > 0 else "0.00"
                else:
                    weight_str = f"{weight_val:.2f}"
                
                index_val = v_dict['index']
                if isinstance(index_val, np.ndarray):
                    index_str = str(index_val[0]) if len(index_val) > 0 else "0"
                else:
                    index_str = str(index_val)
                
                bone_id_val = v_dict['bone_id']
                if isinstance(bone_id_val, np.ndarray):
                    bone_id_str = str(bone_id_val[0]) if len(bone_id_val) > 0 else "0"
                else:
                    bone_id_str = str(bone_id_val)
                
                print(f"  v{i}: pos=({v_dict['pos'][0]:.2f}, {v_dict['pos'][1]:.2f}, {v_dict['pos'][2]:.2f}), "
                      f"normal=({v_dict['normal'][0]:.2f}, {v_dict['normal'][1]:.2f}, {v_dict['normal'][2]:.2f}), "
                      f"uv0=({v_dict['uv0'][0]:.2f}, {v_dict['uv0'][1]:.2f}), "
                      f"weight={weight_str}, index={index_str}, bone_id={bone_id_str}")
            elif model_type == ModelType.StaticModel:
                print(f"  v{i}: pos=({v_dict['pos'][0]:.2f}, {v_dict['pos'][1]:.2f}, {v_dict['pos'][2]:.2f}), "
                      f"normal=({v_dict['normal'][0]:.2f}, {v_dict['normal'][1]:.2f}, {v_dict['normal'][2]:.2f}), "
                      f"uv0=({v_dict['uv0'][0]:.2f}, {v_dict['uv0'][1]:.2f})")
            elif model_type == ModelType.LightmappedModel:
                print(f"  v{i}: pos=({v_dict['pos'][0]:.2f}, {v_dict['pos'][1]:.2f}, {v_dict['pos'][2]:.2f}), "
                      f"uv0=({v_dict['uv0'][0]:.2f}, {v_dict['uv0'][1]:.2f}), "
                      f"uv1=({v_dict['uv1'][0]:.2f}, {v_dict['uv1'][1]:.2f})")
            else:
                # صيغة افتراضية
                fields = []
                for name in v.dtype.names:
                    val = v_dict[name]
                    if isinstance(val, np.ndarray):
                        if len(val) >= 3:
                            fields.append(f"{name}=({val[0]:.2f}, {val[1]:.2f}, {val[2]:.2f})")
                        elif len(val) == 2:
                            fields.append(f"{name}=({val[0]:.2f}, {val[1]:.2f})")
                        elif len(val) == 1:
                            fields.append(f"{name}={val[0]:.2f}" if isinstance(val[0], (float, np.float32)) else f"{name}={val[0]}")
                        else:
                            fields.append(f"{name}={val}")
                    else:
                        if isinstance(val, (float, np.float32, np.float64)):
                            fields.append(f"{name}={val:.2f}")
                        else:
                            fields.append(f"{name}={val}")
                print(f"  v{i}: " + ", ".join(fields))
        
        if model_type == ModelType.SkinnedModel and self.bones:
            # تحضير مصفوفات العظام
            parents = [bone.parent_id for bone in self.bones]
            bind_local = [make_translation_matrix(b.pos.x, b.pos.y, b.pos.z) for b in self.bones]
            bind_global = [None] * len(self.bones)
            
            for i in range(len(self.bones)):
                if parents[i] == -1:
                    bind_global[i] = bind_local[i]
                else:
                    bind_global[i] = bind_global[parents[i]] @ bind_local[i]
            
            inverse_bind = [np.linalg.inv(m) for m in bind_global]
            root_inv = np.linalg.inv(bind_global[0]) if bind_global else None
            
            # استخدام bake_skinning_improved المحدثة مع دعم XTRW و debug_params
            vertices_transformed = bake_skinning_improved(
                vertices, bind_global, inverse_bind, root_inv,
                debug_params=self.debug_params,
                extra_weights=self.vertex_weights
            )
        else:
            dtype_out = np.dtype([
                ("px", np.float32), ("py", np.float32), ("pz", np.float32),
                ("nx", np.float32), ("ny", np.float32), ("nz", np.float32),
                ("u", np.float32), ("v", np.float32)
            ])
            new_verts = []
            for v in vertices:
                pos = v["pos"] if "pos" in v.dtype.names else (v["px"], v["py"], v["pz"])
                normal = v["normal"] if "normal" in v.dtype.names else (0, 0, 0)
                uv = v["uv0"] if "uv0" in v.dtype.names else (0, 0)
                
                # ✅ تطبيق swizzle هنا (مرة واحدة فقط)
                px, py, pz = self.debug_params.swizzle(pos[0], pos[1], pos[2], self.debug_params.v_scale)
                nx, ny, nz = self.debug_params.swizzle(normal[0], normal[1], normal[2], 1.0)
                
                new_verts.append((
                    px, py, pz,
                    nx, ny, nz,
                    float(uv[0]), float(uv[1])
                ))
            vertices_transformed = np.array(new_verts, dtype=dtype_out)

        has_normals = "nx" in vertices_transformed.dtype.names
        has_uv = "u" in vertices_transformed.dtype.names
        
        # ========== 🔴 التصحيح هنا ==========
        # إنشاء material_groups قبل استخدامه
        material_groups = []
        if primitives:
            for i, prim in enumerate(primitives):
                texture_index = prim.diffuse_texture if hasattr(prim, 'diffuse_texture') else 0
                texture_name = get_texture_name(texture_index, base_name, i, self.texture_references)
                material_groups.append({
                    "index": i,
                    "texture_index": texture_index,
                    "texture_name": texture_name,
                    "faces": faces[prim.index_offset:prim.index_offset + prim.face_count]
                })
        else:
            # حالة عدم وجود مواد متعددة
            material_groups.append({
                "index": 0,
                "texture_index": 0,
                "texture_name": get_texture_name(0, base_name, 0, self.texture_references),
                "faces": faces
            })
        # =====================================
        
        if "obj" in export_formats:
            # إنشاء أطلس القوام إذا كان هناك أكثر من مادة
            atlas = None
            if primitives and len(primitives) > 1:
                print(f"   DEBUG: Creating texture atlas for {len(primitives)} materials")
                atlas = self.create_texture_atlas(out_dir, base_name)
                if atlas:
                    print(f"   DEBUG: Applying texture atlas")
                    vertices_transformed = self.apply_texture_atlas_igi2(atlas, vertices_transformed, primitives, base_name)
                    print(f"   DEBUG: Atlas applied")
            
            # إنشاء ملف MTL متعدد المواد
            if primitives and len(primitives) > 1:
                mtl_filename = f"{base_name}_render.mtl"
                mtl_path = os.path.join(out_dir, mtl_filename)
                
                with open(mtl_path, "w", encoding="utf-8") as f:
                    for i, prim in enumerate(primitives):
                        texture_index = prim.diffuse_texture if hasattr(prim, 'diffuse_texture') else 0
                        texture_name = get_texture_name(texture_index, base_name, i, self.texture_references)
                        
                        if atlas and atlas.has_multiple_textures():
                            texture_name = f"{base_name}_atlas.png"
                        
                        mat_name = f"Mat_{base_name}_render_{i}"
                        
                        f.write(f"newmtl {mat_name}\n")
                        f.write("Ns 10.0000\n")
                        f.write("Ka 1.0000 1.0000 1.0000\n")
                        f.write("Kd 1.0000 1.0000 1.0000\n")
                        f.write("Ks 0.0000 0.0000 0.0000\n")
                        f.write(f"map_Kd {texture_name}\n")
                        
                        if lightmap_uvs is not None:
                            lightmap_name = f"{base_name}_lightmap_{i}.png"
                            f.write(f"map_Ke {lightmap_name}\n")
                        
                        f.write("\n")
                
                print(f"   MTL (multi-material): {mtl_path}")
                
                # استدعاء export_obj مع اسم ملف MTL الصحيح
                self.export_obj(out_dir, base_name, "_render", faces, vertices_transformed,
                               has_normals, model_type == ModelType.LightmappedModel, 
                               lightmap_uvs, mtl_filename=mtl_filename)
            else:
                # حالة مادة واحدة
                self.export_obj(out_dir, base_name, "_render", faces, vertices_transformed,
                               has_normals, model_type == ModelType.LightmappedModel, lightmap_uvs)
        
        # ========== 🔴 تصدير glTF كامل مع العظام ==========
        if "gltf" in export_formats:
            # تصدير glTF كامل مع العظام
            has_skinning = model_type == ModelType.SkinnedModel and self.bones
            gltf_path = os.path.join(out_dir, f"{base_name}_render")
            
            # تحضير بيانات العظام
            bones_data = None
            if has_skinning and self.bones:
                bones_data = self.bones
            
            # تحضير الرؤوس مع بيانات الوزن والعظام
            if has_skinning:
                # استخدام الرؤوس المحولة التي تحتوي على weight, bone_id
                vertices_for_gltf = self.prepare_skinned_vertices_for_gltf(vertices_transformed)
                print(f"   Prepared skinned vertices for glTF: {len(vertices_for_gltf)} vertices with weight/bone_id")
            else:
                vertices_for_gltf = vertices_transformed
            
            export_to_gltf_full(self, gltf_path, f"{base_name}_render",
                                vertices_for_gltf, faces, 
                                has_normals, has_uv, has_skinning, bones_data)
        
        # ========== 🔴 تصدير DAE ==========
        if "dae" in export_formats:
            # تجميع كل الوجوه من جميع المواد
            all_faces = []
            for mg in material_groups:
                all_faces.extend(mg["faces"])
            all_faces_array = np.array(all_faces)
            
            dae_path = os.path.join(out_dir, f"{base_name}_render.dae")
            export_to_collada(self, dae_path, f"{base_name}_render", 
                             vertices_transformed, all_faces_array, has_normals, has_uv)


    def prepare_skinned_vertices_for_gltf(self, vertices: np.ndarray) -> np.ndarray:
        """
        تحضير الرؤوس الهيكلية لتصدير glTF مع الحفاظ على بيانات الوزن والعظام
        """
        # إنشاء صيغة تحتوي على px,py,pz, nx,ny,nz, u,v, weight, bone_id
        dtype_out = np.dtype([
            ("px", np.float32), ("py", np.float32), ("pz", np.float32),
            ("nx", np.float32), ("ny", np.float32), ("nz", np.float32),
            ("u", np.float32), ("v", np.float32),
            ("weight", np.float32), ("bone_id", np.uint16)
        ])
        
        new_verts = []
        for v in vertices:
            # استخراج الموقع
            px = float(v["px"]) if "px" in v.dtype.names else 0.0
            py = float(v["py"]) if "py" in v.dtype.names else 0.0
            pz = float(v["pz"]) if "pz" in v.dtype.names else 0.0
            
            # استخراج الطبيعية
            nx = float(v["nx"]) if "nx" in v.dtype.names else 0.0
            ny = float(v["ny"]) if "ny" in v.dtype.names else 0.0
            nz = float(v["nz"]) if "nz" in v.dtype.names else 0.0
            
            # استخراج UV
            u = float(v["u"]) if "u" in v.dtype.names else 0.0
            vt = float(v["v"]) if "v" in v.dtype.names else 0.0
            
            # استخراج بيانات التزين
            weight_val = 1.0
            bone_id_val = 0
            
            if "weight" in v.dtype.names:
                w = v["weight"]
                if isinstance(w, np.ndarray):
                    weight_val = float(w[0]) if len(w) > 0 else 1.0
                else:
                    weight_val = float(w)
            
            if "bone_id" in v.dtype.names:
                b = v["bone_id"]
                if isinstance(b, np.ndarray):
                    bone_id_val = int(b[0]) if len(b) > 0 else 0
                else:
                    bone_id_val = int(b)
            
            new_verts.append((
                px, py, pz,
                nx, ny, nz,
                u, vt,
                weight_val, bone_id_val
            ))
        
        return np.array(new_verts, dtype=dtype_out)

    def export_obj_multi_material(self, out_dir, base_name, suffix, 
                                  vertices, material_groups,
                                  has_normals=True, has_uv=True, lightmap_uvs=None,
                                  atlas=None):
        obj_path = os.path.join(out_dir, f"{base_name}{suffix}.obj")
        
        mtl_filename = f"{base_name}{suffix}.mtl"
        mtl_path = os.path.join(out_dir, mtl_filename)
        
        atlas_mode = ATLAS_MODE
        
        with open(mtl_path, "w", encoding="utf-8") as f:
            if atlas and atlas.has_multiple_textures() and atlas_mode == "merge":
                # ========== وضع الدمج: مادة واحدة ==========
                f.write(f"newmtl atlas_material\n")
                f.write("Ns 10.0000\n")
                f.write("Ka 1.0000 1.0000 1.0000\n")
                f.write("Kd 1.0000 1.0000 1.0000\n")
                f.write("Ks 0.0000 0.0000 0.0000\n")
                f.write(f"map_Kd {base_name}_atlas.png\n")
                print(f"   ✅ MTL mode: MERGE (single 'atlas_material')")
                
            else:
                # ========== الوضع العادي أو وضع الحفاظ ==========
                atlas_name = f"{base_name}_atlas.png" if atlas and atlas.has_multiple_textures() else None
                
                for mg in material_groups:
                    mat_index = mg["index"]
                    texture_index = mg.get("texture_index", 0)
                    texture_name = get_texture_name(texture_index, base_name, mat_index, None)
                    
                    if atlas_name:
                        texture_name = atlas_name  # فقط تغيير مسار الصورة
                    
                    mat_name = f"Mat_{base_name}{suffix}_{mat_index}"
                    
                    f.write(f"newmtl {mat_name}\n")
                    f.write("Ns 10.0000\n")
                    f.write("Ka 1.0000 1.0000 1.0000\n")
                    f.write("Kd 1.0000 1.0000 1.0000\n")
                    f.write("Ks 0.0000 0.0000 0.0000\n")
                    f.write(f"map_Kd {texture_name}\n")
                    f.write("\n")
                
                if atlas_name:
                    print(f"   ✅ MTL mode: PRESERVE (keeping {len(material_groups)} materials, using atlas)")
                
                if lightmap_uvs is not None:
                    lightmap_name = f"{base_name}_lightmap_{mat_index}.png"
                    f.write(f"map_Ke {lightmap_name}\n")
                
                f.write("\n")
        
        # كتابة ملف OBJ
        with open(obj_path, "w", encoding="utf-8") as f:
            f.write(f"mtllib {mtl_filename}\n")
            f.write(f"o {base_name}{suffix}\n")
            
            # كتابة الرؤوس
            for v in vertices:
                f.write(f"v {v['px']:.6f} {v['py']:.6f} {v['pz']:.6f}\n")
            
            # كتابة إحداثيات النسيج
            if has_uv:
                for v in vertices:
                    f.write(f"vt {v['u']:.6f} {1.0 - v['v']:.6f}\n")
            
            # كتابة الطبيعيات
            if has_normals:
                for v in vertices:
                    f.write(f"vn {v['nx']:.6f} {v['ny']:.6f} {v['nz']:.6f}\n")
            
            # كتابة الوجوه
            if atlas and atlas.has_multiple_textures() and atlas_mode == "merge":
                # وضع الدمج: usemtl واحد فقط
                f.write(f"usemtl atlas_material\n")
                for mg in material_groups:
                    for face in mg["faces"]:
                        if len(face) >= 3:
                            a, b, c = face[0], face[1], face[2]
                            a1, b1, c1 = a+1, b+1, c+1
                            
                            if has_normals:
                                f.write(f"f {a1}/{a1}/{a1} {b1}/{b1}/{b1} {c1}/{c1}/{c1}\n")
                            else:
                                f.write(f"f {a1}/{a1} {b1}/{b1} {c1}/{c1}\n")
            else:
                # وضع الحفاظ: usemtl لكل مادة
                for mg in material_groups:
                    mat_index = mg["index"]
                    mat_name = f"Mat_{base_name}{suffix}_{mat_index}"
                    f.write(f"usemtl {mat_name}\n")
                    
                    for face in mg["faces"]:
                        if len(face) >= 3:
                            a, b, c = face[0], face[1], face[2]
                            a1, b1, c1 = a+1, b+1, c+1
                            
                            if has_normals:
                                f.write(f"f {a1}/{a1}/{a1} {b1}/{b1}/{b1} {c1}/{c1}/{c1}\n")
                            else:
                                f.write(f"f {a1}/{a1} {b1}/{b1} {c1}/{c1}\n")
                                
        print(f"   OBJ (multi-material): {obj_path}")
        print(f"   MTL (multi-material): {mtl_path}")


    def export_render_mesh_multi_material(self, out_dir, base_name, export_formats=None):
        if export_formats is None:
            export_formats = ["obj"]
        
        if self.render_mesh_data is None:
            print("No render mesh data")
            return
        
        vertices = self.render_mesh_data.vertices
        faces = self.render_mesh_data.faces
        primitives = self.render_mesh_data.primitives
        model_type = self.model_info.model_type
        lightmap_uvs = self.render_mesh_data.lightmap_uvs
        
        if model_type == ModelType.SkinnedModel and self.bones:
            parents = [bone.parent_id for bone in self.bones]
            bind_local = [make_translation_matrix(b.pos.x, b.pos.y, b.pos.z) for b in self.bones]
            bind_global = [None] * len(self.bones)
            
            for i in range(len(self.bones)):
                if parents[i] == -1:
                    bind_global[i] = bind_local[i]
                else:
                    bind_global[i] = bind_global[parents[i]] @ bind_local[i]
            
            inverse_bind = [np.linalg.inv(m) for m in bind_global]
            root_inv = np.linalg.inv(bind_global[0]) if bind_global else None
            
            vertices_transformed = bake_skinning_improved(
                vertices, bind_global, inverse_bind, root_inv,
                debug_params=self.debug_params,
                extra_weights=self.vertex_weights
            )
        else:
            dtype_out = np.dtype([
                ("px", np.float32), ("py", np.float32), ("pz", np.float32),
                ("nx", np.float32), ("ny", np.float32), ("nz", np.float32),
                ("u", np.float32), ("v", np.float32)
            ])
            new_verts = []
            for v in vertices:
                pos = v["pos"] if "pos" in v.dtype.names else (v["px"], v["py"], v["pz"])
                normal = v["normal"] if "normal" in v.dtype.names else (0, 0, 0)
                uv = v["uv0"] if "uv0" in v.dtype.names else (0, 0)
                
                px, py, pz = self.debug_params.swizzle(pos[0], pos[1], pos[2], self.debug_params.v_scale)
                nx, ny, nz = self.debug_params.swizzle(normal[0], normal[1], normal[2], 1.0)
                
                new_verts.append((
                    px, py, pz,
                    nx, ny, nz,
                    float(uv[0]), float(uv[1])
                ))
            vertices_transformed = np.array(new_verts, dtype=dtype_out)

        has_normals = "nx" in vertices_transformed.dtype.names
        has_uv = "u" in vertices_transformed.dtype.names
        
        if primitives:
            print(f"Exporting {len(primitives)} material groups...")
            for i, prim in enumerate(primitives):
                start_idx = prim.index_offset
                face_count = prim.face_count
                if face_count > 0:
                    faces_subset = faces[start_idx:start_idx + face_count]
                    
                    if "obj" in export_formats:
                        self.export_obj_material_group(out_dir, base_name, "_render",
                                                      faces_subset, vertices_transformed,
                                                      i, start_idx, has_normals,
                                                      model_type == ModelType.LightmappedModel,
                                                      lightmap_uvs)
                    
                    if "dae" in export_formats:
                        dae_path = os.path.join(out_dir, f"{base_name}_render_{i}.dae")
                        export_to_collada(self, dae_path, f"{base_name}_render_{i}", 
                                         vertices_transformed, faces_subset, has_normals, has_uv)
                    
                    if "gltf" in export_formats:
                        # تصدير glTF كامل لكل مادة
                        has_skinning = model_type == ModelType.SkinnedModel and self.bones
                        gltf_path = os.path.join(out_dir, f"{base_name}_render_{i}")
                        bones_data = self.bones if has_skinning else None
                        export_to_gltf_full(self, gltf_path, f"{base_name}_render_{i}", 
                                          vertices_transformed, faces_subset, 
                                          has_normals, has_uv, has_skinning, bones_data)
                    
                    if "directx" in export_formats:
                        # تصدير DirectX (.X) لكل مادة
                        print(f"   DEBUG: DirectX export called for {base_name}_render_{i}")
                        dx_path = os.path.join(out_dir, f"{base_name}_render_{i}.x")
                        print(f"   DEBUG: DirectX path: {dx_path}")
                        export_to_directx(self, dx_path, "igi2" if hasattr(self, 'txan_data') else "igi1")
                        print(f"   DEBUG: DirectX export completed for {base_name}_render_{i}")
        else:
            if "obj" in export_formats:
                self.export_obj(out_dir, base_name, "_render", faces, vertices_transformed,
                               has_normals, model_type == ModelType.LightmappedModel, lightmap_uvs)

            if "dae" in export_formats:
                dae_path = os.path.join(out_dir, f"{base_name}_render.dae")
                export_to_collada(self, dae_path, f"{base_name}_render", 
                                 vertices_transformed, faces, has_normals, has_uv)
            
            if "gltf" in export_formats:
                # تصدير glTF كامل
                has_skinning = model_type == ModelType.SkinnedModel and self.bones
                gltf_path = os.path.join(out_dir, f"{base_name}_render")
                bones_data = self.bones if has_skinning else None
                export_to_gltf_full(self, gltf_path, f"{base_name}_render", 
                                  vertices_transformed, faces, 
                                  has_normals, has_uv, has_skinning, bones_data)
        
        if "directx" in export_formats:
            # تصدير DirectX (.X) كامل مع العظام والتزين
            print(f"   DEBUG: DirectX export called for {base_name}")
            dx_path = os.path.join(out_dir, f"{base_name}_render.x")
            print(f"   DEBUG: DirectX path: {dx_path}")
            export_to_directx(self, dx_path, "igi2" if hasattr(self, 'txan_data') else "igi1")
            print(f"   DEBUG: DirectX export completed")

    def export_render_mesh(self, out_dir, base_name, export_formats=None):
        if export_formats is None:
            export_formats = ["obj"]
        
        print(f"   DEBUG: export_render_mesh called with export_mode={self.export_mode}, export_formats={export_formats}")
        if self.export_mode == "multi":
            print(f"   DEBUG: Using multi-material export")
            self.export_render_mesh_multi_material(out_dir, base_name, export_formats)
        else:
            print(f"   DEBUG: Using simple export")
            self.export_render_mesh_simple(out_dir, base_name, export_formats)

    def export_shadow_mesh(self, out_dir, base_name, export_formats=None):
        if export_formats is None:
            export_formats = ["obj"]
        
        if self.shadow_mesh_data is None:
            print("No shadow mesh data found")
            return
        
        if self.shadow_mesh_data.vertices is None or len(self.shadow_mesh_data.vertices) == 0:
            print("Shadow mesh has no vertices")
            return
        
        vertices = self.shadow_mesh_data.vertices
        faces = self.shadow_mesh_data.faces
        
        # ✅ تطبيق swizzle على رؤوس الظل هنا
        new_verts = []
        for v in vertices:
            if len(v) >= 3:
                px, py, pz = self.debug_params.swizzle(v[0], v[1], v[2], self.debug_params.v_scale)
                new_verts.append((px, py, pz, 0, 0, 0, 0, 0))
        
        if not new_verts:
            print("No valid shadow vertices")
            return
        
        dtype_out = np.dtype([
            ("px", np.float32), ("py", np.float32), ("pz", np.float32),
            ("nx", np.float32), ("ny", np.float32), ("nz", np.float32),
            ("u", np.float32), ("v", np.float32)
        ])
        
        verts_arr = np.array(new_verts, dtype=dtype_out)
        
        face_array = None
        if faces is not None and len(faces) > 0:
            if "face" in faces.dtype.names:
                face_array = faces["face"]
            else:
                face_array = faces
            print(f"Exporting shadow mesh with {len(face_array)} faces")
        else:
            print("Shadow mesh has no faces, exporting as point cloud (no faces)")
            face_array = np.array([[0, 0, 0]])
        
        if "obj" in export_formats:
            self.export_obj(out_dir, base_name, "_shadow", face_array, verts_arr, has_normals=False)
        
        if "dae" in export_formats:
            dae_path = os.path.join(out_dir, f"{base_name}_shadow.dae")
            export_to_collada(self, dae_path, f"{base_name}_shadow", verts_arr, face_array, False, False)
        
        if "gltf" in export_formats:
            gltf_path = os.path.join(out_dir, f"{base_name}_shadow")
            export_to_gltf(self, gltf_path, f"{base_name}_shadow", verts_arr, face_array, False, False)

    def export_collision_mesh(self, out_dir, base_name, index=0, export_formats=None):
        if export_formats is None:
            export_formats = ["obj"]
        
        cmesh = self.collision_mesh_data if index == 0 else self.collision_mesh_data2
        if cmesh is None:
            return
        
        faces = cmesh.faces["face"] if "face" in cmesh.faces.dtype.names else cmesh.faces
        vertices = cmesh.vertices
        
        # ✅ تطبيق swizzle على رؤوس التصادم هنا
        new_verts = []
        for v in vertices:
            pos = v["pos"]
            px, py, pz = self.debug_params.swizzle(pos[0], pos[1], pos[2], self.debug_params.v_scale)
            new_verts.append((px, py, pz, 0, 0, 0, 0, 0))
        
        if not new_verts:
            print("No valid collision vertices")
            return
        
        dtype_out = np.dtype([
            ("px", np.float32), ("py", np.float32), ("pz", np.float32),
            ("nx", np.float32), ("ny", np.float32), ("nz", np.float32),
            ("u", np.float32), ("v", np.float32)
        ])
        
        verts_arr = np.array(new_verts, dtype=dtype_out)
        suffix = f"_col{index}" if index > 0 else "_col"
        
        if "obj" in export_formats:
            self.export_obj(out_dir, base_name, suffix, faces, verts_arr, has_normals=False)
            
            # ✅ إضافة معلومات المواد إلى ملف OBJ كتعليقات
            if self.collision_materials:
                obj_path = os.path.join(out_dir, f"{base_name}{suffix}.obj")
                try:
                    # إعادة فتح الملف وإضافة تعليقات المواد
                    with open(obj_path, 'r+', encoding='utf-8') as f:
                        content = f.read()
                        f.seek(0)
                        f.write(f"# Collision Mesh with {len(self.collision_materials)} materials\n")
                        f.write(f"# Material indices in faces: 4th component after a,b,c\n")
                        f.write(f"# Face format: a b c material_id\n\n")
                        f.write(content)
                    print(f"   Added material info to {obj_path}")
                except Exception as e:
                    print(f"   Error adding material info to OBJ: {e}")
        
        if "dae" in export_formats:
            dae_path = os.path.join(out_dir, f"{base_name}{suffix}.dae")
            export_to_collada(self, dae_path, f"{base_name}{suffix}", verts_arr, faces, False, False)
        
        if "gltf" in export_formats:
            gltf_path = os.path.join(out_dir, f"{base_name}{suffix}")
            export_to_gltf(self, gltf_path, f"{base_name}{suffix}", verts_arr, faces, False, False)
            
    def export_lightmaps(self, out_dir, base_name, lightmap_format="png"):
        if not self.lightmaps:
            return
        
        lightmap_dir = os.path.join(out_dir, "lightmaps")
        self.ensure_dir(lightmap_dir)
        
        for i, lightmap in enumerate(self.lightmaps):
            tga_path = os.path.join(lightmap_dir, f"{base_name}_lightmap_{i}.tga")
            try:
                with open(tga_path, "wb") as f:
                    f.write(lightmap.data)
                print(f"   Lightmap {i} (TGA): {tga_path} ({lightmap.width}x{lightmap.height})")
            except Exception as e:
                print(f"   Error saving TGA lightmap {i}: {e}")
            
            if lightmap_format in ["png", "both"] and PIL_AVAILABLE:
                png_path = os.path.join(lightmap_dir, f"{base_name}_lightmap_{i}.png")
                if save_lightmap_as_png(lightmap, png_path):
                    print(f"   Lightmap {i} (PNG): {png_path}")
            
            if lightmap_format in ["dds", "both"]:
                dds_path = os.path.join(lightmap_dir, f"{base_name}_lightmap_{i}.dds")
                if save_lightmap_as_dds(lightmap, dds_path):
                    print(f"   Lightmap {i} (DDS): {dds_path}")

    def export_attachments(self, out_dir, base_name):
        if not self.attachments:
            return
        
        att_path = os.path.join(out_dir, f"{base_name}_attachments.txt")
        with open(att_path, "w", encoding="utf-8") as f:
            f.write("# Attachment points\n")
            f.write("# Format: name\tposition (x,y,z)\tbone_id\n\n")
            for a in self.attachments:
                # ✅ تطبيق swizzle على مواقع المرفقات هنا
                px, py, pz = self.debug_params.swizzle(a.pos.x, a.pos.y, a.pos.z, self.debug_params.v_scale)
                f.write(f"{a.name}\t({px:.2f}, {py:.2f}, {pz:.2f})\tbone_id={a.bone_id}\n")
        print(f"   Attachments: {att_path}")

    def export_extra_data(self, out_dir, base_name):
        if self.magic_vertices:
            path = os.path.join(out_dir, f"{base_name}_magic_vertices.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write("# Magic Vertices (XTVM)\n")
                f.write("# Format: pos_x pos_y pos_z type\n\n")
                for mv in self.magic_vertices:
                    # ✅ تطبيق swizzle على الرؤوس السحرية هنا
                    px, py, pz = self.debug_params.swizzle(mv.pos.x, mv.pos.y, mv.pos.z, self.debug_params.v_scale)
                    f.write(f"{px:.6f} {py:.6f} {pz:.6f} {mv.type}\n")
            print(f"   Magic vertices: {path}")
        
        if self.portals:
            path = os.path.join(out_dir, f"{base_name}_portals.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write("# Portals (TROP)\n")
                f.write("# Format: start_vertex num_vertices start_face num_faces portal_id\n\n")
                for p in self.portals:
                    f.write(f"{p.start_vertex} {p.num_vertices} {p.start_face} {p.num_faces} {p.portal_id}\n")
                
                if self.portal_vertices:
                    f.write("\n# Portal Vertices (XVTP)\n")
                    f.write("# Format: index pos_x pos_y pos_z\n\n")
                    for i, pv in enumerate(self.portal_vertices):
                        # ✅ تطبيق swizzle على رؤوس البوابات هنا
                        px, py, pz = self.debug_params.swizzle(pv.pos.x, pv.pos.y, pv.pos.z, self.debug_params.v_scale)
                        f.write(f"{i} {px:.6f} {py:.6f} {pz:.6f}\n")
                
                if self.portal_faces:
                    f.write("\n# Portal Faces (CFTP)\n")
                    f.write("# Format: a b c\n\n")
                    for pf in self.portal_faces:
                        f.write(f"{pf.a} {pf.b} {pf.c}\n")
            print(f"   Portals: {path}")
        
        if self.glow_sprites:
            path = os.path.join(out_dir, f"{base_name}_glow_sprites.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write("# Glow Sprites (WOLG)\n")
                f.write("# Format: pos_x pos_y pos_z radius color_r color_g color_b\n\n")
                for g in self.glow_sprites:
                    # ✅ تطبيق swizzle على مواقع التوهجات هنا
                    px, py, pz = self.debug_params.swizzle(g.pos.x, g.pos.y, g.pos.z, self.debug_params.v_scale)
                    f.write(f"{px:.6f} {py:.6f} {pz:.6f} {g.radius:.6f} {g.color_r:.6f} {g.color_g:.6f} {g.color_b:.6f}\n")
            print(f"   Glow sprites: {path}")
        
        # ✅ يجب أن يكون if self.collision_materials خارج شرط glow_sprites
        if self.collision_materials:
            path = os.path.join(out_dir, f"{base_name}_collision_materials.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write("# Collision Materials (TAMC)\n")
                f.write("# Format: opacity portal_id texture_id unknown1 game_material_id unknown2\n\n")
                for i, mat in enumerate(self.collision_materials):
                    f.write(f"Material {i}:\n")
                    f.write(f"  opacity: {mat.opacity:.6f}\n")
                    f.write(f"  portal_id: {mat.portal_id} (0x{mat.portal_id:08X})\n")
                    f.write(f"  texture_id: {mat.texture_id}\n")
                    f.write(f"  unknown1: {mat.unknown1}\n")
                    f.write(f"  game_material_id: {mat.game_material_id}\n")
                    f.write(f"  unknown2: {mat.unknown2}\n\n")
            print(f"   Collision materials: {path}")
        
        if self.txan_data:
            path = os.path.join(out_dir, f"{base_name}_txan.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write("# TXAN Animation Data\n")
                f.write("# Format: 28 uint32 fields\n\n")
                for i, txan in enumerate(self.txan_data):
                    f.write(f"TXAN {i}:\n")
                    f.write("Fields: " + " ".join(str(x) for x in txan.unknown_fields) + "\n\n")
            print(f"   TXAN data: {path}")
    
    def export_collision_materials(self, out_dir: str, base_name: str):
        print(f"   DEBUG: export_collision_materials called with {len(self.collision_materials)} materials")
        if self.collision_materials is None:
            print(f"   DEBUG: collision_materials is None")
            return
        if len(self.collision_materials) == 0:
            print(f"   DEBUG: collision_materials is empty")
            return
            
        # تحويل المواد إلى قواميس قابلة للتصدير
        materials_list = []
        for i, mat in enumerate(self.collision_materials):
            mat_dict = {
                "index": i,
                "opacity": mat.opacity,
                "portal_id": mat.portal_id,
                "texture_id": mat.texture_id,
                "unknown1": mat.unknown1,
                "game_material_id": mat.game_material_id,
                "unknown2": mat.unknown2
            }
            materials_list.append(mat_dict)
        
        # تصدير كـ JSON
        json_path = os.path.join(out_dir, f"{base_name}_collision_materials.json")
        data = convert_to_json_serializable(materials_list)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   Collision materials (JSON): {json_path}")
        
        # أيضاً تصدير كملخص نصي
        txt_path = os.path.join(out_dir, f"{base_name}_collision_materials.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# Collision Materials\n")
            f.write("# Format depends on game version\n\n")
            for i, mat_dict in enumerate(materials_list):
                f.write(f"Material {i}:\n")
                for key, value in mat_dict.items():
                    f.write(f"  {key}: {value}\n")
                f.write("\n")
        print(f"   Collision materials (TXT): {txt_path}")
    
    def export_collision_spheres(self, out_dir: str, base_name: str):
        """تصدير كرات التصادم كملف OBJ (كرات) وملف نصي"""
        if not hasattr(self, 'collision_mesh_data') or self.collision_mesh_data is None:
            return
        
        spheres = self.collision_mesh_data.spheres
        if spheres is None or len(spheres) == 0:
            return
        
        # تصدير كملخص نصي
        txt_path = os.path.join(out_dir, f"{base_name}_collision_spheres.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# Collision Spheres (IGI2)\n")
            f.write("# Format: center_x center_y center_z radius type count vertex_a vertex_b\n\n")
            
            for i, sphere in enumerate(spheres):
                pos = sphere["pos"]
                # ✅ تطبيق swizzle على مركز الكرة هنا
                cx, cy, cz = self.debug_params.swizzle(pos[0], pos[1], pos[2], self.debug_params.v_scale)
                radius = sphere["radius"][0]
                sphere_type = sphere["type"][0]
                count = sphere["count"][0]
                vertex_a = sphere["vertex_a"][0]
                vertex_b = sphere["vertex_b"][0]
                f.write(f"Sphere {i}: center=({cx:.2f}, {cy:.2f}, {cz:.2f}), "
                       f"radius={radius:.2f}, type={sphere_type}, count={count}, "
                       f"vertex_a={vertex_a}, vertex_b={vertex_b}\n")
        
        print(f"   Collision spheres (TXT): {txt_path}")
        
    # ========== الدوال الجديدة المضافة ==========
    def export_magic_vertices_improved(self, out_dir, base_name):
        """تصدير الرؤوس السحرية بصيغ متعددة"""
        if not self.magic_vertices:
            return
        
        # 1. الملف النصي الحالي (محسن)
        txt_path = os.path.join(out_dir, f"{base_name}_magic_vertices.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("# Magic Vertices (XTVM) - IGI2\n")
            f.write("# Format: pos_x pos_y pos_z type\n")
            f.write("# type: نوع الحدث (0=?, 1=?, 2=?, ...)\n\n")
            for i, mv in enumerate(self.magic_vertices):
                px, py, pz = self.debug_params.swizzle(mv.pos.x, mv.pos.y, mv.pos.z, self.debug_params.v_scale)
                f.write(f"{i:4d}: {px:8.2f} {py:8.2f} {pz:8.2f} {mv.type:4d}\n")
        print(f"   Magic vertices (TXT): {txt_path}")
        
        # 2. تصدير كـ CSV (للاستيراد في برامج الجداول)
        csv_path = os.path.join(out_dir, f"{base_name}_magic_vertices.csv")
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write("index,pos_x,pos_y,pos_z,type\n")
            for i, mv in enumerate(self.magic_vertices):
                px, py, pz = self.debug_params.swizzle(mv.pos.x, mv.pos.y, mv.pos.z, self.debug_params.v_scale)
                f.write(f"{i},{px:.6f},{py:.6f},{pz:.6f},{mv.type}\n")
        print(f"   Magic vertices (CSV): {csv_path}")
        
        # 3. تصدير كـ JSON (للاستخدام البرمجي)
        json_path = os.path.join(out_dir, f"{base_name}_magic_vertices.json")
        data = [{"index": i, "pos": [px, py, pz], "type": mv.type} 
                for i, mv in enumerate(self.magic_vertices)
                for px, py, pz in [self.debug_params.swizzle(mv.pos.x, mv.pos.y, mv.pos.z, self.debug_params.v_scale)]]
        data = convert_to_json_serializable(data)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"   Magic vertices (JSON): {json_path}")


    def export_portals_as_mesh(self, out_dir, base_name):
        """تصدير البوابات كشبكة منفصلة (OBJ)"""
        if not self.portals or not self.portal_vertices or not self.portal_faces:
            return
        
        # تجهيز الرؤوس (مع تطبيق swizzle)
        vertices = []
        for pv in self.portal_vertices:
            px, py, pz = self.debug_params.swizzle(pv.pos.x, pv.pos.y, pv.pos.z, self.debug_params.v_scale)
            vertices.append([px, py, pz])
        
        # تجهيز الوجوه
        faces = []
        for pf in self.portal_faces:
            faces.append([pf.a, pf.b, pf.c])
        
        if not vertices or not faces:
            return
        
        # إنشاء مصفوفة رؤوس بالصيغة المطلوبة
        dtype_out = np.dtype([
            ("px", np.float32), ("py", np.float32), ("pz", np.float32),
            ("nx", np.float32), ("ny", np.float32), ("nz", np.float32),
            ("u", np.float32), ("v", np.float32)
        ])
        
        verts_arr = np.array([(v[0], v[1], v[2], 0,0,0,0,0) for v in vertices], dtype=dtype_out)
        faces_arr = np.array(faces)
        
        # تصدير كـ OBJ
        obj_path = os.path.join(out_dir, f"{base_name}_portals.obj")
        
        with open(obj_path, "w", encoding="utf-8") as f:
            f.write(f"# Portal mesh for {base_name}\n")
            f.write(f"# {len(self.portals)} portals, {len(vertices)} vertices, {len(faces)} faces\n\n")
            f.write(f"o {base_name}_portals\n")
            
            for v in verts_arr:
                f.write(f"v {v['px']:.6f} {v['py']:.6f} {v['pz']:.6f}\n")
            
            f.write(f"usemtl default\n")
            for face in faces_arr:
                a, b, c = face[0]+1, face[1]+1, face[2]+1
                f.write(f"f {a} {b} {c}\n")
        
        print(f"   Portals mesh (OBJ): {obj_path}")
        
        # أيضاً تصدير معلومات البوابات بشكل مفصل
        portals_txt = os.path.join(out_dir, f"{base_name}_portals_detailed.txt")
        with open(portals_txt, "w", encoding="utf-8") as f:
            f.write("# Portal Definitions (TROP)\n")
            f.write("# Format: portal_id: start_vertex num_vertices start_face num_faces\n\n")
            for p in self.portals:
                f.write(f"Portal {p.portal_id:3d}: "
                       f"vtx={p.start_vertex:4d}-{p.start_vertex+p.num_vertices-1:4d} "
                       f"({p.num_vertices:4d} vertices), "
                       f"faces={p.start_face:4d}-{p.start_face+p.num_faces-1:4d} "
                       f"({p.num_faces:4d} faces)\n")
        print(f"   Portal details (TXT): {portals_txt}")


    def export_glow_sprites_improved(self, out_dir, base_name):
        """تصدير التوهجات ككرات (spheres) في OBJ وملف نصي"""
        if not self.glow_sprites:
            return
        
        # 1. الملف النصي المحسن
        txt_path = os.path.join(out_dir, f"{base_name}_glow_sprites.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("# Glow Sprites (WOLG) - IGI2\n")
            f.write("# Format: pos_x pos_y pos_z radius color_r color_g color_b\n\n")
            for i, g in enumerate(self.glow_sprites):
                px, py, pz = self.debug_params.swizzle(g.pos.x, g.pos.y, g.pos.z, self.debug_params.v_scale)
                f.write(f"{i:3d}: ({px:8.2f}, {py:8.2f}, {pz:8.2f}) "
                       f"r={g.radius:6.2f} "
                       f"color=({g.color_r:.3f}, {g.color_g:.3f}, {g.color_b:.3f})\n")
        print(f"   Glow sprites (TXT): {txt_path}")
        
        # 2. تصدير كـ JSON
        json_path = os.path.join(out_dir, f"{base_name}_glow_sprites.json")
        data = []
        for i, g in enumerate(self.glow_sprites):
            px, py, pz = self.debug_params.swizzle(g.pos.x, g.pos.y, g.pos.z, self.debug_params.v_scale)
            data.append({
                "index": i, 
                "pos": [px, py, pz], 
                "radius": g.radius,
                "color": [g.color_r, g.color_g, g.color_b]
            })
        data = convert_to_json_serializable(data)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"   Glow sprites (JSON): {json_path}")
        
        # 3. تصدير ككرات في OBJ (اختياري)
        if len(self.glow_sprites) <= 100:  # فقط إذا كان العدد معقولاً
            obj_path = os.path.join(out_dir, f"{base_name}_glow_spheres.obj")
            with open(obj_path, "w", encoding="utf-8") as f:
                f.write(f"# Glow spheres for {base_name}\n")
                f.write(f"# Each sphere is represented by its center point\n\n")
                f.write(f"o {base_name}_glow_spheres\n")
                
                for i, g in enumerate(self.glow_sprites):
                    px, py, pz = self.debug_params.swizzle(g.pos.x, g.pos.y, g.pos.z, self.debug_params.v_scale)
                    # نكتب مركز الكرة كنقطة (يمكن استيرادها كنقاط في برامج النمذجة)
                    f.write(f"v {px:.6f} {py:.6f} {pz:.6f}\n")
                    
                    # نضيف تعليقاً بنصف القطر واللون
                    f.write(f"# sphere {i}: radius={g.radius:.2f}, color=({g.color_r:.3f}, {g.color_g:.3f}, {g.color_b:.3f})\n")
                
                # نكتب نقطة واحدة فقط (بدون وجوه)
                f.write(f"p 1\n")
            
            print(f"   Glow spheres as points (OBJ): {obj_path}")

    # ========== دوال HSEM و D3DR الجديدة لـ IGI2 ==========
    def export_hsem_info(self, out_dir: str, base_name: str):
        """تصدير معلومات HSEM (Model Info) كملف JSON ونصي"""
        if not self.model_info:
            return
        
        # 1. تحويل الكائن إلى قاموس
        info_dict = {
            "version": self.model_info.version,
            "creation_date": self.model_info.creation_type.isoformat(),
            "model_type": self.model_info.model_type.name,
            "model_type_value": self.model_info.model_type.value,
            "unknown1": self.model_info.unknown1,
            "unknown2": self.model_info.unknown2,
            "unknown3": self.model_info.unknown3,
            "bounding_sphere1": {
                "center": [self.model_info.bounding_sphere1.pos.x, 
                           self.model_info.bounding_sphere1.pos.y, 
                           self.model_info.bounding_sphere1.pos.z],
                "radius": self.model_info.bounding_sphere1.radius
            },
            "bounding_sphere2": {
                "center": [self.model_info.bounding_sphere2.pos.x, 
                           self.model_info.bounding_sphere2.pos.y, 
                           self.model_info.bounding_sphere2.pos.z],
                "radius": self.model_info.bounding_sphere2.radius
            },
            "bounding_sphere3": {
                "center": [self.model_info.bounding_sphere3.pos.x, 
                           self.model_info.bounding_sphere3.pos.y, 
                           self.model_info.bounding_sphere3.pos.z],
                "radius": self.model_info.bounding_sphere3.radius
            },
            "render_mesh": {
                "face_count": self.model_info.render_mesh_info.face_count,
                "vertex_count": self.model_info.render_mesh_info.vertex_count,
                "buffer_size": self.model_info.render_mesh_info.buffer_size
            },
            "collision_mesh": {
                "face_count": self.model_info.collision_mesh_info.face_count,
                "vertex_count": self.model_info.collision_mesh_info.vertex_count,
                "buffer_size": self.model_info.collision_mesh_info.buffer_size
            },
            "something_radius": self.model_info.something_radius,
            "field_80": self.model_info.field_80,
            "attachment_count": self.model_info.attachment_count,
            "magic_vertex_count": self.model_info.magic_vertex_count,
            "portal_count": self.model_info.portal_count,
            "glow_count": self.model_info.glow_count,
            "bone_count": self.model_info.bone_count,
            "field_8C": self.model_info.field_8C,
            "field_90": self.model_info.field_90,
            "field_94": self.model_info.field_94,
            "field_98": self.model_info.field_98,
            "field_9C": self.model_info.field_9C,
            "field_A0": self.model_info.field_A0,
            "field_A4": self.model_info.field_A4,
            "field_A8": self.model_info.field_A8,
            "field_AC": self.model_info.field_AC,
            "field_B0": self.model_info.field_B0,
        }
        
        # 2. تصدير كـ JSON
        json_path = os.path.join(out_dir, f"{base_name}_hsem.json")
        data = convert_to_json_serializable(info_dict)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   HSEM info (JSON): {json_path}")
        
        # 3. تصدير كملخص نصي
        txt_path = os.path.join(out_dir, f"{base_name}_hsem.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# HSEM (Model Info) - IGI2\n")
            f.write(f"Version: {self.model_info.version}\n")
            f.write(f"Creation Date: {self.model_info.creation_type.isoformat()}\n")
            f.write(f"Model Type: {self.model_info.model_type.name} ({self.model_info.model_type.value})\n")
            f.write(f"Unknown values: {self.model_info.unknown1}, {self.model_info.unknown2}, {self.model_info.unknown3}\n\n")
            
            f.write("Bounding Spheres:\n")
            f.write(f"  Sphere 1: center=({self.model_info.bounding_sphere1.pos.x:.2f}, {self.model_info.bounding_sphere1.pos.y:.2f}, {self.model_info.bounding_sphere1.pos.z:.2f}), radius={self.model_info.bounding_sphere1.radius:.2f}\n")
            f.write(f"  Sphere 2: center=({self.model_info.bounding_sphere2.pos.x:.2f}, {self.model_info.bounding_sphere2.pos.y:.2f}, {self.model_info.bounding_sphere2.pos.z:.2f}), radius={self.model_info.bounding_sphere2.radius:.2f}\n")
            f.write(f"  Sphere 3: center=({self.model_info.bounding_sphere3.pos.x:.2f}, {self.model_info.bounding_sphere3.pos.y:.2f}, {self.model_info.bounding_sphere3.pos.z:.2f}), radius={self.model_info.bounding_sphere3.radius:.2f}\n\n")
            
            f.write("Render Mesh:\n")
            f.write(f"  Faces: {self.model_info.render_mesh_info.face_count}\n")
            f.write(f"  Vertices: {self.model_info.render_mesh_info.vertex_count}\n")
            f.write(f"  Buffer Size: {self.model_info.render_mesh_info.buffer_size}\n\n")
            
            f.write("Collision Mesh:\n")
            f.write(f"  Faces: {self.model_info.collision_mesh_info.face_count}\n")
            f.write(f"  Vertices: {self.model_info.collision_mesh_info.vertex_count}\n")
            f.write(f"  Buffer Size: {self.model_info.collision_mesh_info.buffer_size}\n\n")
            
            f.write(f"Something Radius: {self.model_info.something_radius}\n")
            f.write(f"Field 80: {self.model_info.field_80}\n\n")
            
            f.write("Counts:\n")
            f.write(f"  Attachments: {self.model_info.attachment_count}\n")
            f.write(f"  Magic Vertices: {self.model_info.magic_vertex_count}\n")
            f.write(f"  Portals: {self.model_info.portal_count}\n")
            f.write(f"  Glow Sprites: {self.model_info.glow_count}\n")
            f.write(f"  Bones: {self.model_info.bone_count}\n\n")
            
            f.write("Additional Fields:\n")
            f.write(f"  field_8C: {self.model_info.field_8C}\n")
            f.write(f"  field_90: {self.model_info.field_90}\n")
            f.write(f"  field_94: {self.model_info.field_94}\n")
            f.write(f"  field_98: {self.model_info.field_98}\n")
            f.write(f"  field_9C: {self.model_info.field_9C}\n")
            f.write(f"  field_A0: {self.model_info.field_A0}\n")
            f.write(f"  field_A4: {self.model_info.field_A4}\n")
            f.write(f"  field_A8: {self.model_info.field_A8}\n")
            f.write(f"  field_AC: {self.model_info.field_AC}\n")
            f.write(f"  field_B0: {self.model_info.field_B0}\n")
        
        print(f"   HSEM info (TXT): {txt_path}")

    def export_d3dr_info(self, out_dir: str, base_name: str):
        """تصدير معلومات D3DR (Render Mesh Header) كملف JSON ونصي"""
        if not self.render_mesh_data or not self.render_mesh_data.mesh_header:
            return
        
        header = self.render_mesh_data.mesh_header
        
        # 1. تحويل إلى قاموس
        header_dict = {
            "header_size": header.header_size,
            "dword0": header.dword0,
            "lightmap_count": header.lightmap_count,
            "face_count": header.face_count,
            "face_group_count": header.face_group_count,
            "bone_related_0": header.bone_related_0,
            "bone_related_1": header.bone_related_1,
            "vertex_count": header.vertex_count,
            "dword14": header.dword14,
            "dword18": header.dword18,
            "dword1c": header.dword1c,
            "dword20": header.dword20,
            "dword24": header.dword24,
            "dword28": header.dword28,
        }
        
        # 2. تصدير كـ JSON
        json_path = os.path.join(out_dir, f"{base_name}_d3dr.json")
        data = convert_to_json_serializable(header_dict)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   D3DR info (JSON): {json_path}")
        
        # 3. تصدير كملخص نصي
        txt_path = os.path.join(out_dir, f"{base_name}_d3dr.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# D3DR (Render Mesh Header) - IGI2\n")
            f.write(f"Header Size: {header.header_size} bytes\n")
            f.write(f"dword0: {header.dword0}\n")
            f.write(f"Lightmap Count: {header.lightmap_count}\n")
            f.write(f"Face Count: {header.face_count}\n")
            f.write(f"Material Groups: {header.face_group_count}\n")
            f.write(f"Bone Related 0: {header.bone_related_0}\n")
            f.write(f"Bone Related 1: {header.bone_related_1}\n")
            f.write(f"Vertex Count: {header.vertex_count}\n\n")
            
            f.write("Additional DWORDs:\n")
            f.write(f"  dword14: {header.dword14}\n")
            f.write(f"  dword18: {header.dword18}\n")
            f.write(f"  dword1c: {header.dword1c}\n")
            f.write(f"  dword20: {header.dword20}\n")
            f.write(f"  dword24: {header.dword24}\n")
            f.write(f"  dword28: {header.dword28}\n")
        
        print(f"   D3DR info (TXT): {txt_path}")

    # ========== دوال MANB و REIH الجديدة لـ IGI2 ==========
    def export_manb_detailed(self, out_dir: str, base_name: str):
        """تصدير أسماء العظام (MANB) بشكل تفصيلي"""
        if not self.bones:
            return
        
        # 1. JSON مع معلومات إضافية
        bone_names = [bone.name for bone in self.bones]
        
        # إحصائيات
        name_lengths = [len(name) for name in bone_names]
        stats = {
            "total_bones": len(bone_names),
            "max_name_length": max(name_lengths),
            "min_name_length": min(name_lengths),
            "avg_name_length": sum(name_lengths) / len(name_lengths) if name_lengths else 0,
            "unique_names": len(set(bone_names))
        }
        
        json_path = os.path.join(out_dir, f"{base_name}_manb_detailed.json")
        data = convert_to_json_serializable({
            "statistics": stats,
            "bone_names": [{"index": i, "name": name} for i, name in enumerate(bone_names)]
        })
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   MANB detailed (JSON): {json_path}")
        
        # 2. ملف نصي منسق
        txt_path = os.path.join(out_dir, f"{base_name}_manb.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# MANB (Bone Names)\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Total Bones: {len(bone_names)}\n")
            f.write(f"Statistics:\n")
            f.write(f"  Max name length: {stats['max_name_length']}\n")
            f.write(f"  Min name length: {stats['min_name_length']}\n")
            f.write(f"  Avg name length: {stats['avg_name_length']:.2f}\n")
            f.write(f"  Unique names: {stats['unique_names']}\n\n")
            f.write("Bone Names:\n")
            f.write("-" * 40 + "\n")
            
            for i, name in enumerate(bone_names):
                f.write(f"Bone {i:3d}: {name}\n")
        
        print(f"   MANB (TXT): {txt_path}")
        
        # 3. CSV
        csv_path = os.path.join(out_dir, f"{base_name}_manb.csv")
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write("index,name\n")
            for i, name in enumerate(bone_names):
                f.write(f"{i},{name}\n")
        print(f"   MANB (CSV): {csv_path}")

    def export_reih_detailed(self, out_dir: str, base_name: str):
        """تصدير معلومات هيكل العظام (REIH) بشكل تفصيلي"""
        if not self.bones:
            return
        
        # بناء بيانات الشجرة
        bone_data = []
        for i, bone in enumerate(self.bones):
            # البحث عن الأبناء
            children = [j for j, b in enumerate(self.bones) if b.parent_id == i]
            
            bone_data.append({
                "index": i,
                "name": bone.name,
                "parent_id": bone.parent_id,
                "position": [bone.pos.x, bone.pos.y, bone.pos.z],
                "children": children,
                "child_count": len(children)
            })
        
        # 1. تصدير كـ JSON (هيكل كامل)
        json_path = os.path.join(out_dir, f"{base_name}_reih_detailed.json")
        data = convert_to_json_serializable({
            "bone_count": len(bone_data),
            "bones": bone_data
        })
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   REIH detailed (JSON): {json_path}")
        
        # 2. تصدير كملخص نصي (شجري)
        txt_path = os.path.join(out_dir, f"{base_name}_reih_tree.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# REIH (Bone Hierarchy) - Tree Structure\n")
            f.write(f"Total Bones: {len(bone_data)}\n\n")
            
            def print_tree(bone_idx, level=0, prefix=""):
                bone = bone_data[bone_idx]
                indent = "  " * level
                marker = "├─ " if level > 0 else "└─ "
                f.write(f"{indent}{marker}{bone['name']} [ID:{bone_idx}, Parent:{bone['parent_id']}]\n")
                f.write(f"{indent}   pos: ({bone['position'][0]:.2f}, {bone['position'][1]:.2f}, {bone['position'][2]:.2f})\n")
                
                for i, child in enumerate(bone['children']):
                    is_last = (i == len(bone['children']) - 1)
                    child_prefix = prefix + ("    " if is_last else "│   ")
                    print_tree(child, level + 1, child_prefix)
            
            # اطبع كل العظام الجذرية
            root_bones = [i for i, b in enumerate(self.bones) if b.parent_id == -1]
            for i, root in enumerate(root_bones):
                print_tree(root)
                if i < len(root_bones) - 1:
                    f.write("\n")
        
        print(f"   REIH tree (TXT): {txt_path}")
        
        # 3. تصدير كـ CSV (جدول العلاقات)
        csv_path = os.path.join(out_dir, f"{base_name}_reih.csv")
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write("index,name,parent_id,pos_x,pos_y,pos_z,child_count\n")
            for i, bone in enumerate(bone_data):
                f.write(f"{i},{bone['name']},{bone['parent_id']},{bone['position'][0]:.6f},{bone['position'][1]:.6f},{bone['position'][2]:.6f},{bone['child_count']}\n")
        print(f"   REIH (CSV): {csv_path}")

    # ========== دالة MRPH الجديدة لـ IGI2 ==========
    def export_mrph_info(self, out_dir: str, base_name: str):
        """تصدير رؤوس التشكل (MRPH) لـ IGI2 كملف JSON ونصي (عرض كامل)"""
        if not self.morph_channels:
            return
        
        # 1. تحويل إلى قاموس
        morph_data = {}
        total_vertices = 0
        for channel, vertices in self.morph_channels.items():
            channel_data = []
            for v in vertices:
                # ✅ تطبيق swizzle على مواقع رؤوس التشكل هنا
                px, py, pz = self.debug_params.swizzle(v["pos"][0], v["pos"][1], v["pos"][2], self.debug_params.v_scale)
                channel_data.append({
                    "index": int(v["index"].item()) if hasattr(v["index"], 'item') else int(v["index"]),
                    "position": [px, py, pz]
                })
            morph_data[f"channel_{channel}"] = channel_data
            total_vertices += len(vertices)
        
        # 2. تصدير كـ JSON
        json_path = os.path.join(out_dir, f"{base_name}_mrph.json")
        data = convert_to_json_serializable(morph_data)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   Morph vertices (JSON): {json_path}")
        
        # 3. تصدير كملخص نصي (بدون اختصار - عرض كامل)
        txt_path = os.path.join(out_dir, f"{base_name}_mrph.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# MRPH (Morph Vertices) - IGI2\n")
            f.write(f"Total Channels: {len(self.morph_channels)}\n")
            f.write(f"Total Vertices: {total_vertices}\n\n")
            
            for channel, vertices in self.morph_channels.items():
                f.write(f"Channel {channel}: {len(vertices)} vertices\n")
                f.write("-" * 50 + "\n")
                
                # عرض جميع الرؤوس بدون اختصار - مع استخراج القيمة بشكل صحيح
                for i, v in enumerate(vertices):
                    # استخراج index بشكل صحيح
                    idx_val = v['index']
                    if hasattr(idx_val, 'item'):
                        idx = idx_val.item()
                    elif isinstance(idx_val, np.ndarray):
                        idx = idx_val[0]
                    else:
                        idx = int(idx_val)
                    
                    # استخراج pos بشكل صحيح وتطبيق swizzle
                    pos = v['pos']
                    if hasattr(pos, '__getitem__'):
                        px = float(pos[0]) if hasattr(pos[0], 'item') else float(pos[0])
                        py = float(pos[1]) if hasattr(pos[1], 'item') else float(pos[1])
                        pz = float(pos[2]) if hasattr(pos[2], 'item') else float(pos[2])
                    else:
                        px, py, pz = 0.0, 0.0, 0.0
                    
                    px, py, pz = self.debug_params.swizzle(px, py, pz, self.debug_params.v_scale)
                    
                    f.write(f"  v{i:4d}: idx={idx:4d}, pos=({px:8.2f}, {py:8.2f}, {pz:8.2f})\n")
                
                f.write("\n")
        
        print(f"   Morph vertices (TXT): {txt_path}")

    # ========== دالة TXAN الجديدة لـ IGI2 ==========
    def export_txan_info(self, out_dir: str, base_name: str):
        """تصدير بيانات الحركة (TXAN) لـ IGI2 كملف JSON ونصي (عرض كامل)"""
        if not self.txan_data:
            return
        
        # 1. تحويل إلى قائمة
        txan_list = []
        for i, txan in enumerate(self.txan_data):
            txan_list.append({
                "index": i,
                "fields": txan.unknown_fields
            })
        
        # 2. تصدير كـ JSON
        json_path = os.path.join(out_dir, f"{base_name}_txan.json")
        data = convert_to_json_serializable(txan_list)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   TXAN animation data (JSON): {json_path}")
        
        # 3. تصدير كملخص نصي (بدون اختصار)
        txt_path = os.path.join(out_dir, f"{base_name}_txan.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# TXAN (Animation Data) - IGI2\n")
            f.write(f"Total TXAN chunks: {len(self.txan_data)}\n\n")
            
            # عرض جميع الحقول بدون اختصار
            for i, txan in enumerate(self.txan_data):
                f.write(f"TXAN {i}:\n")
                f.write(f"  Fields (28 uint32):\n")
                for j, val in enumerate(txan.unknown_fields):
                    f.write(f"    [{j:2d}]: {val} (0x{val:08X})\n")
                f.write("\n")
        
        print(f"   TXAN animation data (TXT): {txt_path}")
        
        # 4. تصدير كـ CSV
        csv_path = os.path.join(out_dir, f"{base_name}_txan.csv")
        with open(csv_path, 'w', encoding='utf-8') as f:
            header = ["chunk"] + [f"field_{i:02d}" for i in range(28)]
            f.write(",".join(header) + "\n")
            for i, txan in enumerate(self.txan_data):
                row = [str(i)] + [str(val) for val in txan.unknown_fields]
                f.write(",".join(row) + "\n")
        print(f"   TXAN animation data (CSV): {csv_path}")

    # ========== دوال HSMC الجديدة لـ IGI2 ==========
    def export_hsmc_info(self, out_dir: str, base_name: str):
        """تصدير معلومات HSMC (Collision Mesh Header) لـ IGI2 كملف JSON ونصي"""
        if not self.collision_mesh_data:
            return
        
        header = self.collision_mesh_data.mesh_header
        
        # 1. تحويل إلى قاموس
        hsmc_dict = {
            "mesh0": {
                "face_count": header.mesh0.face_count,
                "vertex_count": header.mesh0.vertex_count,
                "material_count": header.mesh0.material_count,
                "sphere_count": header.mesh0.sphere_count,
                "face_ptr": header.mesh0.face_ptr,
                "vertex_ptr": header.mesh0.vertex_ptr,
                "materials_ptr": header.mesh0.materials_ptr,
                "sphere_ptr": header.mesh0.sphere_ptr,
            },
            "mesh1": {
                "face_count": header.mesh1.face_count,
                "vertex_count": header.mesh1.vertex_count,
                "material_count": header.mesh1.material_count,
                "sphere_count": header.mesh1.sphere_count,
                "face_ptr": header.mesh1.face_ptr,
                "vertex_ptr": header.mesh1.vertex_ptr,
                "materials_ptr": header.mesh1.materials_ptr,
                "sphere_ptr": header.mesh1.sphere_ptr,
            }
        }
        
        # 2. تصدير كـ JSON
        json_path = os.path.join(out_dir, f"{base_name}_hsmc.json")
        data = convert_to_json_serializable(hsmc_dict)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   HSMC info (JSON): {json_path}")
        
        # 3. تصدير كملخص نصي
        txt_path = os.path.join(out_dir, f"{base_name}_hsmc.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# HSMC (Collision Mesh Header) - IGI2\n")
            f.write("=" * 60 + "\n\n")
            
            f.write("Mesh 0 (Primary Collision Mesh):\n")
            f.write("-" * 40 + "\n")
            f.write(f"  Face Count      : {header.mesh0.face_count}\n")
            f.write(f"  Vertex Count    : {header.mesh0.vertex_count}\n")
            f.write(f"  Material Count  : {header.mesh0.material_count}\n")
            f.write(f"  Sphere Count    : {header.mesh0.sphere_count}\n")
            f.write(f"  Face Pointer    : {header.mesh0.face_ptr} (0x{header.mesh0.face_ptr:08X})\n")
            f.write(f"  Vertex Pointer  : {header.mesh0.vertex_ptr} (0x{header.mesh0.vertex_ptr:08X})\n")
            f.write(f"  Materials Pointer: {header.mesh0.materials_ptr} (0x{header.mesh0.materials_ptr:08X})\n")
            f.write(f"  Sphere Pointer  : {header.mesh0.sphere_ptr} (0x{header.mesh0.sphere_ptr:08X})\n\n")
            
            f.write("Mesh 1 (Secondary Collision Mesh):\n")
            f.write("-" * 40 + "\n")
            f.write(f"  Face Count      : {header.mesh1.face_count}\n")
            f.write(f"  Vertex Count    : {header.mesh1.vertex_count}\n")
            f.write(f"  Material Count  : {header.mesh1.material_count}\n")
            f.write(f"  Sphere Count    : {header.mesh1.sphere_count}\n")
            f.write(f"  Face Pointer    : {header.mesh1.face_ptr} (0x{header.mesh1.face_ptr:08X})\n")
            f.write(f"  Vertex Pointer  : {header.mesh1.vertex_ptr} (0x{header.mesh1.vertex_ptr:08X})\n")
            f.write(f"  Materials Pointer: {header.mesh1.materials_ptr} (0x{header.mesh1.materials_ptr:08X})\n")
            f.write(f"  Sphere Pointer  : {header.mesh1.sphere_ptr} (0x{header.mesh1.sphere_ptr:08X})\n")
        
        print(f"   HSMC info (TXT): {txt_path}")
        
        # 4. تصدير كـ CSV (لمقارنة العدادات)
        csv_path = os.path.join(out_dir, f"{base_name}_hsmc.csv")
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write("mesh,face_count,vertex_count,material_count,sphere_count,face_ptr,vertex_ptr,materials_ptr,sphere_ptr\n")
            f.write(f"0,{header.mesh0.face_count},{header.mesh0.vertex_count},{header.mesh0.material_count},{header.mesh0.sphere_count},{header.mesh0.face_ptr},{header.mesh0.vertex_ptr},{header.mesh0.materials_ptr},{header.mesh0.sphere_ptr}\n")
            f.write(f"1,{header.mesh1.face_count},{header.mesh1.vertex_count},{header.mesh1.material_count},{header.mesh1.sphere_count},{header.mesh1.face_ptr},{header.mesh1.vertex_ptr},{header.mesh1.materials_ptr},{header.mesh1.sphere_ptr}\n")
        print(f"   HSMC info (CSV): {csv_path}")

    # ========== دوال قطع التصادم الجديدة لـ IGI2 ==========
    def export_xtvc_info(self, out_dir: str, base_name: str, mesh_index: int = 0):
        """تصدير رؤوس التصادم (XTVC) لـ IGI2 كملف JSON ونصي (عرض كامل)"""
        cmesh = self.collision_mesh_data if mesh_index == 0 else self.collision_mesh_data2
        if not cmesh or cmesh.vertices is None:
            return
        
        vertices = cmesh.vertices
        mesh_type = "type0" if mesh_index == 0 else "type1"
        
        # 1. تحويل إلى قائمة قواميس مع تطبيق swizzle
        verts_list = []
        for i, v in enumerate(vertices):
            px, py, pz = self.debug_params.swizzle(v["pos"][0], v["pos"][1], v["pos"][2], self.debug_params.v_scale)
            verts_list.append({
                "index": i,
                "position": [px, py, pz],
                "uv": [float(v["uv"][0]), float(v["uv"][1])] if "uv" in v.dtype.names else [0, 0]
            })
        
        # 2. تصدير كـ JSON
        suffix = f"_xtvc_{mesh_type}"
        json_path = os.path.join(out_dir, f"{base_name}{suffix}.json")
        data = convert_to_json_serializable({
            "mesh_type": mesh_type,
            "vertex_count": len(verts_list),
            "vertices": verts_list
        })
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   XTVC {mesh_type} (JSON): {json_path}")
        
        # 3. تصدير كملخص نصي (بدون اختصار)
        txt_path = os.path.join(out_dir, f"{base_name}{suffix}.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(f"# XTVC (Collision Mesh Vertices) - IGI2 - {mesh_type}\n")
            f.write(f"Total Vertices: {len(verts_list)}\n\n")
            f.write("Format: index: pos=(x,y,z), uv=(u,v)\n\n")
            
            # عرض جميع الرؤوس بدون اختصار
            for i, v in enumerate(verts_list):
                f.write(f"Vertex {i:6d}: pos=({v['position'][0]:8.2f}, {v['position'][1]:8.2f}, {v['position'][2]:8.2f}), "
                       f"uv=({v['uv'][0]:.4f}, {v['uv'][1]:.4f})\n")
        
        print(f"   XTVC {mesh_type} (TXT): {txt_path}")
        
        # 4. تصدير كـ CSV
        csv_path = os.path.join(out_dir, f"{base_name}{suffix}.csv")
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write("index,pos_x,pos_y,pos_z,uv_u,uv_v\n")
            for i, v in enumerate(verts_list):
                f.write(f"{i},{v['position'][0]:.6f},{v['position'][1]:.6f},{v['position'][2]:.6f},"
                       f"{v['uv'][0]:.6f},{v['uv'][1]:.6f}\n")
        print(f"   XTVC {mesh_type} (CSV): {csv_path}")

    def export_ecfc_info(self, out_dir: str, base_name: str, mesh_index: int = 0):
        """تصدير وجوه التصادم (ECFC) لـ IGI2 كملف JSON ونصي (عرض كامل)"""
        cmesh = self.collision_mesh_data if mesh_index == 0 else self.collision_mesh_data2
        if not cmesh or cmesh.faces is None:
            return
        
        faces = cmesh.faces
        mesh_type = "type0" if mesh_index == 0 else "type1"
        
        # 1. تحويل إلى قائمة قواميس
        faces_list = []
        for i, f in enumerate(faces):
            # استخراج القيم بشكل صحيح مع تجنب DeprecationWarning
            mat_id_val = f["mat_id"]
            mat_id = mat_id_val.item() if hasattr(mat_id_val, 'item') else mat_id_val
            
            lightmap_id_val = f["lightmap_id"]
            lightmap_id = lightmap_id_val.item() if hasattr(lightmap_id_val, 'item') else lightmap_id_val
            
            unknown_val = f["unknown"]
            unknown = unknown_val.item() if hasattr(unknown_val, 'item') else unknown_val
            
            faces_list.append({
                "index": i,
                "vertices": [int(f["face"][0]), int(f["face"][1]), int(f["face"][2])],
                "material_id": int(mat_id),
                "lightmap_id": int(lightmap_id),
                "unknown": int(unknown)
            })
        
        # 2. تصدير كـ JSON
        suffix = f"_ecfc_{mesh_type}"
        json_path = os.path.join(out_dir, f"{base_name}{suffix}.json")
        data = convert_to_json_serializable({
            "mesh_type": mesh_type,
            "face_count": len(faces_list),
            "faces": faces_list
        })
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   ECFC {mesh_type} (JSON): {json_path}")
        
        # 3. تصدير كملخص نصي (بدون اختصار)
        txt_path = os.path.join(out_dir, f"{base_name}{suffix}.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(f"# ECFC (Collision Mesh Faces) - IGI2 - {mesh_type}\n")
            f.write(f"Total Faces: {len(faces_list)}\n\n")
            f.write("Format: index: vertices=(a,b,c), mat_id, lightmap_id, unknown\n\n")
            
            # عرض جميع الوجوه بدون اختصار
            for i, face in enumerate(faces_list):
                f.write(f"Face {i:6d}: vertices=({face['vertices'][0]:6d}, {face['vertices'][1]:6d}, {face['vertices'][2]:6d}), "
                       f"mat_id={face['material_id']:4d}, lightmap_id={face['lightmap_id']:4d}, unknown={face['unknown']:4d}\n")
        
        print(f"   ECFC {mesh_type} (TXT): {txt_path}")
        
        # 4. تصدير كـ CSV
        csv_path = os.path.join(out_dir, f"{base_name}{suffix}.csv")
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write("index,vert_a,vert_b,vert_c,mat_id,lightmap_id,unknown\n")
            for i, face in enumerate(faces_list):
                f.write(f"{i},{face['vertices'][0]},{face['vertices'][1]},{face['vertices'][2]},"
                       f"{face['material_id']},{face['lightmap_id']},{face['unknown']}\n")
        print(f"   ECFC {mesh_type} (CSV): {csv_path}")

    def export_tamc_info(self, out_dir: str, base_name: str, mesh_index: int = 0, use_mesh1_materials: bool = False):
        """تصدير مواد التصادم (TAMC) لـ IGI2 كملف JSON ونصي"""
        
        # اختيار المواد حسب المصدر
        if use_mesh1_materials and hasattr(self, 'collision_materials_mesh1'):
            materials = self.collision_materials_mesh1
        else:
            materials = self.collision_materials
        
        if not materials:
            return
        
        mesh_type = "type0" if mesh_index == 0 else "type1"
        
        # تحويل إلى قائمة قواميس
        mats_list = []
        for i, mat in enumerate(materials):
            mats_list.append({
                "index": i,
                "opacity": mat.opacity,
                "portal_id": mat.portal_id,
                "texture_id": mat.texture_id,
                "unknown1": mat.unknown1,
                "game_material_id": mat.game_material_id,
                "unknown2": mat.unknown2
            })
        
        # تصدير كـ JSON
        suffix = f"_tamc_{mesh_type}"
        json_path = os.path.join(out_dir, f"{base_name}{suffix}.json")
        data = convert_to_json_serializable({
            "mesh_type": mesh_type,
            "material_count": len(mats_list),
            "materials": mats_list
        })
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   TAMC {mesh_type} (JSON): {json_path}")
        
        # تصدير كملخص نصي
        txt_path = os.path.join(out_dir, f"{base_name}{suffix}.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(f"# TAMC (Collision Mesh Materials) - IGI2 - {mesh_type}\n")
            f.write(f"Total Materials: {len(mats_list)}\n\n")
            
            for i, mat in enumerate(mats_list):
                f.write(f"Material {i:3d}: opacity={mat['opacity']:.6f}, portal_id={mat['portal_id']:4d} (0x{mat['portal_id']:04X}), "
                       f"texture_id={mat['texture_id']:4d}, unknown1={mat['unknown1']:8d} (0x{mat['unknown1']:08X}), "
                       f"game_material_id={mat['game_material_id']:4d}, unknown2={mat['unknown2']:4d}\n")
        
        print(f"   TAMC {mesh_type} (TXT): {txt_path}")
        
        # تصدير كـ CSV
        csv_path = os.path.join(out_dir, f"{base_name}{suffix}.csv")
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write("index,opacity,portal_id,texture_id,unknown1,game_material_id,unknown2\n")
            for i, mat in enumerate(mats_list):
                f.write(f"{i},{mat['opacity']:.6f},{mat['portal_id']},{mat['texture_id']},"
                       f"{mat['unknown1']},{mat['game_material_id']},{mat['unknown2']}\n")
        print(f"   TAMC {mesh_type} (CSV): {csv_path}")

    def export_hpsc_info(self, out_dir: str, base_name: str, mesh_index: int = 0):
        """تصدير كرات التصادم (HPSC) لـ IGI2 كملف JSON ونصي (عرض كامل)"""
        cmesh = self.collision_mesh_data if mesh_index == 0 else self.collision_mesh_data2
        if not cmesh or cmesh.spheres is None:
            return
        
        spheres = cmesh.spheres
        mesh_type = "type0" if mesh_index == 0 else "type1"
        
        # 1. تحويل إلى قائمة قواميس مع تطبيق swizzle
        spheres_list = []
        for i, s in enumerate(spheres):
            cx, cy, cz = self.debug_params.swizzle(s["pos"][0], s["pos"][1], s["pos"][2], self.debug_params.v_scale)
            spheres_list.append({
                "index": i,
                "center": [cx, cy, cz],
                "radius": float(s["radius"][0]),
                "type": int(s["type"][0]),
                "count": int(s["count"][0]),
                "vertex_a": int(s["vertex_a"][0]),
                "vertex_b": int(s["vertex_b"][0])
            })
        
        # 2. تصدير كـ JSON
        suffix = f"_hpsc_{mesh_type}"
        json_path = os.path.join(out_dir, f"{base_name}{suffix}.json")
        data = convert_to_json_serializable({
            "mesh_type": mesh_type,
            "sphere_count": len(spheres_list),
            "spheres": spheres_list
        })
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   HPSC {mesh_type} (JSON): {json_path}")
        
        # 3. تصدير كملخص نصي (بدون اختصار)
        txt_path = os.path.join(out_dir, f"{base_name}{suffix}.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(f"# HPSC (Collision Mesh Spheres) - IGI2 - {mesh_type}\n")
            f.write(f"Total Spheres: {len(spheres_list)}\n\n")
            f.write("Format: index: center=(x,y,z), radius, type, count, vertex_a, vertex_b\n\n")
            
            # عرض جميع الكرات بدون اختصار
            for i, s in enumerate(spheres_list):
                f.write(f"Sphere {i:6d}: center=({s['center'][0]:8.2f}, {s['center'][1]:8.2f}, {s['center'][2]:8.2f}), "
                       f"radius={s['radius']:8.2f}, type={s['type']:4d}, count={s['count']:4d}, "
                       f"vertex_a={s['vertex_a']:6d}, vertex_b={s['vertex_b']:6d}\n")
        
        print(f"   HPSC {mesh_type} (TXT): {txt_path}")
        
        # 4. تصدير كـ CSV
        csv_path = os.path.join(out_dir, f"{base_name}{suffix}.csv")
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write("index,center_x,center_y,center_z,radius,type,count,vertex_a,vertex_b\n")
            for i, s in enumerate(spheres_list):
                f.write(f"{i},{s['center'][0]:.6f},{s['center'][1]:.6f},{s['center'][2]:.6f},"
                       f"{s['radius']:.6f},{s['type']},{s['count']},{s['vertex_a']},{s['vertex_b']}\n")
        print(f"   HPSC {mesh_type} (CSV): {csv_path}")
        
        # 5. تصدير كـ OBJ (يبقى كما هو - نقاط)
        obj_path = os.path.join(out_dir, f"{base_name}{suffix}.obj")
        with open(obj_path, 'w', encoding='utf-8') as f:
            f.write(f"# HPSC Collision Spheres - {mesh_type}\n")
            f.write(f"# {len(spheres_list)} spheres\n\n")
            f.write(f"o {base_name}_hpsc_{mesh_type}\n")
            
            for i, s in enumerate(spheres_list):
                f.write(f"v {s['center'][0]:.6f} {s['center'][1]:.6f} {s['center'][2]:.6f}\n")
                f.write(f"# sphere {i}: radius={s['radius']:.2f}, type={s['type']}, count={s['count']}, "
                       f"vertices=({s['vertex_a']}, {s['vertex_b']})\n")
            
            if spheres_list:
                f.write("p 1\n")
        
        print(f"   HPSC {mesh_type} spheres as points (OBJ): {obj_path}")
    
    def export_all_collision_mesh_data(self, out_dir: str, base_name: str):
        """تصدير جميع قطع التصادم (HSMC, XTVC, ECFC, TAMC, HPSC) لكلا النوعين"""
        
        print(f"\n   📦 Exporting all collision mesh data...")
        
        # 1. HSMC (مشترك)
        self.export_hsmc_info(out_dir, base_name)
        
        # 2. بيانات النوع 0 (mesh0)
        if self.collision_mesh_data:
            self.export_xtvc_info(out_dir, base_name, 0)
            self.export_ecfc_info(out_dir, base_name, 0)
            self.export_hpsc_info(out_dir, base_name, 0)
            # TAMC للنوع 0
            if self.collision_materials:
                self.export_tamc_info(out_dir, base_name, 0)
        
        # 3. بيانات النوع 1 (mesh1) - إذا وجدت
        if hasattr(self, 'collision_mesh_data2') and self.collision_mesh_data2:
            print(f"\n   📦 Exporting second collision mesh (type1)...")
            self.export_xtvc_info(out_dir, base_name, 1)
            self.export_ecfc_info(out_dir, base_name, 1)
            self.export_hpsc_info(out_dir, base_name, 1)
            # TAMC للنوع 1 (مواد منفصلة)
            if hasattr(self, 'collision_materials_mesh1') and self.collision_materials_mesh1:
                self.export_tamc_info(out_dir, base_name, 1, use_mesh1_materials=True)
            elif self.collision_materials:
                # إذا لم تكن هناك مواد منفصلة، استخدم نفس المواد
                self.export_tamc_info(out_dir, base_name, 1)
        
        print(f"   ✅ Collision mesh data exported successfully")

    # ========== دوال بيانات الظل الجديدة لـ IGI2 ==========
    def export_sems_info(self, out_dir: str, base_name: str):
        """تصدير معلومات رأس نموذج الظل (SEMS)"""
        if not self.shadow_mesh_data:
            return
        
        header = self.shadow_mesh_data.mesh_header
        
        # 1. JSON
        sems_dict = {
            "face_offset": header.face_offset,
            "vertex_offset": header.vertex_offset,
            "edge_offset": header.edge_offset,
            "face_count": header.face_count,
            "vertex_count": header.vertex_count,
            "edge_count": header.edge_count,
            "bone_index": header.bone_index
        }
        
        json_path = os.path.join(out_dir, f"{base_name}_sems.json")
        data = convert_to_json_serializable(sems_dict)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   SEMS (JSON): {json_path}")
        
        # 2. ملف نصي
        txt_path = os.path.join(out_dir, f"{base_name}_sems.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# SEMS (Shadow Model Header)\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Face Offset    : {header.face_offset}\n")
            f.write(f"Vertex Offset  : {header.vertex_offset}\n")
            f.write(f"Edge Offset    : {header.edge_offset}\n")
            f.write(f"Face Count     : {header.face_count}\n")
            f.write(f"Vertex Count   : {header.vertex_count}\n")
            f.write(f"Edge Count     : {header.edge_count}\n")
            f.write(f"Bone Index     : {header.bone_index}\n")
        
        print(f"   SEMS (TXT): {txt_path}")
        
        # 3. CSV
        csv_path = os.path.join(out_dir, f"{base_name}_sems.csv")
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write("face_offset,vertex_offset,edge_offset,face_count,vertex_count,edge_count,bone_index\n")
            f.write(f"{header.face_offset},{header.vertex_offset},{header.edge_offset},{header.face_count},{header.vertex_count},{header.edge_count},{header.bone_index}\n")
        print(f"   SEMS (CSV): {csv_path}")

    def export_xtvs_info(self, out_dir: str, base_name: str):
        """تصدير رؤوس شبكة الظل (XTVS) - عرض كامل"""
        if not self.shadow_mesh_data or self.shadow_mesh_data.vertices is None:
            return
        
        vertices = self.shadow_mesh_data.vertices
        
        # 1. JSON مع تطبيق swizzle
        verts_list = []
        for i, v in enumerate(vertices):
            if len(v) >= 3:
                px, py, pz = self.debug_params.swizzle(v[0], v[1], v[2], self.debug_params.v_scale)
                verts_list.append({
                    "index": i,
                    "position": [px, py, pz]
                })
        
        json_path = os.path.join(out_dir, f"{base_name}_xtvs.json")
        data = convert_to_json_serializable({
            "vertex_count": len(verts_list),
            "vertices": verts_list
        })
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   XTVS (JSON): {json_path}")
        
        # 2. ملف نصي (بدون اختصار)
        txt_path = os.path.join(out_dir, f"{base_name}_xtvs.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# XTVS (Shadow Mesh Vertices)\n")
            f.write(f"Total Vertices: {len(verts_list)}\n\n")
            f.write("Format: index: (x, y, z)\n\n")
            
            # عرض جميع الرؤوس بدون اختصار
            for i, v in enumerate(verts_list):
                f.write(f"Vertex {i:6d}: ({v['position'][0]:8.2f}, {v['position'][1]:8.2f}, {v['position'][2]:8.2f})\n")
        
        print(f"   XTVS (TXT): {txt_path}")
        
        # 3. CSV
        csv_path = os.path.join(out_dir, f"{base_name}_xtvs.csv")
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write("index,x,y,z\n")
            for i, v in enumerate(verts_list):
                f.write(f"{i},{v['position'][0]:.6f},{v['position'][1]:.6f},{v['position'][2]:.6f}\n")
        print(f"   XTVS (CSV): {csv_path}")
        
        # 4. OBJ
        obj_path = os.path.join(out_dir, f"{base_name}_xtvs.obj")
        with open(obj_path, 'w', encoding='utf-8') as f:
            f.write(f"# XTVS Shadow Vertices\n")
            f.write(f"# {len(verts_list)} vertices\n\n")
            f.write(f"o {base_name}_shadow_verts\n")
            
            for v in verts_list:
                f.write(f"v {v['position'][0]:.6f} {v['position'][1]:.6f} {v['position'][2]:.6f}\n")
            
            if verts_list:
                f.write("p 1\n")
        
        print(f"   XTVS as points (OBJ): {obj_path}")

    def export_cafs_info(self, out_dir: str, base_name: str):
        """تصدير وجوه شبكة الظل (CAFS) - عرض كامل"""
        if not self.shadow_mesh_data or self.shadow_mesh_data.faces is None:
            return
        
        faces = self.shadow_mesh_data.faces
        
        # 1. JSON
        faces_list = []
        for i, f in enumerate(faces):
            if "face" in f.dtype.names:
                faces_list.append({
                    "index": i,
                    "vertices": [int(f["face"][0]), int(f["face"][1]), int(f["face"][2])],
                    "edge_flags": int(f["edge_flags"]),
                    "normal": [float(f["normal"][0]), float(f["normal"][1]), float(f["normal"][2])]
                })
            else:
                faces_list.append({
                    "index": i,
                    "vertices": [int(f[0]), int(f[1]), int(f[2])]
                })
        
        json_path = os.path.join(out_dir, f"{base_name}_cafs.json")
        data = convert_to_json_serializable({
            "face_count": len(faces_list),
            "faces": faces_list
        })
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   CAFS (JSON): {json_path}")
        
        # 2. ملف نصي (بدون اختصار)
        txt_path = os.path.join(out_dir, f"{base_name}_cafs.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# CAFS (Shadow Mesh Faces)\n")
            f.write(f"Total Faces: {len(faces_list)}\n\n")
            
            # عرض جميع الوجوه بدون اختصار
            for i, face in enumerate(faces_list):
                if "normal" in face:
                    f.write(f"Face {i:6d}: vertices=({face['vertices'][0]:6d}, {face['vertices'][1]:6d}, {face['vertices'][2]:6d}), "
                           f"edge_flags={face['edge_flags']:4d}, normal=({face['normal'][0]:8.2f}, {face['normal'][1]:8.2f}, {face['normal'][2]:8.2f})\n")
                else:
                    f.write(f"Face {i:6d}: vertices=({face['vertices'][0]:6d}, {face['vertices'][1]:6d}, {face['vertices'][2]:6d})\n")
        
        print(f"   CAFS (TXT): {txt_path}")
        
        # 3. CSV
        csv_path = os.path.join(out_dir, f"{base_name}_cafs.csv")
        with open(csv_path, 'w', encoding='utf-8') as f:
            if faces_list and "normal" in faces_list[0]:
                f.write("index,a,b,c,edge_flags,nx,ny,nz\n")
                for i, face in enumerate(faces_list):
                    f.write(f"{i},{face['vertices'][0]},{face['vertices'][1]},{face['vertices'][2]},"
                           f"{face['edge_flags']},{face['normal'][0]:.6f},{face['normal'][1]:.6f},{face['normal'][2]:.6f}\n")
            else:
                f.write("index,a,b,c\n")
                for i, face in enumerate(faces_list):
                    f.write(f"{i},{face['vertices'][0]},{face['vertices'][1]},{face['vertices'][2]}\n")
        print(f"   CAFS (CSV): {csv_path}")

    def export_egde_info(self, out_dir: str, base_name: str):
        """تصدير حواف شبكة الظل (EGDE) - عرض كامل"""
        if not self.shadow_mesh_data or self.shadow_mesh_data.edges is None:
            return
        
        edges = self.shadow_mesh_data.edges
        
        # 1. JSON
        edges_list = []
        for i, e in enumerate(edges):
            edges_list.append({
                "index": i,
                "a": int(e[0]),
                "b": int(e[1])
            })
        
        json_path = os.path.join(out_dir, f"{base_name}_egde.json")
        data = convert_to_json_serializable({
            "edge_count": len(edges_list),
            "edges": edges_list
        })
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   EGDE (JSON): {json_path}")
        
        # 2. ملف نصي (بدون اختصار)
        txt_path = os.path.join(out_dir, f"{base_name}_egde.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# EGDE (Shadow Mesh Edges)\n")
            f.write(f"Total Edges: {len(edges_list)}\n\n")
            f.write("Format: index: a - b\n\n")
            
            # عرض جميع الحواف بدون اختصار
            for i, edge in enumerate(edges_list):
                f.write(f"Edge {i:6d}: {edge['a']:6d} - {edge['b']:6d}\n")
        
        print(f"   EGDE (TXT): {txt_path}")
        
        # 3. CSV
        csv_path = os.path.join(out_dir, f"{base_name}_egde.csv")
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write("index,a,b\n")
            for i, edge in enumerate(edges_list):
                f.write(f"{i},{edge['a']},{edge['b']}\n")
        print(f"   EGDE (CSV): {csv_path}")
    
    def export_all_shadow_data(self, out_dir: str, base_name: str):
        """تصدير جميع بيانات الظل (SEMS, XTVS, CAFS, EGDE)"""
        
        print(f"\n   🌑 Exporting all shadow mesh data...")
        
        if not self.shadow_mesh_data:
            print(f"   No shadow mesh data found")
            return
        
        self.export_sems_info(out_dir, base_name)
        self.export_xtvs_info(out_dir, base_name)
        self.export_cafs_info(out_dir, base_name)
        self.export_egde_info(out_dir, base_name)
        
        print(f"   ✅ Shadow mesh data exported successfully")

    # ========== دوال إنشاء وتطبيق أطلس القوام لـ IGI2 ==========
    def create_texture_atlas(self, out_dir: str, base_name: str) -> TextureAtlas:
        """
        إنشاء أطلس قوام لمواد النموذج (IGI2)
        """
        # ✅ التعديل: التحقق من إعداد الإيقاف المؤقت
        if not ENABLE_TEXTURE_ATLAS:
            print(f"   ℹ️ ميزة دمج القوام موقفة مؤقتاً (ENABLE_TEXTURE_ATLAS = False)")
            return None
            
        if not self.render_mesh_data or not self.render_mesh_data.primitives:
            return None
        
        # تحديد مجلد القوام
        texture_dirs = [
            os.path.join(out_dir, "textures"),
            out_dir,
            os.path.join(os.path.dirname(out_dir), "textures")
        ]
        
        atlas = None
        for tex_dir in texture_dirs:
            if os.path.exists(tex_dir):
                atlas = TextureAtlas(tex_dir)
                break
        
        if atlas is None:
            atlas = TextureAtlas(out_dir)
        
        # جمع أسماء ملفات القوام من المواد مع الحفاظ على الترتيب
        texture_names = []
        for i, prim in enumerate(self.render_mesh_data.primitives):
            tex_index = prim.diffuse_texture if hasattr(prim, 'diffuse_texture') else 0
            tex_name = get_texture_name(tex_index, base_name, i, self.texture_references)
            if tex_name not in texture_names:
                texture_names.append(tex_name)
            
            # bump و reflection يمكن إضافتها أيضاً
            if hasattr(prim, 'bump_texture') and prim.bump_texture >= 0:
                bump_name = get_texture_name(prim.bump_texture, base_name, i, self.texture_references)
                if bump_name not in texture_names:
                    texture_names.append(bump_name)
            
            if hasattr(prim, 'reflection_texture') and prim.reflection_texture >= 0:
                refl_name = get_texture_name(prim.reflection_texture, base_name, i, self.texture_references)
                if refl_name not in texture_names:
                    texture_names.append(refl_name)
        
        print(f"   Texture names in order: {texture_names}")
        
        # إضافة القوام إلى الأطلس
        for tex_name in texture_names:
            atlas.add_texture(tex_name)
        
        # دمج القوام إذا كان هناك أكثر من واحد
        if atlas.has_multiple_textures():
            if atlas.pack_textures():
                atlas_path = os.path.join(out_dir, f"{base_name}_atlas.png")
                atlas.save_atlas(atlas_path, 'PNG')
                print(f"   Created texture atlas: {atlas_path} ({atlas.atlas_size[0]}x{atlas.atlas_size[1]}) with {len(atlas.texture_paths)} textures")
                print(f"   Atlas positions: {atlas.positions}")
                return atlas
        
        return None

    def apply_texture_atlas_igi2(self, atlas: TextureAtlas, vertices: np.ndarray, primitives: list, base_name: str) -> np.ndarray:
        """
        تطبيق تحويل UV على الرؤوس باستخدام الأطلس (IGI2)
        """
        # ✅ التعديل: التحقق من إعداد الإيقاف المؤقت
        if not ENABLE_TEXTURE_ATLAS:
            print(f"   ℹ️ تخطي تطبيق الأطلس (الميزة موقفة)")
            return vertices
            
        print(f"   DEBUG: Entering apply_texture_atlas_igi2")
        print(f"   DEBUG: atlas.has_multiple_textures() = {atlas.has_multiple_textures()}")
        print(f"   DEBUG: vertices.shape = {vertices.shape}")
        print(f"   DEBUG: dtype names = {vertices.dtype.names}")
        
        if not atlas or not atlas.has_multiple_textures():
            print(f"   DEBUG: Early return - no atlas or single texture")
            return vertices
        
        # إنشاء نسخة معدلة من الرؤوس
        new_vertices = vertices.copy()
        
        # أولاً: إنشاء تعيين بين المواد وأسماء القوام
        material_texture_map = []
        for i, prim in enumerate(primitives):
            tex_index = prim.diffuse_texture if hasattr(prim, 'diffuse_texture') else 0
            tex_name = get_texture_name(tex_index, base_name, i, self.texture_references)
            material_texture_map.append(tex_name)
        
        print(f"   Material to texture mapping: {material_texture_map}")
        print(f"   Atlas textures: {atlas.texture_names}")
        print(f"   Atlas indices: {atlas.texture_indices}")

        # تطبيق التحويل لكل مادة
        for i, prim in enumerate(primitives):
            print(f"   DEBUG: Processing material {i}")
            
            if i >= len(material_texture_map):
                print(f"   DEBUG: Skipping - i out of range")
                continue
            
            tex_name = material_texture_map[i]
            print(f"   DEBUG: tex_name = {tex_name}")
            
            # التحقق من وجود القوام في الأطلس
            if tex_name not in atlas.texture_indices:
                print(f"   Warning: Texture '{tex_name}' not found in atlas for material {i}")
                continue
            
            atlas_index = atlas.texture_indices[tex_name]
            print(f"   DEBUG: atlas_index = {atlas_index}")
            
            start_idx = prim.vertex_offset
            end_idx = start_idx + prim.vertex_count
            print(f"   DEBUG: vertex range = {start_idx} to {end_idx}")
            
            if end_idx > len(new_vertices):
                print(f"   Warning: Vertex range out of bounds for material {i}")
                continue
            
            # استخراج إحداثيات UV لهذه المجموعة - البحث عن 'u' و 'v' بدلاً من 'uv0'
            if "u" in new_vertices.dtype.names and "v" in new_vertices.dtype.names:
                print(f"   DEBUG: Found u/v fields")
                
                # تجميع UV لكل رأس في المجموعة
                uvs = np.array([[new_vertices[j]["u"], new_vertices[j]["v"]] 
                               for j in range(start_idx, end_idx)])
                
                print(f"   DEBUG: uvs.shape = {uvs.shape}")
                if len(uvs) > 0:
                    print(f"   Original UVs (first 3): {uvs[:3]}")
                
                # تحويل الإحداثيات
                transformed_uvs = atlas.get_uv_transform(tex_name, uvs)
                print(f"   DEBUG: transformed_uvs.shape = {transformed_uvs.shape}")
                
                if len(transformed_uvs) > 0:
                    print(f"   Transformed UVs (first 3): {transformed_uvs[:3]}")
                
                # تطبيق الإحداثيات الجديدة
                for j, idx in enumerate(range(start_idx, end_idx)):
                    new_vertices[idx]["u"] = transformed_uvs[j, 0]
                    new_vertices[idx]["v"] = transformed_uvs[j, 1]
                
                print(f"   DEBUG: Applied UV transform for material {i}")
            else:
                print(f"   DEBUG: u/v fields NOT FOUND in vertices")
        
        return new_vertices
        

    def update_mtl_with_atlas(self, out_dir: str, base_name: str, atlas: TextureAtlas):
        """
        تحديث ملف MTL لاستخدام الأطلس بدلاً من القوام الفردية
        """
        if not atlas or not atlas.has_multiple_textures():
            return
        
        mtl_path = os.path.join(out_dir, f"{base_name}_render.mtl")
        if not os.path.exists(mtl_path):
            return
        
        # قراءة ملف MTL الحالي
        with open(mtl_path, 'r', encoding='utf-8') as f:
            mtl_lines = f.readlines()
        
        # تحديث كل المواد لاستخدام نفس ملف الأطلس
        new_lines = []
        current_material = None
        
        for line in mtl_lines:
            if line.startswith('newmtl '):
                current_material = line.strip()
                new_lines.append(line)
            elif line.startswith('map_Kd ') and current_material:
                # استبدال map_Kd بالإشارة إلى الأطلس
                new_lines.append(f"map_Kd {base_name}_atlas.png\n")
            elif line.startswith('map_Ke ') and current_material:
                # استبدال map_Ke (خرائط الإضاءة) أيضاً
                new_lines.append(f"map_Ke {base_name}_atlas.png\n")
            elif line.startswith('map_') and current_material:
                # أي map_ أخرى (bump, reflection) نستبدلها أيضاً
                new_lines.append(f"map_Kd {base_name}_atlas.png\n")
            else:
                new_lines.append(line)
        
        # حفظ الملف المحدث
        with open(mtl_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
        print(f"   Updated MTL to use texture atlas: {mtl_path}")

    # ========== دالة export_all المحدثة لـ IGI2 ==========
    def export_all(self, out_dir, export_formats=None, lightmap_format="png"):
        """دالة تصدير واحدة شاملة - تصدر كل شيء (أساسي + محسّن)"""
        if export_formats is None:
            export_formats = ["obj"]
        
        base_name = os.path.splitext(os.path.basename(out_dir))[0]
        self.ensure_dir(out_dir)
        
        print(f"\nExporting to {out_dir}")
        print("-" * 50)
        
        # ========== 0. معلومات الرأس ==========
        self.export_hsem_info(out_dir, base_name)
        self.export_d3dr_info(out_dir, base_name)
        
        # ========== 0.5. معلومات العظام ==========
        self.export_manb_detailed(out_dir, base_name)      # ✅ محسّن
        self.export_reih_detailed(out_dir, base_name)      # ✅ محسّن
        
        # ========== 0.6. معلومات التصادم ==========
        self.export_hsmc_info(out_dir, base_name)          # ✅ جديد
        
        # ========== 1. شبكة التصيير ==========
        self.export_render_mesh(out_dir, base_name, export_formats)
        
        # ========== 2. شبكة التصادم (كشبكة) ==========
        self.export_collision_mesh(out_dir, base_name, 0, export_formats)
        if self.collision_mesh_data2:
            self.export_collision_mesh(out_dir, base_name, 1, export_formats)
        
        # ========== 3. بيانات التصادم التفصيلية ==========
        self.export_all_collision_mesh_data(out_dir, base_name)  # ✅ جديد
        
        # ========== 4. شبكة الظل ==========
        self.export_all_shadow_data(out_dir, base_name)          # ✅ جديد
        
        # ========== 5. مواد وكرات التصادم (مكرر لكن نحتفظ به للتوافق) ==========
        self.export_collision_materials(out_dir, base_name)
        self.export_collision_spheres(out_dir, base_name)
        
        # ========== 6. المرفقات ==========
        self.export_attachments(out_dir, base_name)
        
        # ========== 7. خرائط الإضاءة ==========
        self.export_lightmaps(out_dir, base_name, lightmap_format)
        
        # ========== 8. البيانات الإضافية الأساسية ==========
        self.export_extra_data(out_dir, base_name)
        
        # ========== 9. البيانات الإضافية المحسنة ==========
        self.export_magic_vertices_improved(out_dir, base_name)
        self.export_portals_as_mesh(out_dir, base_name)
        self.export_glow_sprites_improved(out_dir, base_name)
        
        # ========== 10. بيانات التشكل والحركة ==========
        self.export_mrph_info(out_dir, base_name)
        self.export_txan_info(out_dir, base_name)
        
        # ========== 11. تصدير القطع الجديدة (XTRW, XTXM, TCST) ==========
        self.export_xtrw_info(out_dir, base_name)
        self.export_xtxm_info(out_dir, base_name)
        self.export_tcst_info(out_dir, base_name)
        self.export_hprm_info(out_dir, base_name)
        
        print("-" * 50)
        print("Export completed successfully!")


# ============================================================
# تحديث هياكل IGI2 بناءً على تحليل igi2.exe
# ============================================================

@dataclass
class HsemHeaderIGI2_V2:
    """HSEM header - دقيق 100% من igi2.exe"""
    version: float              # 0x00 - float (عادة 1.0 أو 2.0)
    model_type: int             # 0x04 - 0=Static,1=Skinned,3=Lightmapped
    unknown1: int               # 0x08
    unknown2: int               # 0x0C
    unknown3: int               # 0x10
    bound_min: Vector3          # 0x14
    bound_max: Vector3          # 0x20
    bounding_radius: float      # 0x2C
    # باقي الحقول (حسب حجم الـ chunk - 156 أو 172 أو 212)
    
    @classmethod
    def from_buffer(cls, buffer: Buffer, size: int):
        """قراءة HSEM حسب الحجم الفعلي"""
        version = buffer.read_float()
        model_type = buffer.read_uint32()
        unk1 = buffer.read_uint32()
        unk2 = buffer.read_uint32()
        unk3 = buffer.read_uint32()
        bound_min = Vector3.from_buffer(buffer)
        bound_max = Vector3.from_buffer(buffer)
        bounding_radius = buffer.read_float()
        
        # قراءة الحقول الإضافية حسب الحجم
        remaining = size - 48  # بعد قراءة 48 بايت
        if remaining > 0:
            extra_data = buffer.read(remaining)
        else:
            extra_data = b''
            
        return cls(version, model_type, unk1, unk2, unk3,
                   bound_min, bound_max, bounding_radius)


@dataclass
class ReihChunkData:
    """REIH (Hierarchy) - هيكل العظام"""
    child_counts: List[int]      # عدد الأبناء لكل عظمة
    bone_positions: List[Vector3]  # مواقع العظام
    bone_names: List[str]         # أسماء العظام (من MANB منفصل)
    
    @classmethod
    def from_buffer(cls, buffer: Buffer, bone_count: int):
        """قراءة هيكل REIH"""
        # قراءة child_counts (unsigned char لكل عظمة)
        child_counts = [buffer.read_uint8() for _ in range(bone_count)]
        
        # محاذاة إلى 4 بايت
        buffer.align(4)
        
        # قراءة مواقع العظام
        bone_positions = [Vector3.from_buffer(buffer) for _ in range(bone_count)]
        
        return cls(child_counts, bone_positions, [])


@dataclass
class SmesHeaderIGI2:
    """SEMS (Shadow Mesh Header) - جديد"""
    face_offset: int       # 0x00
    vertex_offset: int     # 0x04
    edge_offset: int       # 0x08
    face_count: int        # 0x0C
    vertex_count: int      # 0x10
    edge_count: int        # 0x14
    bone_index: int        # 0x18 - عظمة الظل
    
    @classmethod
    def from_buffer(cls, buffer: Buffer):
        return cls(
            buffer.read_uint32(),  # face_offset
            buffer.read_uint32(),  # vertex_offset
            buffer.read_uint32(),  # edge_offset
            buffer.read_uint32(),  # face_count
            buffer.read_uint32(),  # vertex_count
            buffer.read_uint32(),  # edge_count
            buffer.read_uint32()   # bone_index
        )


@dataclass
class CafsFaceIGI2:
    """CAFS (Shadow Face) - وجه ظل مع معلومات إضافية"""
    vertices: Tuple[int, int, int]   # 3 مؤشرات رؤوس
    edge_flags: int                  # flags لكل حافة
    normal: Vector3                  # الطبيعية
    
    @classmethod
    def from_buffer(cls, buffer: Buffer):
        v0 = buffer.read_uint32()
        v1 = buffer.read_uint32()
        v2 = buffer.read_uint32()
        edge_flags = buffer.read_uint32()
        normal = Vector3.from_buffer(buffer)
        return cls((v0, v1, v2), edge_flags, normal)


@dataclass
class EgdeEdgeIGI2:
    """EGDE (Shadow Edge) - حافة ظل"""
    v0: int
    v1: int
    
    @classmethod
    def from_buffer(cls, buffer: Buffer):
        return cls(buffer.read_uint32(), buffer.read_uint32())


# ============================================================
# فئة MefModelIGI2_V2 - نسخة مطورة من MefModelIGI2
# (تُضاف بعد تعريف MefModelIGI2 الأصلي)
# ============================================================
class MefModelIGI2_V2:
    """نسخة مطورة من MefModelIGI2 بناءً على تحليل igi2.exe"""
    
    def __init__(self, buffer: Buffer, export_mode: str = "simple", 
                 debug_params: Optional[MefDebugParams] = None):
        self.debug_params = debug_params or MefDebugParams()
        loop_file = LoopFile(buffer, flip_ident=True)
        
        # بيانات الرأس
        self.hsem: HsemHeaderIGI2_V2 = None
        self.bone_count: int = 0
        
        # بيانات العظام
        self.bones: List[Bone] = []
        self.bone_names: List[str] = []
        self.bone_child_counts: List[int] = []
        self.bone_positions: List[Vector3] = []
        self.bone_extra_params: List[List[float]] = []  # HPRM
        
        # بيانات النموذج الرئيسية
        self.render_mesh_data: RenderMeshDataIGI2 = None
        
        # بيانات الظل (جديدة)
        self.shadow_header: SmesHeaderIGI2 = None
        self.shadow_vertices: np.ndarray = None      # XTVS
        self.shadow_faces: List[CafsFaceIGI2] = []   # CAFS
        self.shadow_edges: List[EgdeEdgeIGI2] = []   # EGDE
        
        # بيانات إضافية
        self.attachments: List[Attachment] = []
        self.magic_vertices: List[MagicVertex] = []
        self.portals: List[Portal] = []
        self.portal_vertices: List[PortalVertex] = []
        self.portal_faces: List[PortalFace] = []
        self.glow_sprites: List[GlowSprite] = []
        self.lightmaps: List[LightmapData] = []
        
        # القطع الجديدة
        self.vertex_weights: List[XTRWEntry] = []
        self.texture_references: List[TextureReference] = []
        self.extra_uv_sets: List[TextureCoordinateSet] = []
        self.external_refs: List[str] = []  # XTRN
        self.skeleton_hints: List[bytes] = []  # NHSA
        
        self.export_mode = export_mode
        
        # المعالجة - نفس تسلسل igi2.exe
        self._load_chunks(loop_file)
    
    def _load_chunks(self, loop_file: LoopFile):
        """تحميل القطع بنفس ترتيب igi2.exe"""
        
        # 1. HSEM - الرأس
        if loop_file.has_chunk("HSEM"):
            chunk = loop_file.expect_chunk("HSEM")
            chunk.buffer.offset = 0
            self.hsem = HsemHeaderIGI2_V2.from_buffer(
                chunk.buffer, chunk.header.data_size
            )
            print(f"✅ HSEM: version={self.hsem.version}, type={self.hsem.model_type}")
        
        # 2. REIH - هيكل العظام
        if loop_file.has_chunk("REIH"):
            chunk = loop_file.expect_chunk("REIH")
            chunk.buffer.offset = 0
            bone_count = self.hsem.model_type == 1 and self.hsem.unknown1 or 0
            # محاولة تقدير عدد العظام من حجم الـ chunk
            if bone_count == 0:
                # تقدير: كل عظمة لها child_count (1 بايت) + 12 بايت position
                data_size = chunk.header.data_size
                bone_count = data_size // 13  # تقريبي
                if bone_count > 100:
                    bone_count = 0
            
            if bone_count > 0:
                reih = ReihChunkData.from_buffer(chunk.buffer, bone_count)
                self.bone_child_counts = reih.child_counts
                self.bone_positions = reih.bone_positions
                print(f"✅ REIH: {len(self.bone_child_counts)} bones")
        
        # 3. MANB - أسماء العظام
        if loop_file.has_chunk("MANB"):
            chunk = loop_file.expect_chunk("MANB")
            chunk.buffer.offset = 0
            bone_count_from_names = chunk.header.data_size // 16
            for i in range(bone_count_from_names):
                name = chunk.buffer.read_ascii_string(16)
                self.bone_names.append(name)
            print(f"✅ MANB: {len(self.bone_names)} bone names")
        
        # 4. HPRM - معاملات العظام الإضافية
        if loop_file.has_chunk("HPRM"):
            chunk = loop_file.expect_chunk("HPRM")
            chunk.buffer.offset = 0
            param_count = chunk.header.data_size // 12  # 3 floats
            for i in range(param_count):
                px = chunk.buffer.read_float()
                py = chunk.buffer.read_float()
                pz = chunk.buffer.read_float()
                self.bone_extra_params.append([px, py, pz])
            print(f"✅ HPRM: {len(self.bone_extra_params)} bone param sets")
        
        # 5. WOLG - التوهجات
        if loop_file.has_chunk("WOLG"):
            chunk = loop_file.expect_chunk("WOLG")
            self._load_glow_sprites(chunk)
        
        # 6. ATTA - المرفقات
        if loop_file.has_chunk("ATTA"):
            chunk = loop_file.expect_chunk("ATTA")
            self._load_attachments(chunk)
        
        # 7. XTVM - الرؤوس السحرية
        if loop_file.has_chunk("XTVM"):
            chunk = loop_file.expect_chunk("XTVM")
            self._load_magic_vertices(chunk)
        
        # 8. TROP - البوابات
        if loop_file.has_chunk("TROP"):
            chunk = loop_file.expect_chunk("TROP")
            self._load_portals(chunk)
        
        # 9. CFTP - وجوه البوابات
        if loop_file.has_chunk("CFTP"):
            chunk = loop_file.expect_chunk("CFTP")
            self._load_portal_faces(chunk)
        
        # 10. XVTP - رؤوس البوابات
        if loop_file.has_chunk("XVTP"):
            chunk = loop_file.expect_chunk("XVTP")
            self._load_portal_vertices(chunk)
        
        # 11. XTRW - أوزان إضافية
        if loop_file.has_chunk("XTRW"):
            chunk = loop_file.expect_chunk("XTRW")
            self._load_xtrw(chunk)
        
        # 12. XTXM - مراجع القوام
        if loop_file.has_chunk("XTXM"):
            chunk = loop_file.expect_chunk("XTXM")
            self._load_xtxm(chunk)
        
        # 13. TCST - مجموعات UV إضافية
        if loop_file.has_chunk("TCST"):
            chunk = loop_file.expect_chunk("TCST")
            self._load_tcst(chunk)
        
        # 14. RD3D - هيدر التصيير
        if loop_file.has_chunk("RD3D"):
            chunk = loop_file.expect_chunk("RD3D")
            self._load_render_header(chunk, loop_file)
        
        # 15. REND - مجموعات المواد
        if loop_file.has_chunk("REND"):
            chunk = loop_file.expect_chunk("REND")
            self._load_render_groups(chunk)
        
        # 16. VRTX - الرؤوس
        if loop_file.has_chunk("VRTX"):
            chunk = loop_file.expect_chunk("VRTX")
            self._load_vertices(chunk)
        
        # 17. FACE - الوجوه
        if loop_file.has_chunk("FACE"):
            chunk = loop_file.expect_chunk("FACE")
            self._load_faces(chunk)
        
        # 18. LTMP - خرائط الإضاءة
        if loop_file.has_chunk("LTMP"):
            chunk = loop_file.expect_chunk("LTMP")
            self._load_lightmaps(chunk)
        
        # 19. SMES - هيدر الظل (جديد)
        if loop_file.has_chunk("SMES"):
            chunk = loop_file.expect_chunk("SMES")
            self._load_shadow_header(chunk)
        
        # 20. SVTX - رؤوس الظل (جديد)
        if loop_file.has_chunk("SVTX"):
            chunk = loop_file.expect_chunk("SVTX")
            self._load_shadow_vertices(chunk)
        
        # 21. SFAC - وجوه الظل (جديد)
        if loop_file.has_chunk("SFAC"):
            chunk = loop_file.expect_chunk("SFAC")
            self._load_shadow_faces(chunk)
        
        # 22. EGDE - حواف الظل (جديد)
        if loop_file.has_chunk("EGDE"):
            chunk = loop_file.expect_chunk("EGDE")
            self._load_shadow_edges(chunk)
        
        # 23. XTRN - مراجع خارجية
        if loop_file.has_chunk("XTRN"):
            chunk = loop_file.expect_chunk("XTRN")
            self._load_xtrn(chunk)
        
        # 24. NHSA - تلميحات هيكلية
        if loop_file.has_chunk("NHSA"):
            chunk = loop_file.expect_chunk("NHSA")
            self._load_nhsa(chunk)
        
        # 25. LLUN - نهاية (تجاهل)
        
        # بناء العظام من البيانات المجمعة
        self._build_bones()
    
    def _load_glow_sprites(self, chunk: Chunk):
        """تحميل WOLG (Glow Sprites)"""
        buffer = chunk.buffer
        count = buffer.size() // 32
        for _ in range(count):
            if buffer.eof():
                break
            g = GlowSprite.from_buffer(buffer)
            self.glow_sprites.append(g)
        print(f"✅ WOLG: {len(self.glow_sprites)} glow sprites")

    def _load_attachments(self, chunk: Chunk):
        """تحميل ATTA (Attachments)"""
        buffer = chunk.buffer
        count = buffer.size() // 48  # 16+12+36+4+4 تقريباً
        for _ in range(count):
            if buffer.eof():
                break
            attachment = Attachment.from_buffer(buffer)
            self.attachments.append(attachment)
        print(f"✅ ATTA: {len(self.attachments)} attachments")

    def _load_magic_vertices(self, chunk: Chunk):
        """تحميل XTVM (Magic Vertices)"""
        buffer = chunk.buffer
        count = buffer.size() // 16
        for _ in range(count):
            if buffer.eof():
                break
            mv = MagicVertex.from_buffer(buffer)
            self.magic_vertices.append(mv)
        print(f"✅ XTVM: {len(self.magic_vertices)} magic vertices")

    def _load_portals(self, chunk: Chunk):
        """تحميل TROP (Portals)"""
        buffer = chunk.buffer
        count = buffer.size() // 20
        for _ in range(count):
            if buffer.eof():
                break
            p = Portal.from_buffer(buffer)
            self.portals.append(p)
        print(f"✅ TROP: {len(self.portals)} portals")

    def _load_portal_faces(self, chunk: Chunk):
        """تحميل CFTP (Portal Faces)"""
        buffer = chunk.buffer
        count = buffer.size() // 12
        for _ in range(count):
            if buffer.eof():
                break
            pf = PortalFace.from_buffer(buffer)
            self.portal_faces.append(pf)
        print(f"✅ CFTP: {len(self.portal_faces)} portal faces")

    def _load_portal_vertices(self, chunk: Chunk):
        """تحميل XVTP (Portal Vertices)"""
        buffer = chunk.buffer
        count = buffer.size() // 12
        for _ in range(count):
            if buffer.eof():
                break
            pv = PortalVertex.from_buffer(buffer)
            self.portal_vertices.append(pv)
        print(f"✅ XVTP: {len(self.portal_vertices)} portal vertices")

    def _load_xtrw(self, chunk: Chunk):
        """تحميل XTRW (Vertex Weights)"""
        buffer = chunk.buffer
        count = buffer.size() // 12
        for i in range(count):
            entry = XTRWEntry.from_buffer(buffer)
            self.vertex_weights.append(entry)
        print(f"✅ XTRW: {len(self.vertex_weights)} weight entries")

    def _load_xtxm(self, chunk: Chunk):
        """تحميل XTXM (Texture References)"""
        buffer = chunk.buffer
        count = buffer.size() // 36
        for i in range(count):
            if buffer.eof():
                break
            ref = TextureReference.from_buffer(buffer)
            self.texture_references.append(ref)
        print(f"✅ XTXM: {len(self.texture_references)} texture references")

    def _load_tcst(self, chunk: Chunk):
        """تحميل TCST (UV Sets)"""
        buffer = chunk.buffer
        uv_count = buffer.size() // 8
        uv_set = TextureCoordinateSet.from_buffer(buffer, uv_count)
        uv_set.index = len(self.extra_uv_sets)
        self.extra_uv_sets.append(uv_set)
        print(f"✅ TCST: {uv_count} UV coordinates")

    def _load_render_header(self, chunk: Chunk, loop_file: LoopFile):
        """تحميل RD3D (Render Header)"""
        chunk.buffer.offset = 0
        self.render_mesh_info = RenderMeshHeader.from_buffer(chunk.buffer)

    def _load_render_groups(self, chunk: Chunk):
        """تحميل REND (Material Groups)"""
        chunk.buffer.offset = 0
        self.render_info = []
        for _ in range(self.render_mesh_info.face_group_count):
            self.render_info.append(FaceGroup.from_buffer(chunk.buffer, self.hsem.model_type))

    def _load_vertices(self, chunk: Chunk):
        """تحميل VRTX (Vertices)"""
        chunk.buffer.offset = 0
        vert_data = chunk.buffer.read(chunk.buffer.size())
        
        model_type = self.hsem.model_type
        if model_type == 0:
            dtype = np.dtype([
                ("pos", np.float32, (3,)),
                ("normal", np.float32, (3,)),
                ("uv0", np.float32, (2,))
            ])
        elif model_type == 1:
            dtype = np.dtype([
                ("pos", np.float32, (3,)),
                ("normal", np.float32, (3,)),
                ("uv0", np.float32, (2,)),
                ("weight", np.float32, (1,)),
                ("index", np.ushort, (1,)),
                ("bone_id", np.ushort, (1,))
            ])
        elif model_type == 3:
            dtype = np.dtype([
                ("pos", np.float32, (3,)),
                ("uv0", np.float32, (2,)),
                ("uv1", np.float32, (2,))
            ])
        else:
            dtype = np.dtype([
                ("pos", np.float32, (3,)),
                ("normal", np.float32, (3,)),
                ("uv0", np.float32, (2,))
            ])
        
        self.render_vertices = np.frombuffer(vert_data, dtype)
        print(f"✅ VRTX: {len(self.render_vertices)} vertices")

    def _load_faces(self, chunk: Chunk):
        """تحميل FACE (Faces)"""
        chunk.buffer.offset = 0
        face_data = chunk.buffer.read(chunk.buffer.size())
        self.render_faces = np.frombuffer(face_data, np.uint16).reshape(-1, 3)
        print(f"✅ FACE: {len(self.render_faces)} faces")

    def _load_lightmaps(self, chunk: Chunk):
        """تحميل LTMP (Lightmaps)"""
        try:
            buffer = chunk.buffer
            width = buffer.read_uint32()
            height = buffer.read_uint32()
            format_type = buffer.read_uint32()
            data_size = buffer.size()
            data = buffer.read(data_size)
            
            lightmap = LightmapData(width, height, format_type, data)
            self.lightmaps.append(lightmap)
            print(f"✅ LTMP: {width}x{height} lightmap")
        except Exception as e:
            print(f"   Error loading lightmap: {e}")

    def _load_shadow_header(self, chunk: Chunk):
        """تحميل SEMS - هيدر شبكة الظل"""
        chunk.buffer.offset = 0
        self.shadow_header = SmesHeaderIGI2.from_buffer(chunk.buffer)
        print(f"✅ SMES: faces={self.shadow_header.face_count}, "
              f"verts={self.shadow_header.vertex_count}, "
              f"edges={self.shadow_header.edge_count}")
    
    def _load_shadow_vertices(self, chunk: Chunk):
        """تحميل XTVS - رؤوس الظل"""
        chunk.buffer.offset = 0
        vertex_count = chunk.header.data_size // 12  # 3 floats
        vertices = []
        for i in range(vertex_count):
            x = chunk.buffer.read_float()
            y = chunk.buffer.read_float()
            z = chunk.buffer.read_float()
            vertices.append((x, y, z))
        self.shadow_vertices = np.array(vertices, dtype=np.float32)
        print(f"✅ SVTX: {len(self.shadow_vertices)} shadow vertices")
    
    def _load_shadow_faces(self, chunk: Chunk):
        """تحميل CAFS - وجوه الظل"""
        chunk.buffer.offset = 0
        face_size = 32  # 3 uint32 + 1 uint32 + 3 floats = 32 bytes
        face_count = chunk.header.data_size // face_size
        for i in range(face_count):
            face = CafsFaceIGI2.from_buffer(chunk.buffer)
            self.shadow_faces.append(face)
        print(f"✅ SFAC: {len(self.shadow_faces)} shadow faces")
    
    def _load_shadow_edges(self, chunk: Chunk):
        """تحميل EGDE - حواف الظل"""
        chunk.buffer.offset = 0
        edge_size = 8  # 2 uint32
        edge_count = chunk.header.data_size // edge_size
        for i in range(edge_count):
            edge = EgdeEdgeIGI2.from_buffer(chunk.buffer)
            self.shadow_edges.append(edge)
        print(f"✅ EGDE: {len(self.shadow_edges)} shadow edges")
    
    def _load_xtrn(self, chunk: Chunk):
        """تحميل XTRN - مرجع خارجي"""
        chunk.buffer.offset = 0
        ref_name = chunk.buffer.read_ascii_string(32)
        self.external_refs.append(ref_name)
        print(f"✅ XTRN: {ref_name}")
    
    def _load_nhsa(self, chunk: Chunk):
        """تحميل NHSA - تلميحات هيكلية"""
        chunk.buffer.offset = 0
        hint_data = chunk.buffer.read(min(64, chunk.header.data_size))
        self.skeleton_hints.append(hint_data)
        print(f"✅ NHSA: {len(hint_data)} bytes")
    
    def _build_bones(self):
        """بناء العظام من البيانات المجمعة"""
        # تحديد عدد العظام
        bone_count = max(
            len(self.bone_child_counts),
            len(self.bone_names),
            len(self.bone_positions)
        )
        
        if bone_count == 0:
            return
        
        # بناء قائمة العظام
        self.bones = []
        for i in range(bone_count):
            name = self.bone_names[i] if i < len(self.bone_names) else f"bone_{i}"
            parent_id = self._find_parent(i)
            pos = self.bone_positions[i] if i < len(self.bone_positions) else Vector3(0, 0, 0)
            
            self.bones.append(Bone(name, pos, parent_id))
        
        print(f"✅ Built {len(self.bones)} bones")
    
    def _find_parent(self, bone_index: int) -> int:
        """العثور على العظمة الأب من child_counts (محسنة جزئياً)"""
        if bone_index == 0:
            return -1
        
        if not self.bone_child_counts:
            return bone_index - 1
        
        # حساب الأب من عدد الأبناء
        # ملاحظة: هذه خوارزمية مؤقتة وقد تحتاج لتحسين حسب البيانات الفعلية
        total_children = sum(self.bone_child_counts)
        if total_children == 0:
            return bone_index - 1
        return max(0, bone_index - 1)

    def ensure_dir(self, path):
        Path(path).mkdir(parents=True, exist_ok=True)

    # ========== دوال التصدير الأساسية (مستعارة من MefModelIGI2 مع تعديلات بسيطة) ==========
    def export_hsem_info(self, out_dir: str, base_name: str):
        if not self.hsem:
            return
        info_dict = {
            "version": self.hsem.version,
            "model_type": self.hsem.model_type,
            "bound_min": [self.hsem.bound_min.x, self.hsem.bound_min.y, self.hsem.bound_min.z],
            "bound_max": [self.hsem.bound_max.x, self.hsem.bound_max.y, self.hsem.bound_max.z],
            "bounding_radius": self.hsem.bounding_radius,
        }
        json_path = os.path.join(out_dir, f"{base_name}_hsem.json")
        data = convert_to_json_serializable(info_dict)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   HSEM info (JSON): {json_path}")

    def export_d3dr_info(self, out_dir: str, base_name: str):
        """تصدير معلومات D3DR"""
        if not hasattr(self, 'render_mesh_info') or not self.render_mesh_info:
            return
        header_dict = {
            "face_count": self.render_mesh_info.face_count,
            "vertex_count": self.render_mesh_info.vertex_count,
            "face_group_count": self.render_mesh_info.face_group_count,
        }
        json_path = os.path.join(out_dir, f"{base_name}_d3dr.json")
        data = convert_to_json_serializable(header_dict)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   D3DR info (JSON): {json_path}")

    def export_manb_detailed(self, out_dir: str, base_name: str):
        if not self.bone_names:
            return
        json_path = os.path.join(out_dir, f"{base_name}_manb.json")
        data = convert_to_json_serializable({"bone_names": self.bone_names})
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   MANB (JSON): {json_path}")

    def export_reih_detailed(self, out_dir: str, base_name: str):
        if not self.bones:
            return
        bone_data = [{"name": b.name, "parent": b.parent_id} for b in self.bones]
        json_path = os.path.join(out_dir, f"{base_name}_reih.json")
        data = convert_to_json_serializable({"bones": bone_data})
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   REIH (JSON): {json_path}")

    def export_attachments(self, out_dir: str, base_name: str):
        att_path = os.path.join(out_dir, f"{base_name}_attachments.txt")
        with open(att_path, "w", encoding="utf-8") as f:
            f.write("# Attachment points\n")
            for a in self.attachments:
                f.write(f"{a.name}\n")
        print(f"   Attachments: {att_path}")

    def export_render_mesh(self, out_dir, base_name, export_formats=None):
        """تصدير الشبكة الرئيسية (نسخة مبسطة)"""
        if export_formats is None:
            export_formats = ["obj"]
        
        if not hasattr(self, 'render_vertices') or not hasattr(self, 'render_faces'):
            print("   No render mesh data")
            return
        
        vertices = self.render_vertices
        faces = self.render_faces
        
        # تحويل الرؤوس
        dtype_out = np.dtype([
            ("px", np.float32), ("py", np.float32), ("pz", np.float32),
            ("nx", np.float32), ("ny", np.float32), ("nz", np.float32),
            ("u", np.float32), ("v", np.float32)
        ])
        
        new_verts = []
        for v in vertices:
            pos = v["pos"]
            px, py, pz = self.debug_params.swizzle(pos[0], pos[1], pos[2], self.debug_params.v_scale)
            
            if "normal" in v.dtype.names:
                normal = v["normal"]
                nx, ny, nz = self.debug_params.swizzle(normal[0], normal[1], normal[2], 1.0)
            else:
                nx, ny, nz = 0, 0, 0
            
            if "uv0" in v.dtype.names:
                u, vt = v["uv0"][0], v["uv0"][1]
            else:
                u, vt = 0, 0
            
            new_verts.append((px, py, pz, nx, ny, nz, u, vt))
        
        verts_arr = np.array(new_verts, dtype=dtype_out)
        
        if "obj" in export_formats:
            obj_path = os.path.join(out_dir, f"{base_name}_render.obj")
            mtl_path = os.path.join(out_dir, f"{base_name}_render.mtl")
            
            with open(mtl_path, 'w', encoding='utf-8') as f:
                f.write("newmtl material\n")
                f.write("Ns 10.0000\n")
                f.write("Ka 1.0000 1.0000 1.0000\n")
                f.write("Kd 1.0000 1.0000 1.0000\n")
                f.write("Ks 0.0000 0.0000 0.0000\n")
            
            with open(obj_path, 'w', encoding='utf-8') as f:
                f.write(f"mtllib {base_name}_render.mtl\n")
                f.write(f"o {base_name}_render\n")
                for v in verts_arr:
                    f.write(f"v {v['px']:.6f} {v['py']:.6f} {v['pz']:.6f}\n")
                for v in verts_arr:
                    f.write(f"vt {v['u']:.6f} {1.0 - v['v']:.6f}\n")
                for v in verts_arr:
                    f.write(f"vn {v['nx']:.6f} {v['ny']:.6f} {v['nz']:.6f}\n")
                f.write(f"usemtl material\n")
                for face in faces:
                    a, b, c = face[0]+1, face[1]+1, face[2]+1
                    f.write(f"f {a}/{a}/{a} {b}/{b}/{b} {c}/{c}/{c}\n")
            print(f"   Render OBJ: {obj_path}")

    def export_all_collision_mesh_data(self, out_dir: str, base_name: str):
        """تصدير بيانات التصادم (نسخة مبسطة)"""
        # لم نضف بيانات تصادم في النسخة المبسطة
        pass

    def export_shadow_mesh_enhanced(self, out_dir: str, base_name: str, 
                                     export_formats: List[str] = None):
        """تصدير شبكة الظل المحسّن - يدعم SEMS, XTVS, CAFS, EGDE"""
        if export_formats is None:
            export_formats = ["obj"]
        
        if self.shadow_vertices is None or len(self.shadow_vertices) == 0:
            print("   No shadow mesh data")
            return
        
        # ========== 1. تصدير OBJ مع الوجوه ==========
        if "obj" in export_formats and self.shadow_faces:
            # تحويل الرؤوس مع swizzle
            transformed_verts = []
            for v in self.shadow_vertices:
                px, py, pz = self.debug_params.swizzle(v[0], v[1], v[2], 
                                                       self.debug_params.v_scale)
                transformed_verts.append((px, py, pz))
            
            # تجهيز الوجوه
            faces = []
            for face in self.shadow_faces:
                faces.append([face.vertices[0], face.vertices[1], face.vertices[2]])
            
            # إنشاء مصفوفة رؤوس
            dtype_out = np.dtype([
                ("px", np.float32), ("py", np.float32), ("pz", np.float32),
                ("nx", np.float32), ("ny", np.float32), ("nz", np.float32),
                ("u", np.float32), ("v", np.float32)
            ])
            
            verts_arr = np.array([(v[0], v[1], v[2], 0,0,0,0,0) 
                                  for v in transformed_verts], dtype=dtype_out)
            faces_arr = np.array(faces)
            
            # حفظ OBJ
            obj_path = os.path.join(out_dir, f"{base_name}_shadow.obj")
            mtl_path = os.path.join(out_dir, f"{base_name}_shadow.mtl")
            
            with open(mtl_path, 'w', encoding='utf-8') as f:
                f.write("newmtl shadow_material\n")
                f.write("Ns 10.0000\n")
                f.write("Ka 1.0000 1.0000 1.0000\n")
                f.write("Kd 0.5000 0.5000 0.5000\n")
                f.write("Ks 0.0000 0.0000 0.0000\n")
            
            with open(obj_path, 'w', encoding='utf-8') as f:
                f.write(f"mtllib {base_name}_shadow.mtl\n")
                f.write(f"o {base_name}_shadow\n")
                
                for v in verts_arr:
                    f.write(f"v {v['px']:.6f} {v['py']:.6f} {v['pz']:.6f}\n")
                
                f.write("usemtl shadow_material\n")
                for face in faces_arr:
                    a, b, c = face[0]+1, face[1]+1, face[2]+1
                    f.write(f"f {a} {b} {c}\n")
            
            print(f"   Shadow OBJ: {obj_path}")
        
        # ========== 2. تصدير معلومات الظل كـ JSON ==========
        if "json" in export_formats and self.shadow_header:
            shadow_data = {
                "header": {
                    "face_offset": self.shadow_header.face_offset,
                    "vertex_offset": self.shadow_header.vertex_offset,
                    "edge_offset": self.shadow_header.edge_offset,
                    "face_count": self.shadow_header.face_count,
                    "vertex_count": self.shadow_header.vertex_count,
                    "edge_count": self.shadow_header.edge_count,
                    "bone_index": self.shadow_header.bone_index
                },
                "vertices": [{"index": i, "pos": list(v)} 
                            for i, v in enumerate(self.shadow_vertices)],
                "faces": [{"index": i, "vertices": list(f.vertices), 
                          "edge_flags": f.edge_flags,
                          "normal": [f.normal.x, f.normal.y, f.normal.z]} 
                         for i, f in enumerate(self.shadow_faces)],
                "edges": [{"index": i, "v0": e.v0, "v1": e.v1} 
                         for i, e in enumerate(self.shadow_edges)]
            }
            
            json_path = os.path.join(out_dir, f"{base_name}_shadow.json")
            data = convert_to_json_serializable(shadow_data)
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            print(f"   Shadow JSON: {json_path}")
        
        # ========== 3. تصدير معلومات الظل كـ TXT ==========
        if "txt" in export_formats and self.shadow_header:
            txt_path = os.path.join(out_dir, f"{base_name}_shadow_info.txt")
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write("# Shadow Mesh (SEMS) - Enhanced Export\n")
                f.write("=" * 60 + "\n\n")
                
                f.write("HEADER (SEMS):\n")
                f.write(f"  Face Offset   : {self.shadow_header.face_offset}\n")
                f.write(f"  Vertex Offset : {self.shadow_header.vertex_offset}\n")
                f.write(f"  Edge Offset   : {self.shadow_header.edge_offset}\n")
                f.write(f"  Face Count    : {self.shadow_header.face_count}\n")
                f.write(f"  Vertex Count  : {self.shadow_header.vertex_count}\n")
                f.write(f"  Edge Count    : {self.shadow_header.edge_count}\n")
                f.write(f"  Bone Index    : {self.shadow_header.bone_index}\n\n")
                
                f.write("VERTICES (XTVS):\n")
                for i, v in enumerate(self.shadow_vertices[:50]):
                    f.write(f"  [{i:4d}]: ({v[0]:8.2f}, {v[1]:8.2f}, {v[2]:8.2f})\n")
                if len(self.shadow_vertices) > 50:
                    f.write(f"  ... and {len(self.shadow_vertices)-50} more\n\n")
                
                f.write("FACES (CAFS):\n")
                for i, face in enumerate(self.shadow_faces[:50]):
                    f.write(f"  [{i:4d}]: v=({face.vertices[0]:4d}, {face.vertices[1]:4d}, {face.vertices[2]:4d}), "
                           f"edge_flags={face.edge_flags:4d}, "
                           f"n=({face.normal.x:6.2f}, {face.normal.y:6.2f}, {face.normal.z:6.2f})\n")
                if len(self.shadow_faces) > 50:
                    f.write(f"  ... and {len(self.shadow_faces)-50} more\n\n")
                
                f.write("EDGES (EGDE):\n")
                for i, edge in enumerate(self.shadow_edges[:50]):
                    f.write(f"  [{i:4d}]: {edge.v0:4d} - {edge.v1:4d}\n")
                if len(self.shadow_edges) > 50:
                    f.write(f"  ... and {len(self.shadow_edges)-50} more\n")
            
            print(f"   Shadow Info TXT: {txt_path}")

    def export_glow_sprites_improved(self, out_dir: str, base_name: str):
        if not self.glow_sprites:
            return
        path = os.path.join(out_dir, f"{base_name}_glow_sprites.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("# Glow Sprites\n")
            for i, g in enumerate(self.glow_sprites):
                px, py, pz = self.debug_params.swizzle(g.pos.x, g.pos.y, g.pos.z, self.debug_params.v_scale)
                f.write(f"{i}: ({px:.2f}, {py:.2f}, {pz:.2f}) r={g.radius:.2f}\n")
        print(f"   Glow sprites: {path}")

    def export_portals_as_mesh(self, out_dir: str, base_name: str):
        if not self.portals or not self.portal_vertices or not self.portal_faces:
            return
        vertices = []
        for pv in self.portal_vertices:
            px, py, pz = self.debug_params.swizzle(pv.pos.x, pv.pos.y, pv.pos.z, self.debug_params.v_scale)
            vertices.append([px, py, pz])
        faces = []
        for pf in self.portal_faces:
            faces.append([pf.a, pf.b, pf.c])
        # تصدير OBJ
        obj_path = os.path.join(out_dir, f"{base_name}_portals.obj")
        with open(obj_path, "w", encoding="utf-8") as f:
            f.write(f"o {base_name}_portals\n")
            for v in vertices:
                f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
            for face in faces:
                a,b,c = face[0]+1, face[1]+1, face[2]+1
                f.write(f"f {a} {b} {c}\n")
        print(f"   Portals mesh: {obj_path}")

    def export_magic_vertices_improved(self, out_dir: str, base_name: str):
        if not self.magic_vertices:
            return
        path = os.path.join(out_dir, f"{base_name}_magic_vertices.txt")
        with open(path, "w", encoding="utf-8") as f:
            for mv in self.magic_vertices:
                px, py, pz = self.debug_params.swizzle(mv.pos.x, mv.pos.y, mv.pos.z, self.debug_params.v_scale)
                f.write(f"{px:.6f} {py:.6f} {pz:.6f} {mv.type}\n")
        print(f"   Magic vertices: {path}")

    def export_lightmaps(self, out_dir, base_name, lightmap_format="png"):
        if not self.lightmaps:
            return
        lightmap_dir = os.path.join(out_dir, "lightmaps")
        self.ensure_dir(lightmap_dir)
        for i, lightmap in enumerate(self.lightmaps):
            tga_path = os.path.join(lightmap_dir, f"{base_name}_lightmap_{i}.tga")
            with open(tga_path, "wb") as f:
                f.write(lightmap.data)
            print(f"   Lightmap {i}: {tga_path}")

    def export_xtrw_info(self, out_dir: str, base_name: str):
        if not self.vertex_weights:
            return
        json_path = os.path.join(out_dir, f"{base_name}_xtrw.json")
        data = convert_to_json_serializable([{"vertex_id": w.vertex_id, "bone_id": w.bone_id, "weight": w.weight} 
                for w in self.vertex_weights])
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   XTRW (JSON): {json_path}")

    def export_xtxm_info(self, out_dir: str, base_name: str):
        if not self.texture_references:
            return
        json_path = os.path.join(out_dir, f"{base_name}_xtxm.json")
        data = convert_to_json_serializable([{"index": ref.index, "name": ref.name} for ref in self.texture_references])
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   XTXM (JSON): {json_path}")

    def export_tcst_info(self, out_dir: str, base_name: str):
        if not self.extra_uv_sets:
            return
        json_path = os.path.join(out_dir, f"{base_name}_tcst.json")
        data = convert_to_json_serializable([{"index": uv_set.index, "uv_count": len(uv_set.uvs), "uvs": uv_set.uvs} 
                for uv_set in self.extra_uv_sets])
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   TCST (JSON): {json_path}")

    def export_hprm_info(self, out_dir: str, base_name: str):
        if not self.bone_extra_params:
            return
        json_path = os.path.join(out_dir, f"{base_name}_hprm.json")
        data = convert_to_json_serializable(self.bone_extra_params)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   HPRM (JSON): {json_path}")

    # ========== دالة export_all الرئيسية الموسعة ==========
    def export_all(self, out_dir, export_formats=None, lightmap_format="png"):
        """دالة تصدير واحدة شاملة - تدعم القطع الجديدة"""
        if export_formats is None:
            export_formats = ["obj"]
        
        base_name = os.path.splitext(os.path.basename(out_dir))[0]
        self.ensure_dir(out_dir)
        
        print(f"\n📦 Exporting to {out_dir}")
        print("-" * 50)
        
        # ========== القطع الأساسية ==========
        self.export_hsem_info(out_dir, base_name)
        self.export_d3dr_info(out_dir, base_name)
        
        # ========== العظام والمرفقات ==========
        self.export_manb_detailed(out_dir, base_name)
        self.export_reih_detailed(out_dir, base_name)
        self.export_attachments(out_dir, base_name)
        
        # ========== شبكة التصيير ==========
        self.export_render_mesh(out_dir, base_name, export_formats)
        
        # ========== بيانات التصادم ==========
        self.export_all_collision_mesh_data(out_dir, base_name)
        
        # ========== شبكة الظل (جديد) ==========
        self.export_shadow_mesh_enhanced(out_dir, base_name, export_formats)
        
        # ========== التوهجات والبوابات ==========
        self.export_glow_sprites_improved(out_dir, base_name)
        self.export_portals_as_mesh(out_dir, base_name)
        self.export_magic_vertices_improved(out_dir, base_name)
        
        # ========== خرائط الإضاءة ==========
        self.export_lightmaps(out_dir, base_name, lightmap_format)
        
        # ========== القطع المتقدمة (جديد) ==========
        self.export_xtrw_info(out_dir, base_name)
        self.export_xtxm_info(out_dir, base_name)
        self.export_tcst_info(out_dir, base_name)
        self.export_hprm_info(out_dir, base_name)
        
        # ========== مراجع خارجية وتلميحات (جديد) ==========
        if self.external_refs:
            refs_path = os.path.join(out_dir, f"{base_name}_external_refs.txt")
            with open(refs_path, 'w', encoding='utf-8') as f:
                f.write("# External References (XTRN)\n\n")
                for ref in self.external_refs:
                    f.write(f"{ref}\n")
            print(f"   External references: {refs_path}")
        
        if self.skeleton_hints:
            hints_path = os.path.join(out_dir, f"{base_name}_skeleton_hints.bin")
            with open(hints_path, 'wb') as f:
                for hint in self.skeleton_hints:
                    f.write(hint)
            print(f"   Skeleton hints: {hints_path}")
        
        print("-" * 50)
        print("✅ Export completed successfully!")


# ========== دالة اختبار سريعة (اختيارية) ==========
def test_enhanced_parser(filepath: str, output_dir: str = "output_enhanced"):
    """اختبار المحلل المحسن على ملف MEF"""
    
    print(f"\n🔬 Testing enhanced MEF parser on: {filepath}")
    print("=" * 60)
    
    with open(filepath, "rb") as f:
        data = f.read()
    
    buffer = Buffer(data)
    model = MefModelIGI2_V2(buffer, export_mode="multi")
    
    # إنشاء المجلد
    base_name = Path(filepath).stem
    out_dir = os.path.join(output_dir, base_name)
    
    # تصدير كل شيء
    model.export_all(out_dir, export_formats=["obj", "json", "txt"])
    
    print(f"\n✅ Test complete! Output: {out_dir}")
    
    # طباعة إحصائيات
    print("\n📊 Statistics:")
    print(f"   Bones: {len(model.bones)}")
    print(f"   Shadow vertices: {len(model.shadow_vertices) if model.shadow_vertices is not None else 0}")
    print(f"   Shadow faces: {len(model.shadow_faces)}")
    print(f"   Shadow edges: {len(model.shadow_edges)}")
    print(f"   External refs: {len(model.external_refs)}")
    print(f"   Skeleton hints: {len(model.skeleton_hints)}")
    
    
# ------------------------------------------------------------
# فئة نموذج IGI1
# ------------------------------------------------------------
class MefModelIGI1:
    def __init__(self, buffer: Buffer, export_mode: str = "simple", debug_params: Optional[MefDebugParams] = None):
        self.debug_params = debug_params or MefDebugParams()
        loop_file = LoopFile(buffer, flip_ident=True)
        loop_file.print_all_chunks()

        self.model_info: ModelInfoIGI1 = None
        self.render_mesh_data: RenderMeshDataIGI1 = None
        self.collision_vertices = None
        self.collision_faces = None
        self.collision_spheres = None
        self.collision_materials = []
        # === متغيرات جديدة للمجموعة الثانية ===
        self.collision_vertices2 = None      # رؤوس المجموعة الثانية
        self.collision_faces2 = None         # وجوه المجموعة الثانية
        self.collision_spheres2 = None       # كرات المجموعة الثانية
        self.collision_materials2 = []       # مواد المجموعة الثانية
        # =====================================
        self.attachments: list[AttachmentIGI1] = []
        self.magic_vertices: list[MagicVertex] = []
        self.portals: list[Portal] = []
        self.portal_vertices: list[PortalVertex] = []
        self.portal_faces: list[PortalFace] = []
        self.lightmaps: list[LightmapData] = []
        self.txan_data: list[TXANData] = []
        
        self.export_mode = export_mode
        self.has_hierarchy = False  # جديد: للكشف عن وجود هيكل عظمي

        loop_file.index = 0
        
        while True:
            chunk = loop_file.next_chunk()
            if chunk is None:
                break
            ident = chunk.header.ident.decode('ascii')
            
            if ident == "MESH":
                self.model_info = ModelInfoIGI1.from_buffer(chunk.buffer)
                print(f"Model type: {ModelType(self.model_info.model_type).name}")
                print(f"  Attachments: {self.model_info.attachment_count}, Magic vertices: {self.model_info.magic_vertex_count}")
                print(f"  Portals: {self.model_info.portal_count}, Glow: {self.model_info.glow_count}, Bones: {self.model_info.bone_count}")
            elif ident == "ATTA":
                for _ in range(self.model_info.attachment_count):
                    self.attachments.append(AttachmentIGI1.from_buffer(chunk.buffer))
                print(f"Processed {len(self.attachments)} attachments")
            elif ident == "MVTX":
                self._process_magic_vertices(chunk)
            elif ident == "PORT":
                self._process_portal(chunk)
            elif ident == "PTVX":
                self._process_portal_vertices(chunk)
            elif ident == "PTFC":
                self._process_portal_faces(chunk)
            elif ident == "RD3D":
                self._process_render_mesh(chunk, loop_file)
            elif ident == "CMSH":
                self._process_collision_mesh(chunk, loop_file)
            elif ident == "LTMP":
                self._process_lightmap(chunk)
            elif ident == "TXAN":
                self._process_txan(chunk)
            else:
                if chunk.header.data_size > 0:
                    print(f"Unhandled chunk: {ident} (size: {chunk.header.data_size})")
    
    def _is_igi1_skinned(self) -> bool:
        """الكشف عما إذا كان النموذج IGI1 هيكلياً (بدون HIER)"""
        return (self.model_info.model_type == ModelType.SkinnedModel and 
                not self.has_hierarchy)
                
    def _process_magic_vertices(self, chunk):
        buffer = chunk.buffer
        count = self.model_info.magic_vertex_count if self.model_info else 0
        if count == 0:
            count = buffer.size() // 16
        for _ in range(count):
            if buffer.eof():
                break
            mv = MagicVertex.from_buffer(buffer)
            # ✅ تم إزالة swizzle من هنا - سيتم تطبيقه عند التصدير فقط
            self.magic_vertices.append(mv)
        print(f"Processed {len(self.magic_vertices)} magic vertices")

    def _process_portal(self, chunk):
        buffer = chunk.buffer
        count = self.model_info.portal_count if self.model_info else 0
        if count == 0:
            count = buffer.size() // 20
        for _ in range(count):
            if buffer.eof():
                break
            p = Portal.from_buffer(buffer)
            self.portals.append(p)
        print(f"Processed {len(self.portals)} portals")

    def _process_portal_vertices(self, chunk):
        buffer = chunk.buffer
        count = buffer.size() // 12
        for _ in range(count):
            if buffer.eof():
                break
            pv = PortalVertex.from_buffer(buffer)
            # ✅ تم إزالة swizzle من هنا - سيتم تطبيقه عند التصدير فقط
            self.portal_vertices.append(pv)
        print(f"Processed {len(self.portal_vertices)} portal vertices")

    def _process_portal_faces(self, chunk):
        buffer = chunk.buffer
        count = buffer.size() // 12
        for _ in range(count):
            if buffer.eof():
                break
            pf = PortalFace.from_buffer(buffer)
            self.portal_faces.append(pf)
        print(f"Processed {len(self.portal_faces)} portal faces")

    def _process_render_mesh(self, chunk, loop_file):
        assert self.render_mesh_data is None, "Render mesh already exists"
        
        # قراءة RD3D
        model_type = self.model_info.model_type
        render_header = RenderMeshHeaderIGI1.from_buffer(chunk.buffer, model_type)
        
        # قراءة REND (المواد والوجوه)
        rend_chunk = loop_file.expect_chunk("REND")
        materials = []
        
        # قراءة المواد حسب نوع النموذج
        for i in range(render_header.mesh_count):
            px = rend_chunk.buffer.read_float()
            py = rend_chunk.buffer.read_float()
            pz = rend_chunk.buffer.read_float()
            
            texture_index = 0
            bump_index = -1
            reflection_index = -1
            
            if model_type == 3:  # lightmapped
                fn, fx, _5, _6, vo, vn, _9, _a, _b, _c = rend_chunk.buffer.read_fmt("10h")
                texture_index = fx  # قد يكون هذا مؤشر النسيج
                bump_index = _5
                reflection_index = _6
            else:  # rigid or skinned
                fn, fx, _5, vo, vn, _8, _9, _a = rend_chunk.buffer.read_fmt("8h")
                texture_index = fx  # مؤشر النسيج
                bump_index = _5
                reflection_index = _8
            
            # قراءة الوجوه
            faces = []
            for j in range(fn):
                f = rend_chunk.buffer.read_uint16()
                faces.append(f)
            
            # تحويل الوجوه إلى مثلثات
            triangles = []
            for j in range(0, len(faces), 3):
                if j + 2 < len(faces):
                    triangles.append([faces[j], faces[j+1], faces[j+2]])
            
            materials.append({
                "origin": [px, py, pz],
                "face_count": fn,
                "vertex_offset": vo,
                "vertex_count": vn,
                "faces": triangles,
                "texture_index": texture_index,
                "bump_index": bump_index,
                "reflection_index": reflection_index
            })
        
        print(f"Processed {len(materials)} materials with faces")
        
        # قراءة VRTX (الرؤوس)
        xtrv_chunk = loop_file.expect_chunk("VRTX")
        
        # تحديد حجم الرأس بناءً على نوع النموذج
        if model_type == 0:  # rigid
            vertex_size = 32
        elif model_type == 1:  # skinned
            # IGI1 skinned: 36 بايت (3+3+2 floats + 2 uint16)
            vertex_size = 40
        elif model_type == 3:  # lightmapped
            vertex_size = 40
        else:
            raise ValueError(f"Unknown model type: {model_type}")
        
        # في دالة _process_render_mesh
        if model_type == 0:  # rigid
            dtype = np.dtype([
                ("px", np.float32), ("py", np.float32), ("pz", np.float32),
                ("nx", np.float32), ("ny", np.float32), ("nz", np.float32),
                ("u", np.float32), ("v", np.float32)
            ])
            vertex_size = 32
        elif model_type == 1:  # skinned IGI1 - حسب المرجع
            dtype = np.dtype([
                ("px", np.float32), ("py", np.float32), ("pz", np.float32),
                ("nx", np.float32), ("ny", np.float32), ("nz", np.float32),  # _3,_4,_5
                ("u", np.float32), ("v", np.float32),                       # u0,v0
                ("u2", np.float32), ("v2", np.float32)                      # u1,v1
            ])
            vertex_size = 40
            # لكن حجم الرأس 40 بايت يعني أن هناك 4 بايت padding أو 2 uint16 إضافيين
            # نضيف padding لجعله 40 بايت
        elif model_type == 3:  # lightmapped IGI1 - تحتوي على UV2
            dtype = np.dtype([
                ("px", np.float32), ("py", np.float32), ("pz", np.float32),
                ("nx", np.float32), ("ny", np.float32), ("nz", np.float32),
                ("u", np.float32), ("v", np.float32),
                ("u2", np.float32), ("v2", np.float32)
            ])
            vertex_size = 40
        
        # قراءة البيانات الخام
        raw_data = xtrv_chunk.buffer.read(xtrv_chunk.buffer.size())

        # تحقق أن الحجم يقبل القسمة على حجم الرأس
        if len(raw_data) % vertex_size != 0:
            raise ValueError(
                f"VRTX size ({len(raw_data)}) is not aligned with vertex size ({vertex_size})!"
            )

        # تحويل إلى numpy
        vertices = np.frombuffer(raw_data, dtype=dtype)

        print(f"Render mesh: {len(vertices)} vertices")
        
        self.render_mesh_data = RenderMeshDataIGI1(render_header, materials, vertices)

    def _process_collision_mesh(self, chunk, loop_file):
        """معالجة شبكة التصادم في IGI1 مع دعم المجموعة الثانية"""
        
        # قراءة HSMC (64 بايت) - قد نحتاج لتحليلها لاحقاً
        hsmc_data = chunk.buffer.read(64)
        
        # ========== المجموعة الأولى (mesh0) ==========
        # قراءة XTVC (رؤوس الاصطدام) للمجموعة الأولى
        if loop_file.has_chunk("CVTX"):
            xtvc_chunk = loop_file.expect_chunk("CVTX")
            vertex_data = xtvc_chunk.buffer.read(xtvc_chunk.buffer.size())
            self.collision_vertices = np.frombuffer(vertex_data, CollisionVertexDtypeIGI1).copy()
            # ✅ تم إزالة swizzle - سيتم تطبيقه عند التصدير فقط
            print(f"Collision vertices 0: {len(self.collision_vertices)}")
        
        # قراءة ECFC (وجوه الاصطدام) للمجموعة الأولى
        if loop_file.has_chunk("CFCE"):
            ecfc_chunk = loop_file.expect_chunk("CFCE")
            face_data = ecfc_chunk.buffer.read(ecfc_chunk.buffer.size())
            self.collision_faces = np.frombuffer(face_data, CollisionFaceDtypeIGI1)
            print(f"Collision faces 0: {len(self.collision_faces)}")
        
        # قراءة TAMC (مواد الاصطدام) للمجموعة الأولى
        if loop_file.has_chunk("CMAT"):
            tamc_chunk = loop_file.expect_chunk("CMAT")
            material_data = tamc_chunk.buffer.read(tamc_chunk.buffer.size())
            self.collision_materials = np.frombuffer(material_data, CollisionMaterialDtypeIGI1)
            print(f"Collision materials 0: {len(self.collision_materials)}")
        
        # قراءة HPSC (مجالات الاصطدام) للمجموعة الأولى
        if loop_file.has_chunk("CSPH"):
            hpsc_chunk = loop_file.expect_chunk("CSPH")
            sphere_data = hpsc_chunk.buffer.read(hpsc_chunk.buffer.size())
            self.collision_spheres = np.frombuffer(sphere_data, CollisionSphereDtypeIGI1).copy()
            # ✅ تم إزالة swizzle - سيتم تطبيقه عند التصدير فقط
            print(f"Collision spheres 0: {len(self.collision_spheres)}")
        
        # ========== المجموعة الثانية (mesh1) - إذا كانت موجودة ==========
        # في IGI1، المجموعة الثانية تأتي بعد الأولى بنفس الترتيب
        print(f"\n   🔍 Checking for second collision mesh (mesh1) in IGI1...")
        
        # قراءة XTVC للمجموعة الثانية
        if loop_file.has_chunk("CVTX"):
            xtvc_chunk2 = loop_file.expect_chunk("CVTX")
            vertex_data2 = xtvc_chunk2.buffer.read(xtvc_chunk2.buffer.size())
            if len(vertex_data2) > 0:
                self.collision_vertices2 = np.frombuffer(vertex_data2, CollisionVertexDtypeIGI1).copy()
                # ✅ تم إزالة swizzle - سيتم تطبيقه عند التصدير فقط
                print(f"   mesh1: Found CVTX with {len(self.collision_vertices2)} vertices")
        
        # قراءة ECFC للمجموعة الثانية
        if loop_file.has_chunk("CFCE"):
            ecfc_chunk2 = loop_file.expect_chunk("CFCE")
            face_data2 = ecfc_chunk2.buffer.read(ecfc_chunk2.buffer.size())
            if len(face_data2) > 0:
                self.collision_faces2 = np.frombuffer(face_data2, CollisionFaceDtypeIGI1)
                print(f"   mesh1: Found CFCE with {len(self.collision_faces2)} faces")
        
        # قراءة TAMC للمجموعة الثانية
        if loop_file.has_chunk("CMAT"):
            tamc_chunk2 = loop_file.expect_chunk("CMAT")
            material_data2 = tamc_chunk2.buffer.read(tamc_chunk2.buffer.size())
            if len(material_data2) > 0:
                self.collision_materials2 = np.frombuffer(material_data2, CollisionMaterialDtypeIGI1)
                print(f"   mesh1: Found CMAT with {len(self.collision_materials2)} materials")
        
        # قراءة HPSC للمجموعة الثانية
        if loop_file.has_chunk("CSPH"):
            hpsc_chunk2 = loop_file.expect_chunk("CSPH")
            sphere_data2 = hpsc_chunk2.buffer.read(hpsc_chunk2.buffer.size())
            if len(sphere_data2) > 0:
                self.collision_spheres2 = np.frombuffer(sphere_data2, CollisionSphereDtypeIGI1).copy()
                # ✅ تم إزالة swizzle - سيتم تطبيقه عند التصدير فقط
                print(f"   mesh1: Found CSPH with {len(self.collision_spheres2)} spheres")
        
        # تأكيد وجود المجموعة الثانية
        if (self.collision_vertices2 is not None and len(self.collision_vertices2) > 0 and
            self.collision_faces2 is not None and len(self.collision_faces2) > 0):
            print(f"   ✅ Second collision mesh (mesh1) detected in IGI1 file")
            print(f"      Vertices: {len(self.collision_vertices2)}")
            print(f"      Faces: {len(self.collision_faces2)}")
            print(f"      Materials: {len(self.collision_materials2)}")
            print(f"      Spheres: {len(self.collision_spheres2)}")
        else:
            print(f"   ℹ️ No second collision mesh found")

    def _process_lightmap(self, chunk):
        try:
            buffer = chunk.buffer
            width = buffer.read_uint32()
            height = buffer.read_uint32()
            format_type = buffer.read_uint32()
            data_size = buffer.size()
            data = buffer.read(data_size)
            
            lightmap = LightmapData(width, height, format_type, data)
            self.lightmaps.append(lightmap)
            print(f"   Found lightmap: {width}x{height}, format={format_type}, size={data_size} bytes")
        except Exception as e:
            print(f"   Error processing lightmap: {e}")

    def _process_txan(self, chunk):
        try:
            buffer = chunk.buffer
            txan = TXANData.from_buffer(buffer)
            self.txan_data.append(txan)
            print(f"   Found TXAN chunk with {len(txan.unknown_fields)} fields")
        except Exception as e:
            print(f"   Error processing TXAN: {e}")

    def ensure_dir(self, path):
        Path(path).mkdir(parents=True, exist_ok=True)

    def export_mtl(self, out_dir, base_name, suffix, texture_name=None, has_lightmap=False, material_index=0):
        if material_index > 0:
            mtl_filename = f"{base_name}{suffix}_{material_index}.mtl"
            mat_name = f"Mat_{base_name}{suffix}_{material_index}"
        else:
            mtl_filename = f"{base_name}{suffix}.mtl"
            mat_name = f"Mat_{base_name}{suffix}"
        
        mtl_path = os.path.join(out_dir, mtl_filename)
        
        if texture_name is None:
            texture_name = f"{base_name}.tga"
        
        with open(mtl_path, "w", encoding="utf-8") as f:
            f.write(f"newmtl {mat_name}\n")
            f.write("Ns 10.0000\n")
            f.write("Ka 1.0000 1.0000 1.0000\n")
            f.write("Kd 1.0000 1.0000 1.0000\n")
            f.write("Ks 0.0000 0.0000 0.0000\n")
            f.write(f"map_Kd {texture_name}\n")
            
            if has_lightmap:
                lightmap_name = f"{base_name}_lightmap_{material_index}.png"
                f.write(f"map_Ke {lightmap_name}\n")
                
        print(f"   MTL: {mtl_filename}")
        return mtl_filename, mat_name

    def export_obj(self, out_dir, base_name, suffix, faces, vertices, 
                   has_normals=True, has_uv2=False, lightmap_uvs=None):
        obj_path = os.path.join(out_dir, f"{base_name}{suffix}.obj")
        mtl_file, mat_name = self.export_mtl(out_dir, base_name, suffix, 
                                             f"{base_name}.tga", 
                                             has_lightmap=(lightmap_uvs is not None))
        
        with open(obj_path, "w", encoding="utf-8") as f:
            f.write(f"mtllib {mtl_file}\n")
            f.write(f"o {base_name}{suffix}\n")
            
            for v in vertices:
                f.write(f"v {v['px']:.6f} {v['py']:.6f} {v['pz']:.6f}\n")
            
            if "u" in vertices.dtype.names and "v" in vertices.dtype.names:
                for v in vertices:
                    f.write(f"vt {v['u']:.6f} {1.0 - v['v']:.6f}\n")
            
            if has_normals and "nx" in vertices.dtype.names:
                for v in vertices:
                    f.write(f"vn {v['nx']:.6f} {v['ny']:.6f} {v['nz']:.6f}\n")
            
            f.write(f"usemtl {mat_name}\n")
            
            if faces is not None and len(faces) > 0:
                for face in faces:
                    if len(face) >= 3:
                        a, b, c = face[0], face[1], face[2]
                        a1 = a + 1
                        b1 = b + 1
                        c1 = c + 1
                        
                        if has_normals:
                            f.write(f"f {a1}/{a1}/{a1} {b1}/{b1}/{b1} {c1}/{c1}/{c1}\n")
                        else:
                            f.write(f"f {a1}/{a1} {b1}/{b1} {c1}/{c1}\n")
            else:
                f.write("# No faces in this mesh\n")
                
        print(f"   OBJ: {obj_path}")

    def export_render_mesh_simple(self, out_dir, base_name, export_formats=None):
        if export_formats is None:
            export_formats = ["obj"]
        
        if self.render_mesh_data is None:
            print("No render mesh data")
            return
        
        vertices = self.render_mesh_data.vertices
        materials = self.render_mesh_data.materials
        model_type = self.model_info.model_type
    
        # 🔴 السطر الأول - هنا بعد تعريف المتغيرات مباشرة
        version = "IGI1" if isinstance(self, MefModelIGI1) else "IGI2"
        
        # كود مؤقت لطباعة أول 10 رؤوس
        print("First 10 vertices raw data:")
        for i in range(min(10, len(vertices))):
            v = vertices[i]
            
            if model_type == 1 and isinstance(self, MefModelIGI1):  # فقط لشخصيات IGI1
                # طباعة مخصصة مع أسماء الحقول الجديدة
                print(f"  v{i}: px={v['px']:.2f}, py={v['py']:.2f}, pz={v['pz']:.2f}, "
                      f"nx={v['nx']:.2f}, ny={v['ny']:.2f}, nz={v['nz']:.2f}, "
                      f"u={v['u']:.2f}, v={v['v']:.2f}, "
                      f"u2={v['u2']:.2f}, v2={v['v2']:.2f}")
            else:
                # الطباعة العادية لبقية النماذج
                fields = []
                for name in v.dtype.names:
                    val = v[name]
                    if isinstance(val, np.ndarray):
                        if len(val) >= 3:
                            fields.append(f"{name}=({val[0]:.2f}, {val[1]:.2f}, {val[2]:.2f})")
                        elif len(val) == 2:
                            fields.append(f"{name}=({val[0]:.2f}, {val[1]:.2f})")
                        else:
                            fields.append(f"{name}={val}")
                    else:
                        if isinstance(val, (float, np.float32, np.float64)):
                            fields.append(f"{name}={val:.2f}")
                        elif isinstance(val, (int, np.uint16)):
                            fields.append(f"{name}={val}")
                        else:
                            fields.append(f"{name}={val}")
                print(f"  v{i}: " + ", ".join(fields))
        
        # تحويل الرؤوس إلى صيغة موحدة مع تطبيق swizzle
        dtype_out = np.dtype([
            ("px", np.float32), ("py", np.float32), ("pz", np.float32),
            ("nx", np.float32), ("ny", np.float32), ("nz", np.float32),
            ("u", np.float32), ("v", np.float32)
        ])
        
        new_verts = []
        for v in vertices:
            # استخراج الموقع
            px, py, pz = v["px"], v["py"], v["pz"]
            
            # تطبيق swizzle
            px, py, pz = self.debug_params.swizzle(px, py, pz, self.debug_params.v_scale)
            
            # استخراج الطبيعية - حسب ما هو متوفر في dtype
            if "nx" in v.dtype.names:
                nx, ny, nz = v["nx"], v["ny"], v["nz"]
            elif "_3" in v.dtype.names:
                nx, ny, nz = v["_3"], v["_4"], v["_5"]
            else:
                nx, ny, nz = 0, 0, 0
            
            # تطبيق swizzle على الطبيعيات
            nx, ny, nz = self.debug_params.swizzle(nx, ny, nz, 1.0)
            
            # استخراج إحداثيات النسيج
            u = v["u"] if "u" in v.dtype.names else 0
            vt = v["v"] if "v" in v.dtype.names else 0
            
            new_verts.append((px, py, pz, nx, ny, nz, u, vt))
        
        vertices_transformed = np.array(new_verts, dtype=dtype_out)
        
        # =====================================================
        # 🔴 أضف الكود هنا بالضبط - بعد vertices_transformed وقبل material_groups
        # =====================================================
        print(f"\n📐 تحليل النطاق المكاني:")
        px_vals = [v['px'] for v in vertices_transformed]
        py_vals = [v['py'] for v in vertices_transformed]
        pz_vals = [v['pz'] for v in vertices_transformed]
        print(f"  X: min={min(px_vals):.2f}, max={max(px_vals):.2f}, range={max(px_vals)-min(px_vals):.2f}")
        print(f"  Y: min={min(py_vals):.2f}, max={max(py_vals):.2f}, range={max(py_vals)-min(py_vals):.2f}")
        print(f"  Z: min={min(pz_vals):.2f}, max={max(pz_vals):.2f}, range={max(pz_vals)-min(pz_vals):.2f}")
        
        # 🔴 الكود التشخيصي الجديد - هنا بالضبط
        print(f"\n🔍 تحليل المواد ({len(materials)} materials):")
        for i, mat in enumerate(materials):
            vo = mat["vertex_offset"]
            vn = mat["vertex_count"]
            fn = len(mat["faces"])
            print(f"  مادة {i}: vertex_offset={vo}, vertex_count={vn}, عدد الوجوه={fn}")
            
            # اطبع أول 3 رؤوس لهذه المادة
            if vn > 0:
                print(f"    أول 3 رؤوس (بإزاحة {vo}):")
                for j in range(min(3, vn)):
                    v = vertices[vo + j]  # ✅ صحيح - يقرأ من بداية المادة
                    print(f"      رأس {vo + j}: ({v['px']:.1f}, {v['py']:.1f}, {v['pz']:.1f})")
        # =====================================================
        
        # تجهيز مجموعات المواد
        material_groups = []
        for i, mat in enumerate(materials):
            vo = mat["vertex_offset"]
            faces = []
            for face in mat["faces"]:
                a = face[0] + vo
                b = face[1] + vo
                c = face[2] + vo
                faces.append([a, b, c])
            
            texture_index = mat.get("texture_index", 0)
            material_groups.append({
                "index": i,
                "texture_index": texture_index,
                "faces": faces
            })
        
        has_normals = True
        has_uv = "u" in vertices_transformed.dtype.names
        
        # تصدير OBJ مع مواد متعددة
        if "obj" in export_formats:
            # إنشاء أطلس القوام إذا كان هناك أكثر من مادة
            atlas = None
            if len(materials) > 1:
                atlas = self.create_texture_atlas_igi1(out_dir, base_name)
                if atlas:
                    vertices_transformed = self.apply_texture_atlas_igi1(atlas, vertices_transformed, materials, base_name)
            
            self.export_obj_multi_material(out_dir, base_name, "_render", 
                                           vertices_transformed, material_groups,
                                           has_normals, has_uv, None, atlas)
        
        # تصدير DAE و glTF (دمج كل المواد)
        if "dae" in export_formats or "gltf" in export_formats:
            all_faces = []
            for mg in material_groups:
                all_faces.extend(mg["faces"])
            all_faces_array = np.array(all_faces)
            
            if "dae" in export_formats:
                dae_path = os.path.join(out_dir, f"{base_name}_render.dae")
                export_to_collada(self, dae_path, f"{base_name}_render", 
                                 vertices_transformed, all_faces_array, has_normals, has_uv)
            
            if "gltf" in export_formats:
                # تصدير glTF كامل لـ IGI1 (بدون تزين لأن IGI1 لا يدعم التزين)
                gltf_path = os.path.join(out_dir, f"{base_name}_render")
                export_to_gltf_full(self, gltf_path, f"{base_name}_render",
                                   vertices_transformed, all_faces_array,
                                   has_normals, has_uv, has_skinning=False, bones=None)


    def export_obj_multi_material(self, out_dir, base_name, suffix, 
                                  vertices, material_groups,
                                  has_normals=True, has_uv=True, lightmap_uvs=None,
                                  atlas=None):
        obj_path = os.path.join(out_dir, f"{base_name}{suffix}.obj")
        
        mtl_filename = f"{base_name}{suffix}.mtl"
        mtl_path = os.path.join(out_dir, mtl_filename)
        
        atlas_mode = ATLAS_MODE
        
        with open(mtl_path, "w", encoding="utf-8") as f:
            if atlas and atlas.has_multiple_textures() and atlas_mode == "merge":
                # ========== وضع الدمج: مادة واحدة ==========
                f.write(f"newmtl atlas_material\n")
                f.write("Ns 10.0000\n")
                f.write("Ka 1.0000 1.0000 1.0000\n")
                f.write("Kd 1.0000 1.0000 1.0000\n")
                f.write("Ks 0.0000 0.0000 0.0000\n")
                f.write(f"map_Kd {base_name}_atlas.png\n")
                print(f"   ✅ MTL mode: MERGE (single 'atlas_material')")
                
            else:
                # ========== الوضع العادي أو وضع الحفاظ ==========
                atlas_name = f"{base_name}_atlas.png" if atlas and atlas.has_multiple_textures() else None
                
                for mg in material_groups:
                    mat_index = mg["index"]
                    texture_index = mg.get("texture_index", 0)
                    texture_name = get_texture_name(texture_index, base_name, mat_index, None)
                    
                    if atlas_name:
                        texture_name = atlas_name  # فقط تغيير مسار الصورة
                    
                    mat_name = f"Mat_{base_name}{suffix}_{mat_index}"
                    
                    f.write(f"newmtl {mat_name}\n")
                    f.write("Ns 10.0000\n")
                    f.write("Ka 1.0000 1.0000 1.0000\n")
                    f.write("Kd 1.0000 1.0000 1.0000\n")
                    f.write("Ks 0.0000 0.0000 0.0000\n")
                    f.write(f"map_Kd {texture_name}\n")
                    f.write("\n")
                
                if atlas_name:
                    print(f"   ✅ MTL mode: PRESERVE (keeping {len(material_groups)} materials, using atlas)")
        
        # كتابة ملف OBJ
        with open(obj_path, "w", encoding="utf-8") as f:
            f.write(f"mtllib {mtl_filename}\n")
            f.write(f"o {base_name}{suffix}\n")
            
            # كتابة الرؤوس
            for v in vertices:
                f.write(f"v {v['px']:.6f} {v['py']:.6f} {v['pz']:.6f}\n")
            
            # كتابة إحداثيات النسيج
            if has_uv:
                for v in vertices:
                    f.write(f"vt {v['u']:.6f} {1.0 - v['v']:.6f}\n")
            
            # كتابة الطبيعيات
            if has_normals:
                for v in vertices:
                    f.write(f"vn {v['nx']:.6f} {v['ny']:.6f} {v['nz']:.6f}\n")
            
            # كتابة الوجوه
            if atlas and atlas.has_multiple_textures() and atlas_mode == "merge":
                # وضع الدمج: usemtl واحد فقط
                f.write(f"usemtl atlas_material\n")
                for mg in material_groups:
                    for face in mg["faces"]:
                        if len(face) >= 3:
                            a, b, c = face[0], face[1], face[2]
                            a1, b1, c1 = a+1, b+1, c+1
                            
                            if has_normals:
                                f.write(f"f {a1}/{a1}/{a1} {b1}/{b1}/{b1} {c1}/{c1}/{c1}\n")
                            else:
                                f.write(f"f {a1}/{a1} {b1}/{b1} {c1}/{c1}\n")
            else:
                # وضع الحفاظ: usemtl لكل مادة
                for mg in material_groups:
                    mat_index = mg["index"]
                    mat_name = f"Mat_{base_name}{suffix}_{mat_index}"
                    f.write(f"usemtl {mat_name}\n")
                    
                    for face in mg["faces"]:
                        if len(face) >= 3:
                            a, b, c = face[0], face[1], face[2]
                            a1, b1, c1 = a+1, b+1, c+1
                            
                            if has_normals:
                                f.write(f"f {a1}/{a1}/{a1} {b1}/{b1}/{b1} {c1}/{c1}/{c1}\n")
                            else:
                                f.write(f"f {a1}/{a1} {b1}/{b1} {c1}/{c1}\n")
                                
        print(f"   OBJ (multi-material): {obj_path}")
        print(f"   MTL (multi-material): {mtl_path}")


    def export_render_mesh(self, out_dir, base_name, export_formats=None):
        if export_formats is None:
            export_formats = ["obj"]
        self.export_render_mesh_simple(out_dir, base_name, export_formats)

    def export_collision_mesh(self, out_dir, base_name, index=0, export_formats=None):
        if export_formats is None:
            export_formats = ["obj"]
        
        # اختيار المجموعة المناسبة
        if index == 0:
            if self.collision_vertices is None or self.collision_faces is None:
                return
            vertices = self.collision_vertices
            faces = self.collision_faces
            suffix = "_col"  # ✅ للمجموعة الأولى
        else:
            if self.collision_vertices2 is None or self.collision_faces2 is None:
                return
            vertices = self.collision_vertices2
            faces = self.collision_faces2
            suffix = "_col1"  # ✅ للمجموعة الثانية
        
        # تحويل رؤوس الاصطدام مع تطبيق swizzle
        dtype_out = np.dtype([
            ("px", np.float32), ("py", np.float32), ("pz", np.float32),
            ("nx", np.float32), ("ny", np.float32), ("nz", np.float32),
            ("u", np.float32), ("v", np.float32)
        ])
        
        new_verts = []
        for v in vertices:
            px, py, pz = self.debug_params.swizzle(v["f0"], v["f1"], v["f2"], self.debug_params.v_scale)
            new_verts.append((px, py, pz, 0, 0, 0, 0, 0))
        
        verts_arr = np.array(new_verts, dtype=dtype_out)
        
        # تحويل الوجوه
        faces_list = []
        for f in faces:
            faces_list.append([f["a"], f["b"], f["c"]])
        
        faces_arr = np.array(faces_list)
        
        if "obj" in export_formats:
            self.export_obj(out_dir, base_name, suffix, faces_arr, verts_arr, has_normals=False)
        
        if "dae" in export_formats:
            dae_path = os.path.join(out_dir, f"{base_name}{suffix}.dae")
            export_to_collada(self, dae_path, f"{base_name}{suffix}", verts_arr, faces_arr, False, False)
        
        if "gltf" in export_formats:
            gltf_path = os.path.join(out_dir, f"{base_name}{suffix}")
            export_to_gltf(self, gltf_path, f"{base_name}{suffix}", verts_arr, faces_arr, False, False)

    def export_lightmaps(self, out_dir, base_name, lightmap_format="png"):
        if not self.lightmaps:
            return
        
        lightmap_dir = os.path.join(out_dir, "lightmaps")
        self.ensure_dir(lightmap_dir)
        
        for i, lightmap in enumerate(self.lightmaps):
            tga_path = os.path.join(lightmap_dir, f"{base_name}_lightmap_{i}.tga")
            try:
                with open(tga_path, "wb") as f:
                    f.write(lightmap.data)
                print(f"   Lightmap {i} (TGA): {tga_path} ({lightmap.width}x{lightmap.height})")
            except Exception as e:
                print(f"   Error saving TGA lightmap {i}: {e}")
            
            if lightmap_format in ["png", "both"] and PIL_AVAILABLE:
                png_path = os.path.join(lightmap_dir, f"{base_name}_lightmap_{i}.png")
                if save_lightmap_as_png(lightmap, png_path):
                    print(f"   Lightmap {i} (PNG): {png_path}")
            
            if lightmap_format in ["dds", "both"]:
                dds_path = os.path.join(lightmap_dir, f"{base_name}_lightmap_{i}.dds")
                if save_lightmap_as_dds(lightmap, dds_path):
                    print(f"   Lightmap {i} (DDS): {dds_path}")

    def export_attachments(self, out_dir, base_name):
        if not self.attachments:
            return
        
        att_path = os.path.join(out_dir, f"{base_name}_attachments.txt")
        with open(att_path, "w", encoding="utf-8") as f:
            f.write("# Attachment points (IGI1)\n")
            f.write("# Format: name\tposition (x,y,z)\n\n")
            for a in self.attachments:
                # ✅ تطبيق swizzle على مواقع المرفقات هنا
                px, py, pz = self.debug_params.swizzle(a.pos.x, a.pos.y, a.pos.z, self.debug_params.v_scale)
                f.write(f"{a.name}\t({px:.2f}, {py:.2f}, {pz:.2f})\n")
        print(f"   Attachments: {att_path}")

    def export_extra_data(self, out_dir, base_name):
        if self.magic_vertices:
            path = os.path.join(out_dir, f"{base_name}_magic_vertices.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write("# Magic Vertices (XTVM)\n")
                f.write("# Format: pos_x pos_y pos_z type\n\n")
                for mv in self.magic_vertices:
                    px, py, pz = self.debug_params.swizzle(mv.pos.x, mv.pos.y, mv.pos.z, self.debug_params.v_scale)
                    f.write(f"{px:.6f} {py:.6f} {pz:.6f} {mv.type}\n")
            print(f"   Magic vertices: {path}")
        
        if self.portals:
            path = os.path.join(out_dir, f"{base_name}_portals.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write("# Portals (TROP)\n")
                f.write("# Format: start_vertex num_vertices start_face num_faces portal_id\n\n")
                for p in self.portals:
                    f.write(f"{p.start_vertex} {p.num_vertices} {p.start_face} {p.num_faces} {p.portal_id}\n")
                
                if self.portal_vertices:
                    f.write("\n# Portal Vertices (XVTP)\n")
                    f.write("# Format: index pos_x pos_y pos_z\n\n")
                    for i, pv in enumerate(self.portal_vertices):
                        px, py, pz = self.debug_params.swizzle(pv.pos.x, pv.pos.y, pv.pos.z, self.debug_params.v_scale)
                        f.write(f"{i} {px:.6f} {py:.6f} {pz:.6f}\n")
                
                if self.portal_faces:
                    f.write("\n# Portal Faces (CFTP)\n")
                    f.write("# Format: a b c\n\n")
                    for pf in self.portal_faces:
                        f.write(f"{pf.a} {pf.b} {pf.c}\n")
            print(f"   Portals: {path}")
        
        if self.txan_data:
            path = os.path.join(out_dir, f"{base_name}_txan.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write("# TXAN Animation Data\n")
                f.write("# Format: 28 uint32 fields\n\n")
                for i, txan in enumerate(self.txan_data):
                    f.write(f"TXAN {i}:\n")
                    f.write("Fields: " + " ".join(str(x) for x in txan.unknown_fields) + "\n\n")
            print(f"   TXAN data: {path}")
    
    def export_xtvc_info_igi1_mesh1(self, out_dir: str, base_name: str):
        """تصدير رؤوس التصادم للمجموعة الثانية (mesh1) لـ IGI1"""
        if self.collision_vertices2 is None or len(self.collision_vertices2) == 0:
            return
        
        vertices = self.collision_vertices2
        
        # تحويل إلى قائمة قواميس مع تطبيق swizzle
        verts_list = []
        for i, v in enumerate(vertices):
            px, py, pz = self.debug_params.swizzle(v["f0"], v["f1"], v["f2"], self.debug_params.v_scale)
            verts_list.append({
                "index": i,
                "f0": px,
                "f1": py,
                "f2": pz,
                "f3": v["f3"]
            })
        
        # JSON
        json_path = os.path.join(out_dir, f"{base_name}_xtvc_mesh1.json")
        data = convert_to_json_serializable({
            "mesh": "mesh1",
            "vertex_count": len(verts_list),
            "vertices": verts_list
        })
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   XTVC mesh1 (JSON): {json_path}")
        
        # TXT
        txt_path = os.path.join(out_dir, f"{base_name}_xtvc_mesh1.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# XTVC (Collision Mesh Vertices) - IGI1 - mesh1\n")
            f.write(f"Total Vertices: {len(verts_list)}\n\n")
            for i, v in enumerate(verts_list):
                f.write(f"Vertex {i:6d}: ({v['f0']:8.2f}, {v['f1']:8.2f}, {v['f2']:8.2f}, {v['f3']:8.2f})\n")
        print(f"   XTVC mesh1 (TXT): {txt_path}")
        
        # CSV
        csv_path = os.path.join(out_dir, f"{base_name}_xtvc_mesh1.csv")
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write("index,f0,f1,f2,f3\n")
            for i, v in enumerate(verts_list):
                f.write(f"{i},{v['f0']:.6f},{v['f1']:.6f},{v['f2']:.6f},{v['f3']:.6f}\n")
        print(f"   XTVC mesh1 (CSV): {csv_path}")
        
        # OBJ
        obj_path = os.path.join(out_dir, f"{base_name}_xtvc_mesh1.obj")
        with open(obj_path, 'w', encoding='utf-8') as f:
            f.write(f"# XTVC Collision Vertices - IGI1 - mesh1\n")
            f.write(f"# {len(verts_list)} vertices\n\n")
            f.write(f"o {base_name}_xtvc_mesh1\n")
            for v in verts_list:
                f.write(f"v {v['f0']:.6f} {v['f1']:.6f} {v['f2']:.6f}\n")
            if verts_list:
                f.write("p 1\n")
        print(f"   XTVC mesh1 as points (OBJ): {obj_path}")

    def export_ecfc_info_igi1_mesh1(self, out_dir: str, base_name: str):
        """تصدير وجوه التصادم للمجموعة الثانية (mesh1) لـ IGI1"""
        if self.collision_faces2 is None or len(self.collision_faces2) == 0:
            return
        
        faces = self.collision_faces2
        
        # تحويل إلى قائمة قواميس
        faces_list = []
        for i, f in enumerate(faces):
            faces_list.append({
                "index": i,
                "a": int(f["a"]),
                "b": int(f["b"]),
                "c": int(f["c"]),
                "material": int(f["mat"])
            })
        
        # JSON
        json_path = os.path.join(out_dir, f"{base_name}_ecfc_mesh1.json")
        data = convert_to_json_serializable({
            "mesh": "mesh1",
            "face_count": len(faces_list),
            "faces": faces_list
        })
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   ECFC mesh1 (JSON): {json_path}")
        
        # TXT
        txt_path = os.path.join(out_dir, f"{base_name}_ecfc_mesh1.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# ECFC (Collision Mesh Faces) - IGI1 - mesh1\n")
            f.write(f"Total Faces: {len(faces_list)}\n\n")
            for i, face in enumerate(faces_list):
                f.write(f"Face {i:6d}: ({face['a']:6d}, {face['b']:6d}, {face['c']:6d}), material={face['material']:4d}\n")
        print(f"   ECFC mesh1 (TXT): {txt_path}")
        
        # CSV
        csv_path = os.path.join(out_dir, f"{base_name}_ecfc_mesh1.csv")
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write("index,a,b,c,material\n")
            for i, face in enumerate(faces_list):
                f.write(f"{i},{face['a']},{face['b']},{face['c']},{face['material']}\n")
        print(f"   ECFC mesh1 (CSV): {csv_path}")

    def export_tamc_info_igi1_mesh1(self, out_dir: str, base_name: str):
        """تصدير مواد التصادم للمجموعة الثانية (mesh1) لـ IGI1"""
        if self.collision_materials2 is None or len(self.collision_materials2) == 0:
            return
        
        materials = self.collision_materials2
        
        # تحويل إلى قائمة قواميس
        mats_list = []
        for i, mat in enumerate(materials):
            mats_list.append({
                "index": i,
                "fields": [int(mat[name]) for name in mat.dtype.names]
            })
        
        # JSON
        json_path = os.path.join(out_dir, f"{base_name}_tamc_mesh1.json")
        data = convert_to_json_serializable({
            "mesh": "mesh1",
            "material_count": len(mats_list),
            "materials": mats_list
        })
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   TAMC mesh1 (JSON): {json_path}")
        
        # TXT
        txt_path = os.path.join(out_dir, f"{base_name}_tamc_mesh1.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# TAMC (Collision Mesh Materials) - IGI1 - mesh1\n")
            f.write(f"Total Materials: {len(mats_list)}\n\n")
            for i, mat in enumerate(mats_list):
                f.write(f"Material {i:3d}: fields = {mat['fields']}\n")
        print(f"   TAMC mesh1 (TXT): {txt_path}")
        
        # CSV
        csv_path = os.path.join(out_dir, f"{base_name}_tamc_mesh1.csv")
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write("index,f0,f1,f2,f3,f4,f5\n")
            for i, mat in enumerate(mats_list):
                f.write(f"{i},{mat['fields'][0]},{mat['fields'][1]},{mat['fields'][2]},"
                       f"{mat['fields'][3]},{mat['fields'][4]},{mat['fields'][5]}\n")
        print(f"   TAMC mesh1 (CSV): {csv_path}")

    def export_hpsc_info_igi1_mesh1(self, out_dir: str, base_name: str):
        """تصدير كرات التصادم للمجموعة الثانية (mesh1) لـ IGI1"""
        if self.collision_spheres2 is None or len(self.collision_spheres2) == 0:
            return
        
        spheres = self.collision_spheres2
        
        # تحويل إلى قائمة قواميس مع تطبيق swizzle على المركز فقط
        spheres_list = []
        for i, s in enumerate(spheres):
            cx, cy, cz = self.debug_params.swizzle(s["f0"], s["f1"], s["f2"], self.debug_params.v_scale)
            spheres_list.append({
                "index": i,
                "f0": cx,
                "f1": cy,
                "f2": cz,
                "f3": s["f3"],
                "s0": int(s["s0"]),
                "s1": int(s["s1"]),
                "s2": int(s["s2"]),
                "s3": int(s["s3"])
            })
        
        # JSON
        json_path = os.path.join(out_dir, f"{base_name}_hpsc_mesh1.json")
        data = convert_to_json_serializable({
            "mesh": "mesh1",
            "sphere_count": len(spheres_list),
            "spheres": spheres_list
        })
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   HPSC mesh1 (JSON): {json_path}")
        
        # TXT
        txt_path = os.path.join(out_dir, f"{base_name}_hpsc_mesh1.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# HPSC (Collision Mesh Spheres) - IGI1 - mesh1\n")
            f.write(f"Total Spheres: {len(spheres_list)}\n\n")
            for i, s in enumerate(spheres_list):
                f.write(f"Sphere {i:6d}: ({s['f0']:8.2f}, {s['f1']:8.2f}, {s['f2']:8.2f}, {s['f3']:8.2f}), "
                       f"({s['s0']:4d}, {s['s1']:4d}, {s['s2']:4d}, {s['s3']:4d})\n")
        print(f"   HPSC mesh1 (TXT): {txt_path}")
        
        # CSV
        csv_path = os.path.join(out_dir, f"{base_name}_hpsc_mesh1.csv")
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write("index,f0,f1,f2,f3,s0,s1,s2,s3\n")
            for i, s in enumerate(spheres_list):
                f.write(f"{i},{s['f0']:.6f},{s['f1']:.6f},{s['f2']:.6f},{s['f3']:.6f},"
                       f"{s['s0']},{s['s1']},{s['s2']},{s['s3']}\n")
        print(f"   HPSC mesh1 (CSV): {csv_path}")
        
        # OBJ
        obj_path = os.path.join(out_dir, f"{base_name}_hpsc_mesh1.obj")
        with open(obj_path, 'w', encoding='utf-8') as f:
            f.write(f"# HPSC Collision Spheres - IGI1 - mesh1\n")
            f.write(f"# {len(spheres_list)} spheres\n\n")
            f.write(f"o {base_name}_hpsc_mesh1\n")
            for i, s in enumerate(spheres_list):
                f.write(f"v {s['f0']:.6f} {s['f1']:.6f} {s['f2']:.6f}\n")
                f.write(f"# sphere {i}: radius={s['f3']:.2f}, ({s['s0']},{s['s1']},{s['s2']},{s['s3']})\n")
            if spheres_list:
                f.write("p 1\n")
        print(f"   HPSC mesh1 spheres as points (OBJ): {obj_path}")
    
    def export_collision_materials(self, out_dir: str, base_name: str):
        """تصدير مواد التصادم كملف JSON"""
        # ✅ التعديل: التحقق الصحيح للمصفوفات والقوائم
        if self.collision_materials is None:
            return
        
        # التحقق من الطول - يعمل مع القوائم والمصفوفات
        if len(self.collision_materials) == 0:
            return
        
        # تحويل المواد إلى قواميس قابلة للتصدير
        materials_list = []
        for i, mat in enumerate(self.collision_materials):
            # IGI1 collision material
            fields = [int(mat[name]) for name in mat.dtype.names]
            mat_dict = {
                "index": i,
                "fields": fields
            }
            materials_list.append(mat_dict)
        
        # تصدير كـ JSON
        json_path = os.path.join(out_dir, f"{base_name}_collision_materials.json")
        data = convert_to_json_serializable(materials_list)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   Collision materials (JSON): {json_path}")
        
        # أيضاً تصدير كملخص نصي
        txt_path = os.path.join(out_dir, f"{base_name}_collision_materials.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# Collision Materials (IGI1)\n")
            f.write("# Format: 6 int16 fields\n\n")
            for i, mat_dict in enumerate(materials_list):
                f.write(f"Material {i}:\n")
                f.write(f"  fields: {mat_dict['fields']}\n\n")
        print(f"   Collision materials (TXT): {txt_path}")
    
    def export_collision_spheres(self, out_dir: str, base_name: str):
        """تصدير كرات التصادم كملف نصي مع عرض المركز ونصف القطر"""
        if not hasattr(self, 'collision_spheres') or self.collision_spheres is None or len(self.collision_spheres) == 0:
            return
        
        spheres = self.collision_spheres
        
        # تصدير كملخص نصي مع تطبيق swizzle
        txt_path = os.path.join(out_dir, f"{base_name}_collision_spheres.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# Collision Spheres (IGI1)\n")
            f.write("# Format: center_x center_y center_z radius  s0 s1 s2 s3\n")
            f.write("# Note: f0,f1,f2 = center (after swizzle), f3 = radius (unchanged)\n\n")
            
            for i, sphere in enumerate(spheres):
                cx, cy, cz = self.debug_params.swizzle(sphere["f0"], sphere["f1"], sphere["f2"], self.debug_params.v_scale)
                f3 = sphere["f3"]
                s0, s1, s2, s3 = sphere["s0"], sphere["s1"], sphere["s2"], sphere["s3"]
                f.write(f"Sphere {i:4d}: center=({cx:8.2f}, {cy:8.2f}, {cz:8.2f}), radius={f3:8.2f}, "
                       f"({s0:4d}, {s1:4d}, {s2:4d}, {s3:4d})\n")
        
        print(f"   Collision spheres (TXT): {txt_path}")

    # ========== دوال HSMC لـ IGI1 ==========
    def export_hsmc_info_igi1_improved(self, out_dir: str, base_name: str):
        """تصدير معلومات HSMC (Collision Mesh Header) لـ IGI1 كملف JSON ونصي"""
        if not hasattr(self, 'collision_vertices') or self.collision_vertices is None:
            return
        
        # بيانات محسوبة من المجموعات الموجودة
        vertex_count = len(self.collision_vertices) if self.collision_vertices is not None else 0
        face_count = len(self.collision_faces) if self.collision_faces is not None else 0
        material_count = len(self.collision_materials) if hasattr(self, 'collision_materials') and self.collision_materials is not None else 0
        sphere_count = len(self.collision_spheres) if hasattr(self, 'collision_spheres') and self.collision_spheres is not None else 0
        
        # هيكل HSMC في IGI1 (كما في المرجع)
        hsmc_dict = {
            "mesh0": {
                "face_count": face_count,
                "vertex_count": vertex_count,
                "material_count": material_count,
                "sphere_count": sphere_count,
                "_0": 0, "_1": 0, "_2": 0, "_3": 0
            },
            "mesh1": {
                "face_count": 0,
                "vertex_count": 0,
                "material_count": 0,
                "sphere_count": 0,
                "_0": 0, "_1": 0, "_2": 0, "_3": 0
            }
        }
        
        # تصدير كـ JSON
        json_path = os.path.join(out_dir, f"{base_name}_hsmc.json")
        data = convert_to_json_serializable(hsmc_dict)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   HSMC (JSON): {json_path}")
        
        # تصدير كملخص نصي
        txt_path = os.path.join(out_dir, f"{base_name}_hsmc.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# HSMC (Collision Mesh Header) - IGI1\n")
            f.write("# Values estimated from available collision data\n")
            f.write("=" * 50 + "\n\n")
            
            f.write("Mesh 0 (Primary Collision Mesh):\n")
            f.write("-" * 30 + "\n")
            f.write(f"  Face Count      : {face_count}\n")
            f.write(f"  Vertex Count    : {vertex_count}\n")
            f.write(f"  Material Count  : {material_count}\n")
            f.write(f"  Sphere Count    : {sphere_count}\n")
            f.write(f"  _0              : 0\n")
            f.write(f"  _1              : 0\n")
            f.write(f"  _2              : 0\n")
            f.write(f"  _3              : 0\n\n")
            
            f.write("Mesh 1 (Secondary Collision Mesh - not used in IGI1):\n")
            f.write("-" * 30 + "\n")
            f.write(f"  Face Count      : 0\n")
            f.write(f"  Vertex Count    : 0\n")
            f.write(f"  Material Count  : 0\n")
            f.write(f"  Sphere Count    : 0\n")
            f.write(f"  _0              : 0\n")
            f.write(f"  _1              : 0\n")
            f.write(f"  _2              : 0\n")
            f.write(f"  _3              : 0\n")
        
        print(f"   HSMC (TXT): {txt_path}")

    # ========== دوال قطع التصادم الجديدة لـ IGI1 ==========
    def export_xtvc_info_igi1(self, out_dir: str, base_name: str):
        """تصدير رؤوس التصادم (XTVC) لـ IGI1 كملف JSON ونصي (عرض كامل)"""
        if not hasattr(self, 'collision_vertices') or self.collision_vertices is None:
            return
        
        vertices = self.collision_vertices
        
        # 1. تحويل إلى قائمة قواميس مع تطبيق swizzle
        verts_list = []
        for i, v in enumerate(vertices):
            px, py, pz = self.debug_params.swizzle(v["f0"], v["f1"], v["f2"], self.debug_params.v_scale)
            verts_list.append({
                "index": i,
                "f0": px,
                "f1": py,
                "f2": pz,
                "f3": v["f3"]
            })
        
        # 2. تصدير كـ JSON
        json_path = os.path.join(out_dir, f"{base_name}_xtvc.json")
        data = convert_to_json_serializable({
            "vertex_count": len(verts_list),
            "vertices": verts_list
        })
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   XTVC (JSON): {json_path}")
        
        # 3. تصدير كملخص نصي (بدون اختصار)
        txt_path = os.path.join(out_dir, f"{base_name}_xtvc.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# XTVC (Collision Mesh Vertices) - IGI1\n")
            f.write("Format: 4 floats per vertex (f0,f1,f2,f3)\n")
            f.write(f"Total Vertices: {len(verts_list)}\n\n")
            
            # عرض جميع الرؤوس بدون اختصار
            for i, v in enumerate(verts_list):
                f.write(f"Vertex {i:6d}: ({v['f0']:8.2f}, {v['f1']:8.2f}, {v['f2']:8.2f}, {v['f3']:8.2f})\n")
        
        print(f"   XTVC (TXT): {txt_path}")
        
        # 4. تصدير كـ CSV
        csv_path = os.path.join(out_dir, f"{base_name}_xtvc.csv")
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write("index,f0,f1,f2,f3\n")
            for i, v in enumerate(verts_list):
                f.write(f"{i},{v['f0']:.6f},{v['f1']:.6f},{v['f2']:.6f},{v['f3']:.6f}\n")
        print(f"   XTVC (CSV): {csv_path}")
        
        # 5. تصدير كـ OBJ (للتصور - نعتبر f0,f1,f2 هي الموضع)
        obj_path = os.path.join(out_dir, f"{base_name}_xtvc.obj")
        with open(obj_path, 'w', encoding='utf-8') as f:
            f.write(f"# XTVC Collision Vertices - IGI1\n")
            f.write(f"# {len(verts_list)} vertices\n\n")
            f.write(f"o {base_name}_xtvc\n")
            
            for v in verts_list:
                f.write(f"v {v['f0']:.6f} {v['f1']:.6f} {v['f2']:.6f}\n")
            
            # لا توجد وجوه، فقط نقاط
            if verts_list:
                f.write("p 1\n")
        
        print(f"   XTVC as points (OBJ): {obj_path}")

    def export_ecfc_info_igi1(self, out_dir: str, base_name: str):
        """تصدير وجوه التصادم (ECFC) لـ IGI1 كملف JSON ونصي (عرض كامل)"""
        if not hasattr(self, 'collision_faces') or self.collision_faces is None:
            return
        
        faces = self.collision_faces
        
        # 1. تحويل إلى قائمة قواميس
        faces_list = []
        for i, f in enumerate(faces):
            faces_list.append({
                "index": i,
                "a": int(f["a"]),
                "b": int(f["b"]),
                "c": int(f["c"]),
                "material": int(f["mat"])
            })
        
        # 2. تصدير كـ JSON
        json_path = os.path.join(out_dir, f"{base_name}_ecfc.json")
        data = convert_to_json_serializable({
            "face_count": len(faces_list),
            "faces": faces_list
        })
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   ECFC (JSON): {json_path}")
        
        # 3. تصدير كملخص نصي (بدون اختصار)
        txt_path = os.path.join(out_dir, f"{base_name}_ecfc.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# ECFC (Collision Mesh Faces) - IGI1\n")
            f.write("Format: a, b, c (vertex indices), material\n")
            f.write(f"Total Faces: {len(faces_list)}\n\n")
            
            # عرض جميع الوجوه بدون اختصار
            for i, face in enumerate(faces_list):
                f.write(f"Face {i:6d}: ({face['a']:6d}, {face['b']:6d}, {face['c']:6d}), material={face['material']:4d}\n")
        
        print(f"   ECFC (TXT): {txt_path}")
        
        # 4. تصدير كـ CSV
        csv_path = os.path.join(out_dir, f"{base_name}_ecfc.csv")
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write("index,a,b,c,material\n")
            for i, face in enumerate(faces_list):
                f.write(f"{i},{face['a']},{face['b']},{face['c']},{face['material']}\n")
        print(f"   ECFC (CSV): {csv_path}")

    def export_tamc_info_igi1(self, out_dir: str, base_name: str):
        """تصدير مواد التصادم (TAMC) لـ IGI1 كملف JSON ونصي"""
        if not hasattr(self, 'collision_materials') or self.collision_materials is None or len(self.collision_materials) == 0:
            return
        
        materials = self.collision_materials
        
        # 1. تحويل إلى قائمة قواميس
        mats_list = []
        for i, mat in enumerate(materials):
            mats_list.append({
                "index": i,
                "fields": [int(mat[name]) for name in mat.dtype.names]
            })
        
        # 2. تصدير كـ JSON
        json_path = os.path.join(out_dir, f"{base_name}_tamc.json")
        data = convert_to_json_serializable({
            "material_count": len(mats_list),
            "materials": mats_list
        })
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   TAMC (JSON): {json_path}")
        
        # 3. تصدير كملخص نصي
        txt_path = os.path.join(out_dir, f"{base_name}_tamc.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# TAMC (Collision Mesh Materials) - IGI1\n")
            f.write("Format: 6 int16 fields\n")
            f.write(f"Total Materials: {len(mats_list)}\n\n")
            
            for i, mat in enumerate(mats_list):
                f.write(f"Material {i:3d}: fields = {mat['fields']}\n")
        
        print(f"   TAMC (TXT): {txt_path}")
        
        # 4. تصدير كـ CSV
        csv_path = os.path.join(out_dir, f"{base_name}_tamc.csv")
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write("index,f0,f1,f2,f3,f4,f5\n")
            for i, mat in enumerate(mats_list):
                f.write(f"{i},{mat['fields'][0]},{mat['fields'][1]},{mat['fields'][2]},"
                       f"{mat['fields'][3]},{mat['fields'][4]},{mat['fields'][5]}\n")
        print(f"   TAMC (CSV): {csv_path}")

    def export_hpsc_info_igi1(self, out_dir: str, base_name: str):
        """تصدير كرات التصادم (HPSC) لـ IGI1 كملف JSON ونصي (عرض كامل)"""
        if not hasattr(self, 'collision_spheres') or self.collision_spheres is None or len(self.collision_spheres) == 0:
            return
        
        spheres = self.collision_spheres
        
        # 1. تحويل إلى قائمة قواميس مع تطبيق swizzle على المركز فقط
        spheres_list = []
        for i, s in enumerate(spheres):
            cx, cy, cz = self.debug_params.swizzle(s["f0"], s["f1"], s["f2"], self.debug_params.v_scale)
            spheres_list.append({
                "index": i,
                "f0": cx,
                "f1": cy,
                "f2": cz,
                "f3": s["f3"],
                "s0": int(s["s0"]),
                "s1": int(s["s1"]),
                "s2": int(s["s2"]),
                "s3": int(s["s3"])
            })
        
        # 2. تصدير كـ JSON
        json_path = os.path.join(out_dir, f"{base_name}_hpsc.json")
        data = convert_to_json_serializable({
            "sphere_count": len(spheres_list),
            "spheres": spheres_list
        })
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   HPSC (JSON): {json_path}")
        
        # 3. تصدير كملخص نصي (بدون اختصار)
        txt_path = os.path.join(out_dir, f"{base_name}_hpsc.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# HPSC (Collision Mesh Spheres) - IGI1\n")
            f.write("Format: f0,f1,f2,f3 (floats), s0,s1,s2,s3 (int16)\n")
            f.write(f"Total Spheres: {len(spheres_list)}\n\n")
            
            # عرض جميع الكرات بدون اختصار
            for i, s in enumerate(spheres_list):
                f.write(f"Sphere {i:6d}: ({s['f0']:8.2f}, {s['f1']:8.2f}, {s['f2']:8.2f}, {s['f3']:8.2f}), "
                       f"({s['s0']:4d}, {s['s1']:4d}, {s['s2']:4d}, {s['s3']:4d})\n")
        
        print(f"   HPSC (TXT): {txt_path}")
        
        # 4. تصدير كـ CSV
        csv_path = os.path.join(out_dir, f"{base_name}_hpsc.csv")
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write("index,f0,f1,f2,f3,s0,s1,s2,s3\n")
            for i, s in enumerate(spheres_list):
                f.write(f"{i},{s['f0']:.6f},{s['f1']:.6f},{s['f2']:.6f},{s['f3']:.6f},"
                       f"{s['s0']},{s['s1']},{s['s2']},{s['s3']}\n")
        print(f"   HPSC (CSV): {csv_path}")
        
        # 5. تصدير كـ OBJ للتصور (نعتبر f0,f1,f2 هي المركز، f3 هو نصف القطر)
        obj_path = os.path.join(out_dir, f"{base_name}_hpsc.obj")
        with open(obj_path, 'w', encoding='utf-8') as f:
            f.write(f"# HPSC Collision Spheres - IGI1\n")
            f.write(f"# {len(spheres_list)} spheres\n\n")
            f.write(f"o {base_name}_hpsc\n")
            
            for i, s in enumerate(spheres_list):
                f.write(f"v {s['f0']:.6f} {s['f1']:.6f} {s['f2']:.6f}\n")
                f.write(f"# sphere {i}: radius={s['f3']:.2f}, s0={s['s0']}, s1={s['s1']}, s2={s['s2']}, s3={s['s3']}\n")
            
            if spheres_list:
                f.write("p 1\n")
        
        print(f"   HPSC spheres as points (OBJ): {obj_path}")

    def export_all_collision_mesh_data_igi1(self, out_dir: str, base_name: str):
        """تصدير جميع قطع التصادم (HSMC, XTVC, ECFC, TAMC, HPSC) لـ IGI1"""
        
        print(f"\n   📦 Exporting all IGI1 collision mesh data...")
        
        # 1. HSMC (مشترك)
        self.export_hsmc_info_igi1_improved(out_dir, base_name)
        
        # ========== المجموعة الأولى (mesh0) ==========
        print(f"\n   📦 Exporting mesh0 collision data...")
        
        # XTVC للمجموعة الأولى
        if hasattr(self, 'collision_vertices') and self.collision_vertices is not None:
            self.export_xtvc_info_igi1(out_dir, base_name)
        
        # ECFC للمجموعة الأولى
        if hasattr(self, 'collision_faces') and self.collision_faces is not None:
            self.export_ecfc_info_igi1(out_dir, base_name)
        
        # TAMC للمجموعة الأولى
        if hasattr(self, 'collision_materials') and self.collision_materials is not None and len(self.collision_materials) > 0:
            self.export_tamc_info_igi1(out_dir, base_name)
        
        # HPSC للمجموعة الأولى
        if hasattr(self, 'collision_spheres') and self.collision_spheres is not None and len(self.collision_spheres) > 0:
            self.export_hpsc_info_igi1(out_dir, base_name)
        
        # ========== المجموعة الثانية (mesh1) - إذا وجدت ==========
        if (hasattr(self, 'collision_vertices2') and self.collision_vertices2 is not None and len(self.collision_vertices2) > 0):
            print(f"\n   📦 Exporting mesh1 collision data...")
            
            # XTVC للمجموعة الثانية
            self.export_xtvc_info_igi1_mesh1(out_dir, base_name)
            
            # ECFC للمجموعة الثانية
            if hasattr(self, 'collision_faces2') and self.collision_faces2 is not None:
                self.export_ecfc_info_igi1_mesh1(out_dir, base_name)
            
            # TAMC للمجموعة الثانية
            if hasattr(self, 'collision_materials2') and self.collision_materials2 is not None and len(self.collision_materials2) > 0:
                self.export_tamc_info_igi1_mesh1(out_dir, base_name)
            
            # HPSC للمجموعة الثانية
            if hasattr(self, 'collision_spheres2') and self.collision_spheres2 is not None and len(self.collision_spheres2) > 0:
                self.export_hpsc_info_igi1_mesh1(out_dir, base_name)
        
        print(f"   ✅ IGI1 collision mesh data exported successfully")

    # ========== دوال بيانات الظل لـ IGI1 (للتوافق) ==========
    def export_sems_info_igi1(self, out_dir: str, base_name: str):
        """تصدير معلومات رأس نموذج الظل (SEMS) لـ IGI1 إذا وجدت"""
        if not hasattr(self, 'shadow_mesh_data') or self.shadow_mesh_data is None:
            return
        
        # IGI1 قد لا يحتوي على SEMS، لكننا نستخدم نفس البنية
        header = self.shadow_mesh_data.mesh_header
        
        sems_dict = {
            "face_offset": header.face_offset,
            "vertex_offset": header.vertex_offset,
            "edge_offset": header.edge_offset,
            "face_count": header.face_count,
            "vertex_count": header.vertex_count,
            "edge_count": header.edge_count,
            "bone_index": header.bone_index,
            "note": "Shadow models are not officially supported in IGI1"
        }
        
        json_path = os.path.join(out_dir, f"{base_name}_sems.json")
        data = convert_to_json_serializable(sems_dict)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   SEMS (IGI1) (JSON): {json_path}")
        
        txt_path = os.path.join(out_dir, f"{base_name}_sems.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# SEMS (Shadow Model Header) - IGI1\n")
            f.write("# Note: Shadow models are not officially supported in IGI1\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Face Offset    : {header.face_offset}\n")
            f.write(f"Vertex Offset  : {header.vertex_offset}\n")
            f.write(f"Edge Offset    : {header.edge_offset}\n")
            f.write(f"Face Count     : {header.face_count}\n")
            f.write(f"Vertex Count   : {header.vertex_count}\n")
            f.write(f"Edge Count     : {header.edge_count}\n")
            f.write(f"Bone Index     : {header.bone_index}\n")
        
        print(f"   SEMS (IGI1) (TXT): {txt_path}")

    def export_xtvs_info_igi1(self, out_dir: str, base_name: str):
        """تصدير رؤوس شبكة الظل (XTVS) لـ IGI1 - عرض كامل"""
        if not hasattr(self, 'shadow_mesh_data') or self.shadow_mesh_data is None or self.shadow_mesh_data.vertices is None:
            return
        
        vertices = self.shadow_mesh_data.vertices
        
        verts_list = []
        for i, v in enumerate(vertices):
            if len(v) >= 3:
                px, py, pz = self.debug_params.swizzle(v[0], v[1], v[2], self.debug_params.v_scale)
                verts_list.append({
                    "index": i,
                    "position": [px, py, pz]
                })
        
        json_path = os.path.join(out_dir, f"{base_name}_xtvs.json")
        data = convert_to_json_serializable({
            "vertex_count": len(verts_list),
            "vertices": verts_list,
            "note": "Shadow models are not officially supported in IGI1"
        })
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   XTVS (IGI1) (JSON): {json_path}")
        
        txt_path = os.path.join(out_dir, f"{base_name}_xtvs.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# XTVS (Shadow Mesh Vertices) - IGI1\n")
            f.write("# Note: Shadow models are not officially supported in IGI1\n")
            f.write(f"Total Vertices: {len(verts_list)}\n\n")
            
            # عرض جميع الرؤوس بدون اختصار
            for i, v in enumerate(verts_list):
                f.write(f"Vertex {i:6d}: ({v['position'][0]:8.2f}, {v['position'][1]:8.2f}, {v['position'][2]:8.2f})\n")
        
        print(f"   XTVS (IGI1) (TXT): {txt_path}")
        
        # CSV
        csv_path = os.path.join(out_dir, f"{base_name}_xtvs.csv")
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write("index,x,y,z\n")
            for i, v in enumerate(verts_list):
                f.write(f"{i},{v['position'][0]:.6f},{v['position'][1]:.6f},{v['position'][2]:.6f}\n")
        print(f"   XTVS (IGI1) (CSV): {csv_path}")
        
        # OBJ
        obj_path = os.path.join(out_dir, f"{base_name}_xtvs.obj")
        with open(obj_path, 'w', encoding='utf-8') as f:
            f.write(f"# XTVS Shadow Vertices - IGI1\n")
            f.write(f"# Note: Shadow models are not officially supported in IGI1\n")
            f.write(f"# {len(verts_list)} vertices\n\n")
            f.write(f"o {base_name}_shadow_verts\n")
            
            for v in verts_list:
                f.write(f"v {v['position'][0]:.6f} {v['position'][1]:.6f} {v['position'][2]:.6f}\n")
            
            if verts_list:
                f.write("p 1\n")
        
        print(f"   XTVS (IGI1) as points (OBJ): {obj_path}")

    def export_cafs_info_igi1(self, out_dir: str, base_name: str):
        """تصدير وجوه شبكة الظل (CAFS) لـ IGI1 - عرض كامل"""
        if not hasattr(self, 'shadow_mesh_data') or self.shadow_mesh_data is None or self.shadow_mesh_data.faces is None:
            return
        
        faces = self.shadow_mesh_data.faces
        
        faces_list = []
        for i, f in enumerate(faces):
            if hasattr(f, 'dtype') and "face" in f.dtype.names:
                # CAFS مع normals
                faces_list.append({
                    "index": i,
                    "vertices": [int(f["face"][0]), int(f["face"][1]), int(f["face"][2])],
                    "edge_flags": int(f["edge_flags"]),
                    "normal": [float(f["normal"][0]), float(f["normal"][1]), float(f["normal"][2])]
                })
            else:
                # CAFS بسيط
                faces_list.append({
                    "index": i,
                    "vertices": [int(f[0]), int(f[1]), int(f[2])]
                })
        
        json_path = os.path.join(out_dir, f"{base_name}_cafs.json")
        data = convert_to_json_serializable({
            "face_count": len(faces_list),
            "faces": faces_list,
            "note": "Shadow models are not officially supported in IGI1"
        })
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   CAFS (IGI1) (JSON): {json_path}")
        
        txt_path = os.path.join(out_dir, f"{base_name}_cafs.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# CAFS (Shadow Mesh Faces) - IGI1\n")
            f.write("# Note: Shadow models are not officially supported in IGI1\n")
            f.write(f"Total Faces: {len(faces_list)}\n\n")
            
            # عرض جميع الوجوه بدون اختصار
            for i, face in enumerate(faces_list):
                if "normal" in face:
                    f.write(f"Face {i:6d}: vertices=({face['vertices'][0]:6d}, {face['vertices'][1]:6d}, {face['vertices'][2]:6d}), "
                           f"edge_flags={face['edge_flags']:4d}, normal=({face['normal'][0]:8.2f}, {face['normal'][1]:8.2f}, {face['normal'][2]:8.2f})\n")
                else:
                    f.write(f"Face {i:6d}: vertices=({face['vertices'][0]:6d}, {face['vertices'][1]:6d}, {face['vertices'][2]:6d})\n")
        
        print(f"   CAFS (IGI1) (TXT): {txt_path}")
        
        # CSV
        csv_path = os.path.join(out_dir, f"{base_name}_cafs.csv")
        with open(csv_path, 'w', encoding='utf-8') as f:
            if faces_list and "normal" in faces_list[0]:
                f.write("index,a,b,c,edge_flags,nx,ny,nz\n")
                for i, face in enumerate(faces_list):
                    f.write(f"{i},{face['vertices'][0]},{face['vertices'][1]},{face['vertices'][2]},"
                           f"{face['edge_flags']},{face['normal'][0]:.6f},{face['normal'][1]:.6f},{face['normal'][2]:.6f}\n")
            else:
                f.write("index,a,b,c\n")
                for i, face in enumerate(faces_list):
                    f.write(f"{i},{face['vertices'][0]},{face['vertices'][1]},{face['vertices'][2]}\n")
        print(f"   CAFS (IGI1) (CSV): {csv_path}")

    def export_egde_info_igi1(self, out_dir: str, base_name: str):
        """تصدير حواف شبكة الظل (EGDE) لـ IGI1 - عرض كامل"""
        if not hasattr(self, 'shadow_mesh_data') or self.shadow_mesh_data is None or self.shadow_mesh_data.edges is None:
            return
        
        edges = self.shadow_mesh_data.edges
        
        edges_list = []
        for i, e in enumerate(edges):
            edges_list.append({
                "index": i,
                "a": int(e[0]),
                "b": int(e[1])
            })
        
        json_path = os.path.join(out_dir, f"{base_name}_egde.json")
        data = convert_to_json_serializable({
            "edge_count": len(edges_list),
            "edges": edges_list,
            "note": "Shadow models are not officially supported in IGI1"
        })
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   EGDE (IGI1) (JSON): {json_path}")
        
        txt_path = os.path.join(out_dir, f"{base_name}_egde.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# EGDE (Shadow Mesh Edges) - IGI1\n")
            f.write("# Note: Shadow models are not officially supported in IGI1\n")
            f.write(f"Total Edges: {len(edges_list)}\n\n")
            
            # عرض جميع الحواف بدون اختصار
            for i, edge in enumerate(edges_list):
                f.write(f"Edge {i:6d}: {edge['a']:6d} - {edge['b']:6d}\n")
        
        print(f"   EGDE (IGI1) (TXT): {txt_path}")
        
        # CSV
        csv_path = os.path.join(out_dir, f"{base_name}_egde.csv")
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write("index,a,b\n")
            for i, edge in enumerate(edges_list):
                f.write(f"{i},{edge['a']},{edge['b']}\n")
        print(f"   EGDE (IGI1) (CSV): {csv_path}")

    def export_all_shadow_data_igi1(self, out_dir: str, base_name: str):
        """تصدير جميع بيانات الظل (SEMS, XTVS, CAFS, EGDE) لـ IGI1 إذا وجدت"""
        
        print(f"\n   🌑 Exporting shadow mesh data (IGI1)...")
        
        if not hasattr(self, 'shadow_mesh_data') or self.shadow_mesh_data is None:
            print(f"   No shadow mesh data found in IGI1 file")
            return
        
        self.export_sems_info_igi1(out_dir, base_name)
        self.export_xtvs_info_igi1(out_dir, base_name)
        self.export_cafs_info_igi1(out_dir, base_name)
        self.export_egde_info_igi1(out_dir, base_name)
        
        print(f"   ✅ Shadow mesh data exported (if present)")

    # ========== دوال HSEM و D3DR الجديدة لـ IGI1 ==========
    def export_hsem_info_igi1(self, out_dir: str, base_name: str):
        """تصدير معلومات HSEM (Model Info) لـ IGI1 كملف JSON ونصي"""
        if not self.model_info:
            return
        
        # تحويل المجالات الكروية (المخزنة في floats)
        # IGI1 يخزن 12 float في floats، قد تكون 3 مجالات (كل مجال 4 floats: x,y,z,radius)
        spheres = []
        if len(self.model_info.floats) >= 12:
            for i in range(3):
                idx = i * 4
                spheres.append({
                    "center": [self.model_info.floats[idx], 
                              self.model_info.floats[idx+1], 
                              self.model_info.floats[idx+2]],
                    "radius": self.model_info.floats[idx+3]
                })
        
        # 1. تحويل الكائن إلى قاموس
        info_dict = {
            "version": self.model_info.version,
            "creation_date": self.model_info.creation_type.isoformat(),
            "model_type": ModelType(self.model_info.model_type).name,
            "model_type_value": self.model_info.model_type,
            "unknown1": self.model_info.unknown1,
            "unknown2": self.model_info.unknown2,
            "unknown3": self.model_info.unknown3,
            "floats_12": self.model_info.floats,  # الـ 12 float كاملة
            "bounding_spheres": spheres,
            "unknown4": self.model_info.unknown4,  # 6 uint32
            "something_radius": self.model_info.something_radius,
            "field_80": self.model_info.field_80,
            "attachment_count": self.model_info.attachment_count,
            "magic_vertex_count": self.model_info.magic_vertex_count,
            "portal_count": self.model_info.portal_count,
            "glow_count": self.model_info.glow_count,
            "bone_count": self.model_info.bone_count,
            "reserved_bytes": list(self.model_info.reserved) if self.model_info.reserved else [],
        }
        
        # 2. تصدير كـ JSON
        json_path = os.path.join(out_dir, f"{base_name}_hsem.json")
        data = convert_to_json_serializable(info_dict)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   HSEM info (JSON): {json_path}")
        
        # 3. تصدير كملخص نصي
        txt_path = os.path.join(out_dir, f"{base_name}_hsem.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# HSEM (Model Info) - IGI1\n")
            f.write(f"Version: {self.model_info.version}\n")
            f.write(f"Creation Date: {self.model_info.creation_type.isoformat()}\n")
            f.write(f"Model Type: {ModelType(self.model_info.model_type).name} ({self.model_info.model_type})\n")
            f.write(f"Unknown values: {self.model_info.unknown1}, {self.model_info.unknown2}, {self.model_info.unknown3}\n\n")
            
            f.write("Bounding Spheres (from floats 0-11):\n")
            for i, sphere in enumerate(spheres):
                f.write(f"  Sphere {i+1}: center=({sphere['center'][0]:.2f}, {sphere['center'][1]:.2f}, {sphere['center'][2]:.2f}), radius={sphere['radius']:.2f}\n")
            f.write("\n")
            
            f.write(f"Unknown4 (6 uint32): {self.model_info.unknown4}\n\n")
            f.write(f"Something Radius: {self.model_info.something_radius}\n")
            f.write(f"Field 80: {self.model_info.field_80}\n\n")
            
            f.write("Counts:\n")
            f.write(f"  Attachments: {self.model_info.attachment_count}\n")
            f.write(f"  Magic Vertices: {self.model_info.magic_vertex_count}\n")
            f.write(f"  Portals: {self.model_info.portal_count}\n")
            f.write(f"  Glow Sprites: {self.model_info.glow_count}\n")
            f.write(f"  Bones: {self.model_info.bone_count}\n\n")
            
            f.write(f"Reserved bytes (20): {list(self.model_info.reserved)}\n")
        
        print(f"   HSEM info (TXT): {txt_path}")

    def export_d3dr_info_igi1(self, out_dir: str, base_name: str):
        """تصدير معلومات D3DR (Render Mesh Header) لـ IGI1 كملف JSON ونصي"""
        if not self.render_mesh_data or not self.render_mesh_data.mesh_header:
            return
        
        header = self.render_mesh_data.mesh_header
        
        # 1. تحويل إلى قاموس
        header_dict = {
            "model_type": header.model_type,
            "dword0": header.dword0,
            "face_count": header.face_count,
            "mesh_count": header.mesh_count,
            "vertex_count": header.vertex_count,
            "extra_fields": header.extra,  # rs[8] أو rs[7] حسب النوع
        }
        
        # إضافة حقول خاصة حسب نوع النموذج
        if header.model_type == 1:  # skinned
            # v0 و v1 تم تضمينهما في extra
            pass
        elif header.model_type == 3:  # lightmapped
            # lightmap_count, _5, _6 تم تضمينها في extra
            pass
        
        # 2. تصدير كـ JSON
        json_path = os.path.join(out_dir, f"{base_name}_d3dr.json")
        data = convert_to_json_serializable(header_dict)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   D3DR info (JSON): {json_path}")
        
        # 3. تصدير كملخص نصي
        txt_path = os.path.join(out_dir, f"{base_name}_d3dr.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# D3DR (Render Mesh Header) - IGI1\n")
            f.write(f"Model Type: {header.model_type} (0=Rigid, 1=Skinned, 3=Lightmapped)\n")
            f.write(f"dword0: {header.dword0} (usually 4)\n")
            f.write(f"Face Count: {header.face_count}\n")
            f.write(f"Mesh Count (material groups): {header.mesh_count}\n")
            f.write(f"Vertex Count: {header.vertex_count}\n\n")
            
            f.write("Extra Fields:\n")
            for i, val in enumerate(header.extra):
                f.write(f"  rs[{i}]: {val}\n")
        
        print(f"   D3DR info (TXT): {txt_path}")

    # ========== دوال MRPH و TXAN لـ IGI1 ==========
    def export_mrph_info_igi1(self, out_dir: str, base_name: str):
        """تصدير رؤوس التشكل (MRPH) لـ IGI1 كملف JSON ونصي (عرض كامل)"""
        if not self.morph_channels:
            return
        
        morph_data = {}
        total_vertices = 0
        for channel, vertices in self.morph_channels.items():
            channel_data = []
            for v in vertices:
                # تطبيق swizzle على مواقع رؤوس التشكل
                px, py, pz = self.debug_params.swizzle(v["pos"][0], v["pos"][1], v["pos"][2], self.debug_params.v_scale)
                channel_data.append({
                    "index": int(v["index"].item()) if hasattr(v["index"], 'item') else int(v["index"]),
                    "position": [px, py, pz]
                })
            morph_data[f"channel_{channel}"] = channel_data
            total_vertices += len(vertices)
        
        json_path = os.path.join(out_dir, f"{base_name}_mrph.json")
        data = convert_to_json_serializable(morph_data)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   Morph vertices (JSON): {json_path}")
        
        txt_path = os.path.join(out_dir, f"{base_name}_mrph.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# MRPH (Morph Vertices) - IGI1\n")
            f.write(f"Total Channels: {len(self.morph_channels)}\n")
            f.write(f"Total Vertices: {total_vertices}\n\n")
            
            for channel, vertices in self.morph_channels.items():
                f.write(f"Channel {channel}: {len(vertices)} vertices\n")
                f.write("-" * 50 + "\n")
                
                # عرض جميع الرؤوس بدون اختصار - مع استخراج القيمة بشكل صحيح
                for i, v in enumerate(vertices):
                    # استخراج index بشكل صحيح
                    idx_val = v['index']
                    if hasattr(idx_val, 'item'):
                        idx = idx_val.item()
                    elif isinstance(idx_val, np.ndarray):
                        idx = idx_val[0]
                    else:
                        idx = int(idx_val)
                    
                    # استخراج pos بشكل صحيح وتطبيق swizzle
                    pos = v['pos']
                    if hasattr(pos, '__getitem__'):
                        px = float(pos[0]) if hasattr(pos[0], 'item') else float(pos[0])
                        py = float(pos[1]) if hasattr(pos[1], 'item') else float(pos[1])
                        pz = float(pos[2]) if hasattr(pos[2], 'item') else float(pos[2])
                    else:
                        px, py, pz = 0.0, 0.0, 0.0
                    
                    px, py, pz = self.debug_params.swizzle(px, py, pz, self.debug_params.v_scale)
                    
                    f.write(f"  v{i:4d}: idx={idx:4d}, pos=({px:8.2f}, {py:8.2f}, {pz:8.2f})\n")
                
                f.write("\n")
        
        print(f"   Morph vertices (TXT): {txt_path}")

    def export_txan_info_igi1(self, out_dir: str, base_name: str):
        """تصدير بيانات الحركة (TXAN) لـ IGI1 كملف JSON ونصي"""
        if not self.txan_data:
            return
        
        txan_list = []
        for i, txan in enumerate(self.txan_data):
            txan_list.append({
                "index": i,
                "fields": txan.unknown_fields
            })
        
        json_path = os.path.join(out_dir, f"{base_name}_txan.json")
        data = convert_to_json_serializable(txan_list)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   TXAN animation data (JSON): {json_path}")
        
        txt_path = os.path.join(out_dir, f"{base_name}_txan.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# TXAN (Animation Data) - IGI1\n")
            f.write(f"Total TXAN chunks: {len(self.txan_data)}\n\n")
            for i, txan in enumerate(self.txan_data):
                f.write(f"TXAN {i}:\n")
                f.write(f"  Fields (28 uint32):\n")
                for j, val in enumerate(txan.unknown_fields):
                    f.write(f"    [{j:2d}]: {val} (0x{val:08X})\n")
                f.write("\n")
        
        print(f"   TXAN animation data (TXT): {txt_path}")
        
        csv_path = os.path.join(out_dir, f"{base_name}_txan.csv")
        with open(csv_path, 'w', encoding='utf-8') as f:
            header = ["chunk"] + [f"field_{i:02d}" for i in range(28)]
            f.write(",".join(header) + "\n")
            for i, txan in enumerate(self.txan_data):
                row = [str(i)] + [str(val) for val in txan.unknown_fields]
                f.write(",".join(row) + "\n")
        print(f"   TXAN animation data (CSV): {csv_path}")

    # ========== دوال إنشاء وتطبيق أطلس القوام لـ IGI1 ==========
    def create_texture_atlas_igi1(self, out_dir: str, base_name: str) -> TextureAtlas:
        """
        إنشاء أطلس قوام لمواد النموذج (IGI1)
        """
        # ✅ التعديل: التحقق من إعداد الإيقاف المؤقت
        if not ENABLE_TEXTURE_ATLAS:
            print(f"   ℹ️ ميزة دمج القوام موقفة مؤقتاً (ENABLE_TEXTURE_ATLAS = False)")
            return None
            
        if not self.render_mesh_data or not self.render_mesh_data.materials:
            return None
        
        # تحديد مجلد القوام
        texture_dirs = [
            os.path.join(out_dir, "textures"),
            out_dir,
            os.path.join(os.path.dirname(out_dir), "textures")
        ]
        
        atlas = None
        for tex_dir in texture_dirs:
            if os.path.exists(tex_dir):
                atlas = TextureAtlas(tex_dir)
                break
        
        if atlas is None:
            atlas = TextureAtlas(out_dir)
        
        # جمع أسماء ملفات القوام من المواد
        texture_names = set()
        for i, mat in enumerate(self.render_mesh_data.materials):
            tex_index = mat.get("texture_index", 0)
            tex_name = get_texture_name(tex_index, base_name, i, None)
            texture_names.add(tex_name)
            
            bump_index = mat.get("bump_index", -1)
            if bump_index >= 0:
                tex_name = get_texture_name(bump_index, base_name, i, None)
                texture_names.add(tex_name)
            
            refl_index = mat.get("reflection_index", -1)
            if refl_index >= 0:
                tex_name = get_texture_name(refl_index, base_name, i, None)
                texture_names.add(tex_name)
        
        # إضافة القوام إلى الأطلس
        for tex_name in sorted(texture_names):
            atlas.add_texture(tex_name)
        
        # دمج القوام إذا كان هناك أكثر من واحد
        if atlas.has_multiple_textures():
            if atlas.pack_textures():
                atlas_path = os.path.join(out_dir, f"{base_name}_atlas.png")
                atlas.save_atlas(atlas_path, 'PNG')
                print(f"   Created texture atlas: {atlas_path} ({atlas.atlas_size[0]}x{atlas.atlas_size[1]}) with {len(atlas.texture_paths)} textures")
                return atlas
        
        return None

    def apply_texture_atlas_igi1(self, atlas: TextureAtlas, vertices: np.ndarray, materials: list, base_name: str) -> np.ndarray:
        """
        تطبيق تحويل UV على الرؤوس باستخدام الأطلس (IGI1)
        """
        # ✅ التعديل: التحقق من إعداد الإيقاف المؤقت
        if not ENABLE_TEXTURE_ATLAS:
            return vertices
            
        if not atlas or not atlas.has_multiple_textures():
            return vertices
        
        new_vertices = vertices.copy()
        
        for i, mat in enumerate(materials):
            if i >= len(atlas.texture_names):
                continue
            
            tex_index = mat.get("texture_index", 0)
            tex_name = get_texture_name(tex_index, base_name, i, None)
            
            if tex_name in atlas.texture_indices:
                vo = mat["vertex_offset"]
                vn = mat["vertex_count"]
                
                if vo + vn > len(new_vertices):
                    continue
                
                if "u" in new_vertices.dtype.names and "v" in new_vertices.dtype.names:
                    uvs = np.array([[new_vertices[j]["u"], new_vertices[j]["v"]] 
                                   for j in range(vo, vo + vn)])
                    
                    transformed_uvs = atlas.get_uv_transform(tex_name, uvs)
                    
                    for j, idx in enumerate(range(vo, vo + vn)):
                        new_vertices[idx]["u"] = transformed_uvs[j, 0]
                        new_vertices[idx]["v"] = transformed_uvs[j, 1]
        
        return new_vertices

    def update_mtl_with_atlas_igi1(self, out_dir: str, base_name: str, atlas: TextureAtlas):
        """
        تحديث ملف MTL لاستخدام الأطلس (IGI1)
        """
        if not atlas or not atlas.has_multiple_textures():
            return
        
        mtl_path = os.path.join(out_dir, f"{base_name}_render.mtl")
        if not os.path.exists(mtl_path):
            return
        
        with open(mtl_path, 'r', encoding='utf-8') as f:
            mtl_lines = f.readlines()
        
        new_lines = []
        current_material = None
        
        for line in mtl_lines:
            if line.startswith('newmtl '):
                current_material = line.strip()
                new_lines.append(line)
            elif line.startswith('map_Kd ') and current_material:
                new_lines.append(f"map_Kd {base_name}_atlas.png\n")
            elif line.startswith('map_') and current_material:
                new_lines.append(f"map_Kd {base_name}_atlas.png\n")
            else:
                new_lines.append(line)
        
        with open(mtl_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
        print(f"   Updated MTL to use texture atlas: {mtl_path}")

    # ========== دالة export_all المحدثة لـ IGI1 ==========
    def export_all(self, out_dir, export_formats=None, lightmap_format="png"):
        """دالة تصدير واحدة شاملة لـ IGI1"""
        if export_formats is None:
            export_formats = ["obj"]
        
        base_name = os.path.splitext(os.path.basename(out_dir))[0]
        self.ensure_dir(out_dir)
        
        print(f"\nExporting to {out_dir}")
        print("-" * 50)
        
        # ========== 0. معلومات الرأس ==========
        self.export_hsem_info_igi1(out_dir, base_name)
        self.export_d3dr_info_igi1(out_dir, base_name)
        
        # ========== 0.5. معلومات التصادم ==========
        self.export_hsmc_info_igi1_improved(out_dir, base_name)
        
        # ========== 0.6. معلومات العظام (إذا وجدت) ==========
        if hasattr(self, 'bones') and self.bones:
            self.export_manb_detailed(out_dir, base_name)
            self.export_reih_detailed(out_dir, base_name)
        
        # ========== 1. شبكة التصيير ==========
        self.export_render_mesh(out_dir, base_name, export_formats)
        
        # ========== 2. شبكة التصادم (كشبكة) ==========
        self.export_collision_mesh(out_dir, base_name, 0, export_formats)
        
        # ========== 3. مواد وكرات التصادم ==========
        # ✅ أضف هذين السطرين هنا
        self.export_collision_materials(out_dir, base_name)
        self.export_collision_spheres(out_dir, base_name)
        
        # ========== 4. بيانات التصادم التفصيلية ==========
        self.export_all_collision_mesh_data_igi1(out_dir, base_name)
        
        # ========== 5. شبكة الظل (إذا وجدت) ==========
        self.export_all_shadow_data_igi1(out_dir, base_name)
        
        # ========== 6. المرفقات ==========
        self.export_attachments(out_dir, base_name)
        
        # ========== 7. خرائط الإضاءة ==========
        self.export_lightmaps(out_dir, base_name, lightmap_format)
        
        # ========== 8. البيانات الإضافية الأساسية ==========
        self.export_extra_data(out_dir, base_name)
        
        # ========== 9. التحسينات الإضافية لـ IGI1 ==========
        if self.magic_vertices:
            # CSV
            csv_path = os.path.join(out_dir, f"{base_name}_magic_vertices.csv")
            with open(csv_path, "w", encoding="utf-8") as f:
                f.write("index,pos_x,pos_y,pos_z,type\n")
                for i, mv in enumerate(self.magic_vertices):
                    px, py, pz = self.debug_params.swizzle(mv.pos.x, mv.pos.y, mv.pos.z, self.debug_params.v_scale)
                    f.write(f"{i},{px:.6f},{py:.6f},{pz:.6f},{mv.type}\n")
            print(f"   Magic vertices (CSV): {csv_path}")
            
            # JSON
            json_path = os.path.join(out_dir, f"{base_name}_magic_vertices.json")
            data = []
            for i, mv in enumerate(self.magic_vertices):
                px, py, pz = self.debug_params.swizzle(mv.pos.x, mv.pos.y, mv.pos.z, self.debug_params.v_scale)
                data.append({"index": i, "pos": [px, py, pz], "type": mv.type})
            data = convert_to_json_serializable(data)
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            print(f"   Magic vertices (JSON): {json_path}")
        
        if self.portals and self.portal_vertices and self.portal_faces:
            # تجهيز الرؤوس والوجوه
            vertices = []
            for pv in self.portal_vertices:
                px, py, pz = self.debug_params.swizzle(pv.pos.x, pv.pos.y, pv.pos.z, self.debug_params.v_scale)
                vertices.append([px, py, pz])
            
            faces = []
            for pf in self.portal_faces:
                faces.append([pf.a, pf.b, pf.c])
            
            if vertices and faces:
                dtype_out = np.dtype([
                    ("px", np.float32), ("py", np.float32), ("pz", np.float32),
                    ("nx", np.float32), ("ny", np.float32), ("nz", np.float32),
                    ("u", np.float32), ("v", np.float32)
                ])
                
                verts_arr = np.array([(v[0], v[1], v[2], 0,0,0,0,0) for v in vertices], dtype=dtype_out)
                faces_arr = np.array(faces)
                
                # OBJ
                obj_path = os.path.join(out_dir, f"{base_name}_portals.obj")
                with open(obj_path, "w", encoding="utf-8") as f:
                    f.write(f"# Portal mesh for {base_name} (IGI1)\n")
                    f.write(f"# {len(self.portals)} portals, {len(vertices)} vertices, {len(faces)} faces\n\n")
                    f.write(f"o {base_name}_portals\n")
                    for v in verts_arr:
                        f.write(f"v {v['px']:.6f} {v['py']:.6f} {v['pz']:.6f}\n")
                    f.write(f"usemtl default\n")
                    for face in faces_arr:
                        a, b, c = face[0]+1, face[1]+1, face[2]+1
                        f.write(f"f {a} {b} {c}\n")
                print(f"   Portals mesh (OBJ): {obj_path}")
                
                portals_txt = os.path.join(out_dir, f"{base_name}_portals_detailed.txt")
                with open(portals_txt, "w", encoding="utf-8") as f:
                    f.write("# Portal Definitions (TROP) - IGI1\n")
                    f.write("# Format: portal_id: start_vertex num_vertices start_face num_faces\n\n")
                    for p in self.portals:
                        f.write(f"Portal {p.portal_id:3d}: "
                               f"vtx={p.start_vertex:4d}-{p.start_vertex+p.num_vertices-1:4d} "
                               f"({p.num_vertices:4d} vertices), "
                               f"faces={p.start_face:4d}-{p.start_face+p.num_faces-1:4d} "
                               f"({p.num_faces:4d} faces)\n")
                print(f"   Portal details (TXT): {portals_txt}")
        
        # ========== 9. بيانات التشكل والحركة ==========
        if hasattr(self, 'morph_channels') and self.morph_channels:
            self.export_mrph_info_igi1(out_dir, base_name)
        
        if hasattr(self, 'txan_data') and self.txan_data:
            self.export_txan_info_igi1(out_dir, base_name)
        
        print("-" * 50)
        print("Export completed successfully!")

# ============================================================
# الفئة الرئيسية للنموذج IGI2 (نسخة كاملة ومحدثة)
# ============================================================

class MefModelIGI2:
    def __init__(self, buffer: Buffer, export_mode: str = "simple", debug_params: Optional[MefDebugParams] = None):
        self.debug_params = debug_params or MefDebugParams()
        loop_file = LoopFile(buffer, flip_ident=True)
        loop_file.print_all_chunks()

        self.model_info: ModelInfoIGI2 = None
        self.render_mesh_data: RenderMeshDataIGI2 = None
        self.collision_mesh_data: CollisionMeshDataIGI2 = None
        self.collision_mesh_data2: CollisionMeshDataIGI2 = None
        self.shadow_mesh_data: ShadowMeshDataIGI2 = None
        self.bones: list[Bone] = []
        self.attachments: list[Attachment] = []
        self.magic_vertices: list[MagicVertex] = []
        self.portals: list[Portal] = []
        self.portal_vertices: list[PortalVertex] = []
        self.portal_faces: list[PortalFace] = []
        self.glow_sprites: list[GlowSprite] = []
        self.morph_channels: dict[int, np.ndarray] = {}
        self.lightmaps: list[LightmapData] = []
        self.collision_materials: list[CollisionMaterialIGI2] = []
        self.txan_data: list[TXANData] = []
        
        # بيانات جديدة من وثائق Tav EndeR
        self.hsem_info: HSEMInfo = None
        self.vertex_weights: list[XTRWEntry] = []
        self.texture_references: list[TextureReference] = []
        self.extra_uv_sets: list[TextureCoordinateSet] = []
        
        self.export_mode = export_mode

        # متغيرات مؤقتة
        self._child_counts = None
        self._bone_positions = None
        
        # المتغيرات الجديدة للقطع المضافة
        self.bone_extra_params = []
        self.external_refs = []
        self.skeleton_hints = []
        self.shadow_faces_detailed = []
        self.shadow_edges_raw = None
        self.hsem_raw_data = None
        self.collision_materials_mesh1 = []
        
        loop_file.index = 0
        
        while True:
            chunk = loop_file.next_chunk()
            if chunk is None:
                break
            ident = chunk.header.ident.decode('ascii')
            
            if ident == "MESH":
                self.model_info = ModelInfoIGI2.from_buffer(chunk.buffer)
                print(f"Model type: {self.model_info.model_type.name}")
                print(f"  Attachments: {self.model_info.attachment_count}, Magic vertices: {self.model_info.magic_vertex_count}")
                print(f"  Portals: {self.model_info.portal_count}, Glow: {self.model_info.glow_count}, Bones: {self.model_info.bone_count}")
            elif ident == "HIER":
                self._process_hierarchy(chunk, loop_file)
            elif ident == "BNAM":
                pass
            elif ident == "ATTA":
                for _ in range(self.model_info.attachment_count):
                    self.attachments.append(Attachment.from_buffer(chunk.buffer))
                print(f"Processed {len(self.attachments)} attachments")
            elif ident == "MVTX":
                self._process_magic_vertices(chunk)
            elif ident == "PORT":
                self._process_portal(chunk)
            elif ident == "PTVX":
                self._process_portal_vertices(chunk)
            elif ident == "PTFC":
                self._process_portal_faces(chunk)
            elif ident == "GLOW":
                self._process_glow(chunk)
            elif ident == "RD3D":
                self._process_render_mesh(chunk, loop_file)
            elif ident == "CMSH":
                self._process_collision_mesh(chunk, loop_file)
            elif ident == "CMAT":
                self._process_collision_materials(chunk)
            elif ident == "SMES":
                print("Found SMES chunk, processing shadow mesh...")
                self._process_shadow_mesh(chunk, loop_file)
            elif ident == "MRPH":
                self._process_morph(chunk)
            elif ident == "LTMP":
                self._process_lightmap(chunk)
            elif ident == "TXAN":
                self._process_txan(chunk)
            elif ident == "XTRW":
                self._process_xtrw(chunk)
            elif ident == "XTXM":
                self._process_xtxm(chunk)
            elif ident == "TCST":
                self._process_tcst(chunk)
            elif ident == "HPRM":
                self._process_hprm(chunk)
            elif ident == "XTRN":
                self._process_xtrn(chunk)
            elif ident == "NHSA":
                self._process_nhsa(chunk)
            elif ident == "LLUN":
                self._process_llun(chunk)
            else:
                if chunk.header.data_size > 0:
                    print(f"Unhandled chunk: {ident} (size: {chunk.header.data_size})")

    # ========== الدوال الأصلية (الموجودة مسبقاً) ==========
    
    def _process_magic_vertices(self, chunk):
        buffer = chunk.buffer
        count = self.model_info.magic_vertex_count if self.model_info else 0
        if count == 0:
            count = buffer.size() // 16
        for _ in range(count):
            if buffer.eof():
                break
            mv = MagicVertex.from_buffer(buffer)
            self.magic_vertices.append(mv)
        print(f"Processed {len(self.magic_vertices)} magic vertices")

    def _process_portal(self, chunk):
        buffer = chunk.buffer
        count = self.model_info.portal_count if self.model_info else 0
        if count == 0:
            count = buffer.size() // 20
        for _ in range(count):
            if buffer.eof():
                break
            p = Portal.from_buffer(buffer)
            self.portals.append(p)
        print(f"Processed {len(self.portals)} portals")

    def _process_portal_vertices(self, chunk):
        buffer = chunk.buffer
        count = buffer.size() // 12
        for _ in range(count):
            if buffer.eof():
                break
            pv = PortalVertex.from_buffer(buffer)
            self.portal_vertices.append(pv)
        print(f"Processed {len(self.portal_vertices)} portal vertices")

    def _process_portal_faces(self, chunk):
        buffer = chunk.buffer
        count = buffer.size() // 12
        for _ in range(count):
            if buffer.eof():
                break
            pf = PortalFace.from_buffer(buffer)
            self.portal_faces.append(pf)
        print(f"Processed {len(self.portal_faces)} portal faces")

    def _process_glow(self, chunk):
        buffer = chunk.buffer
        count = self.model_info.glow_count if self.model_info else 0
        if count == 0:
            count = buffer.size() // 32
        for _ in range(count):
            if buffer.eof():
                break
            g = GlowSprite.from_buffer(buffer)
            self.glow_sprites.append(g)
        print(f"Processed {len(self.glow_sprites)} glow sprites")

    def _process_collision_materials(self, chunk):
        buffer = chunk.buffer
        data_size = buffer.size()
        material_size = 16
        count = data_size // material_size
        remainder = data_size % material_size
        
        print(f"   CMAT chunk: {data_size} bytes, expecting {count} materials, remainder {remainder} bytes")
        
        for i in range(count):
            if buffer.eof():
                break
            try:
                mat = CollisionMaterialIGI2.from_buffer(buffer)
                self.collision_materials.append(mat)
                print(f"     Material {len(self.collision_materials)-1}: opacity={mat.opacity:.3f}, portal_id={mat.portal_id}, "
                      f"texture_id={mat.texture_id}, game_material_id={mat.game_material_id}")
            except Exception as e:
                print(f"   Error reading material {i}: {e}")
                break
        
        if remainder > 0 and not buffer.eof():
            print(f"   Found partial material data: {remainder} bytes")
            remaining_data = buffer.read(remainder)
            
            if remainder >= 16:
                temp_buffer = Buffer(remaining_data)
                try:
                    opacity = temp_buffer.read_float()
                    portal_id = temp_buffer.read_uint32()
                    texture_id = temp_buffer.read_uint32()
                    unknown1 = 0
                    game_material_id = 0
                    unknown2 = 0
                    
                    partial_mat = CollisionMaterialIGI2(
                        opacity=opacity,
                        portal_id=portal_id,
                        texture_id=texture_id,
                        unknown1=unknown1,
                        game_material_id=game_material_id,
                        unknown2=unknown2
                    )
                    self.collision_materials.append(partial_mat)
                    print(f"     Added partial material: opacity={opacity:.3f}, portal_id={portal_id}, texture_id={texture_id}")
                except:
                    pass
            elif remainder == 12:
                temp_buffer = Buffer(remaining_data)
                try:
                    opacity = temp_buffer.read_float()
                    portal_id = temp_buffer.read_uint32()
                    texture_id = 0
                    
                    partial_mat = CollisionMaterialIGI2(
                        opacity=opacity,
                        portal_id=portal_id,
                        texture_id=texture_id,
                        unknown1=0,
                        game_material_id=0,
                        unknown2=0
                    )
                    self.collision_materials.append(partial_mat)
                    print(f"     Added partial material (12 bytes): opacity={opacity:.3f}, portal_id={portal_id}")
                except:
                    pass
        
        print(f"   Processed {len(self.collision_materials)} collision materials")
    
    def _process_collision_materials_mesh1(self, chunk):
        buffer = chunk.buffer
        data_size = buffer.size()
        material_size = 16
        count = data_size // material_size
        remainder = data_size % material_size
        
        print(f"   mesh1 CMAT chunk: {data_size} bytes, expecting {count} materials, remainder {remainder} bytes")
        
        if not hasattr(self, 'collision_materials_mesh1'):
            self.collision_materials_mesh1 = []
        
        for i in range(count):
            if buffer.eof():
                break
            try:
                mat = CollisionMaterialIGI2.from_buffer(buffer)
                self.collision_materials_mesh1.append(mat)
                print(f"     Material {len(self.collision_materials_mesh1)-1}: opacity={mat.opacity:.3f}, portal_id={mat.portal_id}, "
                      f"texture_id={mat.texture_id}, game_material_id={mat.game_material_id}")
            except Exception as e:
                print(f"   Error reading material {i}: {e}")
                break
        
        if remainder > 0 and not buffer.eof():
            print(f"   Found partial material data in mesh1: {remainder} bytes")
            remaining_data = buffer.read(remainder)
            
            if remainder >= 16:
                temp_buffer = Buffer(remaining_data)
                try:
                    opacity = temp_buffer.read_float()
                    portal_id = temp_buffer.read_uint32()
                    texture_id = temp_buffer.read_uint32()
                    unknown1 = 0
                    game_material_id = 0
                    unknown2 = 0
                    
                    partial_mat = CollisionMaterialIGI2(
                        opacity=opacity,
                        portal_id=portal_id,
                        texture_id=texture_id,
                        unknown1=unknown1,
                        game_material_id=game_material_id,
                        unknown2=unknown2
                    )
                    self.collision_materials_mesh1.append(partial_mat)
                    print(f"     Added partial material (mesh1): opacity={opacity:.3f}, portal_id={portal_id}, texture_id={texture_id}")
                except:
                    pass
            elif remainder == 12:
                temp_buffer = Buffer(remaining_data)
                try:
                    opacity = temp_buffer.read_float()
                    portal_id = temp_buffer.read_uint32()
                    texture_id = 0
                    
                    partial_mat = CollisionMaterialIGI2(
                        opacity=opacity,
                        portal_id=portal_id,
                        texture_id=texture_id,
                        unknown1=0,
                        game_material_id=0,
                        unknown2=0
                    )
                    self.collision_materials_mesh1.append(partial_mat)
                    print(f"     Added partial material (mesh1, 12 bytes): opacity={opacity:.3f}, portal_id={portal_id}")
                except:
                    pass
        
        print(f"   Processed {len(self.collision_materials_mesh1)} collision materials for mesh1")
    
    def _process_hierarchy(self, chunk, loop_file):
        self._child_counts = [chunk.buffer.read_uint8() for _ in range(self.model_info.bone_count)]
        chunk.buffer.align(4)
        self._bone_positions = [Vector3.from_buffer(chunk.buffer) for _ in range(self.model_info.bone_count)]
        
        name_chunk = loop_file.expect_chunk("BNAM")
        bone_names = [name_chunk.buffer.read_ascii_string(16) for _ in range(self.model_info.bone_count)]

        child_counts = self._child_counts.copy()
        bone_positions = self._bone_positions.copy()
        
        bone_queue = []
        def create_bone(parent_id: int, name: str, position: Vector3, child_count: int):
            bone = Bone(name, position, parent_id)
            next_parent_id = len(self.bones)
            self.bones.append(bone)
            for _ in range(child_count):
                if not bone_queue and not (child_counts and bone_names and bone_positions):
                    break
                cnt = child_counts.pop(0) if child_counts else 0
                nm = bone_names.pop(0) if bone_names else ""
                pos_raw = bone_positions.pop(0) if bone_positions else Vector3(0, 0, 0)
                bone_queue.append((next_parent_id, nm, pos_raw, cnt))

        if bone_names and bone_positions and child_counts:
            bone_queue.append((-1, bone_names.pop(0), bone_positions.pop(0), child_counts.pop(0) if child_counts else 0))
        
        while bone_queue:
            create_bone(*bone_queue.pop(0))
        
        print(f"Processed {len(self.bones)} bones")
        print(f"  Stored {len(self._child_counts)} child counts and {len(self._bone_positions)} bone positions for later use")

    def _process_render_mesh(self, chunk, loop_file):
        assert self.render_mesh_data is None, "Render mesh already exists"
        render_mesh_info = RenderMeshHeader.from_buffer(chunk.buffer)
        
        face_chunk = loop_file.expect_chunk("FACE")
        faces_data = face_chunk.buffer.read(face_chunk.buffer.size())
        faces = np.frombuffer(faces_data, np.uint16).reshape(-1, 3)
        
        rend_chunk = loop_file.expect_chunk("REND")
        render_info = []
        for _ in range(render_mesh_info.face_group_count):
            render_info.append(FaceGroup.from_buffer(rend_chunk.buffer, self.model_info.model_type))
        
        vert_chunk = loop_file.expect_chunk("VRTX")
        model_type = self.model_info.model_type
        
        if model_type == ModelType.StaticModel:
            dtype = np.dtype([
                ("pos", np.float32, (3,)),
                ("normal", np.float32, (3,)),
                ("uv0", np.float32, (2,))
            ])
        elif model_type == ModelType.SkinnedModel:
            dtype = np.dtype([
                ("pos", np.float32, (3,)),
                ("normal", np.float32, (3,)),
                ("uv0", np.float32, (2,)),
                ("weight", np.float32, (1,)),
                ("index", np.ushort, (1,)),
                ("bone_id", np.ushort, (1,))
            ])
        elif model_type == ModelType.LightmappedModel:
            dtype = np.dtype([
                ("pos", np.float32, (3,)),
                ("uv0", np.float32, (2,)),
                ("uv1", np.float32, (2,))
            ])
        else:
            dtype = np.dtype([
                ("pos", np.float32, (3,)),
                ("normal", np.float32, (3,)),
                ("uv0", np.float32, (2,))
            ])
            print(f"Unknown model type {model_type}, using StaticModel dtype")
        
        vert_data = vert_chunk.buffer.read(vert_chunk.buffer.size())
        vertices = np.frombuffer(vert_data, dtype)
        
        lightmap_uvs = None
        if loop_file.has_chunk("LTMP"):
            try:
                lightmap_chunk = loop_file.expect_chunk("LTMP")
                lightmap_data = lightmap_chunk.buffer.read(lightmap_chunk.buffer.size())
                if lightmap_chunk.buffer.size() > 1000:
                    pass
                else:
                    uv_count = len(lightmap_data) // 8
                    if uv_count > 0:
                        lightmap_uvs = np.frombuffer(lightmap_data, np.float32).reshape(-1, 2)
                        print(f"   Found lightmap UVs: {len(lightmap_uvs)}")
            except Exception as e:
                print(f"   Error reading lightmap UVs: {e}")
        
        self.render_mesh_data = RenderMeshDataIGI2(render_mesh_info, faces, vertices, render_info, lightmap_uvs)
        print(f"Render mesh: {len(vertices)} vertices, {len(faces)} faces, {len(render_info)} material groups")

    def _process_collision_mesh(self, chunk, loop_file):
        collision_mesh_info = CollisionMeshHeader.from_buffer(chunk.buffer)
        
        vertices_chunk = loop_file.expect_chunk("CVTX")
        vertices_data = vertices_chunk.buffer.read(vertices_chunk.buffer.size())
        
        faces_chunk = loop_file.expect_chunk("CFCE")
        faces_data = faces_chunk.buffer.read(faces_chunk.buffer.size())
        
        try:
            materials_chunk = loop_file.expect_chunk("CMAT")
            print(f"DEBUG: Found CMAT for mesh0! size={materials_chunk.header.data_size}")
            self._process_collision_materials(materials_chunk)
            materials0 = self.collision_materials.copy()
        except ValueError:
            print("   No CMAT chunk found for mesh0")
            materials0 = []
        
        spheres_chunk = loop_file.expect_chunk("CSPH")
        spheres_data = spheres_chunk.buffer.read(spheres_chunk.buffer.size())
        
        vertices0 = np.frombuffer(vertices_data, CollisionVertexDtype).copy()
        faces0 = np.frombuffer(faces_data, CollisionFaceDtype)
        spheres0 = np.frombuffer(spheres_data, CollisionSphereDtype).copy()
        
        self.collision_mesh_data = CollisionMeshDataIGI2(
            collision_mesh_info, spheres0, faces0, vertices0, materials0
        )
        print(f"Collision mesh 0: {len(vertices0)} vertices, {len(faces0)} faces, {len(materials0)} materials")
        
        if collision_mesh_info.mesh1.face_count > 0:
            print(f"\n   📦 Found second collision mesh (mesh1) with {collision_mesh_info.mesh1.face_count} faces")
            
            self.collision_materials_mesh1 = []
            
            try:
                vertices_chunk2 = loop_file.expect_chunk("CVTX")
                vertices_data2 = vertices_chunk2.buffer.read(vertices_chunk2.buffer.size())
                vertices1 = np.frombuffer(vertices_data2, CollisionVertexDtype).copy()
                print(f"   mesh1: Found CVTX with {len(vertices1)} vertices")
            except ValueError:
                print("   mesh1: No CVTX chunk found")
                vertices1 = np.array([], dtype=CollisionVertexDtype)
            
            try:
                faces_chunk2 = loop_file.expect_chunk("CFCE")
                faces_data2 = faces_chunk2.buffer.read(faces_chunk2.buffer.size())
                faces1 = np.frombuffer(faces_data2, CollisionFaceDtype)
                print(f"   mesh1: Found CFCE with {len(faces1)} faces")
            except ValueError:
                print("   mesh1: No CFCE chunk found")
                faces1 = np.array([], dtype=CollisionFaceDtype)
            
            try:
                materials_chunk2 = loop_file.expect_chunk("CMAT")
                print(f"   mesh1: Found CMAT! size={materials_chunk2.header.data_size}")
                self._process_collision_materials_mesh1(materials_chunk2)
                materials1 = self.collision_materials_mesh1.copy()
                print(f"   mesh1: Processed {len(materials1)} materials")
            except ValueError:
                print("   mesh1: No CMAT chunk found")
                materials1 = []
            
            try:
                spheres_chunk2 = loop_file.expect_chunk("CSPH")
                spheres_data2 = spheres_chunk2.buffer.read(spheres_chunk2.buffer.size())
                spheres1 = np.frombuffer(spheres_data2, CollisionSphereDtype).copy()
                print(f"   mesh1: Found CSPH with {len(spheres1)} spheres")
            except ValueError:
                print("   mesh1: No CSPH chunk found")
                spheres1 = np.array([], dtype=CollisionSphereDtype)
            
            if len(vertices1) > 0 and len(faces1) > 0:
                self.collision_mesh_data2 = CollisionMeshDataIGI2(
                    collision_mesh_info, spheres1, faces1, vertices1, materials1
                )
                print(f"   ✅ Collision mesh 1 created: {len(vertices1)} vertices, {len(faces1)} faces, {len(materials1)} materials")
            else:
                print("   ⚠️ Second collision mesh has no vertices or faces, skipping")
                self.collision_mesh_data2 = None
            
    def _process_shadow_mesh(self, chunk, loop_file):
        try:
            shadow_header = ShadowMeshHeader.from_buffer(chunk.buffer)
            print(f"Shadow header: faces={shadow_header.face_count}, vertices={shadow_header.vertex_count}, edges={shadow_header.edge_count}, bone={shadow_header.bone_index}")
        except Exception as e:
            print(f"Error reading shadow header: {e}")
            return
        
        vertices = None
        faces = None
        edges = None
        
        if loop_file.has_chunk("SVTX"):
            try:
                vertex_chunk = loop_file.expect_chunk("SVTX")
                vertex_data = vertex_chunk.buffer.read(vertex_chunk.buffer.size())
                vertices = np.frombuffer(vertex_data, np.float32)
                if len(vertices) == shadow_header.vertex_count * 3:
                    vertices = vertices.reshape(-1, 3)
                else:
                    print(f"   Warning: Shadow vertex count mismatch. Expected {shadow_header.vertex_count*3}, got {len(vertices)}")
                    vertices = vertices.reshape(-1, 3) if len(vertices) % 3 == 0 else np.array([])
                print(f"   Found shadow vertices: {len(vertices)}")
            except Exception as e:
                print(f"   Error reading shadow vertices: {e}")
        
        if loop_file.has_chunk("SFAC"):
            try:
                face_chunk = loop_file.expect_chunk("SFAC")
                face_data = face_chunk.buffer.read(face_chunk.buffer.size())
                if len(face_data) > 0:
                    try:
                        faces = np.frombuffer(face_data, ShadowFaceDtype)
                        print(f"   Found shadow faces (with normals): {len(faces)}")
                    except:
                        faces = np.frombuffer(face_data, np.uint32).reshape(-1, 3)
                        print(f"   Found shadow faces (simple indices): {len(faces)}")
            except Exception as e:
                print(f"   Error reading shadow faces: {e}")
        
        if loop_file.has_chunk("EDGE"):
            try:
                edge_chunk = loop_file.expect_chunk("EDGE")
                edge_data = edge_chunk.buffer.read(edge_chunk.buffer.size())
                if len(edge_data) > 0:
                    edges = np.frombuffer(edge_data, np.uint32).reshape(-1, 2)
                    print(f"   Found shadow edges: {len(edges)}")
            except Exception as e:
                print(f"   Error reading shadow edges: {e}")
        
        if vertices is not None and len(vertices) > 0:
            self.shadow_mesh_data = ShadowMeshDataIGI2(shadow_header, faces, vertices, edges)
            print(f"Shadow mesh loaded: {len(vertices)} vertices")
        else:
            print("No shadow vertices found")

    def _process_morph(self, chunk):
        buffer = chunk.buffer
        counts = [buffer.read_uint32() for _ in range(16)]
        for channel, count in enumerate(counts):
            if count > 0:
                morph_data = buffer.read(MorphVertexDtype.itemsize * count)
                vertices = np.frombuffer(morph_data, MorphVertexDtype).copy()
                self.morph_channels[channel] = vertices
                print(f"Found morph channel {channel} with {count} vertices")

    def _process_lightmap(self, chunk):
        try:
            buffer = chunk.buffer
            width = buffer.read_uint32()
            height = buffer.read_uint32()
            format_type = buffer.read_uint32()
            data_size = buffer.size()
            data = buffer.read(data_size)
            
            lightmap = LightmapData(width, height, format_type, data)
            self.lightmaps.append(lightmap)
            print(f"   Found lightmap: {width}x{height}, format={format_type}, size={data_size} bytes")
        except Exception as e:
            print(f"   Error processing lightmap: {e}")

    def _process_txan(self, chunk):
        try:
            buffer = chunk.buffer
            txan = TXANData.from_buffer(buffer)
            self.txan_data.append(txan)
            print(f"   Found TXAN chunk with {len(txan.unknown_fields)} fields")
        except Exception as e:
            print(f"   Error processing TXAN: {e}")

    def _process_xtrw(self, chunk):
        buffer = chunk.buffer
        count = buffer.size() // 12
        for i in range(count):
            entry = XTRWEntry.from_buffer(buffer)
            self.vertex_weights.append(entry)
        print(f"   Processed {len(self.vertex_weights)} XTRW weight entries")

    def _process_xtxm(self, chunk):
        buffer = chunk.buffer
        count = buffer.size() // 36
        for i in range(count):
            if buffer.eof():
                break
            ref = TextureReference.from_buffer(buffer)
            self.texture_references.append(ref)
        print(f"   Processed {len(self.texture_references)} texture references")

    def _process_tcst(self, chunk):
        buffer = chunk.buffer
        uv_count = buffer.size() // 8
        uv_set = TextureCoordinateSet.from_buffer(buffer, uv_count)
        uv_set.index = len(self.extra_uv_sets)
        self.extra_uv_sets.append(uv_set)
        print(f"   Processed TCST with {uv_count} UV coordinates")

    def _process_hprm(self, chunk):
        buffer = chunk.buffer
        bone_param_count = buffer.size() // 12
        print(f"   Found HPRM chunk with {bone_param_count} bone parameter sets")
        
        if not hasattr(self, 'hprm_data'):
            self.hprm_data = []
        
        for i in range(bone_param_count):
            param_x = buffer.read_float()
            param_y = buffer.read_float()
            param_z = buffer.read_float()
            
            self.hprm_data.append({
                "bone_index": i if i < len(self.bones) else -1,
                "params": (param_x, param_y, param_z)
            })
            
            if i < len(self.bones) and hasattr(self, 'bones'):
                if not hasattr(self.bones[i], 'hprm_params'):
                    self.bones[i].hprm_params = []
                self.bones[i].hprm_params.append((param_x, param_y, param_z))
        
        print(f"   Processed {len(self.hprm_data)} HPRM bone parameter sets")

    def _process_xtrn(self, chunk):
        buffer = chunk.buffer
        ref_name = buffer.read_ascii_string(32) if buffer.size() >= 32 else ""
        print(f"   Found XTRN external reference: {ref_name}")

    def _process_nhsa(self, chunk):
        buffer = chunk.buffer
        hint_data = buffer.read(min(16, buffer.size()))
        print(f"   Found NHSA skeleton hint: {hint_data.hex()[:32]}...")

    def _process_llun(self, chunk):
        print(f"   Found LLUN null chunk (size: {chunk.header.data_size})")

    # ========== الدوال المحسنة الجديدة (مرة واحدة فقط) ==========
    
    def _process_chunks_enhanced(self, loop_file: LoopFile):
        """معالجة القطع بنفس ترتيب igi2.exe مع التحقق من الصلاحية"""
        
        if loop_file.has_chunk("HSEM"):
            chunk = loop_file.expect_chunk("HSEM")
            self.hsem_raw_data = chunk.buffer.data.copy()
            self.model_info = ModelInfoIGI2.from_buffer(chunk.buffer)
            print(f"✅ HSEM: version={self.model_info.version}, type={self.model_info.model_type.name}")
            print(f"   model_info size: {chunk.header.data_size} bytes")
        
        if loop_file.has_chunk("HIER"):
            chunk = loop_file.expect_chunk("HIER")
            self._process_hierarchy_enhanced(chunk, loop_file)
        
        if loop_file.has_chunk("BNAM"):
            chunk = loop_file.expect_chunk("BNAM")
            self._process_bone_names_enhanced(chunk)
        
        if loop_file.has_chunk("HPRM"):
            chunk = loop_file.expect_chunk("HPRM")
            self._process_hprm_enhanced(chunk)
        
        if loop_file.has_chunk("GLOW"):
            chunk = loop_file.expect_chunk("GLOW")
            self._process_glow_enhanced(chunk)
        
        if loop_file.has_chunk("ATTA"):
            chunk = loop_file.expect_chunk("ATTA")
            self._process_attachments_enhanced(chunk)
        
        if loop_file.has_chunk("MVTX"):
            chunk = loop_file.expect_chunk("MVTX")
            self._process_magic_vertices_enhanced(chunk)
        
        if loop_file.has_chunk("PORT"):
            chunk = loop_file.expect_chunk("PORT")
            self._process_portal_enhanced(chunk)
        
        if loop_file.has_chunk("PTFC"):
            chunk = loop_file.expect_chunk("PTFC")
            self._process_portal_faces_enhanced(chunk)
        
        if loop_file.has_chunk("PTVX"):
            chunk = loop_file.expect_chunk("PTVX")
            self._process_portal_vertices_enhanced(chunk)
        
        if loop_file.has_chunk("XTRW"):
            chunk = loop_file.expect_chunk("XTRW")
            self._process_xtrw_enhanced(chunk)
        
        if loop_file.has_chunk("XTXM"):
            chunk = loop_file.expect_chunk("XTXM")
            self._process_xtxm_enhanced(chunk)
        
        if loop_file.has_chunk("TCST"):
            chunk = loop_file.expect_chunk("TCST")
            self._process_tcst_enhanced(chunk)
        
        if loop_file.has_chunk("RD3D"):
            chunk = loop_file.expect_chunk("RD3D")
            self._process_render_mesh_enhanced(chunk, loop_file)
        
        if loop_file.has_chunk("CMSH"):
            chunk = loop_file.expect_chunk("CMSH")
            self._process_collision_mesh_enhanced(chunk, loop_file)
        
        if loop_file.has_chunk("SMES"):
            chunk = loop_file.expect_chunk("SMES")
            self._process_shadow_mesh_enhanced(chunk, loop_file)
        
        if loop_file.has_chunk("XTRN"):
            chunk = loop_file.expect_chunk("XTRN")
            self._process_xtrn_enhanced(chunk)
        
        if loop_file.has_chunk("NHSA"):
            chunk = loop_file.expect_chunk("NHSA")
            self._process_nhsa_enhanced(chunk)
        
        if loop_file.has_chunk("TXAN"):
            chunk = loop_file.expect_chunk("TXAN")
            self._process_txan_enhanced(chunk)
        
        print(f"\n📊 Enhanced parsing complete:")
        print(f"   Bones: {len(self.bones)}")
        print(f"   Shadow data: {self.shadow_mesh_data is not None}")
        print(f"   External refs: {len(self.external_refs)}")
        print(f"   Skeleton hints: {len(self.skeleton_hints)}")
    
    def _process_hierarchy_enhanced(self, chunk: Chunk, loop_file: LoopFile):
        buffer = chunk.buffer
        bone_count = self.model_info.bone_count if self.model_info else 0
        
        if bone_count == 0:
            data_size = buffer.size()
            bone_count = data_size // 13
            if bone_count > 100 or bone_count == 0:
                print(f"   ⚠️ Warning: Could not estimate bone count from {data_size} bytes")
                return
        
        self._child_counts = []
        for i in range(bone_count):
            if buffer.eof():
                break
            self._child_counts.append(buffer.read_uint8())
        
        buffer.align(4)
        
        self._bone_positions = []
        for i in range(bone_count):
            if buffer.eof():
                break
            pos = Vector3.from_buffer(buffer)
            self._bone_positions.append(pos)
        
        if loop_file.has_chunk("BNAM"):
            name_chunk = loop_file.expect_chunk("BNAM")
            for i in range(bone_count):
                if name_chunk.buffer.eof():
                    break
                name = name_chunk.buffer.read_ascii_string(16)
                self.bone_names.append(name)
        
        print(f"✅ HIER: {len(self._child_counts)} bones, {len(self._bone_positions)} positions, {len(self.bone_names)} names")
    
    def _process_bone_names_enhanced(self, chunk: Chunk):
        buffer = chunk.buffer
        name_count = buffer.size() // 16
        for i in range(name_count):
            if buffer.eof():
                break
            name = buffer.read_ascii_string(16)
            if name not in self.bone_names:
                self.bone_names.append(name)
        print(f"✅ BNAM: {len(self.bone_names)} bone names")
    
    def _process_hprm_enhanced(self, chunk: Chunk):
        buffer = chunk.buffer
        param_count = buffer.size() // 12
        for i in range(param_count):
            if buffer.eof():
                break
            px = buffer.read_float()
            py = buffer.read_float()
            pz = buffer.read_float()
            self.bone_extra_params.append((px, py, pz))
        print(f"✅ HPRM: {len(self.bone_extra_params)} bone parameter sets")
    
    def _process_glow_enhanced(self, chunk: Chunk):
        buffer = chunk.buffer
        count = self.model_info.glow_count if self.model_info else 0
        if count == 0:
            count = buffer.size() // 32
        for _ in range(count):
            if buffer.eof():
                break
            g = GlowSprite.from_buffer(buffer)
            self.glow_sprites.append(g)
        print(f"✅ GLOW: {len(self.glow_sprites)} sprites")
    
    def _process_attachments_enhanced(self, chunk: Chunk):
        buffer = chunk.buffer
        count = self.model_info.attachment_count if self.model_info else 0
        if count == 0:
            count = buffer.size() // 64
        for _ in range(count):
            if buffer.eof():
                break
            a = Attachment.from_buffer(buffer)
            self.attachments.append(a)
        print(f"✅ ATTA: {len(self.attachments)} attachments")
    
    def _process_magic_vertices_enhanced(self, chunk: Chunk):
        buffer = chunk.buffer
        count = self.model_info.magic_vertex_count if self.model_info else 0
        if count == 0:
            count = buffer.size() // 16
        for _ in range(count):
            if buffer.eof():
                break
            mv = MagicVertex.from_buffer(buffer)
            self.magic_vertices.append(mv)
        print(f"✅ MVTX: {len(self.magic_vertices)} magic vertices")
    
    def _process_portal_enhanced(self, chunk: Chunk):
        buffer = chunk.buffer
        count = self.model_info.portal_count if self.model_info else 0
        if count == 0:
            count = buffer.size() // 20
        for _ in range(count):
            if buffer.eof():
                break
            p = Portal.from_buffer(buffer)
            self.portals.append(p)
        print(f"✅ PORT: {len(self.portals)} portals")
    
    def _process_portal_faces_enhanced(self, chunk: Chunk):
        buffer = chunk.buffer
        count = buffer.size() // 12
        for _ in range(count):
            if buffer.eof():
                break
            pf = PortalFace.from_buffer(buffer)
            self.portal_faces.append(pf)
        print(f"✅ PTFC: {len(self.portal_faces)} portal faces")
    
    def _process_portal_vertices_enhanced(self, chunk: Chunk):
        buffer = chunk.buffer
        count = buffer.size() // 12
        for _ in range(count):
            if buffer.eof():
                break
            pv = PortalVertex.from_buffer(buffer)
            self.portal_vertices.append(pv)
        print(f"✅ PTVX: {len(self.portal_vertices)} portal vertices")
    
    def _process_xtrw_enhanced(self, chunk: Chunk):
        buffer = chunk.buffer
        count = buffer.size() // 12
        for i in range(count):
            entry = XTRWEntry.from_buffer(buffer)
            self.vertex_weights.append(entry)
        print(f"✅ XTRW: {len(self.vertex_weights)} weight entries")
    
    def _process_xtxm_enhanced(self, chunk: Chunk):
        buffer = chunk.buffer
        count = buffer.size() // 36
        for i in range(count):
            if buffer.eof():
                break
            ref = TextureReference.from_buffer(buffer)
            self.texture_references.append(ref)
        print(f"✅ XTXM: {len(self.texture_references)} texture references")
    
    def _process_tcst_enhanced(self, chunk: Chunk):
        buffer = chunk.buffer
        uv_count = buffer.size() // 8
        uv_set = TextureCoordinateSet.from_buffer(buffer, uv_count)
        uv_set.index = len(self.extra_uv_sets)
        self.extra_uv_sets.append(uv_set)
        print(f"✅ TCST: {uv_count} UV coordinates")
    
    def _process_xtrn_enhanced(self, chunk: Chunk):
        buffer = chunk.buffer
        ref_name = buffer.read_ascii_string(min(64, buffer.size()))
        self.external_refs.append(ref_name)
        print(f"✅ XTRN: {ref_name}")
    
    def _process_nhsa_enhanced(self, chunk: Chunk):
        buffer = chunk.buffer
        hint_data = buffer.read(min(64, buffer.size()))
        self.skeleton_hints.append(hint_data)
        print(f"✅ NHSA: {len(hint_data)} bytes")
    
    def _process_txan_enhanced(self, chunk: Chunk):
        try:
            buffer = chunk.buffer
            txan = TXANData.from_buffer(buffer)
            self.txan_data.append(txan)
            print(f"✅ TXAN: {len(txan.unknown_fields)} fields")
        except Exception as e:
            print(f"   ⚠️ TXAN error: {e}")
    
    def _process_shadow_mesh_enhanced(self, chunk: Chunk, loop_file: LoopFile):
        try:
            buffer = chunk.buffer
            self.shadow_header_raw = buffer.data.copy()
            shadow_header = ShadowMeshHeader.from_buffer(buffer)
            print(f"✅ SMES: faces={shadow_header.face_count}, vertices={shadow_header.vertex_count}, edges={shadow_header.edge_count}")
            
            vertices = None
            faces = None
            edges = None
            
            if loop_file.has_chunk("SVTX"):
                vertex_chunk = loop_file.expect_chunk("SVTX")
                vertex_data = vertex_chunk.buffer.read(vertex_chunk.buffer.size())
                vertices = np.frombuffer(vertex_data, np.float32)
                if len(vertices) == shadow_header.vertex_count * 3:
                    vertices = vertices.reshape(-1, 3)
                print(f"   ✅ SVTX: {len(vertices)} vertices")
            
            if loop_file.has_chunk("SFAC"):
                face_chunk = loop_file.expect_chunk("SFAC")
                face_data = face_chunk.buffer.read(face_chunk.buffer.size())
                face_size = 32
                face_count = len(face_data) // face_size
                self.shadow_faces_detailed = []
                
                for i in range(face_count):
                    offset = i * face_size
                    v0 = int.from_bytes(face_data[offset:offset+4], 'little')
                    v1 = int.from_bytes(face_data[offset+4:offset+8], 'little')
                    v2 = int.from_bytes(face_data[offset+8:offset+12], 'little')
                    edge_flags = int.from_bytes(face_data[offset+12:offset+16], 'little')
                    nx = struct.unpack('<f', face_data[offset+16:offset+20])[0]
                    ny = struct.unpack('<f', face_data[offset+20:offset+24])[0]
                    nz = struct.unpack('<f', face_data[offset+24:offset+28])[0]
                    
                    self.shadow_faces_detailed.append({
                        'vertices': (v0, v1, v2),
                        'edge_flags': edge_flags,
                        'normal': (nx, ny, nz)
                    })
                
                faces = np.array([f['vertices'] for f in self.shadow_faces_detailed], dtype=np.uint32)
                print(f"   ✅ SFAC (detailed): {len(self.shadow_faces_detailed)} faces with normals")
            
            if loop_file.has_chunk("EGDE"):
                edge_chunk = loop_file.expect_chunk("EGDE")
                edge_data = edge_chunk.buffer.read(edge_chunk.buffer.size())
                if len(edge_data) > 0:
                    edges = np.frombuffer(edge_data, np.uint32).reshape(-1, 2)
                    self.shadow_edges_raw = edges
                    print(f"   ✅ EGDE: {len(edges)} edges")
            
            if vertices is not None and len(vertices) > 0:
                self.shadow_mesh_data = ShadowMeshDataIGI2(shadow_header, faces, vertices, edges)
                print(f"   ✅ Shadow mesh loaded: {len(vertices)} vertices, {len(faces) if faces is not None else 0} faces")
            else:
                print("   ⚠️ No shadow vertices found")
                
        except Exception as e:
            print(f"   ⚠️ Shadow mesh error: {e}")
    
    def _process_render_mesh_enhanced(self, chunk: Chunk, loop_file: LoopFile):
        try:
            assert self.render_mesh_data is None, "Render mesh already exists"
            render_mesh_info = RenderMeshHeader.from_buffer(chunk.buffer)
            
            if not loop_file.has_chunk("FACE"):
                print("   ⚠️ Missing FACE chunk, skipping render mesh")
                return
            
            face_chunk = loop_file.expect_chunk("FACE")
            faces_data = face_chunk.buffer.read(face_chunk.buffer.size())
            faces = np.frombuffer(faces_data, np.uint16).reshape(-1, 3)
            
            if not loop_file.has_chunk("REND"):
                print("   ⚠️ Missing REND chunk, skipping render mesh")
                return
            
            rend_chunk = loop_file.expect_chunk("REND")
            render_info = []
            for _ in range(render_mesh_info.face_group_count):
                render_info.append(FaceGroup.from_buffer(rend_chunk.buffer, self.model_info.model_type))
            
            if not loop_file.has_chunk("VRTX"):
                print("   ⚠️ Missing VRTX chunk, skipping render mesh")
                return
            
            vert_chunk = loop_file.expect_chunk("VRTX")
            model_type = self.model_info.model_type
            
            if model_type == ModelType.StaticModel:
                dtype = np.dtype([
                    ("pos", np.float32, (3,)),
                    ("normal", np.float32, (3,)),
                    ("uv0", np.float32, (2,))
                ])
            elif model_type == ModelType.SkinnedModel:
                dtype = np.dtype([
                    ("pos", np.float32, (3,)),
                    ("normal", np.float32, (3,)),
                    ("uv0", np.float32, (2,)),
                    ("weight", np.float32, (1,)),
                    ("index", np.ushort, (1,)),
                    ("bone_id", np.ushort, (1,))
                ])
            elif model_type == ModelType.LightmappedModel:
                dtype = np.dtype([
                    ("pos", np.float32, (3,)),
                    ("uv0", np.float32, (2,)),
                    ("uv1", np.float32, (2,))
                ])
            else:
                dtype = np.dtype([
                    ("pos", np.float32, (3,)),
                    ("normal", np.float32, (3,)),
                    ("uv0", np.float32, (2,))
                ])
            
            vert_data = vert_chunk.buffer.read(vert_chunk.buffer.size())
            vertices = np.frombuffer(vert_data, dtype)
            
            lightmap_uvs = None
            if loop_file.has_chunk("LTMP"):
                try:
                    lightmap_chunk = loop_file.expect_chunk("LTMP")
                    lightmap_data = lightmap_chunk.buffer.read(lightmap_chunk.buffer.size())
                    uv_count = len(lightmap_data) // 8
                    if uv_count > 0:
                        lightmap_uvs = np.frombuffer(lightmap_data, np.float32).reshape(-1, 2)
                        print(f"   ✅ LTMP: {len(lightmap_uvs)} lightmap UVs")
                except Exception as e:
                    print(f"   ⚠️ LTMP error: {e}")
            
            self.render_mesh_data = RenderMeshDataIGI2(render_mesh_info, faces, vertices, render_info, lightmap_uvs)
            print(f"✅ RD3D: {len(vertices)} vertices, {len(faces)} faces, {len(render_info)} material groups")
            
        except Exception as e:
            print(f"   ⚠️ Render mesh error: {e}")
    
    def _process_collision_mesh_enhanced(self, chunk: Chunk, loop_file: LoopFile):
        try:
            collision_mesh_info = CollisionMeshHeader.from_buffer(chunk.buffer)
            
            if loop_file.has_chunk("CVTX"):
                vertices_chunk = loop_file.expect_chunk("CVTX")
                vertices_data = vertices_chunk.buffer.read(vertices_chunk.buffer.size())
                vertices0 = np.frombuffer(vertices_data, CollisionVertexDtype).copy()
                print(f"   ✅ CVTX0: {len(vertices0)} vertices")
            else:
                vertices0 = np.array([], dtype=CollisionVertexDtype)
            
            if loop_file.has_chunk("CFCE"):
                faces_chunk = loop_file.expect_chunk("CFCE")
                faces_data = faces_chunk.buffer.read(faces_chunk.buffer.size())
                faces0 = np.frombuffer(faces_data, CollisionFaceDtype)
                print(f"   ✅ CFCE0: {len(faces0)} faces")
            else:
                faces0 = np.array([], dtype=CollisionFaceDtype)
            
            if loop_file.has_chunk("CMAT"):
                try:
                    materials_chunk = loop_file.expect_chunk("CMAT")
                    self._process_collision_materials_enhanced(materials_chunk)
                    materials0 = self.collision_materials.copy()
                except:
                    materials0 = []
            else:
                materials0 = []
            
            if loop_file.has_chunk("CSPH"):
                spheres_chunk = loop_file.expect_chunk("CSPH")
                spheres_data = spheres_chunk.buffer.read(spheres_chunk.buffer.size())
                spheres0 = np.frombuffer(spheres_data, CollisionSphereDtype).copy()
                print(f"   ✅ CSPH0: {len(spheres0)} spheres")
            else:
                spheres0 = np.array([], dtype=CollisionSphereDtype)
            
            self.collision_mesh_data = CollisionMeshDataIGI2(
                collision_mesh_info, spheres0, faces0, vertices0, materials0
            )
            print(f"✅ CMSH0: {len(vertices0)} vertices, {len(faces0)} faces")
            
            if collision_mesh_info.mesh1.face_count > 0:
                print(f"\n   📦 Processing second collision mesh (mesh1)")
                
                try:
                    vertices_chunk2 = loop_file.expect_chunk("CVTX")
                    vertices_data2 = vertices_chunk2.buffer.read(vertices_chunk2.buffer.size())
                    vertices1 = np.frombuffer(vertices_data2, CollisionVertexDtype).copy()
                    print(f"   ✅ CVTX1: {len(vertices1)} vertices")
                except:
                    vertices1 = np.array([], dtype=CollisionVertexDtype)
                
                try:
                    faces_chunk2 = loop_file.expect_chunk("CFCE")
                    faces_data2 = faces_chunk2.buffer.read(faces_chunk2.buffer.size())
                    faces1 = np.frombuffer(faces_data2, CollisionFaceDtype)
                    print(f"   ✅ CFCE1: {len(faces1)} faces")
                except:
                    faces1 = np.array([], dtype=CollisionFaceDtype)
                
                try:
                    materials_chunk2 = loop_file.expect_chunk("CMAT")
                    self.collision_materials_mesh1 = []
                    self._process_collision_materials_enhanced(materials_chunk2, use_mesh1=True)
                    materials1 = self.collision_materials_mesh1
                    print(f"   ✅ CMAT1: {len(materials1)} materials")
                except:
                    materials1 = []
                
                try:
                    spheres_chunk2 = loop_file.expect_chunk("CSPH")
                    spheres_data2 = spheres_chunk2.buffer.read(spheres_chunk2.buffer.size())
                    spheres1 = np.frombuffer(spheres_data2, CollisionSphereDtype).copy()
                    print(f"   ✅ CSPH1: {len(spheres1)} spheres")
                except:
                    spheres1 = np.array([], dtype=CollisionSphereDtype)
                
                if len(vertices1) > 0 and len(faces1) > 0:
                    self.collision_mesh_data2 = CollisionMeshDataIGI2(
                        collision_mesh_info, spheres1, faces1, vertices1, materials1
                    )
                    print(f"   ✅ Second collision mesh loaded")
                    
        except Exception as e:
            print(f"   ⚠️ Collision mesh error: {e}")
    
    def _process_collision_materials_enhanced(self, chunk: Chunk, use_mesh1: bool = False):
        buffer = chunk.buffer
        data_size = buffer.size()
        material_size = 16
        count = data_size // material_size
        
        materials = []
        for i in range(count):
            if buffer.eof():
                break
            try:
                mat = CollisionMaterialIGI2.from_buffer(buffer)
                materials.append(mat)
            except Exception as e:
                print(f"   ⚠️ Material {i} error: {e}")
                break
        
        if use_mesh1:
            if not hasattr(self, 'collision_materials_mesh1'):
                self.collision_materials_mesh1 = []
            self.collision_materials_mesh1.extend(materials)
        else:
            self.collision_materials = materials
        
        print(f"   ✅ CMAT: {len(materials)} materials" + (" (mesh1)" if use_mesh1 else ""))
    
    def export_shadow_detailed(self, out_dir: str, base_name: str):
        if not hasattr(self, 'shadow_faces_detailed') or not self.shadow_faces_detailed:
            return
        
        json_path = os.path.join(out_dir, f"{base_name}_shadow_faces_detailed.json")
        data = convert_to_json_serializable(self.shadow_faces_detailed)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   Shadow faces detailed (JSON): {json_path}")
        
        txt_path = os.path.join(out_dir, f"{base_name}_shadow_faces_detailed.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# CAFS (Shadow Faces with Normals) - Detailed\n")
            f.write(f"Total Faces: {len(self.shadow_faces_detailed)}\n\n")
            for i, face in enumerate(self.shadow_faces_detailed):
                nx, ny, nz = face['normal']
                f.write(f"Face {i:6d}: v=({face['vertices'][0]:4d}, {face['vertices'][1]:4d}, {face['vertices'][2]:4d}), "
                       f"edge_flags={face['edge_flags']:4d}, "
                       f"n=({nx:7.3f}, {ny:7.3f}, {nz:7.3f})\n")
        print(f"   Shadow faces detailed (TXT): {txt_path}")
    
    def export_hprm_detailed(self, out_dir: str, base_name: str):
        if not hasattr(self, 'bone_extra_params') or not self.bone_extra_params:
            return
        
        json_path = os.path.join(out_dir, f"{base_name}_hprm.json")
        data = convert_to_json_serializable([
            {"bone_index": i, "params": list(params)} 
            for i, params in enumerate(self.bone_extra_params)
        ])
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   HPRM (JSON): {json_path}")
        
        txt_path = os.path.join(out_dir, f"{base_name}_hprm.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# HPRM (Additional Bone Parameters)\n")
            f.write("# Format: bone_index: param_x, param_y, param_z\n\n")
            for i, params in enumerate(self.bone_extra_params):
                bone_name = self.bone_names[i] if i < len(self.bone_names) else f"bone_{i}"
                f.write(f"Bone {i:3d} ({bone_name}): ({params[0]:8.4f}, {params[1]:8.4f}, {params[2]:8.4f})\n")
        print(f"   HPRM (TXT): {txt_path}")
    
    def export_external_refs(self, out_dir: str, base_name: str):
        if not hasattr(self, 'external_refs') or not self.external_refs:
            return
        
        txt_path = os.path.join(out_dir, f"{base_name}_external_refs.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# XTRN (External References)\n\n")
            for i, ref in enumerate(self.external_refs):
                f.write(f"{i:3d}: {ref}\n")
        print(f"   External references (TXT): {txt_path}")
    
    def export_skeleton_hints(self, out_dir: str, base_name: str):
        if not hasattr(self, 'skeleton_hints') or not self.skeleton_hints:
            return
        
        bin_path = os.path.join(out_dir, f"{base_name}_skeleton_hints.bin")
        with open(bin_path, 'wb') as f:
            for hint in self.skeleton_hints:
                f.write(hint)
        print(f"   Skeleton hints (BIN): {bin_path}")
        
        hex_path = os.path.join(out_dir, f"{base_name}_skeleton_hints.txt")
        with open(hex_path, 'w', encoding='utf-8') as f:
            f.write("# NHSA (Skeleton Hints)\n\n")
            for i, hint in enumerate(self.skeleton_hints):
                hex_str = ' '.join(f'{b:02x}' for b in hint)
                f.write(f"Hint {i} ({len(hint)} bytes): {hex_str}\n")
        print(f"   Skeleton hints hex (TXT): {hex_path}")
    
    def export_all_enhanced(self, out_dir, export_formats=None, lightmap_format="png"):
        if export_formats is None:
            export_formats = ["obj", "json", "txt"]
        
        base_name = os.path.splitext(os.path.basename(out_dir))[0]
        self.ensure_dir(out_dir)
        
        print(f"\n📦 Enhanced Export to {out_dir}")
        print("-" * 50)
        
        self.export_hsem_info(out_dir, base_name)
        self.export_d3dr_info(out_dir, base_name)
        self.export_manb_detailed(out_dir, base_name)
        self.export_reih_detailed(out_dir, base_name)
        
        self.export_hprm_detailed(out_dir, base_name)
        self.export_shadow_detailed(out_dir, base_name)
        self.export_external_refs(out_dir, base_name)
        self.export_skeleton_hints(out_dir, base_name)
        
        self.export_render_mesh(out_dir, base_name, export_formats)
        self.export_collision_mesh(out_dir, base_name, 0, export_formats)
        if self.collision_mesh_data2:
            self.export_collision_mesh(out_dir, base_name, 1, export_formats)
        
        self.export_all_collision_mesh_data(out_dir, base_name)
        self.export_shadow_mesh_enhanced(out_dir, base_name, export_formats)
        self.export_attachments(out_dir, base_name)
        self.export_lightmaps(out_dir, base_name, lightmap_format)
        self.export_extra_data(out_dir, base_name)
        
        self.export_magic_vertices_improved(out_dir, base_name)
        self.export_portals_as_mesh(out_dir, base_name)
        self.export_glow_sprites_improved(out_dir, base_name)
        self.export_mrph_info(out_dir, base_name)
        self.export_txan_info(out_dir, base_name)
        self.export_xtrw_info(out_dir, base_name)
        self.export_xtxm_info(out_dir, base_name)
        self.export_tcst_info(out_dir, base_name)
        
        print("-" * 50)
        print("✅ Enhanced export completed successfully!")

    # ========== دوال التصدير الأساسية (الموجودة مسبقاً) ==========
    
    def ensure_dir(self, path):
        Path(path).mkdir(parents=True, exist_ok=True)

    def export_mtl(self, out_dir, base_name, suffix, texture_name=None, has_lightmap=False, material_index=0):
        if material_index > 0:
            mtl_filename = f"{base_name}{suffix}_{material_index}.mtl"
            mat_name = f"Mat_{base_name}{suffix}_{material_index}"
        else:
            mtl_filename = f"{base_name}{suffix}.mtl"
            mat_name = f"Mat_{base_name}{suffix}"
        
        mtl_path = os.path.join(out_dir, mtl_filename)
        
        if texture_name is None:
            texture_name = f"{base_name}.tga"
        
        with open(mtl_path, "w", encoding="utf-8") as f:
            f.write(f"newmtl {mat_name}\n")
            f.write("Ns 10.0000\n")
            f.write("Ka 1.0000 1.0000 1.0000\n")
            f.write("Kd 1.0000 1.0000 1.0000\n")
            f.write("Ks 0.0000 0.0000 0.0000\n")
            f.write(f"map_Kd {texture_name}\n")
            
            if has_lightmap:
                lightmap_name = f"{base_name}_lightmap_{material_index}.png"
                f.write(f"map_Ke {lightmap_name}\n")
                
        print(f"   MTL: {mtl_filename}")
        return mtl_filename, mat_name

    def export_obj(self, out_dir, base_name, suffix, faces, vertices, 
                   has_normals=True, has_uv2=False, lightmap_uvs=None, mtl_filename=None):
        obj_path = os.path.join(out_dir, f"{base_name}{suffix}.obj")
        
        if mtl_filename is None:
            mtl_file, mat_name = self.export_mtl(out_dir, base_name, suffix, 
                                                 f"{base_name}.tga", 
                                                 has_lightmap=(lightmap_uvs is not None))
            using_multi_material = False
            default_mat_name = mat_name
        else:
            mtl_file = mtl_filename
            using_multi_material = True
            default_mat_name = f"Mat_{base_name}{suffix}_0"
        
        with open(obj_path, "w", encoding="utf-8") as f:
            f.write(f"mtllib {mtl_file}\n")
            f.write(f"o {base_name}{suffix}\n")
            
            for v in vertices:
                f.write(f"v {v['px']:.6f} {v['py']:.6f} {v['pz']:.6f}\n")
            
            if "u" in vertices.dtype.names and "v" in vertices.dtype.names:
                for v in vertices:
                    f.write(f"vt {v['u']:.6f} {1.0 - v['v']:.6f}\n")
            
            if lightmap_uvs is not None:
                for uv in lightmap_uvs:
                    f.write(f"vt {uv[0]:.6f} {1.0 - uv[1]:.6f}\n")
            elif has_uv2 and "u1" in vertices.dtype.names and "v1" in vertices.dtype.names:
                for v in vertices:
                    f.write(f"vt {v['u1']:.6f} {1.0 - v['v1']:.6f}\n")
            
            if has_normals and "nx" in vertices.dtype.names:
                for v in vertices:
                    f.write(f"vn {v['nx']:.6f} {v['ny']:.6f} {v['nz']:.6f}\n")
            
            if faces is not None and len(faces) > 0:
                if not using_multi_material or not hasattr(self.render_mesh_data, 'primitives') or not self.render_mesh_data.primitives:
                    f.write(f"usemtl {default_mat_name}\n")
                    for face in faces:
                        if len(face) >= 3:
                            a, b, c = face[0], face[1], face[2]
                            a1 = a + 1
                            b1 = b + 1
                            c1 = c + 1
                            
                            if has_normals:
                                f.write(f"f {a1}/{a1}/{a1} {b1}/{b1}/{b1} {c1}/{c1}/{c1}\n")
                            else:
                                f.write(f"f {a1}/{a1} {b1}/{b1} {c1}/{c1}\n")
                else:
                    primitives = self.render_mesh_data.primitives
                    current_face_index = 0
                    
                    for i, prim in enumerate(primitives):
                        face_count = prim.face_count
                        if face_count > 0:
                            mat_name = f"Mat_{base_name}{suffix}_{i}"
                            f.write(f"usemtl {mat_name}\n")
                            
                            for j in range(face_count):
                                if current_face_index + j < len(faces):
                                    face = faces[current_face_index + j]
                                    if len(face) >= 3:
                                        a, b, c = face[0], face[1], face[2]
                                        a1 = a + 1
                                        b1 = b + 1
                                        c1 = c + 1
                                        
                                        if has_normals:
                                            f.write(f"f {a1}/{a1}/{a1} {b1}/{b1}/{b1} {c1}/{c1}/{c1}\n")
                                        else:
                                            f.write(f"f {a1}/{a1} {b1}/{b1} {c1}/{c1}\n")
                            
                            current_face_index += face_count
            else:
                f.write("# No faces in this mesh\n")
                
        print(f"   OBJ: {obj_path}")

    def export_obj_material_group(self, out_dir, base_name, suffix, 
                                  faces_subset, vertices, 
                                  material_index, face_offset,
                                  has_normals=True, has_uv2=False, lightmap_uvs=None):
        obj_filename = f"{base_name}{suffix}_{material_index}.obj"
        obj_path = os.path.join(out_dir, obj_filename)
        mtl_file, mat_name = self.export_mtl(out_dir, base_name, suffix, 
                                             f"{base_name}_{material_index}.tga", 
                                             has_lightmap=(lightmap_uvs is not None),
                                             material_index=material_index)
        
        with open(obj_path, "w", encoding="utf-8") as f:
            f.write(f"mtllib {mtl_file}\n")
            f.write(f"o {base_name}{suffix}_{material_index}\n")
            
            for v in vertices:
                f.write(f"v {v['px']:.6f} {v['py']:.6f} {v['pz']:.6f}\n")
            
            if "u" in vertices.dtype.names and "v" in vertices.dtype.names:
                for v in vertices:
                    f.write(f"vt {v['u']:.6f} {1.0 - v['v']:.6f}\n")
            
            if has_normals and "nx" in vertices.dtype.names:
                for v in vertices:
                    f.write(f"vn {v['nx']:.6f} {v['ny']:.6f} {v['nz']:.6f}\n")
            
            f.write(f"usemtl {mat_name}\n")
            
            if faces_subset is not None and len(faces_subset) > 0:
                for face in faces_subset:
                    if len(face) >= 3:
                        a, b, c = face[0], face[1], face[2]
                        a1 = a + 1
                        b1 = b + 1
                        c1 = c + 1
                        
                        if has_normals:
                            f.write(f"f {a1}/{a1}/{a1} {b1}/{b1}/{b1} {c1}/{c1}/{c1}\n")
                        else:
                            f.write(f"f {a1}/{a1} {b1}/{b1} {c1}/{c1}\n")
        
        print(f"   OBJ material group {material_index}: {obj_path}")
        return obj_path

    def export_render_mesh_simple(self, out_dir, base_name, export_formats=None):
        if export_formats is None:
            export_formats = ["obj"]
        
        if self.render_mesh_data is None:
            print("No render mesh data")
            return
        
        vertices = self.render_mesh_data.vertices
        faces = self.render_mesh_data.faces
        primitives = self.render_mesh_data.primitives
        model_type = self.model_info.model_type
        lightmap_uvs = self.render_mesh_data.lightmap_uvs
        
        print("First 10 vertices raw data:")
        for i in range(min(10, len(vertices))):
            v = vertices[i]
            v_dict = {}
            for name in v.dtype.names:
                v_dict[name] = v[name]
            
            if model_type == ModelType.SkinnedModel:
                weight_val = v_dict['weight']
                if isinstance(weight_val, np.ndarray):
                    weight_str = f"{weight_val[0]:.2f}" if len(weight_val) > 0 else "0.00"
                else:
                    weight_str = f"{weight_val:.2f}"
                
                index_val = v_dict['index']
                if isinstance(index_val, np.ndarray):
                    index_str = str(index_val[0]) if len(index_val) > 0 else "0"
                else:
                    index_str = str(index_val)
                
                bone_id_val = v_dict['bone_id']
                if isinstance(bone_id_val, np.ndarray):
                    bone_id_str = str(bone_id_val[0]) if len(bone_id_val) > 0 else "0"
                else:
                    bone_id_str = str(bone_id_val)
                
                print(f"  v{i}: pos=({v_dict['pos'][0]:.2f}, {v_dict['pos'][1]:.2f}, {v_dict['pos'][2]:.2f}), "
                      f"normal=({v_dict['normal'][0]:.2f}, {v_dict['normal'][1]:.2f}, {v_dict['normal'][2]:.2f}), "
                      f"uv0=({v_dict['uv0'][0]:.2f}, {v_dict['uv0'][1]:.2f}), "
                      f"weight={weight_str}, index={index_str}, bone_id={bone_id_str}")
            elif model_type == ModelType.StaticModel:
                print(f"  v{i}: pos=({v_dict['pos'][0]:.2f}, {v_dict['pos'][1]:.2f}, {v_dict['pos'][2]:.2f}), "
                      f"normal=({v_dict['normal'][0]:.2f}, {v_dict['normal'][1]:.2f}, {v_dict['normal'][2]:.2f}), "
                      f"uv0=({v_dict['uv0'][0]:.2f}, {v_dict['uv0'][1]:.2f})")
            elif model_type == ModelType.LightmappedModel:
                print(f"  v{i}: pos=({v_dict['pos'][0]:.2f}, {v_dict['pos'][1]:.2f}, {v_dict['pos'][2]:.2f}), "
                      f"uv0=({v_dict['uv0'][0]:.2f}, {v_dict['uv0'][1]:.2f}), "
                      f"uv1=({v_dict['uv1'][0]:.2f}, {v_dict['uv1'][1]:.2f})")
            else:
                fields = []
                for name in v.dtype.names:
                    val = v_dict[name]
                    if isinstance(val, np.ndarray):
                        if len(val) >= 3:
                            fields.append(f"{name}=({val[0]:.2f}, {val[1]:.2f}, {val[2]:.2f})")
                        elif len(val) == 2:
                            fields.append(f"{name}=({val[0]:.2f}, {val[1]:.2f})")
                        elif len(val) == 1:
                            fields.append(f"{name}={val[0]:.2f}" if isinstance(val[0], (float, np.float32)) else f"{name}={val[0]}")
                        else:
                            fields.append(f"{name}={val}")
                    else:
                        if isinstance(val, (float, np.float32, np.float64)):
                            fields.append(f"{name}={val:.2f}")
                        else:
                            fields.append(f"{name}={val}")
                print(f"  v{i}: " + ", ".join(fields))
        
        if model_type == ModelType.SkinnedModel and self.bones:
            parents = [bone.parent_id for bone in self.bones]
            bind_local = [make_translation_matrix(b.pos.x, b.pos.y, b.pos.z) for b in self.bones]
            bind_global = [None] * len(self.bones)
            
            for i in range(len(self.bones)):
                if parents[i] == -1:
                    bind_global[i] = bind_local[i]
                else:
                    bind_global[i] = bind_global[parents[i]] @ bind_local[i]
            
            inverse_bind = [np.linalg.inv(m) for m in bind_global]
            root_inv = np.linalg.inv(bind_global[0]) if bind_global else None
            
            vertices_transformed = bake_skinning_improved(
                vertices, bind_global, inverse_bind, root_inv,
                debug_params=self.debug_params,
                extra_weights=self.vertex_weights
            )
        else:
            dtype_out = np.dtype([
                ("px", np.float32), ("py", np.float32), ("pz", np.float32),
                ("nx", np.float32), ("ny", np.float32), ("nz", np.float32),
                ("u", np.float32), ("v", np.float32)
            ])
            new_verts = []
            for v in vertices:
                pos = v["pos"] if "pos" in v.dtype.names else (v["px"], v["py"], v["pz"])
                normal = v["normal"] if "normal" in v.dtype.names else (0, 0, 0)
                uv = v["uv0"] if "uv0" in v.dtype.names else (0, 0)
                
                px, py, pz = self.debug_params.swizzle(pos[0], pos[1], pos[2], self.debug_params.v_scale)
                nx, ny, nz = self.debug_params.swizzle(normal[0], normal[1], normal[2], 1.0)
                
                new_verts.append((
                    px, py, pz,
                    nx, ny, nz,
                    float(uv[0]), float(uv[1])
                ))
            vertices_transformed = np.array(new_verts, dtype=dtype_out)

        has_normals = "nx" in vertices_transformed.dtype.names
        has_uv = "u" in vertices_transformed.dtype.names
        
        material_groups = []
        if primitives:
            for i, prim in enumerate(primitives):
                texture_index = prim.diffuse_texture if hasattr(prim, 'diffuse_texture') else 0
                texture_name = get_texture_name(texture_index, base_name, i, self.texture_references)
                material_groups.append({
                    "index": i,
                    "texture_index": texture_index,
                    "texture_name": texture_name,
                    "faces": faces[prim.index_offset:prim.index_offset + prim.face_count]
                })
        else:
            material_groups.append({
                "index": 0,
                "texture_index": 0,
                "texture_name": get_texture_name(0, base_name, 0, self.texture_references),
                "faces": faces
            })
        
        if "obj" in export_formats:
            atlas = None
            if primitives and len(primitives) > 1:
                print(f"   DEBUG: Creating texture atlas for {len(primitives)} materials")
                atlas = self.create_texture_atlas(out_dir, base_name)
                if atlas:
                    print(f"   DEBUG: Applying texture atlas")
                    vertices_transformed = self.apply_texture_atlas_igi2(atlas, vertices_transformed, primitives, base_name)
                    print(f"   DEBUG: Atlas applied")
            
            if primitives and len(primitives) > 1:
                mtl_filename = f"{base_name}_render.mtl"
                mtl_path = os.path.join(out_dir, mtl_filename)
                
                with open(mtl_path, "w", encoding="utf-8") as f:
                    for i, prim in enumerate(primitives):
                        texture_index = prim.diffuse_texture if hasattr(prim, 'diffuse_texture') else 0
                        texture_name = get_texture_name(texture_index, base_name, i, self.texture_references)
                        
                        if atlas and atlas.has_multiple_textures():
                            texture_name = f"{base_name}_atlas.png"
                        
                        mat_name = f"Mat_{base_name}_render_{i}"
                        
                        f.write(f"newmtl {mat_name}\n")
                        f.write("Ns 10.0000\n")
                        f.write("Ka 1.0000 1.0000 1.0000\n")
                        f.write("Kd 1.0000 1.0000 1.0000\n")
                        f.write("Ks 0.0000 0.0000 0.0000\n")
                        f.write(f"map_Kd {texture_name}\n")
                        
                        if lightmap_uvs is not None:
                            lightmap_name = f"{base_name}_lightmap_{i}.png"
                            f.write(f"map_Ke {lightmap_name}\n")
                        
                        f.write("\n")
                
                print(f"   MTL (multi-material): {mtl_path}")
                
                self.export_obj(out_dir, base_name, "_render", faces, vertices_transformed,
                               has_normals, model_type == ModelType.LightmappedModel, 
                               lightmap_uvs, mtl_filename=mtl_filename)
            else:
                self.export_obj(out_dir, base_name, "_render", faces, vertices_transformed,
                               has_normals, model_type == ModelType.LightmappedModel, lightmap_uvs)
        
        if "gltf" in export_formats:
            has_skinning = model_type == ModelType.SkinnedModel and self.bones
            gltf_path = os.path.join(out_dir, f"{base_name}_render")
            
            bones_data = None
            if has_skinning and self.bones:
                bones_data = self.bones
            
            if has_skinning:
                vertices_for_gltf = self.prepare_skinned_vertices_for_gltf(vertices_transformed)
                print(f"   Prepared skinned vertices for glTF: {len(vertices_for_gltf)} vertices with weight/bone_id")
            else:
                vertices_for_gltf = vertices_transformed
            
            export_to_gltf_full(self, gltf_path, f"{base_name}_render",
                                vertices_for_gltf, faces, 
                                has_normals, has_uv, has_skinning, bones_data)
        
        if "dae" in export_formats:
            all_faces = []
            for mg in material_groups:
                all_faces.extend(mg["faces"])
            all_faces_array = np.array(all_faces)
            
            dae_path = os.path.join(out_dir, f"{base_name}_render.dae")
            export_to_collada(self, dae_path, f"{base_name}_render", 
                             vertices_transformed, all_faces_array, has_normals, has_uv)
        
        if "directx" in export_formats:
            # تصدير DirectX (.X) كامل مع العظام والتزين
            print(f"   DEBUG: DirectX export called for {base_name}")
            dx_path = os.path.join(out_dir, f"{base_name}_render.x")
            print(f"   DEBUG: DirectX path: {dx_path}")
            export_to_directx(self, dx_path, "igi2" if hasattr(self, 'txan_data') else "igi1")
            print(f"   DEBUG: DirectX export completed")

    def prepare_skinned_vertices_for_gltf(self, vertices: np.ndarray) -> np.ndarray:
        dtype_out = np.dtype([
            ("px", np.float32), ("py", np.float32), ("pz", np.float32),
            ("nx", np.float32), ("ny", np.float32), ("nz", np.float32),
            ("u", np.float32), ("v", np.float32),
            ("weight", np.float32), ("bone_id", np.uint16)
        ])
        
        new_verts = []
        for v in vertices:
            px = float(v["px"]) if "px" in v.dtype.names else 0.0
            py = float(v["py"]) if "py" in v.dtype.names else 0.0
            pz = float(v["pz"]) if "pz" in v.dtype.names else 0.0
            
            nx = float(v["nx"]) if "nx" in v.dtype.names else 0.0
            ny = float(v["ny"]) if "ny" in v.dtype.names else 0.0
            nz = float(v["nz"]) if "nz" in v.dtype.names else 0.0
            
            u = float(v["u"]) if "u" in v.dtype.names else 0.0
            vt = float(v["v"]) if "v" in v.dtype.names else 0.0
            
            weight_val = 1.0
            bone_id_val = 0
            
            if "weight" in v.dtype.names:
                w = v["weight"]
                if isinstance(w, np.ndarray):
                    weight_val = float(w[0]) if len(w) > 0 else 1.0
                else:
                    weight_val = float(w)
            
            if "bone_id" in v.dtype.names:
                b = v["bone_id"]
                if isinstance(b, np.ndarray):
                    bone_id_val = int(b[0]) if len(b) > 0 else 0
                else:
                    bone_id_val = int(b)
            
            new_verts.append((
                px, py, pz,
                nx, ny, nz,
                u, vt,
                weight_val, bone_id_val
            ))
        
        return np.array(new_verts, dtype=dtype_out)

    def export_obj_multi_material(self, out_dir, base_name, suffix, 
                                  vertices, material_groups,
                                  has_normals=True, has_uv=True, lightmap_uvs=None,
                                  atlas=None):
        obj_path = os.path.join(out_dir, f"{base_name}{suffix}.obj")
        
        mtl_filename = f"{base_name}{suffix}.mtl"
        mtl_path = os.path.join(out_dir, mtl_filename)
        
        atlas_mode = ATLAS_MODE
        
        with open(mtl_path, "w", encoding="utf-8") as f:
            if atlas and atlas.has_multiple_textures() and atlas_mode == "merge":
                f.write(f"newmtl atlas_material\n")
                f.write("Ns 10.0000\n")
                f.write("Ka 1.0000 1.0000 1.0000\n")
                f.write("Kd 1.0000 1.0000 1.0000\n")
                f.write("Ks 0.0000 0.0000 0.0000\n")
                f.write(f"map_Kd {base_name}_atlas.png\n")
                print(f"   ✅ MTL mode: MERGE (single 'atlas_material')")
                
            else:
                atlas_name = f"{base_name}_atlas.png" if atlas and atlas.has_multiple_textures() else None
                
                for mg in material_groups:
                    mat_index = mg["index"]
                    texture_index = mg.get("texture_index", 0)
                    texture_name = get_texture_name(texture_index, base_name, mat_index, None)
                    
                    if atlas_name:
                        texture_name = atlas_name
                    
                    mat_name = f"Mat_{base_name}{suffix}_{mat_index}"
                    
                    f.write(f"newmtl {mat_name}\n")
                    f.write("Ns 10.0000\n")
                    f.write("Ka 1.0000 1.0000 1.0000\n")
                    f.write("Kd 1.0000 1.0000 1.0000\n")
                    f.write("Ks 0.0000 0.0000 0.0000\n")
                    f.write(f"map_Kd {texture_name}\n")
                    f.write("\n")
                
                if atlas_name:
                    print(f"   ✅ MTL mode: PRESERVE (keeping {len(material_groups)} materials, using atlas)")
                
                if lightmap_uvs is not None:
                    lightmap_name = f"{base_name}_lightmap_{mat_index}.png"
                    f.write(f"map_Ke {lightmap_name}\n")
                
                f.write("\n")
        
        with open(obj_path, "w", encoding="utf-8") as f:
            f.write(f"mtllib {mtl_filename}\n")
            f.write(f"o {base_name}{suffix}\n")
            
            for v in vertices:
                f.write(f"v {v['px']:.6f} {v['py']:.6f} {v['pz']:.6f}\n")
            
            if has_uv:
                for v in vertices:
                    f.write(f"vt {v['u']:.6f} {1.0 - v['v']:.6f}\n")
            
            if has_normals:
                for v in vertices:
                    f.write(f"vn {v['nx']:.6f} {v['ny']:.6f} {v['nz']:.6f}\n")
            
            if atlas and atlas.has_multiple_textures() and atlas_mode == "merge":
                f.write(f"usemtl atlas_material\n")
                for mg in material_groups:
                    for face in mg["faces"]:
                        if len(face) >= 3:
                            a, b, c = face[0], face[1], face[2]
                            a1, b1, c1 = a+1, b+1, c+1
                            
                            if has_normals:
                                f.write(f"f {a1}/{a1}/{a1} {b1}/{b1}/{b1} {c1}/{c1}/{c1}\n")
                            else:
                                f.write(f"f {a1}/{a1} {b1}/{b1} {c1}/{c1}\n")
            else:
                for mg in material_groups:
                    mat_index = mg["index"]
                    mat_name = f"Mat_{base_name}{suffix}_{mat_index}"
                    f.write(f"usemtl {mat_name}\n")
                    
                    for face in mg["faces"]:
                        if len(face) >= 3:
                            a, b, c = face[0], face[1], face[2]
                            a1, b1, c1 = a+1, b+1, c+1
                            
                            if has_normals:
                                f.write(f"f {a1}/{a1}/{a1} {b1}/{b1}/{b1} {c1}/{c1}/{c1}\n")
                            else:
                                f.write(f"f {a1}/{a1} {b1}/{b1} {c1}/{c1}\n")
                                
        print(f"   OBJ (multi-material): {obj_path}")
        print(f"   MTL (multi-material): {mtl_path}")

    def export_render_mesh_multi_material(self, out_dir, base_name, export_formats=None):
        if export_formats is None:
            export_formats = ["obj"]
        
        if self.render_mesh_data is None:
            print("No render mesh data")
            return
        
        vertices = self.render_mesh_data.vertices
        faces = self.render_mesh_data.faces
        primitives = self.render_mesh_data.primitives
        model_type = self.model_info.model_type
        lightmap_uvs = self.render_mesh_data.lightmap_uvs
        
        if model_type == ModelType.SkinnedModel and self.bones:
            parents = [bone.parent_id for bone in self.bones]
            bind_local = [make_translation_matrix(b.pos.x, b.pos.y, b.pos.z) for b in self.bones]
            bind_global = [None] * len(self.bones)
            
            for i in range(len(self.bones)):
                if parents[i] == -1:
                    bind_global[i] = bind_local[i]
                else:
                    bind_global[i] = bind_global[parents[i]] @ bind_local[i]
            
            inverse_bind = [np.linalg.inv(m) for m in bind_global]
            root_inv = np.linalg.inv(bind_global[0]) if bind_global else None
            
            vertices_transformed = bake_skinning_improved(
                vertices, bind_global, inverse_bind, root_inv,
                debug_params=self.debug_params,
                extra_weights=self.vertex_weights
            )
        else:
            dtype_out = np.dtype([
                ("px", np.float32), ("py", np.float32), ("pz", np.float32),
                ("nx", np.float32), ("ny", np.float32), ("nz", np.float32),
                ("u", np.float32), ("v", np.float32)
            ])
            new_verts = []
            for v in vertices:
                pos = v["pos"] if "pos" in v.dtype.names else (v["px"], v["py"], v["pz"])
                normal = v["normal"] if "normal" in v.dtype.names else (0, 0, 0)
                uv = v["uv0"] if "uv0" in v.dtype.names else (0, 0)
                
                px, py, pz = self.debug_params.swizzle(pos[0], pos[1], pos[2], self.debug_params.v_scale)
                nx, ny, nz = self.debug_params.swizzle(normal[0], normal[1], normal[2], 1.0)
                
                new_verts.append((
                    px, py, pz,
                    nx, ny, nz,
                    float(uv[0]), float(uv[1])
                ))
            vertices_transformed = np.array(new_verts, dtype=dtype_out)

        has_normals = "nx" in vertices_transformed.dtype.names
        has_uv = "u" in vertices_transformed.dtype.names
        
        if primitives:
            print(f"Exporting {len(primitives)} material groups...")
            for i, prim in enumerate(primitives):
                start_idx = prim.index_offset
                face_count = prim.face_count
                if face_count > 0:
                    faces_subset = faces[start_idx:start_idx + face_count]
                    
                    if "obj" in export_formats:
                        self.export_obj_material_group(out_dir, base_name, "_render",
                                                      faces_subset, vertices_transformed,
                                                      i, start_idx, has_normals,
                                                      model_type == ModelType.LightmappedModel,
                                                      lightmap_uvs)
                    
                    if "dae" in export_formats:
                        dae_path = os.path.join(out_dir, f"{base_name}_render_{i}.dae")
                        export_to_collada(self, dae_path, f"{base_name}_render_{i}", 
                                         vertices_transformed, faces_subset, has_normals, has_uv)
                    
                    if "gltf" in export_formats:
                        has_skinning = model_type == ModelType.SkinnedModel and self.bones
                        gltf_path = os.path.join(out_dir, f"{base_name}_render_{i}")
                        bones_data = self.bones if has_skinning else None
                        export_to_gltf_full(self, gltf_path, f"{base_name}_render_{i}", 
                                          vertices_transformed, faces_subset, 
                                          has_normals, has_uv, has_skinning, bones_data)
                    
                    if "directx" in export_formats:
                        # تصدير DirectX (.X) لكل مادة
                        print(f"   DEBUG: DirectX export called for {base_name}_render_{i}")
                        dx_path = os.path.join(out_dir, f"{base_name}_render_{i}.x")
                        print(f"   DEBUG: DirectX path: {dx_path}")
                        export_to_directx(self, dx_path, "igi2" if hasattr(self, 'txan_data') else "igi1")
                        print(f"   DEBUG: DirectX export completed for {base_name}_render_{i}")
        else:
            if "obj" in export_formats:
                self.export_obj(out_dir, base_name, "_render", faces, vertices_transformed,
                               has_normals, model_type == ModelType.LightmappedModel, lightmap_uvs)

            if "dae" in export_formats:
                dae_path = os.path.join(out_dir, f"{base_name}_render.dae")
                export_to_collada(self, dae_path, f"{base_name}_render", 
                                 vertices_transformed, faces, has_normals, has_uv)
            
            if "gltf" in export_formats:
                has_skinning = model_type == ModelType.SkinnedModel and self.bones
                gltf_path = os.path.join(out_dir, f"{base_name}_render")
                bones_data = self.bones if has_skinning else None
                export_to_gltf_full(self, gltf_path, f"{base_name}_render", 
                                  vertices_transformed, faces, 
                                  has_normals, has_uv, has_skinning, bones_data)
            
            if "directx" in export_formats:
                # تصدير DirectX (.X) كامل مع العظام والتزين
                print(f"   DEBUG: DirectX export called for {base_name}")
                dx_path = os.path.join(out_dir, f"{base_name}_render.x")
                print(f"   DEBUG: DirectX path: {dx_path}")
                export_to_directx(self, dx_path, "igi2" if hasattr(self, 'txan_data') else "igi1")
                print(f"   DEBUG: DirectX export completed")

    def export_render_mesh(self, out_dir, base_name, export_formats=None):
        if export_formats is None:
            export_formats = ["obj"]
        
        if self.export_mode == "multi":
            self.export_render_mesh_multi_material(out_dir, base_name, export_formats)
        else:
            self.export_render_mesh_simple(out_dir, base_name, export_formats)

    def export_shadow_mesh(self, out_dir, base_name, export_formats=None):
        if export_formats is None:
            export_formats = ["obj"]
        
        if self.shadow_mesh_data is None:
            print("No shadow mesh data found")
            return
        
        if self.shadow_mesh_data.vertices is None or len(self.shadow_mesh_data.vertices) == 0:
            print("Shadow mesh has no vertices")
            return
        
        vertices = self.shadow_mesh_data.vertices
        faces = self.shadow_mesh_data.faces
        
        new_verts = []
        for v in vertices:
            if len(v) >= 3:
                px, py, pz = self.debug_params.swizzle(v[0], v[1], v[2], self.debug_params.v_scale)
                new_verts.append((px, py, pz, 0, 0, 0, 0, 0))
        
        if not new_verts:
            print("No valid shadow vertices")
            return
        
        dtype_out = np.dtype([
            ("px", np.float32), ("py", np.float32), ("pz", np.float32),
            ("nx", np.float32), ("ny", np.float32), ("nz", np.float32),
            ("u", np.float32), ("v", np.float32)
        ])
        
        verts_arr = np.array(new_verts, dtype=dtype_out)
        
        face_array = None
        if faces is not None and len(faces) > 0:
            if "face" in faces.dtype.names:
                face_array = faces["face"]
            else:
                face_array = faces
            print(f"Exporting shadow mesh with {len(face_array)} faces")
        else:
            print("Shadow mesh has no faces, exporting as point cloud (no faces)")
            face_array = np.array([[0, 0, 0]])
        
        if "obj" in export_formats:
            self.export_obj(out_dir, base_name, "_shadow", face_array, verts_arr, has_normals=False)
        
        if "dae" in export_formats:
            dae_path = os.path.join(out_dir, f"{base_name}_shadow.dae")
            export_to_collada(self, dae_path, f"{base_name}_shadow", verts_arr, face_array, False, False)
        
        if "gltf" in export_formats:
            gltf_path = os.path.join(out_dir, f"{base_name}_shadow")
            export_to_gltf(self, gltf_path, f"{base_name}_shadow", verts_arr, face_array, False, False)

    def export_collision_mesh(self, out_dir, base_name, index=0, export_formats=None):
        if export_formats is None:
            export_formats = ["obj"]
        
        cmesh = self.collision_mesh_data if index == 0 else self.collision_mesh_data2
        if cmesh is None:
            return
        
        faces = cmesh.faces["face"] if "face" in cmesh.faces.dtype.names else cmesh.faces
        vertices = cmesh.vertices
        
        new_verts = []
        for v in vertices:
            pos = v["pos"]
            px, py, pz = self.debug_params.swizzle(pos[0], pos[1], pos[2], self.debug_params.v_scale)
            new_verts.append((px, py, pz, 0, 0, 0, 0, 0))
        
        if not new_verts:
            print("No valid collision vertices")
            return
        
        dtype_out = np.dtype([
            ("px", np.float32), ("py", np.float32), ("pz", np.float32),
            ("nx", np.float32), ("ny", np.float32), ("nz", np.float32),
            ("u", np.float32), ("v", np.float32)
        ])
        
        verts_arr = np.array(new_verts, dtype=dtype_out)
        suffix = f"_col{index}" if index > 0 else "_col"
        
        if "obj" in export_formats:
            self.export_obj(out_dir, base_name, suffix, faces, verts_arr, has_normals=False)
            
            if self.collision_materials:
                obj_path = os.path.join(out_dir, f"{base_name}{suffix}.obj")
                try:
                    with open(obj_path, 'r+', encoding='utf-8') as f:
                        content = f.read()
                        f.seek(0)
                        f.write(f"# Collision Mesh with {len(self.collision_materials)} materials\n")
                        f.write(f"# Material indices in faces: 4th component after a,b,c\n")
                        f.write(f"# Face format: a b c material_id\n\n")
                        f.write(content)
                    print(f"   Added material info to {obj_path}")
                except Exception as e:
                    print(f"   Error adding material info to OBJ: {e}")
        
        if "dae" in export_formats:
            dae_path = os.path.join(out_dir, f"{base_name}{suffix}.dae")
            export_to_collada(self, dae_path, f"{base_name}{suffix}", verts_arr, faces, False, False)
        
        if "gltf" in export_formats:
            gltf_path = os.path.join(out_dir, f"{base_name}{suffix}")
            export_to_gltf(self, gltf_path, f"{base_name}{suffix}", verts_arr, faces, False, False)
            
    def export_lightmaps(self, out_dir, base_name, lightmap_format="png"):
        if not self.lightmaps:
            return
        
        lightmap_dir = os.path.join(out_dir, "lightmaps")
        self.ensure_dir(lightmap_dir)
        
        for i, lightmap in enumerate(self.lightmaps):
            tga_path = os.path.join(lightmap_dir, f"{base_name}_lightmap_{i}.tga")
            try:
                with open(tga_path, "wb") as f:
                    f.write(lightmap.data)
                print(f"   Lightmap {i} (TGA): {tga_path} ({lightmap.width}x{lightmap.height})")
            except Exception as e:
                print(f"   Error saving TGA lightmap {i}: {e}")
            
            if lightmap_format in ["png", "both"] and PIL_AVAILABLE:
                png_path = os.path.join(lightmap_dir, f"{base_name}_lightmap_{i}.png")
                if save_lightmap_as_png(lightmap, png_path):
                    print(f"   Lightmap {i} (PNG): {png_path}")
            
            if lightmap_format in ["dds", "both"]:
                dds_path = os.path.join(lightmap_dir, f"{base_name}_lightmap_{i}.dds")
                if save_lightmap_as_dds(lightmap, dds_path):
                    print(f"   Lightmap {i} (DDS): {dds_path}")

    def export_attachments(self, out_dir, base_name):
        if not self.attachments:
            return
        
        att_path = os.path.join(out_dir, f"{base_name}_attachments.txt")
        with open(att_path, "w", encoding="utf-8") as f:
            f.write("# Attachment points\n")
            f.write("# Format: name\tposition (x,y,z)\tbone_id\n\n")
            for a in self.attachments:
                px, py, pz = self.debug_params.swizzle(a.pos.x, a.pos.y, a.pos.z, self.debug_params.v_scale)
                f.write(f"{a.name}\t({px:.2f}, {py:.2f}, {pz:.2f})\tbone_id={a.bone_id}\n")
        print(f"   Attachments: {att_path}")

    def export_extra_data(self, out_dir, base_name):
        if self.magic_vertices:
            path = os.path.join(out_dir, f"{base_name}_magic_vertices.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write("# Magic Vertices (XTVM)\n")
                f.write("# Format: pos_x pos_y pos_z type\n\n")
                for mv in self.magic_vertices:
                    px, py, pz = self.debug_params.swizzle(mv.pos.x, mv.pos.y, mv.pos.z, self.debug_params.v_scale)
                    f.write(f"{px:.6f} {py:.6f} {pz:.6f} {mv.type}\n")
            print(f"   Magic vertices: {path}")
        
        if self.portals:
            path = os.path.join(out_dir, f"{base_name}_portals.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write("# Portals (TROP)\n")
                f.write("# Format: start_vertex num_vertices start_face num_faces portal_id\n\n")
                for p in self.portals:
                    f.write(f"{p.start_vertex} {p.num_vertices} {p.start_face} {p.num_faces} {p.portal_id}\n")
                
                if self.portal_vertices:
                    f.write("\n# Portal Vertices (XVTP)\n")
                    f.write("# Format: index pos_x pos_y pos_z\n\n")
                    for i, pv in enumerate(self.portal_vertices):
                        px, py, pz = self.debug_params.swizzle(pv.pos.x, pv.pos.y, pv.pos.z, self.debug_params.v_scale)
                        f.write(f"{i} {px:.6f} {py:.6f} {pz:.6f}\n")
                
                if self.portal_faces:
                    f.write("\n# Portal Faces (CFTP)\n")
                    f.write("# Format: a b c\n\n")
                    for pf in self.portal_faces:
                        f.write(f"{pf.a} {pf.b} {pf.c}\n")
            print(f"   Portals: {path}")
        
        if self.glow_sprites:
            path = os.path.join(out_dir, f"{base_name}_glow_sprites.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write("# Glow Sprites (WOLG)\n")
                f.write("# Format: pos_x pos_y pos_z radius color_r color_g color_b\n\n")
                for g in self.glow_sprites:
                    px, py, pz = self.debug_params.swizzle(g.pos.x, g.pos.y, g.pos.z, self.debug_params.v_scale)
                    f.write(f"{px:.6f} {py:.6f} {pz:.6f} {g.radius:.6f} {g.color_r:.6f} {g.color_g:.6f} {g.color_b:.6f}\n")
            print(f"   Glow sprites: {path}")
        
        if self.collision_materials:
            path = os.path.join(out_dir, f"{base_name}_collision_materials.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write("# Collision Materials (TAMC)\n")
                f.write("# Format: opacity portal_id texture_id unknown1 game_material_id unknown2\n\n")
                for i, mat in enumerate(self.collision_materials):
                    f.write(f"Material {i}:\n")
                    f.write(f"  opacity: {mat.opacity:.6f}\n")
                    f.write(f"  portal_id: {mat.portal_id} (0x{mat.portal_id:08X})\n")
                    f.write(f"  texture_id: {mat.texture_id}\n")
                    f.write(f"  unknown1: {mat.unknown1}\n")
                    f.write(f"  game_material_id: {mat.game_material_id}\n")
                    f.write(f"  unknown2: {mat.unknown2}\n\n")
            print(f"   Collision materials: {path}")
        
        if self.txan_data:
            path = os.path.join(out_dir, f"{base_name}_txan.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write("# TXAN Animation Data\n")
                f.write("# Format: 28 uint32 fields\n\n")
                for i, txan in enumerate(self.txan_data):
                    f.write(f"TXAN {i}:\n")
                    f.write("Fields: " + " ".join(str(x) for x in txan.unknown_fields) + "\n\n")
            print(f"   TXAN data: {path}")
    
    def export_collision_materials(self, out_dir: str, base_name: str):
        print(f"   DEBUG: export_collision_materials called with {len(self.collision_materials)} materials")
        if self.collision_materials is None:
            print(f"   DEBUG: collision_materials is None")
            return
        if len(self.collision_materials) == 0:
            print(f"   DEBUG: collision_materials is empty")
            return
            
        materials_list = []
        for i, mat in enumerate(self.collision_materials):
            mat_dict = {
                "index": i,
                "opacity": mat.opacity,
                "portal_id": mat.portal_id,
                "texture_id": mat.texture_id,
                "unknown1": mat.unknown1,
                "game_material_id": mat.game_material_id,
                "unknown2": mat.unknown2
            }
            materials_list.append(mat_dict)
        
        json_path = os.path.join(out_dir, f"{base_name}_collision_materials.json")
        data = convert_to_json_serializable(materials_list)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   Collision materials (JSON): {json_path}")
        
        txt_path = os.path.join(out_dir, f"{base_name}_collision_materials.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# Collision Materials\n")
            f.write("# Format depends on game version\n\n")
            for i, mat_dict in enumerate(materials_list):
                f.write(f"Material {i}:\n")
                for key, value in mat_dict.items():
                    f.write(f"  {key}: {value}\n")
                f.write("\n")
        print(f"   Collision materials (TXT): {txt_path}")
    
    def export_collision_spheres(self, out_dir: str, base_name: str):
        if not hasattr(self, 'collision_mesh_data') or self.collision_mesh_data is None:
            return
        
        spheres = self.collision_mesh_data.spheres
        if spheres is None or len(spheres) == 0:
            return
        
        txt_path = os.path.join(out_dir, f"{base_name}_collision_spheres.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# Collision Spheres (IGI2)\n")
            f.write("# Format: center_x center_y center_z radius type count vertex_a vertex_b\n\n")
            
            for i, sphere in enumerate(spheres):
                pos = sphere["pos"]
                cx, cy, cz = self.debug_params.swizzle(pos[0], pos[1], pos[2], self.debug_params.v_scale)
                radius = sphere["radius"][0]
                sphere_type = sphere["type"][0]
                count = sphere["count"][0]
                vertex_a = sphere["vertex_a"][0]
                vertex_b = sphere["vertex_b"][0]
                f.write(f"Sphere {i}: center=({cx:.2f}, {cy:.2f}, {cz:.2f}), "
                       f"radius={radius:.2f}, type={sphere_type}, count={count}, "
                       f"vertex_a={vertex_a}, vertex_b={vertex_b}\n")
        
        print(f"   Collision spheres (TXT): {txt_path}")
        
    # ========== الدوال المحسنة الإضافية (الموجودة مسبقاً) ==========
    
    def export_magic_vertices_improved(self, out_dir, base_name):
        if not self.magic_vertices:
            return
        
        txt_path = os.path.join(out_dir, f"{base_name}_magic_vertices.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("# Magic Vertices (XTVM) - IGI2\n")
            f.write("# Format: pos_x pos_y pos_z type\n")
            f.write("# type: نوع الحدث (0=?, 1=?, 2=?, ...)\n\n")
            for i, mv in enumerate(self.magic_vertices):
                px, py, pz = self.debug_params.swizzle(mv.pos.x, mv.pos.y, mv.pos.z, self.debug_params.v_scale)
                f.write(f"{i:4d}: {px:8.2f} {py:8.2f} {pz:8.2f} {mv.type:4d}\n")
        print(f"   Magic vertices (TXT): {txt_path}")
        
        csv_path = os.path.join(out_dir, f"{base_name}_magic_vertices.csv")
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write("index,pos_x,pos_y,pos_z,type\n")
            for i, mv in enumerate(self.magic_vertices):
                px, py, pz = self.debug_params.swizzle(mv.pos.x, mv.pos.y, mv.pos.z, self.debug_params.v_scale)
                f.write(f"{i},{px:.6f},{py:.6f},{pz:.6f},{mv.type}\n")
        print(f"   Magic vertices (CSV): {csv_path}")
        
        json_path = os.path.join(out_dir, f"{base_name}_magic_vertices.json")
        data = [{"index": i, "pos": [px, py, pz], "type": mv.type} 
                for i, mv in enumerate(self.magic_vertices)
                for px, py, pz in [self.debug_params.swizzle(mv.pos.x, mv.pos.y, mv.pos.z, self.debug_params.v_scale)]]
        data = convert_to_json_serializable(data)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"   Magic vertices (JSON): {json_path}")

    def export_portals_as_mesh(self, out_dir, base_name):
        if not self.portals or not self.portal_vertices or not self.portal_faces:
            return
        
        vertices = []
        for pv in self.portal_vertices:
            px, py, pz = self.debug_params.swizzle(pv.pos.x, pv.pos.y, pv.pos.z, self.debug_params.v_scale)
            vertices.append([px, py, pz])
        
        faces = []
        for pf in self.portal_faces:
            faces.append([pf.a, pf.b, pf.c])
        
        if not vertices or not faces:
            return
        
        dtype_out = np.dtype([
            ("px", np.float32), ("py", np.float32), ("pz", np.float32),
            ("nx", np.float32), ("ny", np.float32), ("nz", np.float32),
            ("u", np.float32), ("v", np.float32)
        ])
        
        verts_arr = np.array([(v[0], v[1], v[2], 0,0,0,0,0) for v in vertices], dtype=dtype_out)
        faces_arr = np.array(faces)
        
        obj_path = os.path.join(out_dir, f"{base_name}_portals.obj")
        
        with open(obj_path, "w", encoding="utf-8") as f:
            f.write(f"# Portal mesh for {base_name}\n")
            f.write(f"# {len(self.portals)} portals, {len(vertices)} vertices, {len(faces)} faces\n\n")
            f.write(f"o {base_name}_portals\n")
            
            for v in verts_arr:
                f.write(f"v {v['px']:.6f} {v['py']:.6f} {v['pz']:.6f}\n")
            
            f.write(f"usemtl default\n")
            for face in faces_arr:
                a, b, c = face[0]+1, face[1]+1, face[2]+1
                f.write(f"f {a} {b} {c}\n")
        
        print(f"   Portals mesh (OBJ): {obj_path}")
        
        portals_txt = os.path.join(out_dir, f"{base_name}_portals_detailed.txt")
        with open(portals_txt, "w", encoding="utf-8") as f:
            f.write("# Portal Definitions (TROP)\n")
            f.write("# Format: portal_id: start_vertex num_vertices start_face num_faces\n\n")
            for p in self.portals:
                f.write(f"Portal {p.portal_id:3d}: "
                       f"vtx={p.start_vertex:4d}-{p.start_vertex+p.num_vertices-1:4d} "
                       f"({p.num_vertices:4d} vertices), "
                       f"faces={p.start_face:4d}-{p.start_face+p.num_faces-1:4d} "
                       f"({p.num_faces:4d} faces)\n")
        print(f"   Portal details (TXT): {portals_txt}")

    def export_glow_sprites_improved(self, out_dir, base_name):
        if not self.glow_sprites:
            return
        
        txt_path = os.path.join(out_dir, f"{base_name}_glow_sprites.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("# Glow Sprites (WOLG) - IGI2\n")
            f.write("# Format: pos_x pos_y pos_z radius color_r color_g color_b\n\n")
            for i, g in enumerate(self.glow_sprites):
                px, py, pz = self.debug_params.swizzle(g.pos.x, g.pos.y, g.pos.z, self.debug_params.v_scale)
                f.write(f"{i:3d}: ({px:8.2f}, {py:8.2f}, {pz:8.2f}) "
                       f"r={g.radius:6.2f} "
                       f"color=({g.color_r:.3f}, {g.color_g:.3f}, {g.color_b:.3f})\n")
        print(f"   Glow sprites (TXT): {txt_path}")
        
        json_path = os.path.join(out_dir, f"{base_name}_glow_sprites.json")
        data = []
        for i, g in enumerate(self.glow_sprites):
            px, py, pz = self.debug_params.swizzle(g.pos.x, g.pos.y, g.pos.z, self.debug_params.v_scale)
            data.append({
                "index": i, 
                "pos": [px, py, pz], 
                "radius": g.radius,
                "color": [g.color_r, g.color_g, g.color_b]
            })
        data = convert_to_json_serializable(data)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"   Glow sprites (JSON): {json_path}")
        
        if len(self.glow_sprites) <= 100:
            obj_path = os.path.join(out_dir, f"{base_name}_glow_spheres.obj")
            with open(obj_path, "w", encoding="utf-8") as f:
                f.write(f"# Glow spheres for {base_name}\n")
                f.write(f"# Each sphere is represented by its center point\n\n")
                f.write(f"o {base_name}_glow_spheres\n")
                
                for i, g in enumerate(self.glow_sprites):
                    px, py, pz = self.debug_params.swizzle(g.pos.x, g.pos.y, g.pos.z, self.debug_params.v_scale)
                    f.write(f"v {px:.6f} {py:.6f} {pz:.6f}\n")
                    f.write(f"# sphere {i}: radius={g.radius:.2f}, color=({g.color_r:.3f}, {g.color_g:.3f}, {g.color_b:.3f})\n")
                
                f.write(f"p 1\n")
            
            print(f"   Glow spheres as points (OBJ): {obj_path}")

    def export_hsem_info(self, out_dir: str, base_name: str):
        if not self.model_info:
            return
        
        info_dict = {
            "version": self.model_info.version,
            "creation_date": self.model_info.creation_type.isoformat(),
            "model_type": self.model_info.model_type.name,
            "model_type_value": self.model_info.model_type.value,
            "unknown1": self.model_info.unknown1,
            "unknown2": self.model_info.unknown2,
            "unknown3": self.model_info.unknown3,
            "bounding_sphere1": {
                "center": [self.model_info.bounding_sphere1.pos.x, 
                           self.model_info.bounding_sphere1.pos.y, 
                           self.model_info.bounding_sphere1.pos.z],
                "radius": self.model_info.bounding_sphere1.radius
            },
            "bounding_sphere2": {
                "center": [self.model_info.bounding_sphere2.pos.x, 
                           self.model_info.bounding_sphere2.pos.y, 
                           self.model_info.bounding_sphere2.pos.z],
                "radius": self.model_info.bounding_sphere2.radius
            },
            "bounding_sphere3": {
                "center": [self.model_info.bounding_sphere3.pos.x, 
                           self.model_info.bounding_sphere3.pos.y, 
                           self.model_info.bounding_sphere3.pos.z],
                "radius": self.model_info.bounding_sphere3.radius
            },
            "render_mesh": {
                "face_count": self.model_info.render_mesh_info.face_count,
                "vertex_count": self.model_info.render_mesh_info.vertex_count,
                "buffer_size": self.model_info.render_mesh_info.buffer_size
            },
            "collision_mesh": {
                "face_count": self.model_info.collision_mesh_info.face_count,
                "vertex_count": self.model_info.collision_mesh_info.vertex_count,
                "buffer_size": self.model_info.collision_mesh_info.buffer_size
            },
            "something_radius": self.model_info.something_radius,
            "field_80": self.model_info.field_80,
            "attachment_count": self.model_info.attachment_count,
            "magic_vertex_count": self.model_info.magic_vertex_count,
            "portal_count": self.model_info.portal_count,
            "glow_count": self.model_info.glow_count,
            "bone_count": self.model_info.bone_count,
            "field_8C": self.model_info.field_8C,
            "field_90": self.model_info.field_90,
            "field_94": self.model_info.field_94,
            "field_98": self.model_info.field_98,
            "field_9C": self.model_info.field_9C,
            "field_A0": self.model_info.field_A0,
            "field_A4": self.model_info.field_A4,
            "field_A8": self.model_info.field_A8,
            "field_AC": self.model_info.field_AC,
            "field_B0": self.model_info.field_B0,
        }
        
        json_path = os.path.join(out_dir, f"{base_name}_hsem.json")
        data = convert_to_json_serializable(info_dict)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   HSEM info (JSON): {json_path}")
        
        txt_path = os.path.join(out_dir, f"{base_name}_hsem.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# HSEM (Model Info) - IGI2\n")
            f.write(f"Version: {self.model_info.version}\n")
            f.write(f"Creation Date: {self.model_info.creation_type.isoformat()}\n")
            f.write(f"Model Type: {self.model_info.model_type.name} ({self.model_info.model_type.value})\n")
            f.write(f"Unknown values: {self.model_info.unknown1}, {self.model_info.unknown2}, {self.model_info.unknown3}\n\n")
            
            f.write("Bounding Spheres:\n")
            f.write(f"  Sphere 1: center=({self.model_info.bounding_sphere1.pos.x:.2f}, {self.model_info.bounding_sphere1.pos.y:.2f}, {self.model_info.bounding_sphere1.pos.z:.2f}), radius={self.model_info.bounding_sphere1.radius:.2f}\n")
            f.write(f"  Sphere 2: center=({self.model_info.bounding_sphere2.pos.x:.2f}, {self.model_info.bounding_sphere2.pos.y:.2f}, {self.model_info.bounding_sphere2.pos.z:.2f}), radius={self.model_info.bounding_sphere2.radius:.2f}\n")
            f.write(f"  Sphere 3: center=({self.model_info.bounding_sphere3.pos.x:.2f}, {self.model_info.bounding_sphere3.pos.y:.2f}, {self.model_info.bounding_sphere3.pos.z:.2f}), radius={self.model_info.bounding_sphere3.radius:.2f}\n\n")
            
            f.write("Render Mesh:\n")
            f.write(f"  Faces: {self.model_info.render_mesh_info.face_count}\n")
            f.write(f"  Vertices: {self.model_info.render_mesh_info.vertex_count}\n")
            f.write(f"  Buffer Size: {self.model_info.render_mesh_info.buffer_size}\n\n")
            
            f.write("Collision Mesh:\n")
            f.write(f"  Faces: {self.model_info.collision_mesh_info.face_count}\n")
            f.write(f"  Vertices: {self.model_info.collision_mesh_info.vertex_count}\n")
            f.write(f"  Buffer Size: {self.model_info.collision_mesh_info.buffer_size}\n\n")
            
            f.write(f"Something Radius: {self.model_info.something_radius}\n")
            f.write(f"Field 80: {self.model_info.field_80}\n\n")
            
            f.write("Counts:\n")
            f.write(f"  Attachments: {self.model_info.attachment_count}\n")
            f.write(f"  Magic Vertices: {self.model_info.magic_vertex_count}\n")
            f.write(f"  Portals: {self.model_info.portal_count}\n")
            f.write(f"  Glow Sprites: {self.model_info.glow_count}\n")
            f.write(f"  Bones: {self.model_info.bone_count}\n\n")
            
            f.write("Additional Fields:\n")
            f.write(f"  field_8C: {self.model_info.field_8C}\n")
            f.write(f"  field_90: {self.model_info.field_90}\n")
            f.write(f"  field_94: {self.model_info.field_94}\n")
            f.write(f"  field_98: {self.model_info.field_98}\n")
            f.write(f"  field_9C: {self.model_info.field_9C}\n")
            f.write(f"  field_A0: {self.model_info.field_A0}\n")
            f.write(f"  field_A4: {self.model_info.field_A4}\n")
            f.write(f"  field_A8: {self.model_info.field_A8}\n")
            f.write(f"  field_AC: {self.model_info.field_AC}\n")
            f.write(f"  field_B0: {self.model_info.field_B0}\n")
        
        print(f"   HSEM info (TXT): {txt_path}")

    def export_d3dr_info(self, out_dir: str, base_name: str):
        if not self.render_mesh_data or not self.render_mesh_data.mesh_header:
            return
        
        header = self.render_mesh_data.mesh_header
        
        header_dict = {
            "header_size": header.header_size,
            "dword0": header.dword0,
            "lightmap_count": header.lightmap_count,
            "face_count": header.face_count,
            "face_group_count": header.face_group_count,
            "bone_related_0": header.bone_related_0,
            "bone_related_1": header.bone_related_1,
            "vertex_count": header.vertex_count,
            "dword14": header.dword14,
            "dword18": header.dword18,
            "dword1c": header.dword1c,
            "dword20": header.dword20,
            "dword24": header.dword24,
            "dword28": header.dword28,
        }
        
        json_path = os.path.join(out_dir, f"{base_name}_d3dr.json")
        data = convert_to_json_serializable(header_dict)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   D3DR info (JSON): {json_path}")
        
        txt_path = os.path.join(out_dir, f"{base_name}_d3dr.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# D3DR (Render Mesh Header) - IGI2\n")
            f.write(f"Header Size: {header.header_size} bytes\n")
            f.write(f"dword0: {header.dword0}\n")
            f.write(f"Lightmap Count: {header.lightmap_count}\n")
            f.write(f"Face Count: {header.face_count}\n")
            f.write(f"Material Groups: {header.face_group_count}\n")
            f.write(f"Bone Related 0: {header.bone_related_0}\n")
            f.write(f"Bone Related 1: {header.bone_related_1}\n")
            f.write(f"Vertex Count: {header.vertex_count}\n\n")
            
            f.write("Additional DWORDs:\n")
            f.write(f"  dword14: {header.dword14}\n")
            f.write(f"  dword18: {header.dword18}\n")
            f.write(f"  dword1c: {header.dword1c}\n")
            f.write(f"  dword20: {header.dword20}\n")
            f.write(f"  dword24: {header.dword24}\n")
            f.write(f"  dword28: {header.dword28}\n")
        
        print(f"   D3DR info (TXT): {txt_path}")

    def export_manb_detailed(self, out_dir: str, base_name: str):
        if not self.bones:
            return
        
        bone_names = [bone.name for bone in self.bones]
        
        name_lengths = [len(name) for name in bone_names]
        stats = {
            "total_bones": len(bone_names),
            "max_name_length": max(name_lengths),
            "min_name_length": min(name_lengths),
            "avg_name_length": sum(name_lengths) / len(name_lengths) if name_lengths else 0,
            "unique_names": len(set(bone_names))
        }
        
        json_path = os.path.join(out_dir, f"{base_name}_manb_detailed.json")
        data = convert_to_json_serializable({
            "statistics": stats,
            "bone_names": [{"index": i, "name": name} for i, name in enumerate(bone_names)]
        })
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   MANB detailed (JSON): {json_path}")
        
        txt_path = os.path.join(out_dir, f"{base_name}_manb.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# MANB (Bone Names)\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Total Bones: {len(bone_names)}\n")
            f.write(f"Statistics:\n")
            f.write(f"  Max name length: {stats['max_name_length']}\n")
            f.write(f"  Min name length: {stats['min_name_length']}\n")
            f.write(f"  Avg name length: {stats['avg_name_length']:.2f}\n")
            f.write(f"  Unique names: {stats['unique_names']}\n\n")
            f.write("Bone Names:\n")
            f.write("-" * 40 + "\n")
            
            for i, name in enumerate(bone_names):
                f.write(f"Bone {i:3d}: {name}\n")
        
        print(f"   MANB (TXT): {txt_path}")
        
        csv_path = os.path.join(out_dir, f"{base_name}_manb.csv")
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write("index,name\n")
            for i, name in enumerate(bone_names):
                f.write(f"{i},{name}\n")
        print(f"   MANB (CSV): {csv_path}")

    def export_reih_detailed(self, out_dir: str, base_name: str):
        if not self.bones:
            return
        
        bone_data = []
        for i, bone in enumerate(self.bones):
            children = [j for j, b in enumerate(self.bones) if b.parent_id == i]
            
            bone_data.append({
                "index": i,
                "name": bone.name,
                "parent_id": bone.parent_id,
                "position": [bone.pos.x, bone.pos.y, bone.pos.z],
                "children": children,
                "child_count": len(children)
            })
        
        json_path = os.path.join(out_dir, f"{base_name}_reih_detailed.json")
        data = convert_to_json_serializable({
            "bone_count": len(bone_data),
            "bones": bone_data
        })
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   REIH detailed (JSON): {json_path}")
        
        txt_path = os.path.join(out_dir, f"{base_name}_reih_tree.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# REIH (Bone Hierarchy) - Tree Structure\n")
            f.write(f"Total Bones: {len(bone_data)}\n\n")
            
            def print_tree(bone_idx, level=0, prefix=""):
                bone = bone_data[bone_idx]
                indent = "  " * level
                marker = "├─ " if level > 0 else "└─ "
                f.write(f"{indent}{marker}{bone['name']} [ID:{bone_idx}, Parent:{bone['parent_id']}]\n")
                f.write(f"{indent}   pos: ({bone['position'][0]:.2f}, {bone['position'][1]:.2f}, {bone['position'][2]:.2f})\n")
                
                for i, child in enumerate(bone['children']):
                    is_last = (i == len(bone['children']) - 1)
                    child_prefix = prefix + ("    " if is_last else "│   ")
                    print_tree(child, level + 1, child_prefix)
            
            root_bones = [i for i, b in enumerate(self.bones) if b.parent_id == -1]
            for i, root in enumerate(root_bones):
                print_tree(root)
                if i < len(root_bones) - 1:
                    f.write("\n")
        
        print(f"   REIH tree (TXT): {txt_path}")
        
        csv_path = os.path.join(out_dir, f"{base_name}_reih.csv")
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write("index,name,parent_id,pos_x,pos_y,pos_z,child_count\n")
            for i, bone in enumerate(bone_data):
                f.write(f"{i},{bone['name']},{bone['parent_id']},{bone['position'][0]:.6f},{bone['position'][1]:.6f},{bone['position'][2]:.6f},{bone['child_count']}\n")
        print(f"   REIH (CSV): {csv_path}")

    def export_mrph_info(self, out_dir: str, base_name: str):
        if not self.morph_channels:
            return
        
        morph_data = {}
        total_vertices = 0
        for channel, vertices in self.morph_channels.items():
            channel_data = []
            for v in vertices:
                px, py, pz = self.debug_params.swizzle(v["pos"][0], v["pos"][1], v["pos"][2], self.debug_params.v_scale)
                channel_data.append({
                    "index": int(v["index"].item()) if hasattr(v["index"], 'item') else int(v["index"]),
                    "position": [px, py, pz]
                })
            morph_data[f"channel_{channel}"] = channel_data
            total_vertices += len(vertices)
        
        json_path = os.path.join(out_dir, f"{base_name}_mrph.json")
        data = convert_to_json_serializable(morph_data)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   Morph vertices (JSON): {json_path}")
        
        txt_path = os.path.join(out_dir, f"{base_name}_mrph.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# MRPH (Morph Vertices) - IGI2\n")
            f.write(f"Total Channels: {len(self.morph_channels)}\n")
            f.write(f"Total Vertices: {total_vertices}\n\n")
            
            for channel, vertices in self.morph_channels.items():
                f.write(f"Channel {channel}: {len(vertices)} vertices\n")
                f.write("-" * 50 + "\n")
                
                for i, v in enumerate(vertices):
                    idx_val = v['index']
                    if hasattr(idx_val, 'item'):
                        idx = idx_val.item()
                    elif isinstance(idx_val, np.ndarray):
                        idx = idx_val[0]
                    else:
                        idx = int(idx_val)
                    
                    pos = v['pos']
                    if hasattr(pos, '__getitem__'):
                        px = float(pos[0]) if hasattr(pos[0], 'item') else float(pos[0])
                        py = float(pos[1]) if hasattr(pos[1], 'item') else float(pos[1])
                        pz = float(pos[2]) if hasattr(pos[2], 'item') else float(pos[2])
                    else:
                        px, py, pz = 0.0, 0.0, 0.0
                    
                    px, py, pz = self.debug_params.swizzle(px, py, pz, self.debug_params.v_scale)
                    
                    f.write(f"  v{i:4d}: idx={idx:4d}, pos=({px:8.2f}, {py:8.2f}, {pz:8.2f})\n")
                
                f.write("\n")
        
        print(f"   Morph vertices (TXT): {txt_path}")

    def export_txan_info(self, out_dir: str, base_name: str):
        if not self.txan_data:
            return
        
        txan_list = []
        for i, txan in enumerate(self.txan_data):
            txan_list.append({
                "index": i,
                "fields": txan.unknown_fields
            })
        
        json_path = os.path.join(out_dir, f"{base_name}_txan.json")
        data = convert_to_json_serializable(txan_list)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   TXAN animation data (JSON): {json_path}")
        
        txt_path = os.path.join(out_dir, f"{base_name}_txan.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# TXAN (Animation Data) - IGI2\n")
            f.write(f"Total TXAN chunks: {len(self.txan_data)}\n\n")
            
            for i, txan in enumerate(self.txan_data):
                f.write(f"TXAN {i}:\n")
                f.write(f"  Fields (28 uint32):\n")
                for j, val in enumerate(txan.unknown_fields):
                    f.write(f"    [{j:2d}]: {val} (0x{val:08X})\n")
                f.write("\n")
        
        print(f"   TXAN animation data (TXT): {txt_path}")
        
        csv_path = os.path.join(out_dir, f"{base_name}_txan.csv")
        with open(csv_path, 'w', encoding='utf-8') as f:
            header = ["chunk"] + [f"field_{i:02d}" for i in range(28)]
            f.write(",".join(header) + "\n")
            for i, txan in enumerate(self.txan_data):
                row = [str(i)] + [str(val) for val in txan.unknown_fields]
                f.write(",".join(row) + "\n")
        print(f"   TXAN animation data (CSV): {csv_path}")

    def export_hsmc_info(self, out_dir: str, base_name: str):
        if not self.collision_mesh_data:
            return
        
        header = self.collision_mesh_data.mesh_header
        
        hsmc_dict = {
            "mesh0": {
                "face_count": header.mesh0.face_count,
                "vertex_count": header.mesh0.vertex_count,
                "material_count": header.mesh0.material_count,
                "sphere_count": header.mesh0.sphere_count,
                "face_ptr": header.mesh0.face_ptr,
                "vertex_ptr": header.mesh0.vertex_ptr,
                "materials_ptr": header.mesh0.materials_ptr,
                "sphere_ptr": header.mesh0.sphere_ptr,
            },
            "mesh1": {
                "face_count": header.mesh1.face_count,
                "vertex_count": header.mesh1.vertex_count,
                "material_count": header.mesh1.material_count,
                "sphere_count": header.mesh1.sphere_count,
                "face_ptr": header.mesh1.face_ptr,
                "vertex_ptr": header.mesh1.vertex_ptr,
                "materials_ptr": header.mesh1.materials_ptr,
                "sphere_ptr": header.mesh1.sphere_ptr,
            }
        }
        
        json_path = os.path.join(out_dir, f"{base_name}_hsmc.json")
        data = convert_to_json_serializable(hsmc_dict)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   HSMC info (JSON): {json_path}")
        
        txt_path = os.path.join(out_dir, f"{base_name}_hsmc.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# HSMC (Collision Mesh Header) - IGI2\n")
            f.write("=" * 60 + "\n\n")
            
            f.write("Mesh 0 (Primary Collision Mesh):\n")
            f.write("-" * 40 + "\n")
            f.write(f"  Face Count      : {header.mesh0.face_count}\n")
            f.write(f"  Vertex Count    : {header.mesh0.vertex_count}\n")
            f.write(f"  Material Count  : {header.mesh0.material_count}\n")
            f.write(f"  Sphere Count    : {header.mesh0.sphere_count}\n")
            f.write(f"  Face Pointer    : {header.mesh0.face_ptr} (0x{header.mesh0.face_ptr:08X})\n")
            f.write(f"  Vertex Pointer  : {header.mesh0.vertex_ptr} (0x{header.mesh0.vertex_ptr:08X})\n")
            f.write(f"  Materials Pointer: {header.mesh0.materials_ptr} (0x{header.mesh0.materials_ptr:08X})\n")
            f.write(f"  Sphere Pointer  : {header.mesh0.sphere_ptr} (0x{header.mesh0.sphere_ptr:08X})\n\n")
            
            f.write("Mesh 1 (Secondary Collision Mesh):\n")
            f.write("-" * 40 + "\n")
            f.write(f"  Face Count      : {header.mesh1.face_count}\n")
            f.write(f"  Vertex Count    : {header.mesh1.vertex_count}\n")
            f.write(f"  Material Count  : {header.mesh1.material_count}\n")
            f.write(f"  Sphere Count    : {header.mesh1.sphere_count}\n")
            f.write(f"  Face Pointer    : {header.mesh1.face_ptr} (0x{header.mesh1.face_ptr:08X})\n")
            f.write(f"  Vertex Pointer  : {header.mesh1.vertex_ptr} (0x{header.mesh1.vertex_ptr:08X})\n")
            f.write(f"  Materials Pointer: {header.mesh1.materials_ptr} (0x{header.mesh1.materials_ptr:08X})\n")
            f.write(f"  Sphere Pointer  : {header.mesh1.sphere_ptr} (0x{header.mesh1.sphere_ptr:08X})\n")
        
        print(f"   HSMC info (TXT): {txt_path}")
        
        csv_path = os.path.join(out_dir, f"{base_name}_hsmc.csv")
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write("mesh,face_count,vertex_count,material_count,sphere_count,face_ptr,vertex_ptr,materials_ptr,sphere_ptr\n")
            f.write(f"0,{header.mesh0.face_count},{header.mesh0.vertex_count},{header.mesh0.material_count},{header.mesh0.sphere_count},{header.mesh0.face_ptr},{header.mesh0.vertex_ptr},{header.mesh0.materials_ptr},{header.mesh0.sphere_ptr}\n")
            f.write(f"1,{header.mesh1.face_count},{header.mesh1.vertex_count},{header.mesh1.material_count},{header.mesh1.sphere_count},{header.mesh1.face_ptr},{header.mesh1.vertex_ptr},{header.mesh1.materials_ptr},{header.mesh1.sphere_ptr}\n")
        print(f"   HSMC info (CSV): {csv_path}")

    def export_xtvc_info(self, out_dir: str, base_name: str, mesh_index: int = 0):
        cmesh = self.collision_mesh_data if mesh_index == 0 else self.collision_mesh_data2
        if not cmesh or cmesh.vertices is None:
            return
        
        vertices = cmesh.vertices
        mesh_type = "type0" if mesh_index == 0 else "type1"
        
        verts_list = []
        for i, v in enumerate(vertices):
            px, py, pz = self.debug_params.swizzle(v["pos"][0], v["pos"][1], v["pos"][2], self.debug_params.v_scale)
            verts_list.append({
                "index": i,
                "position": [px, py, pz],
                "uv": [float(v["uv"][0]), float(v["uv"][1])] if "uv" in v.dtype.names else [0, 0]
            })
        
        suffix = f"_xtvc_{mesh_type}"
        json_path = os.path.join(out_dir, f"{base_name}{suffix}.json")
        data = convert_to_json_serializable({
            "mesh_type": mesh_type,
            "vertex_count": len(verts_list),
            "vertices": verts_list
        })
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   XTVC {mesh_type} (JSON): {json_path}")
        
        txt_path = os.path.join(out_dir, f"{base_name}{suffix}.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(f"# XTVC (Collision Mesh Vertices) - IGI2 - {mesh_type}\n")
            f.write(f"Total Vertices: {len(verts_list)}\n\n")
            f.write("Format: index: pos=(x,y,z), uv=(u,v)\n\n")
            
            for i, v in enumerate(verts_list):
                f.write(f"Vertex {i:6d}: pos=({v['position'][0]:8.2f}, {v['position'][1]:8.2f}, {v['position'][2]:8.2f}), "
                       f"uv=({v['uv'][0]:.4f}, {v['uv'][1]:.4f})\n")
        
        print(f"   XTVC {mesh_type} (TXT): {txt_path}")
        
        csv_path = os.path.join(out_dir, f"{base_name}{suffix}.csv")
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write("index,pos_x,pos_y,pos_z,uv_u,uv_v\n")
            for i, v in enumerate(verts_list):
                f.write(f"{i},{v['position'][0]:.6f},{v['position'][1]:.6f},{v['position'][2]:.6f},"
                       f"{v['uv'][0]:.6f},{v['uv'][1]:.6f}\n")
        print(f"   XTVC {mesh_type} (CSV): {csv_path}")

    def export_ecfc_info(self, out_dir: str, base_name: str, mesh_index: int = 0):
        cmesh = self.collision_mesh_data if mesh_index == 0 else self.collision_mesh_data2
        if not cmesh or cmesh.faces is None:
            return
        
        faces = cmesh.faces
        mesh_type = "type0" if mesh_index == 0 else "type1"
        
        faces_list = []
        for i, f in enumerate(faces):
            mat_id_val = f["mat_id"]
            mat_id = mat_id_val.item() if hasattr(mat_id_val, 'item') else mat_id_val
            
            lightmap_id_val = f["lightmap_id"]
            lightmap_id = lightmap_id_val.item() if hasattr(lightmap_id_val, 'item') else lightmap_id_val
            
            unknown_val = f["unknown"]
            unknown = unknown_val.item() if hasattr(unknown_val, 'item') else unknown_val
            
            faces_list.append({
                "index": i,
                "vertices": [int(f["face"][0]), int(f["face"][1]), int(f["face"][2])],
                "material_id": int(mat_id),
                "lightmap_id": int(lightmap_id),
                "unknown": int(unknown)
            })
        
        suffix = f"_ecfc_{mesh_type}"
        json_path = os.path.join(out_dir, f"{base_name}{suffix}.json")
        data = convert_to_json_serializable({
            "mesh_type": mesh_type,
            "face_count": len(faces_list),
            "faces": faces_list
        })
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   ECFC {mesh_type} (JSON): {json_path}")
        
        txt_path = os.path.join(out_dir, f"{base_name}{suffix}.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(f"# ECFC (Collision Mesh Faces) - IGI2 - {mesh_type}\n")
            f.write(f"Total Faces: {len(faces_list)}\n\n")
            f.write("Format: index: vertices=(a,b,c), mat_id, lightmap_id, unknown\n\n")
            
            for i, face in enumerate(faces_list):
                f.write(f"Face {i:6d}: vertices=({face['vertices'][0]:6d}, {face['vertices'][1]:6d}, {face['vertices'][2]:6d}), "
                       f"mat_id={face['material_id']:4d}, lightmap_id={face['lightmap_id']:4d}, unknown={face['unknown']:4d}\n")
        
        print(f"   ECFC {mesh_type} (TXT): {txt_path}")
        
        csv_path = os.path.join(out_dir, f"{base_name}{suffix}.csv")
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write("index,vert_a,vert_b,vert_c,mat_id,lightmap_id,unknown\n")
            for i, face in enumerate(faces_list):
                f.write(f"{i},{face['vertices'][0]},{face['vertices'][1]},{face['vertices'][2]},"
                       f"{face['material_id']},{face['lightmap_id']},{face['unknown']}\n")
        print(f"   ECFC {mesh_type} (CSV): {csv_path}")

    def export_tamc_info(self, out_dir: str, base_name: str, mesh_index: int = 0, use_mesh1_materials: bool = False):
        if use_mesh1_materials and hasattr(self, 'collision_materials_mesh1'):
            materials = self.collision_materials_mesh1
        else:
            materials = self.collision_materials
        
        if not materials:
            return
        
        mesh_type = "type0" if mesh_index == 0 else "type1"
        
        mats_list = []
        for i, mat in enumerate(materials):
            mats_list.append({
                "index": i,
                "opacity": mat.opacity,
                "portal_id": mat.portal_id,
                "texture_id": mat.texture_id,
                "unknown1": mat.unknown1,
                "game_material_id": mat.game_material_id,
                "unknown2": mat.unknown2
            })
        
        suffix = f"_tamc_{mesh_type}"
        json_path = os.path.join(out_dir, f"{base_name}{suffix}.json")
        data = convert_to_json_serializable({
            "mesh_type": mesh_type,
            "material_count": len(mats_list),
            "materials": mats_list
        })
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   TAMC {mesh_type} (JSON): {json_path}")
        
        txt_path = os.path.join(out_dir, f"{base_name}{suffix}.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(f"# TAMC (Collision Mesh Materials) - IGI2 - {mesh_type}\n")
            f.write(f"Total Materials: {len(mats_list)}\n\n")
            
            for i, mat in enumerate(mats_list):
                f.write(f"Material {i:3d}: opacity={mat['opacity']:.6f}, portal_id={mat['portal_id']:4d} (0x{mat['portal_id']:04X}), "
                       f"texture_id={mat['texture_id']:4d}, unknown1={mat['unknown1']:8d} (0x{mat['unknown1']:08X}), "
                       f"game_material_id={mat['game_material_id']:4d}, unknown2={mat['unknown2']:4d}\n")
        
        print(f"   TAMC {mesh_type} (TXT): {txt_path}")
        
        csv_path = os.path.join(out_dir, f"{base_name}{suffix}.csv")
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write("index,opacity,portal_id,texture_id,unknown1,game_material_id,unknown2\n")
            for i, mat in enumerate(mats_list):
                f.write(f"{i},{mat['opacity']:.6f},{mat['portal_id']},{mat['texture_id']},"
                       f"{mat['unknown1']},{mat['game_material_id']},{mat['unknown2']}\n")
        print(f"   TAMC {mesh_type} (CSV): {csv_path}")

    def export_hpsc_info(self, out_dir: str, base_name: str, mesh_index: int = 0):
        cmesh = self.collision_mesh_data if mesh_index == 0 else self.collision_mesh_data2
        if not cmesh or cmesh.spheres is None:
            return
        
        spheres = cmesh.spheres
        mesh_type = "type0" if mesh_index == 0 else "type1"
        
        spheres_list = []
        for i, s in enumerate(spheres):
            cx, cy, cz = self.debug_params.swizzle(s["pos"][0], s["pos"][1], s["pos"][2], self.debug_params.v_scale)
            spheres_list.append({
                "index": i,
                "center": [cx, cy, cz],
                "radius": float(s["radius"][0]),
                "type": int(s["type"][0]),
                "count": int(s["count"][0]),
                "vertex_a": int(s["vertex_a"][0]),
                "vertex_b": int(s["vertex_b"][0])
            })
        
        suffix = f"_hpsc_{mesh_type}"
        json_path = os.path.join(out_dir, f"{base_name}{suffix}.json")
        data = convert_to_json_serializable({
            "mesh_type": mesh_type,
            "sphere_count": len(spheres_list),
            "spheres": spheres_list
        })
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   HPSC {mesh_type} (JSON): {json_path}")
        
        txt_path = os.path.join(out_dir, f"{base_name}{suffix}.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(f"# HPSC (Collision Mesh Spheres) - IGI2 - {mesh_type}\n")
            f.write(f"Total Spheres: {len(spheres_list)}\n\n")
            f.write("Format: index: center=(x,y,z), radius, type, count, vertex_a, vertex_b\n\n")
            
            for i, s in enumerate(spheres_list):
                f.write(f"Sphere {i:6d}: center=({s['center'][0]:8.2f}, {s['center'][1]:8.2f}, {s['center'][2]:8.2f}), "
                       f"radius={s['radius']:8.2f}, type={s['type']:4d}, count={s['count']:4d}, "
                       f"vertex_a={s['vertex_a']:6d}, vertex_b={s['vertex_b']:6d}\n")
        
        print(f"   HPSC {mesh_type} (TXT): {txt_path}")
        
        csv_path = os.path.join(out_dir, f"{base_name}{suffix}.csv")
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write("index,center_x,center_y,center_z,radius,type,count,vertex_a,vertex_b\n")
            for i, s in enumerate(spheres_list):
                f.write(f"{i},{s['center'][0]:.6f},{s['center'][1]:.6f},{s['center'][2]:.6f},"
                       f"{s['radius']:.6f},{s['type']},{s['count']},{s['vertex_a']},{s['vertex_b']}\n")
        print(f"   HPSC {mesh_type} (CSV): {csv_path}")
        
        obj_path = os.path.join(out_dir, f"{base_name}{suffix}.obj")
        with open(obj_path, 'w', encoding='utf-8') as f:
            f.write(f"# HPSC Collision Spheres - {mesh_type}\n")
            f.write(f"# {len(spheres_list)} spheres\n\n")
            f.write(f"o {base_name}_hpsc_{mesh_type}\n")
            
            for i, s in enumerate(spheres_list):
                f.write(f"v {s['center'][0]:.6f} {s['center'][1]:.6f} {s['center'][2]:.6f}\n")
                f.write(f"# sphere {i}: radius={s['radius']:.2f}, type={s['type']}, count={s['count']}, "
                       f"vertices=({s['vertex_a']}, {s['vertex_b']})\n")
            
            if spheres_list:
                f.write("p 1\n")
        
        print(f"   HPSC {mesh_type} spheres as points (OBJ): {obj_path}")
    
    def export_all_collision_mesh_data(self, out_dir: str, base_name: str):
        print(f"\n   📦 Exporting all collision mesh data...")
        
        self.export_hsmc_info(out_dir, base_name)
        
        if self.collision_mesh_data:
            self.export_xtvc_info(out_dir, base_name, 0)
            self.export_ecfc_info(out_dir, base_name, 0)
            self.export_hpsc_info(out_dir, base_name, 0)
            if self.collision_materials:
                self.export_tamc_info(out_dir, base_name, 0)
        
        if hasattr(self, 'collision_mesh_data2') and self.collision_mesh_data2:
            print(f"\n   📦 Exporting second collision mesh (type1)...")
            self.export_xtvc_info(out_dir, base_name, 1)
            self.export_ecfc_info(out_dir, base_name, 1)
            self.export_hpsc_info(out_dir, base_name, 1)
            if hasattr(self, 'collision_materials_mesh1') and self.collision_materials_mesh1:
                self.export_tamc_info(out_dir, base_name, 1, use_mesh1_materials=True)
            elif self.collision_materials:
                self.export_tamc_info(out_dir, base_name, 1)
        
        print(f"   ✅ Collision mesh data exported successfully")

    def export_sems_info(self, out_dir: str, base_name: str):
        if not self.shadow_mesh_data:
            return
        
        header = self.shadow_mesh_data.mesh_header
        
        sems_dict = {
            "face_offset": header.face_offset,
            "vertex_offset": header.vertex_offset,
            "edge_offset": header.edge_offset,
            "face_count": header.face_count,
            "vertex_count": header.vertex_count,
            "edge_count": header.edge_count,
            "bone_index": header.bone_index
        }
        
        json_path = os.path.join(out_dir, f"{base_name}_sems.json")
        data = convert_to_json_serializable(sems_dict)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   SEMS (JSON): {json_path}")
        
        txt_path = os.path.join(out_dir, f"{base_name}_sems.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# SEMS (Shadow Model Header)\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Face Offset    : {header.face_offset}\n")
            f.write(f"Vertex Offset  : {header.vertex_offset}\n")
            f.write(f"Edge Offset    : {header.edge_offset}\n")
            f.write(f"Face Count     : {header.face_count}\n")
            f.write(f"Vertex Count   : {header.vertex_count}\n")
            f.write(f"Edge Count     : {header.edge_count}\n")
            f.write(f"Bone Index     : {header.bone_index}\n")
        
        print(f"   SEMS (TXT): {txt_path}")
        
        csv_path = os.path.join(out_dir, f"{base_name}_sems.csv")
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write("face_offset,vertex_offset,edge_offset,face_count,vertex_count,edge_count,bone_index\n")
            f.write(f"{header.face_offset},{header.vertex_offset},{header.edge_offset},{header.face_count},{header.vertex_count},{header.edge_count},{header.bone_index}\n")
        print(f"   SEMS (CSV): {csv_path}")

    def export_xtvs_info(self, out_dir: str, base_name: str):
        if not self.shadow_mesh_data or self.shadow_mesh_data.vertices is None:
            return
        
        vertices = self.shadow_mesh_data.vertices
        
        verts_list = []
        for i, v in enumerate(vertices):
            if len(v) >= 3:
                px, py, pz = self.debug_params.swizzle(v[0], v[1], v[2], self.debug_params.v_scale)
                verts_list.append({
                    "index": i,
                    "position": [px, py, pz]
                })
        
        json_path = os.path.join(out_dir, f"{base_name}_xtvs.json")
        data = convert_to_json_serializable({
            "vertex_count": len(verts_list),
            "vertices": verts_list
        })
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   XTVS (JSON): {json_path}")
        
        txt_path = os.path.join(out_dir, f"{base_name}_xtvs.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# XTVS (Shadow Mesh Vertices)\n")
            f.write(f"Total Vertices: {len(verts_list)}\n\n")
            f.write("Format: index: (x, y, z)\n\n")
            
            for i, v in enumerate(verts_list):
                f.write(f"Vertex {i:6d}: ({v['position'][0]:8.2f}, {v['position'][1]:8.2f}, {v['position'][2]:8.2f})\n")
        
        print(f"   XTVS (TXT): {txt_path}")
        
        csv_path = os.path.join(out_dir, f"{base_name}_xtvs.csv")
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write("index,x,y,z\n")
            for i, v in enumerate(verts_list):
                f.write(f"{i},{v['position'][0]:.6f},{v['position'][1]:.6f},{v['position'][2]:.6f}\n")
        print(f"   XTVS (CSV): {csv_path}")
        
        obj_path = os.path.join(out_dir, f"{base_name}_xtvs.obj")
        with open(obj_path, 'w', encoding='utf-8') as f:
            f.write(f"# XTVS Shadow Vertices\n")
            f.write(f"# {len(verts_list)} vertices\n\n")
            f.write(f"o {base_name}_shadow_verts\n")
            
            for v in verts_list:
                f.write(f"v {v['position'][0]:.6f} {v['position'][1]:.6f} {v['position'][2]:.6f}\n")
            
            if verts_list:
                f.write("p 1\n")
        
        print(f"   XTVS as points (OBJ): {obj_path}")

    def export_cafs_info(self, out_dir: str, base_name: str):
        if not self.shadow_mesh_data or self.shadow_mesh_data.faces is None:
            return
        
        faces = self.shadow_mesh_data.faces
        
        faces_list = []
        for i, f in enumerate(faces):
            if "face" in f.dtype.names:
                faces_list.append({
                    "index": i,
                    "vertices": [int(f["face"][0]), int(f["face"][1]), int(f["face"][2])],
                    "edge_flags": int(f["edge_flags"]),
                    "normal": [float(f["normal"][0]), float(f["normal"][1]), float(f["normal"][2])]
                })
            else:
                faces_list.append({
                    "index": i,
                    "vertices": [int(f[0]), int(f[1]), int(f[2])]
                })
        
        json_path = os.path.join(out_dir, f"{base_name}_cafs.json")
        data = convert_to_json_serializable({
            "face_count": len(faces_list),
            "faces": faces_list
        })
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   CAFS (JSON): {json_path}")
        
        txt_path = os.path.join(out_dir, f"{base_name}_cafs.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# CAFS (Shadow Mesh Faces)\n")
            f.write(f"Total Faces: {len(faces_list)}\n\n")
            
            for i, face in enumerate(faces_list):
                if "normal" in face:
                    f.write(f"Face {i:6d}: vertices=({face['vertices'][0]:6d}, {face['vertices'][1]:6d}, {face['vertices'][2]:6d}), "
                           f"edge_flags={face['edge_flags']:4d}, normal=({face['normal'][0]:8.2f}, {face['normal'][1]:8.2f}, {face['normal'][2]:8.2f})\n")
                else:
                    f.write(f"Face {i:6d}: vertices=({face['vertices'][0]:6d}, {face['vertices'][1]:6d}, {face['vertices'][2]:6d})\n")
        
        print(f"   CAFS (TXT): {txt_path}")
        
        csv_path = os.path.join(out_dir, f"{base_name}_cafs.csv")
        with open(csv_path, 'w', encoding='utf-8') as f:
            if faces_list and "normal" in faces_list[0]:
                f.write("index,a,b,c,edge_flags,nx,ny,nz\n")
                for i, face in enumerate(faces_list):
                    f.write(f"{i},{face['vertices'][0]},{face['vertices'][1]},{face['vertices'][2]},"
                           f"{face['edge_flags']},{face['normal'][0]:.6f},{face['normal'][1]:.6f},{face['normal'][2]:.6f}\n")
            else:
                f.write("index,a,b,c\n")
                for i, face in enumerate(faces_list):
                    f.write(f"{i},{face['vertices'][0]},{face['vertices'][1]},{face['vertices'][2]}\n")
        print(f"   CAFS (CSV): {csv_path}")

    def export_egde_info(self, out_dir: str, base_name: str):
        if not self.shadow_mesh_data or self.shadow_mesh_data.edges is None:
            return
        
        edges = self.shadow_mesh_data.edges
        
        edges_list = []
        for i, e in enumerate(edges):
            edges_list.append({
                "index": i,
                "a": int(e[0]),
                "b": int(e[1])
            })
        
        json_path = os.path.join(out_dir, f"{base_name}_egde.json")
        data = convert_to_json_serializable({
            "edge_count": len(edges_list),
            "edges": edges_list
        })
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   EGDE (JSON): {json_path}")
        
        txt_path = os.path.join(out_dir, f"{base_name}_egde.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# EGDE (Shadow Mesh Edges)\n")
            f.write(f"Total Edges: {len(edges_list)}\n\n")
            f.write("Format: index: a - b\n\n")
            
            for i, edge in enumerate(edges_list):
                f.write(f"Edge {i:6d}: {edge['a']:6d} - {edge['b']:6d}\n")
        
        print(f"   EGDE (TXT): {txt_path}")
        
        csv_path = os.path.join(out_dir, f"{base_name}_egde.csv")
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write("index,a,b\n")
            for i, edge in enumerate(edges_list):
                f.write(f"{i},{edge['a']},{edge['b']}\n")
        print(f"   EGDE (CSV): {csv_path}")
    
    def export_all_shadow_data(self, out_dir: str, base_name: str):
        print(f"\n   🌑 Exporting all shadow mesh data...")
        
        if not self.shadow_mesh_data:
            print(f"   No shadow mesh data found")
            return
        
        self.export_sems_info(out_dir, base_name)
        self.export_xtvs_info(out_dir, base_name)
        self.export_cafs_info(out_dir, base_name)
        self.export_egde_info(out_dir, base_name)
        
        print(f"   ✅ Shadow mesh data exported successfully")

    def create_texture_atlas(self, out_dir: str, base_name: str) -> TextureAtlas:
        if not ENABLE_TEXTURE_ATLAS:
            print(f"   ℹ️ ميزة دمج القوام موقفة مؤقتاً (ENABLE_TEXTURE_ATLAS = False)")
            return None
            
        if not self.render_mesh_data or not self.render_mesh_data.primitives:
            return None
        
        texture_dirs = [
            os.path.join(out_dir, "textures"),
            out_dir,
            os.path.join(os.path.dirname(out_dir), "textures")
        ]
        
        atlas = None
        for tex_dir in texture_dirs:
            if os.path.exists(tex_dir):
                atlas = TextureAtlas(tex_dir)
                break
        
        if atlas is None:
            atlas = TextureAtlas(out_dir)
        
        texture_names = []
        for i, prim in enumerate(self.render_mesh_data.primitives):
            tex_index = prim.diffuse_texture if hasattr(prim, 'diffuse_texture') else 0
            tex_name = get_texture_name(tex_index, base_name, i, self.texture_references)
            if tex_name not in texture_names:
                texture_names.append(tex_name)
            
            if hasattr(prim, 'bump_texture') and prim.bump_texture >= 0:
                bump_name = get_texture_name(prim.bump_texture, base_name, i, self.texture_references)
                if bump_name not in texture_names:
                    texture_names.append(bump_name)
            
            if hasattr(prim, 'reflection_texture') and prim.reflection_texture >= 0:
                refl_name = get_texture_name(prim.reflection_texture, base_name, i, self.texture_references)
                if refl_name not in texture_names:
                    texture_names.append(refl_name)
        
        print(f"   Texture names in order: {texture_names}")
        
        for tex_name in texture_names:
            atlas.add_texture(tex_name)
        
        if atlas.has_multiple_textures():
            if atlas.pack_textures():
                atlas_path = os.path.join(out_dir, f"{base_name}_atlas.png")
                atlas.save_atlas(atlas_path, 'PNG')
                print(f"   Created texture atlas: {atlas_path} ({atlas.atlas_size[0]}x{atlas.atlas_size[1]}) with {len(atlas.texture_paths)} textures")
                print(f"   Atlas positions: {atlas.positions}")
                return atlas
        
        return None

    def apply_texture_atlas_igi2(self, atlas: TextureAtlas, vertices: np.ndarray, primitives: list, base_name: str) -> np.ndarray:
        if not ENABLE_TEXTURE_ATLAS:
            print(f"   ℹ️ تخطي تطبيق الأطلس (الميزة موقفة)")
            return vertices
            
        print(f"   DEBUG: Entering apply_texture_atlas_igi2")
        print(f"   DEBUG: atlas.has_multiple_textures() = {atlas.has_multiple_textures()}")
        print(f"   DEBUG: vertices.shape = {vertices.shape}")
        print(f"   DEBUG: dtype names = {vertices.dtype.names}")
        
        if not atlas or not atlas.has_multiple_textures():
            print(f"   DEBUG: Early return - no atlas or single texture")
            return vertices
        
        new_vertices = vertices.copy()
        
        material_texture_map = []
        for i, prim in enumerate(primitives):
            tex_index = prim.diffuse_texture if hasattr(prim, 'diffuse_texture') else 0
            tex_name = get_texture_name(tex_index, base_name, i, self.texture_references)
            material_texture_map.append(tex_name)
        
        print(f"   Material to texture mapping: {material_texture_map}")
        print(f"   Atlas textures: {atlas.texture_names}")
        print(f"   Atlas indices: {atlas.texture_indices}")

        for i, prim in enumerate(primitives):
            print(f"   DEBUG: Processing material {i}")
            
            if i >= len(material_texture_map):
                print(f"   DEBUG: Skipping - i out of range")
                continue
            
            tex_name = material_texture_map[i]
            print(f"   DEBUG: tex_name = {tex_name}")
            
            if tex_name not in atlas.texture_indices:
                print(f"   Warning: Texture '{tex_name}' not found in atlas for material {i}")
                continue
            
            atlas_index = atlas.texture_indices[tex_name]
            print(f"   DEBUG: atlas_index = {atlas_index}")
            
            start_idx = prim.vertex_offset
            end_idx = start_idx + prim.vertex_count
            print(f"   DEBUG: vertex range = {start_idx} to {end_idx}")
            
            if end_idx > len(new_vertices):
                print(f"   Warning: Vertex range out of bounds for material {i}")
                continue
            
            if "u" in new_vertices.dtype.names and "v" in new_vertices.dtype.names:
                print(f"   DEBUG: Found u/v fields")
                
                uvs = np.array([[new_vertices[j]["u"], new_vertices[j]["v"]] 
                               for j in range(start_idx, end_idx)])
                
                print(f"   DEBUG: uvs.shape = {uvs.shape}")
                if len(uvs) > 0:
                    print(f"   Original UVs (first 3): {uvs[:3]}")
                
                transformed_uvs = atlas.get_uv_transform(tex_name, uvs)
                print(f"   DEBUG: transformed_uvs.shape = {transformed_uvs.shape}")
                
                if len(transformed_uvs) > 0:
                    print(f"   Transformed UVs (first 3): {transformed_uvs[:3]}")
                
                for j, idx in enumerate(range(start_idx, end_idx)):
                    new_vertices[idx]["u"] = transformed_uvs[j, 0]
                    new_vertices[idx]["v"] = transformed_uvs[j, 1]
                
                print(f"   DEBUG: Applied UV transform for material {i}")
            else:
                print(f"   DEBUG: u/v fields NOT FOUND in vertices")
        
        return new_vertices

    def update_mtl_with_atlas(self, out_dir: str, base_name: str, atlas: TextureAtlas):
        if not atlas or not atlas.has_multiple_textures():
            return
        
        mtl_path = os.path.join(out_dir, f"{base_name}_render.mtl")
        if not os.path.exists(mtl_path):
            return
        
        with open(mtl_path, 'r', encoding='utf-8') as f:
            mtl_lines = f.readlines()
        
        new_lines = []
        current_material = None
        
        for line in mtl_lines:
            if line.startswith('newmtl '):
                current_material = line.strip()
                new_lines.append(line)
            elif line.startswith('map_Kd ') and current_material:
                new_lines.append(f"map_Kd {base_name}_atlas.png\n")
            elif line.startswith('map_Ke ') and current_material:
                new_lines.append(f"map_Ke {base_name}_atlas.png\n")
            elif line.startswith('map_') and current_material:
                new_lines.append(f"map_Kd {base_name}_atlas.png\n")
            else:
                new_lines.append(line)
        
        with open(mtl_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
        print(f"   Updated MTL to use texture atlas: {mtl_path}")
    
    # ========== دوال تصدير القطع الجديدة ==========
    
    def export_xtrw_info(self, out_dir: str, base_name: str):
        """تصدير أوزان العظام المنفصلة (XTRW)"""
        if not self.vertex_weights:
            return
        
        # JSON
        json_path = os.path.join(out_dir, f"{base_name}_xtrw.json")
        data = convert_to_json_serializable([{"vertex_id": w.vertex_id, "bone_id": w.bone_id, "weight": w.weight} 
                for w in self.vertex_weights])
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   XTRW (JSON): {json_path}")
        
        # TXT
        txt_path = os.path.join(out_dir, f"{base_name}_xtrw.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# XTRW (Separate Bone Weights)\n")
            f.write("# Format: vertex_id, bone_id, weight\n\n")
            for w in self.vertex_weights:
                f.write(f"{w.vertex_id:6d}, {w.bone_id:3d}, {w.weight:.6f}\n")
        print(f"   XTRW (TXT): {txt_path}")
        
        # CSV
        csv_path = os.path.join(out_dir, f"{base_name}_xtrw.csv")
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write("vertex_id,bone_id,weight\n")
            for w in self.vertex_weights:
                f.write(f"{w.vertex_id},{w.bone_id},{w.weight:.6f}\n")
        print(f"   XTRW (CSV): {csv_path}")

    def export_xtxm_info(self, out_dir: str, base_name: str):
        """تصدير مراجع القوام (XTXM)"""
        if not self.texture_references:
            return
        
        # JSON
        json_path = os.path.join(out_dir, f"{base_name}_xtxm.json")
        data = convert_to_json_serializable([{"index": ref.index, "name": ref.name} for ref in self.texture_references])
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   XTXM (JSON): {json_path}")
        
        # TXT
        txt_path = os.path.join(out_dir, f"{base_name}_xtxm.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# XTXM (Texture References)\n")
            f.write("# Format: index, name\n\n")
            for ref in self.texture_references:
                f.write(f"{ref.index:4d}: {ref.name}\n")
        print(f"   XTXM (TXT): {txt_path}")

    def export_tcst_info(self, out_dir: str, base_name: str):
        """تصدير مجموعات UV الإضافية (TCST)"""
        if not self.extra_uv_sets:
            return
        
        # JSON
        json_path = os.path.join(out_dir, f"{base_name}_tcst.json")
        data = convert_to_json_serializable([{"index": uv_set.index, "uv_count": len(uv_set.uvs), "uvs": uv_set.uvs} 
                for uv_set in self.extra_uv_sets])
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   TCST (JSON): {json_path}")
        
        # TXT
        txt_path = os.path.join(out_dir, f"{base_name}_tcst.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# TCST (Texture Coordinate Sets)\n")
            f.write("# Format: set_index, uv_index, u, v\n\n")
            for uv_set in self.extra_uv_sets:
                f.write(f"Set {uv_set.index}:\n")
                for i, (u, v) in enumerate(uv_set.uvs):
                    f.write(f"  [{i:4d}]: u={u:.6f}, v={v:.6f}\n")
                f.write("\n")
        print(f"   TCST (TXT): {txt_path}")

    def export_hprm_info(self, out_dir: str, base_name: str):
        """تصدير معاملات العظام الإضافية (HPRM)"""
        if not hasattr(self, 'bone_extra_params') or not self.bone_extra_params:
            return
        
        # JSON
        json_path = os.path.join(out_dir, f"{base_name}_hprm.json")
        data = convert_to_json_serializable([
            {"bone_index": i, "params": list(params)} 
            for i, params in enumerate(self.bone_extra_params)
        ])
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   HPRM (JSON): {json_path}")
        
        # TXT
        txt_path = os.path.join(out_dir, f"{base_name}_hprm.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# HPRM (Additional Bone Parameters)\n")
            f.write("# Format: bone_index: param_x, param_y, param_z\n\n")
            for i, params in enumerate(self.bone_extra_params):
                bone_name = self.bone_names[i] if i < len(self.bone_names) else f"bone_{i}"
                f.write(f"Bone {i:3d} ({bone_name}): ({params[0]:8.4f}, {params[1]:8.4f}, {params[2]:8.4f})\n")
        print(f"   HPRM (TXT): {txt_path}")
        
        # CSV
        csv_path = os.path.join(out_dir, f"{base_name}_hprm.csv")
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write("bone_index,bone_name,param_x,param_y,param_z\n")
            for i, params in enumerate(self.bone_extra_params):
                bone_name = self.bone_names[i] if i < len(self.bone_names) else f"bone_{i}"
                f.write(f"{i},{bone_name},{params[0]:.6f},{params[1]:.6f},{params[2]:.6f}\n")
        print(f"   HPRM (CSV): {csv_path}")
        
    # ========== دالة export_all النهائية ==========
    
    def export_all(self, out_dir, export_formats=None, lightmap_format="png"):
        if export_formats is None:
            export_formats = ["obj"]
        
        base_name = os.path.splitext(os.path.basename(out_dir))[0]
        self.ensure_dir(out_dir)
        
        print(f"\nExporting to {out_dir}")
        print("-" * 50)
        
        self.export_hsem_info(out_dir, base_name)
        self.export_d3dr_info(out_dir, base_name)
        
        self.export_manb_detailed(out_dir, base_name)
        self.export_reih_detailed(out_dir, base_name)
        
        self.export_hsmc_info(out_dir, base_name)
        
        self.export_render_mesh(out_dir, base_name, export_formats)
        
        self.export_collision_mesh(out_dir, base_name, 0, export_formats)
        if self.collision_mesh_data2:
            self.export_collision_mesh(out_dir, base_name, 1, export_formats)
        
        self.export_all_collision_mesh_data(out_dir, base_name)
        
        self.export_all_shadow_data(out_dir, base_name)
        
        self.export_collision_materials(out_dir, base_name)
        self.export_collision_spheres(out_dir, base_name)
        
        self.export_attachments(out_dir, base_name)
        
        self.export_lightmaps(out_dir, base_name, lightmap_format)
        
        self.export_extra_data(out_dir, base_name)
        
        self.export_magic_vertices_improved(out_dir, base_name)
        self.export_portals_as_mesh(out_dir, base_name)
        self.export_glow_sprites_improved(out_dir, base_name)
        
        self.export_mrph_info(out_dir, base_name)
        self.export_txan_info(out_dir, base_name)
        
        self.export_xtrw_info(out_dir, base_name)
        self.export_xtxm_info(out_dir, base_name)
        self.export_tcst_info(out_dir, base_name)
        self.export_hprm_info(out_dir, base_name)
        
        print("-" * 50)
        print("Export completed successfully!")
        
        
# ========== دالة اختبار شاملة ==========
def comprehensive_test(input_file: str, output_dir: str = "test_output"):
    """اختبار شامل للمحلل المحسن"""
    
    print("\n" + "=" * 70)
    print("🧪 COMPREHENSIVE TEST - Enhanced MEF Parser")
    print("=" * 70)
    
    with open(input_file, "rb") as f:
        data = f.read()
    
    buffer = Buffer(data)
    model = MefModelIGI2(buffer, export_mode="multi")
    
    # اختبار التصدير المحسن
    base_name = Path(input_file).stem
    out_path = os.path.join(output_dir, base_name)
    model.export_all_enhanced(out_path, export_formats=["obj", "json", "txt"])
    
    # طباعة التقرير
    print("\n" + "=" * 70)
    print("📊 TEST REPORT")
    print("=" * 70)
    
    report = {
        "File": input_file,
        "File size": f"{len(data)} bytes",
        "Model type": model.model_info.model_type.name if model.model_info else "Unknown",
        "Bones": len(model.bones),
        "Bone names": len(model.bone_names),
        "Bone extra params (HPRM)": len(model.bone_extra_params) if hasattr(model, 'bone_extra_params') else 0,
        "Attachments": len(model.attachments),
        "Magic vertices": len(model.magic_vertices),
        "Portals": len(model.portals),
        "Portal faces": len(model.portal_faces),
        "Portal vertices": len(model.portal_vertices),
        "Glow sprites": len(model.glow_sprites),
        "Lightmaps": len(model.lightmaps),
        "TXAN chunks": len(model.txan_data),
        "XTRW weights": len(model.vertex_weights),
        "XTXM textures": len(model.texture_references),
        "TCST UV sets": len(model.extra_uv_sets),
        "External refs (XTRN)": len(model.external_refs) if hasattr(model, 'external_refs') else 0,
        "Skeleton hints (NHSA)": len(model.skeleton_hints) if hasattr(model, 'skeleton_hints') else 0,
        "Shadow faces detailed": len(model.shadow_faces_detailed) if hasattr(model, 'shadow_faces_detailed') else 0,
        "Output directory": out_path,
    }
    
    for key, value in report.items():
        print(f"   {key:28}: {value}")
    
    print("=" * 70)
    print("✅ Test complete!")
    
    return report
    
    
# ------------------------------------------------------------
# الدالة الرئيسية (معدلة لدعم MDL)
# ------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="IGI1/IGI2 MEF & Half-Life MDL Model Exporter")
    parser.add_argument("input", nargs="?", default=INPUT_DIR,
                       help=f"Input file or folder (default: {INPUT_DIR})")
    parser.add_argument("-o", "--output", default=OUTPUT_DIR,
                       help=f"Output directory (default: {OUTPUT_DIR})")
    parser.add_argument("-m", "--mode", choices=["simple", "multi"], default="simple",
                       help="Export mode: simple (single file) or multi (separate material groups)")
    parser.add_argument("-f", "--file", action="store_true",
                       help="Treat input as single file (default: folder mode)")
    parser.add_argument("-F", "--format", choices=["obj", "dae", "gltf", "json", "txt", "directx", "all"], default="obj",
                       help="Export format: obj, dae, gltf, json, txt, directx, or all")
    parser.add_argument("-L", "--lightmap-format", choices=["tga", "png", "dds", "both"], default="png",
                       help="Lightmap format (for MEF only)")
    parser.add_argument("--force-version", choices=["IGI1", "IGI2", "auto"], default="auto",
                       help="Force MEF version (default: auto-detect)")
    parser.add_argument("--atlas", choices=["true", "false", "smd", "obj", "mdl"], default=None,
                       help="Enable/disable texture atlas: true, false, smd, obj, mdl (default: None)")
    parser.add_argument("--atlas-mode", choices=["preserve", "merge"], default="preserve",
                       help="Texture atlas mode: preserve (keep materials) or merge (single material)")
                   
    args = parser.parse_args()
    
    # ========== معالجة وسيط الأطلس ==========
    if args.atlas == "true":
        enable_texture_atlas_for_all(True)
    elif args.atlas == "false":
        enable_texture_atlas_for_all(False)
    elif args.atlas == "smd":
        global ENABLE_TEXTURE_ATLAS_SMD, ENABLE_TEXTURE_ATLAS_OBJ, ENABLE_TEXTURE_ATLAS_MDL
        ENABLE_TEXTURE_ATLAS_SMD = True
        ENABLE_TEXTURE_ATLAS_OBJ = False
        ENABLE_TEXTURE_ATLAS_MDL = False
        print("✅ Texture Atlas enabled only for SMD")
    elif args.atlas == "obj":
        ENABLE_TEXTURE_ATLAS_SMD = False
        ENABLE_TEXTURE_ATLAS_OBJ = True
        ENABLE_TEXTURE_ATLAS_MDL = False
        print("✅ Texture Atlas enabled only for OBJ")
    elif args.atlas == "mdl":
        ENABLE_TEXTURE_ATLAS_SMD = False
        ENABLE_TEXTURE_ATLAS_OBJ = False
        ENABLE_TEXTURE_ATLAS_MDL = True
        print("✅ Texture Atlas enabled only for MDL")
    
    # ========== معالجة وسيط وضع الأطلس ==========
    global ATLAS_MODE
    ATLAS_MODE = args.atlas_mode
    print(f"✅ Texture Atlas mode: {ATLAS_MODE}")
    # ============================================
    
    export_formats = ["obj"]
    if args.format == "dae":
        export_formats = ["dae"]
    elif args.format == "gltf":
        export_formats = ["gltf"]
    elif args.format == "json":
        export_formats = ["json"]
    elif args.format == "txt":
        export_formats = ["txt"]
    elif args.format == "directx":
        export_formats = ["directx"]
    elif args.format == "all":
        export_formats = ["obj", "dae", "gltf", "json", "txt", "directx"]
    
    print(f"\nMulti-Format Model Exporter (MEF + MDL)")
    print("=" * 60)
    print(f"Export mode : {args.mode}")
    print(f"Export formats : {', '.join(export_formats)}")
    print(f"Output dir : {args.output}")
    print("=" * 60)
    
    Path(args.output).mkdir(parents=True, exist_ok=True)
    
    # دعم صيغة SMD (Crowbar)
    if args.input.endswith('.smd') or args.input.endswith('.SMD'):
        print(f"\nSMD file detected - converting to {', '.join(export_formats)}")
        success = convert_smd_to_formats_fixed(args.input, args.output, export_formats)  # استخدم الدالة المصلحة
        
        # DirectX export for SMD
        if success and "directx" in export_formats:
            try:
                with open(args.input, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                smd = SMDExporter.from_string(content)
                dx_path = os.path.join(args.output, f"{Path(args.input).stem}.x")
                export_to_directx(smd, dx_path, "smd")
                print(f"   ✅ DirectX export completed: {dx_path}")
            except Exception as e:
                print(f"   ⚠️ DirectX export failed: {e}")
        
        if success:
            print(f"\n✓ Successfully converted SMD: {args.input}")
        else:
            print(f"\n✗ Failed to convert SMD: {args.input}")
        return
    
    # دعم صيغة OBJ
    if args.input.endswith('.obj') or args.input.endswith('.OBJ'):
        print(f"\nOBJ file detected - converting to {', '.join(export_formats)}")
        success = convert_obj_to_formats_fixed(args.input, args.output, export_formats)  # استخدم الدالة المصلحة
        
        # DirectX export for OBJ
        if success and "directx" in export_formats:
            try:
                obj = OBJExporter.from_file(args.input)
                dx_path = os.path.join(args.output, f"{Path(args.input).stem}.x")
                export_to_directx(obj, dx_path, "obj")
                print(f"   ✅ DirectX export completed: {dx_path}")
            except Exception as e:
                print(f"   ⚠️ DirectX export failed: {e}")
        
        if success:
            print(f"\n✓ Successfully converted OBJ: {args.input}")
        else:
            print(f"\n✗ Failed to convert OBJ: {args.input}")
        return
    
    # معالجة ملف واحد
    if args.file or (os.path.isfile(args.input) and not os.path.isdir(args.input)):
        input_path = args.input
        if not os.path.isfile(input_path):
            print(f"\nError: File not found: {input_path}")
            sys.exit(1)
        
        output_subdir = os.path.join(args.output, Path(input_path).stem)
        
        print(f"\nProcessing single file: {input_path}")
        print(f"Output folder: {output_subdir}")
        print("=" * 60)
        
        try:
            with open(input_path, "rb") as f:
                data = f.read()
            
            print(f"File size: {len(data)} bytes")
            buffer = Buffer(data)
            
            file_type = detect_file_type(buffer, str(input_path))
            print(f"Detected file type: {file_type}")
            
            model = None
            
            if file_type == "MDL":
                model = StudioHeader(buffer)
                model.export_all(output_subdir, export_formats)
            elif file_type == "MEF":
                version = detect_mef_version(buffer)
                if version == "IGI2":
                    model = MefModelIGI2(buffer, export_mode=args.mode)
                else:
                    model = MefModelIGI1(buffer, export_mode=args.mode)
                model.export_all(output_subdir, export_formats, args.lightmap_format)
            else:
                print(f"Unknown file type: {file_type}")
                sys.exit(1)
            
            # تصدير DirectX - استخدم الدالة المساعدة
            fix_export_to_directx_in_main(input_path, output_subdir, file_type, model, export_formats)
            
            print(f"\n✓ Successfully processed: {Path(input_path).name}")
            print(f"   Output folder: {output_subdir}")
            
        except Exception as e:
            print(f"\n✗ Error processing {input_path}: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    else:
        input_dir = args.input
        if not os.path.exists(input_dir):
            print(f"\nError: Input folder '{input_dir}' not found!")
            sys.exit(1)
        
        # البحث عن الملفات
        mef_files = set()
        for ext in ['*.mef', '*.MEF']:
            mef_files.update(Path(input_dir).glob(ext))

        mdl_files = set()
        for ext in ['*.mdl', '*.MDL']:
            mdl_files.update(Path(input_dir).glob(ext))

        smd_files = set()
        for ext in ['*.smd', '*.SMD']:
            smd_files.update(Path(input_dir).glob(ext))
        
        obj_files = set()
        for ext in ['*.obj', '*.OBJ']:
            obj_files.update(Path(input_dir).glob(ext))

        all_files = list(mef_files.union(mdl_files).union(smd_files).union(obj_files))
        
        if not all_files:
            print(f"\nNo .mef, .mdl, .smd, or .obj files found in '{input_dir}' folder.")
            sys.exit(1)
        
        all_files.sort()
        
        print(f"\nFound {len(all_files)} file(s) to process:")
        for f in all_files:
            print(f"  - {f.name}")
        
        print("\n" + "=" * 60)
        
        successful = 0
        failed = 0
        
        for file_path in all_files:
            print(f"\n{'=' * 60}")
            print(f"Processing: {file_path.name}")
            print(f"{'=' * 60}")
            
            output_subdir = os.path.join(args.output, file_path.stem)
            
            try:
                if file_path.suffix.lower() in ['.smd']:
                    # معالجة SMD
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    smd = SMDExporter.from_string(content)
                    base_name = file_path.stem
                    smd.export_all(output_subdir, base_name, export_formats)
                    
                    # DirectX for SMD
                    if "directx" in export_formats:
                        dx_path = os.path.join(output_subdir, f"{base_name}.x")
                        export_to_directx(smd, dx_path, "smd")
                    
                elif file_path.suffix.lower() in ['.obj']:
                    # معالجة OBJ
                    obj = OBJExporter.from_file(str(file_path))
                    base_name = file_path.stem
                    obj.export_all(output_subdir, base_name, export_formats)
                    
                    # DirectX for OBJ
                    if "directx" in export_formats:
                        dx_path = os.path.join(output_subdir, f"{base_name}.x")
                        export_to_directx(obj, dx_path, "obj")
                    
                else:
                    # معالجة MEF أو MDL
                    with open(file_path, "rb") as f:
                        data = f.read()
                    
                    buffer = Buffer(data)
                    file_type = detect_file_type(buffer, str(file_path))
                    
                    if file_type == "MDL":
                        model = StudioHeader(buffer)
                        model.export_all(output_subdir, export_formats)
                    else:
                        version = detect_mef_version(buffer)
                        if version == "IGI2":
                            model = MefModelIGI2(buffer, export_mode=args.mode)
                        else:
                            model = MefModelIGI1(buffer, export_mode=args.mode)
                        model.export_all(output_subdir, export_formats, args.lightmap_format)
                    
                    # DirectX for MEF/MDL
                    fix_export_to_directx_in_main(str(file_path), output_subdir, file_type, model, export_formats)
                
                successful += 1
                print(f"\n✓ Successfully processed: {file_path.name}")
                
            except Exception as e:
                failed += 1
                print(f"\n✗ Error processing {file_path.name}: {e}")
                import traceback
                traceback.print_exc()
        
        print("\n" + "=" * 60)
        print("BATCH PROCESSING COMPLETE")
        print("=" * 60)
        print(f"Total files found : {len(all_files)}")
        print(f"Successfully processed : {successful}")
        print(f"Failed : {failed}")
        print(f"Output folder : {args.output}")
        print("=" * 60)


# تفعيل الإضافات
def apply_all_fixes():
    """تطبيق جميع الإصلاحات والإضافات"""
    
    # إضافة دوال DirectX إلى MefModelIGI2 و MefModelIGI1
    add_directx_export_to_mef_model_igi2()
    add_directx_export_to_mef_model_igi1()
    
    # إعادة تعريف دوال SMD و OBJ العامة
    # (هذه الدوال موجودة بالفعل في السكربت، فقط نحتاج للتأكد من أنها معرفة بشكل صحيح)
    
    print("✅ All fixes applied successfully")


# استدعاء تطبيق الإصلاحات
apply_all_fixes()

# ============================================================
# المرحلة 5: تحسين الأداء وإضافة دعم متقدم
# أضف هذا الكود إلى نهاية السكربت (قبل if __name__ == "__main__":)
# ============================================================

import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from functools import partial
import hashlib
import pickle
import time
from contextlib import contextmanager

# ============================================================
# معالجة متوازية للبيانات الكبيرة
# ============================================================

class ParallelProcessor:
    """معالج متوازي للبيانات الكبيرة"""
    
    def __init__(self, max_workers: int = None):
        if max_workers is None:
            max_workers = mp.cpu_count()
        self.max_workers = max_workers
        print(f"🚀 Parallel processor initialized with {max_workers} workers")
    
    @staticmethod
    def process_vertices_chunk(vertices_chunk: np.ndarray, 
                               bone_matrices: np.ndarray,
                               debug_params) -> np.ndarray:
        """معالجة مجموعة من الرؤوس (للعمل المتوازي)"""
        result = []
        for v in vertices_chunk:
            # تطبيق swizzle والتحويلات
            if hasattr(v, '__getitem__') and len(v) >= 3:
                px, py, pz = debug_params.swizzle(v[0], v[1], v[2], debug_params.v_scale)
                result.append((px, py, pz))
            else:
                result.append((0, 0, 0))
        return np.array(result)
    
    def process_skin_batch(self, vertices: np.ndarray, 
                           bones: List, 
                           debug_params,
                           batch_size: int = 10000) -> np.ndarray:
        """معالجة التزين بشكل متوازي على دفعات"""
        vertex_count = len(vertices)
        batches = []
        
        # تقسيم البيانات إلى دفعات
        for i in range(0, vertex_count, batch_size):
            batch = vertices[i:i+batch_size]
            batches.append(batch)
        
        print(f"   📦 Split {vertex_count} vertices into {len(batches)} batches")
        
        # المعالجة المتوازية
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for batch in batches:
                future = executor.submit(
                    self.process_vertices_chunk,
                    batch, None, debug_params
                )
                futures.append(future)
            
            # جمع النتائج
            results = []
            for future in futures:
                results.append(future.result())
        
        # دمج النتائج
        return np.vstack(results) if results else np.array([])


# ============================================================
# تحسين MefModelIGI2 مع المعالجة المتوازية
# ============================================================

class OptimizedMefModelIGI2(MefModelIGI2):
    def __init__(self, buffer: Buffer, export_mode: str = "simple",
                 debug_params: Optional[MefDebugParams] = None,
                 use_parallel: bool = True):
        self.use_parallel = use_parallel
        if use_parallel:
            self.parallel = ParallelProcessor()
        # استدعاء مُهيئ MefModelIGI2 الأصلي
        MefModelIGI2.__init__(self, buffer, export_mode, debug_params)
        
    def _transform_vertices_optimized(self, vertices: np.ndarray, 
                                       model_type) -> np.ndarray:
        """تحويل الرؤوس بشكل محسن مع استخدام vectorized operations"""
        
        # استخراج البيانات باستخدام vectorized operations
        positions = None
        if "pos" in vertices.dtype.names:
            positions = vertices["pos"]
        else:
            # بناء مصفوفة المواضع من الحقول المنفصلة
            if "px" in vertices.dtype.names:
                positions = np.column_stack((
                    vertices["px"], vertices["py"], vertices["pz"]
                ))
            else:
                positions = np.array([(0,0,0) for _ in range(len(vertices))])
        
        # تطبيق swizzle بشكل vectorized
        if self.debug_params.swizzle_mode == "XZY" and positions is not None:
            # XZY swizzle: (x, z, -y)
            transformed = np.zeros_like(positions)
            transformed[:, 0] = positions[:, 0] * self.debug_params.v_scale
            transformed[:, 1] = positions[:, 2] * self.debug_params.v_scale
            transformed[:, 2] = -positions[:, 1] * self.debug_params.v_scale
        elif positions is not None:
            transformed = positions * self.debug_params.v_scale
        else:
            transformed = np.array([])
        
        return transformed
    
    def export_render_mesh_optimized(self, out_dir: str, base_name: str, 
                                      export_formats: List[str] = None):
        """تصدير شبكة التصيير مع معالجة متوازية"""
        if export_formats is None:
            export_formats = ["obj"]
        
        if self.render_mesh_data is None:
            print("No render mesh data")
            return
        
        vertices = self.render_mesh_data.vertices
        faces = self.render_mesh_data.faces
        model_type = self.model_info.model_type
        
        # تحويل الرؤوس مع معالجة متوازية
        if self.use_parallel and len(vertices) > 10000:
            print(f"   🚀 Using parallel processing for {len(vertices)} vertices")
            vertices_transformed = self.parallel.process_skin_batch(
                vertices, self.bones, self.debug_params
            )
        else:
            # معالجة عادية للمجموعات الصغيرة
            vertices_transformed = self._transform_vertices_optimized(vertices, model_type)
        
        # تصدير باستخدام الدوال الموجودة
        self._export_render_mesh_fast(out_dir, base_name, vertices_transformed, faces, export_formats)
    
    def _export_render_mesh_fast(self, out_dir: str, base_name: str, 
                                  vertices_transformed: np.ndarray,
                                  faces: np.ndarray, export_formats: List[str]):
        """تصدير سريع لشبكة التصيير"""
        has_normals = "nx" in vertices_transformed.dtype.names if hasattr(vertices_transformed, 'dtype') else False
        has_uv = "u" in vertices_transformed.dtype.names if hasattr(vertices_transformed, 'dtype') else False
        
        if "obj" in export_formats:
            obj_path = os.path.join(out_dir, f"{base_name}_optimized.obj")
            mtl_path = os.path.join(out_dir, f"{base_name}_optimized.mtl")
            
            with open(mtl_path, 'w', encoding='utf-8') as f:
                f.write("newmtl material\n")
                f.write("Ns 10.0000\n")
                f.write("Ka 1.0000 1.0000 1.0000\n")
                f.write("Kd 1.0000 1.0000 1.0000\n")
                f.write("Ks 0.0000 0.0000 0.0000\n")
            
            with open(obj_path, 'w', encoding='utf-8') as f:
                f.write(f"mtllib {base_name}_optimized.mtl\n")
                f.write(f"o {base_name}_optimized\n")
                
                # كتابة الرؤوس
                for v in vertices_transformed:
                    if len(v) >= 3:
                        f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
                
                f.write("usemtl material\n")
                for face in faces:
                    if len(face) >= 3:
                        a, b, c = face[0]+1, face[1]+1, face[2]+1
                        f.write(f"f {a} {b} {c}\n")
            
            print(f"   Optimized OBJ: {obj_path}")


# ============================================================
# نظام تخزين مؤقت (Caching) متقدم
# ============================================================

class MefCache:
    """نظام تخزين مؤقت لنتائج تحويل النماذج"""
    
    CACHE_DIR = ".mef_cache"
    
    def __init__(self, enabled: bool = True, max_size_mb: int = 500):
        self.enabled = enabled
        self.max_size_mb = max_size_mb
        self.cache = {}
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self):
        """إنشاء مجلد التخزين المؤقت"""
        if self.enabled:
            Path(self.CACHE_DIR).mkdir(exist_ok=True)
    
    def _get_file_hash(self, filepath: str) -> str:
        """حساب هاش للملف لتحديد فريد"""
        hasher = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def _get_cache_path(self, file_hash: str, format_name: str) -> Path:
        """الحصول على مسار ملف التخزين المؤقت"""
        return Path(self.CACHE_DIR) / f"{file_hash}_{format_name}.cache"
    
    def get_cached_result(self, filepath: str, format_name: str):
        """استرجاع نتيجة مخزنة مؤقتاً"""
        if not self.enabled:
            return None
        
        file_hash = self._get_file_hash(filepath)
        cache_path = self._get_cache_path(file_hash, format_name)
        
        if cache_path.exists():
            try:
                with open(cache_path, 'rb') as f:
                    result = pickle.load(f)
                print(f"   📦 Cache hit for {Path(filepath).name} ({format_name})")
                return result
            except Exception as e:
                print(f"   ⚠️ Cache read error: {e}")
        return None
    
    def store_cached_result(self, filepath: str, format_name: str, result: any):
        """تخزين نتيجة في التخزين المؤقت"""
        if not self.enabled:
            return
        
        file_hash = self._get_file_hash(filepath)
        cache_path = self._get_cache_path(file_hash, format_name)
        
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(result, f)
            print(f"   💾 Cached result for {Path(filepath).name} ({format_name})")
        except Exception as e:
            print(f"   ⚠️ Cache write error: {e}")
    
    def clear_cache(self):
        """مسح جميع الملفات المخزنة مؤقتاً"""
        if self.enabled:
            for cache_file in Path(self.CACHE_DIR).glob("*.cache"):
                cache_file.unlink()
            print(f"   🧹 Cache cleared: {self.CACHE_DIR}")
    
    def get_cache_size(self) -> int:
        """الحصول على حجم التخزين المؤقت بالبايت"""
        if not self.enabled:
            return 0
        total = sum(f.stat().st_size for f in Path(self.CACHE_DIR).glob("*.cache"))
        return total


# ============================================================
# دعم الرسوم المتحركة (Animation)
# ============================================================

@dataclass
class AnimationKeyframe:
    """إطار مفتاحي للحركة"""
    time: float
    bone_id: int
    position: Vector3
    rotation: Vector3
    scale: Vector3


@dataclass
class Animation:
    """رسوم متحركة للنموذج"""
    name: str
    duration: float
    fps: float
    keyframes: List[AnimationKeyframe]
    bone_count: int


class AnimationExporter:
    """مصدر للرسوم المتحركة من XTRW/ TXAN"""
    
    def __init__(self, model):
        self.model = model
        self.animations: List[Animation] = []
    
    def extract_from_txan(self) -> List[Animation]:
        """استخراج الرسوم المتحركة من بيانات TXAN"""
        if not hasattr(self.model, 'txan_data') or not self.model.txan_data:
            return []
        
        animations = []
        for i, txan in enumerate(self.model.txan_data):
            # تحليل بيانات TXAN
            fields = txan.unknown_fields
            
            # تخمين معنى الحقول
            if len(fields) >= 28:
                bone_count = fields[0] if fields[0] < 100 else 0
                frame_count = fields[1] if fields[1] < 1000 else 0
                duration = fields[2] / 1000.0 if fields[2] > 0 else 1.0
                
                keyframes = []
                for frame in range(min(frame_count, 100)):
                    for bone in range(min(bone_count, 10)):
                        # قراءة الموضع (تخميني - يحتاج لتحليل دقيق)
                        pos = Vector3(
                            fields[4 + bone * 3] if 4 + bone * 3 < len(fields) else 0,
                            fields[5 + bone * 3] if 5 + bone * 3 < len(fields) else 0,
                            fields[6 + bone * 3] if 6 + bone * 3 < len(fields) else 0
                        )
                        
                        keyframes.append(AnimationKeyframe(
                            time=frame / max(frame_count, 1) * duration,
                            bone_id=bone,
                            position=pos,
                            rotation=Vector3(0, 0, 0),
                            scale=Vector3(1, 1, 1)
                        ))
                
                if keyframes:
                    animations.append(Animation(
                        name=f"animation_{i}",
                        duration=duration,
                        fps=30.0,
                        keyframes=keyframes,
                        bone_count=bone_count
                    ))
        
        self.animations = animations
        return animations
    
    def export_to_gltf_animations(self, output_path: str) -> bool:
        """تصدير الرسوم المتحركة إلى glTF (مع دعم الحركة)"""
        if not GLTF_AVAILABLE:
            print("   pygltflib not available")
            return False
        
        if not self.animations:
            print("   No animations to export")
            return False
        
        try:
            from pygltflib import GLTF2, Animation as GltfAnimation, AnimationChannel, AnimationSampler
            
            gltf = GLTF2()
            
            # بناء العقد للعظام
            bone_nodes = []
            for i, bone in enumerate(self.model.bones):
                node = Node(name=bone.name)
                gltf.nodes.append(node)
                bone_nodes.append(len(gltf.nodes)-1)
            
            # بناء الرسوم المتحركة
            for anim in self.animations:
                gltf_anim = GltfAnimation()
                gltf_anim.name = anim.name
                
                # تجميع الإطارات المفتاحية لكل عظمة
                for bone_id in range(min(anim.bone_count, len(bone_nodes))):
                    bone_keyframes = [kf for kf in anim.keyframes if kf.bone_id == bone_id]
                    if not bone_keyframes:
                        continue
                    
                    # إعداد sampler للحركة
                    sampler = AnimationSampler()
                    sampler.input = [kf.time for kf in bone_keyframes]
                    sampler.output = [
                        [kf.position.x, kf.position.y, kf.position.z] 
                        for kf in bone_keyframes
                    ]
                    
                    # إضافة channel للعظمة
                    channel = AnimationChannel()
                    channel.sampler = len(gltf_anim.samplers)
                    channel.target.node = bone_nodes[bone_id]
                    channel.target.path = "translation"
                    
                    gltf_anim.samplers.append(sampler)
                    gltf_anim.channels.append(channel)
                
                gltf.animations.append(gltf_anim)
            
            # حفظ الملف
            gltf.save(f"{output_path}_animated.gltf")
            print(f"   🎬 Exported {len(self.animations)} animations to glTF")
            return True
            
        except Exception as e:
            print(f"   Error exporting animations: {e}")
            return False
    
    def export_to_json(self, output_path: str):
        """تصدير الرسوم المتحركة إلى JSON"""
        data = {
            "animations": [
                {
                    "name": anim.name,
                    "duration": anim.duration,
                    "fps": anim.fps,
                    "bone_count": anim.bone_count,
                    "keyframes": [
                        {
                            "time": kf.time,
                            "bone_id": kf.bone_id,
                            "position": [kf.position.x, kf.position.y, kf.position.z],
                            "rotation": [kf.rotation.x, kf.rotation.y, kf.rotation.z],
                            "scale": [kf.scale.x, kf.scale.y, kf.scale.z]
                        }
                        for kf in anim.keyframes
                    ]
                }
                for anim in self.animations
            ]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"   🎬 Animations (JSON): {output_path}")


# ============================================================
# نظام مراقبة الأداء
# ============================================================

class PerformanceMonitor:
    """مراقبة أداء عمليات التحويل"""
    
    def __init__(self):
        self.metrics = {}
        self.current_operation = None
    
    @contextmanager
    def measure(self, operation_name: str):
        """قياس وقت تنفيذ عملية"""
        start = time.time()
        self.current_operation = operation_name
        try:
            yield
        finally:
            elapsed = time.time() - start
            if operation_name not in self.metrics:
                self.metrics[operation_name] = []
            self.metrics[operation_name].append(elapsed)
            print(f"   ⏱️ {operation_name}: {elapsed:.3f}s")
    
    def print_report(self):
        """طباعة تقرير الأداء"""
        print("\n" + "=" * 60)
        print("📊 PERFORMANCE REPORT")
        print("=" * 60)
        
        for op_name, times in self.metrics.items():
            avg_time = sum(times) / len(times)
            total_time = sum(times)
            print(f"   {op_name:30}: avg={avg_time:.3f}s, total={total_time:.3f}s, calls={len(times)}")
        
        total = sum(sum(times) for times in self.metrics.values())
        print(f"\n   {'TOTAL':30}: {total:.3f}s")
        print("=" * 60)


# ============================================================
# دالة تحويل رئيسية محسنة
# ============================================================

def optimized_convert_file(input_path: str, output_dir: str, 
                          use_parallel: bool = True,
                          use_cache: bool = True,
                          extract_animations: bool = True,
                          export_formats: List[str] = None) -> dict:
    """
    دالة تحويل محسنة مع دعم متقدم
    
    Args:
        input_path: مسار ملف الإدخال
        output_dir: مجلد الإخراج
        use_parallel: استخدام المعالجة المتوازية
        use_cache: استخدام التخزين المؤقت
        extract_animations: استخراج الرسوم المتحركة
        export_formats: صيغ التصدير المطلوبة
    
    Returns:
        قاموس يحتوي على نتائج التحويل
    """
    
    if export_formats is None:
        export_formats = ["obj", "gltf", "json", "txt"]
    
    monitor = PerformanceMonitor()
    cache = MefCache(enabled=use_cache)
    
    result = {
        "success": False,
        "input": input_path,
        "output": output_dir,
        "metrics": {},
        "animations_found": 0,
        "cached": False
    }
    
    # التحقق من التخزين المؤقت
    if use_cache:
        cached_result = cache.get_cached_result(input_path, "full_export")
        if cached_result:
            result["cached"] = True
            result["success"] = True
            result["metrics"] = cached_result.get("metrics", {})
            print(f"   ✅ Using cached result for {Path(input_path).name}")
            return result
    
    try:
        # قراءة الملف
        with monitor.measure("File read"):
            with open(input_path, "rb") as f:
                data = f.read()
        
        # إنشاء النموذج المحسن
        with monitor.measure("Model parsing"):
            buffer = Buffer(data)
            model = OptimizedMefModelIGI2(buffer, export_mode="multi", 
                                          use_parallel=use_parallel)
        
        # استخراج الرسوم المتحركة
        if extract_animations and hasattr(model, 'txan_data') and model.txan_data:
            with monitor.measure("Animation extraction"):
                anim_exporter = AnimationExporter(model)
                animations = anim_exporter.extract_from_txan()
                result["animations_found"] = len(animations)
                
                if animations and "gltf" in export_formats:
                    anim_exporter.export_to_gltf_animations(
                        os.path.join(output_dir, Path(input_path).stem)
                    )
                
                if animations and "json" in export_formats:
                    anim_exporter.export_to_json(
                        os.path.join(output_dir, f"{Path(input_path).stem}_animations.json")
                    )
        
        # تصدير النموذج
        with monitor.measure("Model export"):
            base_name = Path(input_path).stem
            out_path = os.path.join(output_dir, base_name)
            if hasattr(model, 'export_all_enhanced'):
                model.export_all_enhanced(out_path, export_formats)
            else:
                model.export_all(out_path, export_formats)
        
        # تخزين النتيجة في التخزين المؤقت
        if use_cache:
            cache.store_cached_result(input_path, "full_export", {
                "metrics": monitor.metrics,
                "animations": result["animations_found"],
                "export_formats": export_formats
            })
        
        result["success"] = True
        result["metrics"] = monitor.metrics
        
        # طباعة تقرير الأداء
        monitor.print_report()
        
        return result
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        result["error"] = str(e)
        return result


# ============================================================
# دالة معالجة مجلد كامل بشكل متوازي
# ============================================================

def parallel_process_folder(input_dir: str, output_dir: str,
                           max_workers: int = None,
                           use_cache: bool = True,
                           export_formats: List[str] = None) -> dict:
    """
    معالجة مجلد كامل من ملفات MEF بشكل متوازي
    
    Args:
        input_dir: مجلد الإدخال
        output_dir: مجلد الإخراج
        max_workers: عدد العمليات المتوازية
        use_cache: استخدام التخزين المؤقت
        export_formats: صيغ التصدير
    
    Returns:
        قاموس بنتائج المعالجة
    """
    
    if max_workers is None:
        max_workers = mp.cpu_count()
    
    # البحث عن ملفات MEF
    mef_files = []
    for ext in ['*.mef', '*.MEF']:
        mef_files.extend(Path(input_dir).glob(ext))
    
    if not mef_files:
        print(f"No MEF files found in {input_dir}")
        return {"total": 0, "successful": 0, "failed": 0}
    
    print(f"\n📁 Found {len(mef_files)} MEF files")
    print(f"🚀 Using {max_workers} parallel workers")
    print("=" * 60)
    
    # إعداد المعالجة المتوازية
    results = []
    successful = 0
    failed = 0
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # تجهيز المهام
        futures = []
        for mef_file in mef_files:
            output_subdir = os.path.join(output_dir, mef_file.stem)
            future = executor.submit(
                optimized_convert_file,
                str(mef_file),
                output_subdir,
                True,  # use_parallel
                use_cache,
                True,  # extract_animations
                export_formats
            )
            futures.append((mef_file.name, future))
        
        # جمع النتائج
        for filename, future in futures:
            try:
                result = future.result()
                if result["success"]:
                    successful += 1
                    print(f"   ✅ {filename}: success (cached={result.get('cached', False)})")
                else:
                    failed += 1
                    print(f"   ❌ {filename}: failed - {result.get('error', 'Unknown error')}")
                results.append(result)
            except Exception as e:
                failed += 1
                print(f"   ❌ {filename}: exception - {e}")
    
    # تقرير نهائي
    print("\n" + "=" * 60)
    print("📊 BATCH PROCESSING REPORT")
    print("=" * 60)
    print(f"   Total files    : {len(mef_files)}")
    print(f"   Successful     : {successful}")
    print(f"   Failed         : {failed}")
    print(f"   Output folder  : {output_dir}")
    print("=" * 60)
    
    return {
        "total": len(mef_files),
        "successful": successful,
        "failed": failed,
        "results": results
    }


# ============================================================
# واجهة سطر أوامر محسنة
# ============================================================

def main_optimized():
    """الدالة الرئيسية المحسنة مع خيارات متقدمة"""
    
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Optimized MEF Model Exporter for IGI1/IGI2 (with caching & parallel processing)"
    )
    parser.add_argument("input", nargs="?", default=INPUT_DIR,
                       help=f"Input file or folder (default: {INPUT_DIR})")
    parser.add_argument("-o", "--output", default=OUTPUT_DIR,
                       help=f"Output directory (default: {OUTPUT_DIR})")
    parser.add_argument("-f", "--format", choices=["obj", "dae", "gltf", "json", "txt", "all"], 
                       default="obj", help="Export format")
    parser.add_argument("--parallel", action="store_true", default=True,
                       help="Enable parallel processing (default: True)")
    parser.add_argument("--no-parallel", action="store_false", dest="parallel",
                       help="Disable parallel processing")
    parser.add_argument("--cache", action="store_true", default=True,
                       help="Enable caching (default: True)")
    parser.add_argument("--no-cache", action="store_false", dest="cache",
                       help="Disable caching")
    parser.add_argument("--animations", action="store_true", default=True,
                       help="Extract animations (default: True)")
    parser.add_argument("--no-animations", action="store_false", dest="animations",
                       help="Disable animation extraction")
    parser.add_argument("--workers", type=int, default=None,
                       help=f"Number of parallel workers (default: CPU count)")
    parser.add_argument("--clear-cache", action="store_true",
                       help="Clear cache before processing")
    
    args = parser.parse_args()
    
    # إعدادات التصدير
    export_formats = ["obj"]
    if args.format == "dae":
        export_formats = ["dae"]
    elif args.format == "gltf":
        export_formats = ["gltf"]
    elif args.format == "json":
        export_formats = ["json"]
    elif args.format == "txt":
        export_formats = ["txt"]
    elif args.format == "directx":
        export_formats = ["directx"]
    elif args.format == "all":
        export_formats = ["obj", "dae", "gltf", "json", "txt", "directx"]
    
    print("\n" + "=" * 70)
    print("🚀 OPTIMIZED MEF MODEL EXPORTER")
    print("=" * 70)
    print(f"   Parallel processing : {args.parallel}")
    print(f"   Caching            : {args.cache}")
    print(f"   Extract animations : {args.animations}")
    print(f"   Workers            : {args.workers or 'auto'}")
    print(f"   Export formats     : {', '.join(export_formats)}")
    print("=" * 70)
    
    # مسح التخزين المؤقت إذا طلب
    if args.clear_cache:
        cache = MefCache(enabled=True)
        cache.clear_cache()
    
    # إنشاء مجلد الإخراج
    Path(args.output).mkdir(parents=True, exist_ok=True)
    
    # معالجة ملف واحد أو مجلد
    if os.path.isfile(args.input):
        result = optimized_convert_file(
            args.input, args.output,
            use_parallel=args.parallel,
            use_cache=args.cache,
            extract_animations=args.animations,
            export_formats=export_formats
        )
        
        if result["success"]:
            print(f"\n✅ Successfully converted: {Path(args.input).name}")
            if result.get("cached"):
                print(f"   (Result from cache)")
            if result.get("animations_found", 0) > 0:
                print(f"   🎬 Found {result['animations_found']} animations")
        else:
            print(f"\n❌ Failed to convert: {Path(args.input).name}")
            
    elif os.path.isdir(args.input):
        # معالجة متوازية للمجلد
        result = parallel_process_folder(
            args.input, args.output,
            max_workers=args.workers,
            use_cache=args.cache,
            export_formats=export_formats
        )
    else:
        print(f"\n❌ Error: Input '{args.input}' not found!")
        sys.exit(1)
        

# ============================================================
# المرحلة المتقدمة: Blender Add-on، تحليل حركة متقدم، IGI1 محسن، واجهة PyQt5
# أضف هذا الكود إلى نهاية السكربت (قبل if __name__ == "__main__":)
# ============================================================

# ============================================================
# الجزء 1: تحليل أعمق للرسوم المتحركة
# ============================================================

import struct
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field

@dataclass
class BoneAnimationTrack:
    """مسار حركة لعظمة واحدة"""
    bone_id: int
    bone_name: str
    positions: List[Tuple[float, float, float]] = field(default_factory=list)
    rotations: List[Tuple[float, float, float, float]] = field(default_factory=list)  # quaternion
    scales: List[Tuple[float, float, float]] = field(default_factory=list)
    times: List[float] = field(default_factory=list)


@dataclass
class AdvancedAnimation:
    """رسوم متحركة متقدمة مع جميع البيانات"""
    name: str
    duration: float
    frame_count: int
    fps: float
    bone_tracks: Dict[int, BoneAnimationTrack] = field(default_factory=dict)
    morph_targets: List[str] = field(default_factory=list)  # أهداف التشكل
    event_markers: Dict[float, str] = field(default_factory=dict)  # أحداث في أطر زمنية


class AdvancedAnimationAnalyzer:
    """محلل متقدم للرسوم المتحركة من بيانات MEF"""
    
    def __init__(self):
        self.animations: List[AdvancedAnimation] = []
    
    def analyze_txan(self, txan_data: List, bone_count: int, frame_rate: float = 30.0) -> List[AdvancedAnimation]:
        """تحليل متقدم لبيانات TXAN"""
        animations = []
        
        for txan_idx, txan in enumerate(txan_data):
            fields = txan.unknown_fields
            
            if len(fields) < 28:
                continue
            
            # تحليل الحقول حسب فهم أعمق لـ TXAN
            # ملاحظة: هذه التحليلات تحتاج لاختبار على ملفات حقيقية
            
            # ---- تخمين معنى الحقول ----
            version = fields[0]          # غالباً 1 أو 2
            frame_count = fields[1]      # عدد الإطارات
            duration_ms = fields[2]      # المدة بالميلي ثانية
            bone_count_anim = fields[3]  # عدد العظام المتحركة
            
            duration = duration_ms / 1000.0 if duration_ms > 0 else frame_count / frame_rate
            
            # إنشاء كائن الحركة
            anim = AdvancedAnimation(
                name=f"animation_{txan_idx}",
                duration=duration,
                frame_count=frame_count,
                fps=frame_rate
            )
            
            # استخراج مسارات العظام
            frame_data_size = bone_count_anim * 6  # 3 موضع + 3 دوران (تخميني)
            
            for frame in range(min(frame_count, 100)):  # حد أقصى 100 إطار
                frame_time = frame / frame_count * duration if frame_count > 0 else 0
                
                for bone in range(min(bone_count_anim, bone_count)):
                    # حساب المؤشر في المصفوفة
                    idx = 4 + (frame * bone_count_anim + bone) * 6
                    
                    if idx + 5 < len(fields):
                        # قراءة موضع العظمة
                        px = fields[idx] / 100.0 if fields[idx] != 0 else 0
                        py = fields[idx + 1] / 100.0 if fields[idx + 1] != 0 else 0
                        pz = fields[idx + 2] / 100.0 if fields[idx + 2] != 0 else 0
                        
                        # قراءة دوران العظمة (كأويلر)
                        rx = fields[idx + 3] / 32768.0 * 180.0
                        ry = fields[idx + 4] / 32768.0 * 180.0
                        rz = fields[idx + 5] / 32768.0 * 180.0
                        
                        # إنشاء المسار إذا لم يكن موجوداً
                        if bone not in anim.bone_tracks:
                            anim.bone_tracks[bone] = BoneAnimationTrack(
                                bone_id=bone,
                                bone_name=f"bone_{bone}"
                            )
                        
                        # إضافة البيانات للإطار
                        anim.bone_tracks[bone].times.append(frame_time)
                        anim.bone_tracks[bone].positions.append((px, py, pz))
                        
                        # تحويل أويلر إلى كواترنيون
                        quat = self.euler_to_quaternion(rx, ry, rz)
                        anim.bone_tracks[bone].rotations.append(quat)
                        anim.bone_tracks[bone].scales.append((1.0, 1.0, 1.0))
            
            if anim.bone_tracks:
                animations.append(anim)
        
        self.animations = animations
        return animations
    
    def euler_to_quaternion(self, rx: float, ry: float, rz: float) -> Tuple[float, float, float, float]:
        """تحويل زوايا أويلر (بالدرجات) إلى كواترنيون"""
        # تحويل إلى راديان
        rx_rad = np.radians(rx)
        ry_rad = np.radians(ry)
        rz_rad = np.radians(rz)
        
        # حساب الكواترنيون
        cx = np.cos(rx_rad * 0.5)
        sx = np.sin(rx_rad * 0.5)
        cy = np.cos(ry_rad * 0.5)
        sy = np.sin(ry_rad * 0.5)
        cz = np.cos(rz_rad * 0.5)
        sz = np.sin(rz_rad * 0.5)
        
        qw = cx * cy * cz + sx * sy * sz
        qx = sx * cy * cz - cx * sy * sz
        qy = cx * sy * cz + sx * cy * sz
        qz = cx * cy * sz - sx * sy * cz
        
        return (qx, qy, qz, qw)
    
    def analyze_morph_targets(self, morph_channels: Dict, frame_rate: float = 30.0) -> List[AdvancedAnimation]:
        """تحليل أهداف التشكل للرسوم المتحركة"""
        animations = []
        
        for channel_id, vertices in morph_channels.items():
            if len(vertices) == 0:
                continue
            
            # إنشاء حركة للتشكل
            anim = AdvancedAnimation(
                name=f"morph_channel_{channel_id}",
                duration=1.0,
                frame_count=1,
                fps=frame_rate
            )
            
            # إضافة أهداف التشكل
            for v in vertices[:10]:  # حد أقصى 10 أهداف
                target_name = f"morph_target_{v['index']}"
                anim.morph_targets.append(target_name)
            
            animations.append(anim)
        
        self.animations.extend(animations)
        return animations
    
    def blend_animations(self, anim1: AdvancedAnimation, anim2: AdvancedAnimation, 
                         weight: float) -> AdvancedAnimation:
        """دمج حركتين مع وزن معين"""
        if weight <= 0:
            return anim1
        if weight >= 1:
            return anim2
        
        blended = AdvancedAnimation(
            name=f"blended_{anim1.name}_{anim2.name}",
            duration=max(anim1.duration, anim2.duration),
            frame_count=max(anim1.frame_count, anim2.frame_count),
            fps=anim1.fps
        )
        
        # دمج مسارات العظام المشتركة
        common_bones = set(anim1.bone_tracks.keys()) & set(anim2.bone_tracks.keys())
        
        for bone_id in common_bones:
            track1 = anim1.bone_tracks[bone_id]
            track2 = anim2.bone_tracks[bone_id]
            
            # دمج البيانات
            blended_track = BoneAnimationTrack(
                bone_id=bone_id,
                bone_name=track1.bone_name,
                times=track1.times[:],  # استخدام وقت الحركة الأولى
                positions=[],
                rotations=[],
                scales=[]
            )
            
            # دمج المواضع
            for i in range(min(len(track1.positions), len(track2.positions))):
                pos1 = track1.positions[i]
                pos2 = track2.positions[i]
                blended_pos = (
                    pos1[0] * (1 - weight) + pos2[0] * weight,
                    pos1[1] * (1 - weight) + pos2[1] * weight,
                    pos1[2] * (1 - weight) + pos2[2] * weight
                )
                blended_track.positions.append(blended_pos)
            
            # دمج الدورانات (Slerp للكواترنيونات)
            for i in range(min(len(track1.rotations), len(track2.rotations))):
                quat1 = track1.rotations[i]
                quat2 = track2.rotations[i]
                blended_quat = self.slerp_quaternion(quat1, quat2, weight)
                blended_track.rotations.append(blended_quat)
            
            blended.bone_tracks[bone_id] = blended_track
        
        return blended
    
    def slerp_quaternion(self, q1: Tuple[float, ...], q2: Tuple[float, ...], 
                         t: float) -> Tuple[float, float, float, float]:
        """SLERP بين كواترنيونين"""
        # نُحوّل إلى numpy arrays
        q1_arr = np.array(q1)
        q2_arr = np.array(q2)
        
        # حساب جيب التمام
        dot = np.dot(q1_arr, q2_arr)
        
        # إذا كانت الزاوية صغيرة، استخدم LERP
        if dot < 0:
            q2_arr = -q2_arr
            dot = -dot
        
        if dot > 0.9995:
            # LERP
            result = q1_arr + t * (q2_arr - q1_arr)
            result = result / np.linalg.norm(result)
            return tuple(result)
        
        # SLERP
        theta_0 = np.arccos(dot)
        theta = theta_0 * t
        sin_theta = np.sin(theta)
        sin_theta_0 = np.sin(theta_0)
        
        s1 = np.cos(theta) - dot * sin_theta / sin_theta_0
        s2 = sin_theta / sin_theta_0
        
        result = (q1_arr * s1) + (q2_arr * s2)
        return tuple(result)
    
    def export_to_mmd(self, output_path: str) -> bool:
        """تصدير الحركة إلى صيغة MMD (.vmd)"""
        if not self.animations:
            return False
        
        # MMD VMD format
        # Header: "Vocaloid Motion Data 0002"
        header = b"Vocaloid Motion Data 0002\0"
        
        with open(output_path, 'wb') as f:
            f.write(header)
            
            # عدد الحركات
            f.write(struct.pack('<I', len(self.animations)))
            
            for anim in self.animations:
                # اسم الحركة (15 بايت + null)
                name_bytes = anim.name.encode('utf-8', errors='ignore')[:15]
                f.write(name_bytes.ljust(15, b'\x00'))
                f.write(b'\x00')
                
                # عدد الإطارات
                f.write(struct.pack('<I', anim.frame_count))
                
                # كتابة إطارات الحركة
                for bone_id, track in anim.bone_tracks.items():
                    for i, time in enumerate(track.times):
                        frame_idx = int(time * anim.fps)
                        
                        # بيانات الإطار
                        f.write(struct.pack('<I', frame_idx))  # رقم الإطار
                        
                        # اسم العظمة (15 بايت + null)
                        bone_name = track.bone_name.encode('utf-8', errors='ignore')[:15]
                        f.write(bone_name.ljust(15, b'\x00'))
                        f.write(b'\x00')
                        
                        # الموضع
                        if i < len(track.positions):
                            px, py, pz = track.positions[i]
                            f.write(struct.pack('<fff', px, py, pz))
                        else:
                            f.write(struct.pack('<fff', 0, 0, 0))
                        
                        # الدوران (كواترنيون)
                        if i < len(track.rotations):
                            qx, qy, qz, qw = track.rotations[i]
                            f.write(struct.pack('<ffff', qx, qy, qz, qw))
                        else:
                            f.write(struct.pack('<ffff', 0, 0, 0, 1))
                        
                        # الإقحام (interpolation) - بيانات افتراضية
                        f.write(b'\x00' * 64)
        
        print(f"   🎬 Exported animation to MMD: {output_path}")
        return True
    
    def export_to_fbx_style(self, output_path: str) -> bool:
        """تصدير الحركة إلى صيغة تشبه FBX (JSON)"""
        if not self.animations:
            return False
        
        data = {
            "animations": [],
            "format": "Advanced Animation Data",
            "version": "1.0"
        }
        
        for anim in self.animations:
            anim_data = {
                "name": anim.name,
                "duration": anim.duration,
                "frame_count": anim.frame_count,
                "fps": anim.fps,
                "bone_tracks": [],
                "morph_targets": anim.morph_targets,
                "event_markers": anim.event_markers
            }
            
            for bone_id, track in anim.bone_tracks.items():
                track_data = {
                    "bone_id": bone_id,
                    "bone_name": track.bone_name,
                    "frames": [
                        {
                            "time": track.times[i],
                            "position": list(track.positions[i]) if i < len(track.positions) else [0, 0, 0],
                            "rotation": list(track.rotations[i]) if i < len(track.rotations) else [0, 0, 0, 1],
                            "scale": list(track.scales[i]) if i < len(track.scales) else [1, 1, 1]
                        }
                        for i in range(len(track.times))
                    ]
                }
                anim_data["bone_tracks"].append(track_data)
            
            data["animations"].append(anim_data)
        
        import json
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        print(f"   🎬 Exported animation to JSON: {output_path}")
        return True


# ============================================================
# الجزء 2: دعم محسن لـ IGI1
# ============================================================

class OptimizedMefModelIGI1(MefModelIGI1):
    """نسخة محسنة من MefModelIGI1 مع دعم متقدم"""
    
    def __init__(self, buffer: Buffer, export_mode: str = "simple",
                 debug_params: Optional[MefDebugParams] = None,
                 use_parallel: bool = True):
        
        # تسجيل بيانات الأداء
        self.use_parallel = use_parallel
        self.performance_stats = {}
        
        # استدعاء المُنشئ الأصلي
        super().__init__(buffer, export_mode, debug_params)
        
        # تحسينات إضافية لـ IGI1
        self._post_process_igi1()
    
    def _post_process_igi1(self):
        """معالجة لاحقة لتحسين بيانات IGI1"""
        # معالجة العظام (IGI1 قد يكون لها تزين بدون HIER)
        if not self.bones and self.model_info and self.model_info.bone_count > 0:
            self._infer_bones_from_vertices()
        
        # معالجة المواد
        if self.render_mesh_data and self.render_mesh_data.materials:
            self._enhance_materials()
        
        # معالجة القوام
        self._collect_texture_references()
    
    def _infer_bones_from_vertices(self):
        """استنتاج العظام من بيانات الرؤوس (عند عدم وجود HIER)"""
        if not self.render_mesh_data:
            return
        
        vertices = self.render_mesh_data.vertices
        if "bone_id" not in vertices.dtype.names:
            return
        
        unique_bones = set()
        for v in vertices:
            if hasattr(v, 'bone_id'):
                bone_id = v['bone_id'][0] if isinstance(v['bone_id'], np.ndarray) else v['bone_id']
                unique_bones.add(int(bone_id))
        
        # إنشاء عظام افتراضية
        self.bones = []
        for bone_id in sorted(unique_bones):
            self.bones.append(Bone(
                name=f"bone_{bone_id}",
                pos=Vector3(0, 0, 0),
                parent_id=-1
            ))
        
        # إضافة أسماء من BNAM إن وجدت
        if hasattr(self, 'bone_names') and self.bone_names:
            for i, name in enumerate(self.bone_names):
                if i < len(self.bones):
                    self.bones[i].name = name
        
        print(f"   🦴 Inferred {len(self.bones)} bones from vertex data")
    
    def _enhance_materials(self):
        """تحسين بيانات المواد"""
        for i, mat in enumerate(self.render_mesh_data.materials):
            # البحث عن القوام المرتبط
            tex_index = mat.get("texture_index", 0)
            if tex_index >= 0:
                tex_name = get_texture_name(tex_index, "model", i, None)
                mat["texture_name"] = tex_name
            
            # حساب مركز المادة (متوسط الموضع)
            vo = mat.get("vertex_offset", 0)
            vn = mat.get("vertex_count", 0)
            if vo is not None and vn > 0:
                vertices = self.render_mesh_data.vertices
                if vo + vn <= len(vertices):
                    centers = []
                    for j in range(vo, vo + vn):
                        v = vertices[j]
                        if hasattr(v, 'pos'):
                            centers.append(v['pos'])
                        elif hasattr(v, 'px'):
                            centers.append((v['px'], v['py'], v['pz']))
                    if centers:
                        avg_center = np.mean(centers, axis=0)
                        mat["center"] = avg_center.tolist()
    
    def _collect_texture_references(self):
        """جمع مراجع القوام لإنشاء أطلس"""
        self.texture_references = []
        
        if self.render_mesh_data and self.render_mesh_data.materials:
            for i, mat in enumerate(self.render_mesh_data.materials):
                tex_name = mat.get("texture_name", f"texture_{i}.tga")
                self.texture_references.append(TextureReference(i, tex_name))
        
        print(f"   📦 Collected {len(self.texture_references)} texture references")
    
    def export_all_enhanced(self, out_dir, export_formats=None, lightmap_format="png"):
        """تصدير محسن لـ IGI1"""
        if export_formats is None:
            export_formats = ["obj", "gltf", "json", "txt"]
        
        base_name = os.path.splitext(os.path.basename(out_dir))[0]
        self.ensure_dir(out_dir)
        
        print(f"\n📦 Exporting IGI1 model to {out_dir}")
        print("-" * 50)
        
        # ========== تصدير أساسي ==========
        self.export_hsem_info_igi1(out_dir, base_name)
        self.export_d3dr_info_igi1(out_dir, base_name)
        
        # ========== العظام إن وجدت ==========
        if self.bones:
            self.export_manb_detailed(out_dir, base_name)
            self.export_reih_detailed(out_dir, base_name)
        
        # ========== الشبكة الرئيسية ==========
        self.export_render_mesh(out_dir, base_name, export_formats)
        
        # ========== شبكة التصادم ==========
        self.export_collision_mesh(out_dir, base_name, 0, export_formats)
        if hasattr(self, 'collision_mesh_data2') and self.collision_mesh_data2:
            self.export_collision_mesh(out_dir, base_name, 1, export_formats)
        
        # ========== البيانات الإضافية ==========
        self.export_attachments(out_dir, base_name)
        self.export_lightmaps(out_dir, base_name, lightmap_format)
        self.export_extra_data(out_dir, base_name)
        
        # ========== تصدير محسن لـ IGI1 ==========
        self._export_enhanced_igi1_data(out_dir, base_name)
        
        print("-" * 50)
        print("✅ IGI1 enhanced export completed!")
    
    def _export_enhanced_igi1_data(self, out_dir: str, base_name: str):
        """تصدير بيانات محسنة خاصة بـ IGI1"""
        
        # مواد محسنة (JSON)
        if self.render_mesh_data and self.render_mesh_data.materials:
            mat_path = os.path.join(out_dir, f"{base_name}_materials_enhanced.json")
            data = convert_to_json_serializable(self.render_mesh_data.materials)
            with open(mat_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            print(f"   Enhanced materials (JSON): {mat_path}")
        
        # معلومات العظام المستنتجة
        if self.bones:
            bones_path = os.path.join(out_dir, f"{base_name}_inferred_bones.txt")
            with open(bones_path, 'w', encoding='utf-8') as f:
                f.write("# Inferred Bones from IGI1 Model\n\n")
                for i, bone in enumerate(self.bones):
                    f.write(f"Bone {i:3d}: {bone.name} (parent: {bone.parent_id})\n")
            print(f"   Inferred bones (TXT): {bones_path}")
        
        # إحصائيات النموذج
        stats = self._calculate_model_stats()
        stats_path = os.path.join(out_dir, f"{base_name}_statistics.json")
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)
        print(f"   Model statistics (JSON): {stats_path}")
    
    def _calculate_model_stats(self) -> dict:
        """حساب إحصائيات النموذج"""
        stats = {
            "model_type": self.model_info.model_type if self.model_info else None,
            "version": self.model_info.version if self.model_info else None,
            "bones": len(self.bones),
            "attachments": len(self.attachments),
            "magic_vertices": len(self.magic_vertices),
            "portals": len(self.portals),
            "glow_sprites": len(self.glow_sprites),
            "lightmaps": len(self.lightmaps),
            "txan_chunks": len(self.txan_data),
        }
        
        if self.render_mesh_data:
            stats["render_vertices"] = len(self.render_mesh_data.vertices)
            stats["render_materials"] = len(self.render_mesh_data.materials)
            stats["render_faces"] = sum(len(mat.get("faces", [])) for mat in self.render_mesh_data.materials)
        
        if hasattr(self, 'collision_vertices') and self.collision_vertices is not None:
            stats["collision_vertices"] = len(self.collision_vertices)
            stats["collision_faces"] = len(self.collision_faces) if self.collision_faces is not None else 0
        
        return stats
    
    # دمج مع نظام التخزين المؤقت
    def get_cache_key(self) -> str:
        """إنشاء مفتاح للتخزين المؤقت"""
        import hashlib
        key_data = f"{self.model_info.version if self.model_info else 0}_{len(self.bones)}_{len(self.render_mesh_data.vertices) if self.render_mesh_data else 0}"
        return hashlib.md5(key_data.encode()).hexdigest()


# ============================================================
# الجزء 3: وظائف مساعدة لـ Blender Add-on (محاكاة)
# ============================================================

# ملاحظة: هذا الكود هو واجهة محاكاة لـ Blender Add-on
# للاستخدام الفعلي في Blender، يجب وضعه في ملف منفصل داخل مجلد addons

def create_blender_addon_script(output_path: str):
    """إنشاء سكربت Blender Add-on جاهز للاستخدام"""
    
    addon_script = '''# ============================================================
# blender_addon.py - إضافة Blender لاستيراد ملفات MEF/MDL
# ============================================================
# وضع هذا الملف في: %APPDATA%\\Blender Foundation\\Blender\\X.XX\\scripts\\addons\\
# أو: ~/.config/blender/X.XX/scripts/addons/

bl_info = {
    "name": "IGI & Half-Life Model Importer",
    "author": "Tavrixender",
    "version": (2, 0, 0),
    "blender": (3, 0, 0),
    "location": "File > Import > IGI Model (.mef/.mdl)",
    "description": "Import IGI1/IGI2 MEF and Half-Life MDL models with full animation support",
    "category": "Import-Export",
}

import bpy
import bmesh
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty, FloatProperty
import struct
import numpy as np
from mathutils import Matrix, Vector, Quaternion
import os
import sys

# إضافة مسار السكربت الرئيسي
blend_dir = os.path.dirname(__file__)
if blend_dir not in sys.path:
    sys.path.append(blend_dir)

# ============================================================
# كلاس استيراد IGI
# ============================================================

class ImportIGIModel(bpy.types.Operator, ImportHelper):
    """استيراد نموذج من IGI1/IGI2 أو Half-Life MDL"""
    bl_idname = "import_scene.igi_model"
    bl_label = "Import IGI Model"
    bl_options = {'UNDO', 'PRESET'}
    
    # خيارات الملف
    files: bpy.props.CollectionProperty(
        type=bpy.types.OperatorFileListElement,
        options={'HIDDEN', 'SKIP_SAVE'}
    )
    directory: StringProperty(subtype='DIR_PATH')
    
    # خيارات الاستيراد
    import_animations: BoolProperty(
        name="Import Animations",
        description="Import skeletal animations if available",
        default=True
    )
    
    import_textures: BoolProperty(
        name="Import Textures",
        description="Import and assign textures",
        default=True
    )
    
    scale: FloatProperty(
        name="Scale",
        description="Model scale",
        default=1.0,
        min=0.01,
        max=100.0
    )
    
    create_atlas: BoolProperty(
        name="Create Texture Atlas",
        description="Merge multiple textures into one atlas",
        default=False
    )
    
    import_type: EnumProperty(
        name="Model Type",
        description="Type of model to import",
        items=[
            ('AUTO', "Auto-detect", "Automatically detect file type"),
            ('IGI1', "IGI1", "Project IGI 1 model"),
            ('IGI2', "IGI2", "Project IGI 2 model"),
            ('MDL', "Half-Life MDL", "Half-Life/Counter-Strike model"),
            ('SMD', "SMD", "StudioMDL file"),
            ('OBJ', "OBJ", "Wavefront OBJ file"),
        ],
        default='AUTO'
    )
    
    # خيارات متقدمة
    use_parallel: BoolProperty(
        name="Parallel Processing",
        description="Use multiple CPU cores for faster loading",
        default=True
    )
    
    load_collision: BoolProperty(
        name="Load Collision Mesh",
        description="Import collision mesh as separate object",
        default=False
    )
    
    load_shadow: BoolProperty(
        name="Load Shadow Mesh",
        description="Import shadow mesh as separate object",
        default=False
    )
    
    def execute(self, context):
        """تنفيذ الاستيراد"""
        self.report({'INFO'}, f"Importing {len(self.files)} file(s)")
        self.report({'INFO'}, "IGI Model Importer - Requires main script to be installed")
        return {'FINISHED'}


def menu_func_import(self, context):
    self.layout.operator(ImportIGIModel.bl_idname, text="IGI Model (.mef/.mdl)")


def register():
    bpy.utils.register_class(ImportIGIModel)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_class(ImportIGIModel)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)


if __name__ == "__main__":
    register()
'''
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(addon_script)
    
    print(f"✅ Blender Add-on script created: {output_path}")
    print("   Installation: Copy this file to Blender's addons folder")


# ============================================================
# الجزء 4: واجهة مستخدم رسومية (PyQt5) - مبسطة للتكامل
# ============================================================

def create_gui_launcher_script(output_path: str):
    """إنشاء سكربت تشغيل واجهة PyQt5"""
    
    gui_script = '''#!/usr/bin/env python3
# ============================================================
# mef_gui_launcher.py - تشغيل واجهة MEF Converter
# ============================================================

import sys
import os
from pathlib import Path

# إضافة مسار السكربت الرئيسي
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.append(script_dir)

def launch_gui():
    """تشغيل واجهة PyQt5"""
    try:
        from PyQt5.QtWidgets import QApplication
        from mef_gui import MEFConverterGUI
        
        app = QApplication(sys.argv)
        app.setStyle("Fusion")
        
        window = MEFConverterGUI()
        window.show()
        
        sys.exit(app.exec_())
    except ImportError as e:
        print(f"Error: {e}")
        print("\\nPlease install required packages:")
        print("  pip install PyQt5 numpy pillow pygltflib")
        sys.exit(1)
    except Exception as e:
        print(f"Error launching GUI: {e}")
        sys.exit(1)

if __name__ == "__main__":
    launch_gui()
'''
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(gui_script)
    
    print(f"✅ GUI launcher script created: {output_path}")


# ============================================================
# الجزء 5: وظائف مساعدة للرسوم المتحركة في MefModelIGI2
# ============================================================

def add_animation_support_to_igi2():
    """إضافة دعم الرسوم المتحركة إلى MefModelIGI2"""
    
    def extract_animations(self) -> List[AdvancedAnimation]:
        """استخراج الرسوم المتحركة من النموذج"""
        analyzer = AdvancedAnimationAnalyzer()
        
        # من TXAN
        if hasattr(self, 'txan_data') and self.txan_data:
            bone_count = len(self.bones) if hasattr(self, 'bones') else 0
            animations = analyzer.analyze_txan(self.txan_data, bone_count)
            print(f"   🎬 Extracted {len(animations)} animations from TXAN")
        
        # من Morph Channels
        if hasattr(self, 'morph_channels') and self.morph_channels:
            morph_anims = analyzer.analyze_morph_targets(self.morph_channels)
            animations.extend(morph_anims)
            print(f"   🎬 Extracted {len(morph_anims)} morph animations")
        
        return animations
    
    def export_animations(self, out_dir: str, base_name: str, formats: List[str] = None):
        """تصدير الرسوم المتحركة إلى صيغ متعددة"""
        if formats is None:
            formats = ["json", "mmd"]
        
        animations = self.extract_animations()
        if not animations:
            print("   No animations to export")
            return
        
        analyzer = AdvancedAnimationAnalyzer()
        analyzer.animations = animations
        
        for fmt in formats:
            if fmt == "json":
                analyzer.export_to_fbx_style(os.path.join(out_dir, f"{base_name}_animations.json"))
            elif fmt == "mmd":
                analyzer.export_to_mmd(os.path.join(out_dir, f"{base_name}.vmd"))
    
    # إضافة الدوال إلى الكلاس
    MefModelIGI2.extract_animations = extract_animations
    MefModelIGI2.export_animations = export_animations
    
    print("✅ Animation support added to MefModelIGI2")


# ============================================================
# تنفيذ الإضافات
# ============================================================

# إنشاء ملفات الإضافات (اختياري)
def create_addon_files(output_dir: str = "."):
    """إنشاء ملفات الإضافات في المجلد المحدد"""
    create_blender_addon_script(os.path.join(output_dir, "blender_addon.py"))
    create_gui_launcher_script(os.path.join(output_dir, "mef_gui_launcher.py"))
    print(f"\\n📁 Addon files created in: {output_dir}")


# تفعيل دعم الرسوم المتحركة لـ IGI2
add_animation_support_to_igi2()


# ============================================================
# دالة اختبار سريعة للرسوم المتحركة
# ============================================================

def test_animation_extraction(filepath: str, output_dir: str = "animation_test"):
    """اختبار استخراج الرسوم المتحركة من ملف MEF"""
    
    print(f"\\n🎬 Testing animation extraction on: {filepath}")
    print("=" * 60)
    
    with open(filepath, "rb") as f:
        data = f.read()
    
    buffer = Buffer(data)
    model = MefModelIGI2(buffer, export_mode="multi")
    
    # استخراج الرسوم المتحركة
    animations = model.extract_animations()
    
    print(f"\\n📊 Found {len(animations)} animations:")
    for anim in animations:
        print(f"   - {anim.name}: {anim.duration:.2f}s, {anim.frame_count} frames, {len(anim.bone_tracks)} bone tracks")
    
    # تصدير الرسوم المتحركة
    base_name = Path(filepath).stem
    out_path = os.path.join(output_dir, base_name)
    os.makedirs(out_path, exist_ok=True)
    
    model.export_animations(out_path, base_name, ["json", "mmd"])
    
    print(f"\\n✅ Animation export complete! Output: {out_path}")
    return animations


# ============================================================
# تشغيل الواجهة الرسومية
# ============================================================

def launch_gui():
    """تشغيل واجهة PyQt5"""
    try:
        from PyQt5.QtWidgets import QApplication
        from mef_gui import MEFConverterGUI
        
        app = QApplication(sys.argv)
        app.setStyle("Fusion")
        
        window = MEFConverterGUI()
        window.show()
        
        sys.exit(app.exec_())
    except ImportError as e:
        print(f"Error: {e}")
        print("\nPlease install required packages:")
        print("  pip install PyQt5 numpy pillow pygltflib")
        sys.exit(1)
    except Exception as e:
        print(f"Error launching GUI: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # إذا كان هناك وسيط --gui أو -g، شغل الواجهة
    if len(sys.argv) > 1 and sys.argv[1] in ['--gui', '-g']:
        launch_gui()
    else:
        main()    