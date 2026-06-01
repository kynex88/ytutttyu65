#!/usr/bin/env python3
# ============================================================
# mef_gui.py - واجهة مستخدم رسومية (PyQt5) لـ MEF Converter
# النسخة المحسنة - مع دعم Blender و Log Filtering المتقدم
# ============================================================

import sys
import os
import threading
import subprocess
from pathlib import Path
from PyQt5 import QtCore
from datetime import datetime

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QProgressBar, QTextEdit,
    QTreeWidget, QTreeWidgetItem, QTabWidget, QGroupBox,
    QCheckBox, QComboBox, QSpinBox, QDoubleSpinBox, QSplitter,
    QMessageBox, QStatusBar, QToolBar, QAction, QListWidget,
    QListWidgetItem, QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame, QScrollArea, QGridLayout, QSplitter, QLineEdit, QMenu
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QSettings, QPropertyAnimation, QEasingCurve, QSize
from PyQt5.QtGui import QFont, QIcon, QColor, QTextCursor, QPalette, QLinearGradient, QBrush, QPixmap

# ============================================================
# استيراد السكربت الرئيسي
# ============================================================

try:
    from import_mef_standalone_with_x_w import (
        MefModelIGI2, MefModelIGI1, StudioHeader,
        SMDExporter, OBJExporter, Buffer,
        detect_file_type, detect_mef_version,
        set_global_debug_params, MefDebugParams,
        convert_smd_to_formats, convert_obj_to_formats,
        ParallelProcessor, MefCache, AnimationExporter,
        AdvancedAnimationAnalyzer
    )
    IMPORT_SUCCESS = True
except ImportError as e:
    print(f"Warning: Could not import main script: {e}")
    IMPORT_SUCCESS = False

# ============================================================
# خصائص التطبيق
# ============================================================

APP_NAME = "MEF Model Converter"
APP_VERSION = "2.1.0"
APP_DevEngineered_By = "Tavrixender"
APP_COPYRIGHT = "© 2024 Tavrixender"

# مسار Blender (لـ Windows)
BLENDER_PATH = r"C:\Program Files\Blender Foundation\Blender 2.70\blender.exe"
ALTERNATIVE_BLENDER_PATHS = [
    r"C:\Program Files\Blender Foundation\Blender\blender.exe",
    r"C:\Program Files\Blender\blender.exe",
    r"C:\Program Files (x86)\Blender\blender.exe",
]

# ============================================================
# الألوان المخصصة (محسنة مع إضافة missing colors)
# ============================================================

COLORS = {
    # الأحمر القاتم (Dark Red / Crimson)
    "dark_red": "#8B0000",
    "crimson": "#DC143C",
    "blood_red": "#660000",
    "dark_burgundy": "#4A0000",
    
    # الأسود الغامق (Deep Black)
    "pure_black": "#000000",
    "dark_black": "#0a0a0a",
    "charcoal": "#1a1a1a",
    "dark_gray": "#2a2a2a",
    
    # الأصفر المشع (Radiant Yellow)
    "radiant_yellow": "#FFD700",
    "bright_yellow": "#FFFF00",
    "amber": "#FFBF00",
    "gold": "#FFD700",
    
    # الأزرق المشع (Electric Blue)
    "electric_blue": "#00BFFF",
    "neon_blue": "#1E90FF",
    "cyan_blue": "#00FFFF",
    "royal_blue": "#4169E1",
    
    # ألوان إضافية للتباين
    "white": "#FFFFFF",
    "light_gray": "#CCCCCC",
    "medium_gray": "#888888",
    
    # ========== الألوان المضافة ==========
    "warning_color": "#FFAA00",    # اللون الأصفر للتحذيرات
    "success_color": "#00FF88",    # اللون الأخضر للنجاح
    "error_color": "#FF4444",      # اللون الأحمر للأخطاء
    "info_color": "#44AAFF",       # اللون الأزرق للمعلومات
}

# ============================================================
# خيط المعالجة الخلفية
# ============================================================

class ConversionThread(QThread):
    """خيط منفصل لمعالجة الملفات"""
    
    progress_updated = pyqtSignal(int, str)
    log_message = pyqtSignal(str, str)
    finished = pyqtSignal(bool, dict)
    file_done = pyqtSignal(str, bool, str)
    
    def __init__(self, input_paths: list, output_dir: str, options: dict):
        super().__init__()
        self.input_paths = input_paths
        self.output_dir = output_dir
        self.options = options
        self.is_cancelled = False
        self.current_file = ""
    
    def run(self):
        results = {
            "total": len(self.input_paths),
            "successful": 0,
            "failed": 0,
            "details": []
        }
        
        for i, filepath in enumerate(self.input_paths):
            if self.is_cancelled:
                self.log_message.emit("❌ Process cancelled by user!", "danger")
                break
            
            self.current_file = Path(filepath).name
            progress = int((i / len(self.input_paths)) * 100)
            self.progress_updated.emit(progress, f"Processing: {self.current_file}")
            
            try:
                success, error_msg, output_paths = self.process_single_file(filepath)
                
                if success:
                    results["successful"] += 1
                    self.file_done.emit(self.current_file, True, "")
                    self.log_message.emit(f"✅ Success: {self.current_file}", "success")
                    
                    # حفظ مسار الإخراج لفتحه في Blender لاحقاً
                    if output_paths and self.options.get("open_in_blender", False):
                        self.options["last_output"] = output_paths
                else:
                    results["failed"] += 1
                    self.file_done.emit(self.current_file, False, error_msg)
                    self.log_message.emit(f"❌ Failed: {self.current_file} - {error_msg}", "danger")
                
                results["details"].append({
                    "file": str(filepath),
                    "success": success,
                    "error": error_msg if not success else "",
                    "output": output_paths if success else None
                })
                
            except Exception as e:
                results["failed"] += 1
                error_msg = str(e)
                self.file_done.emit(self.current_file, False, error_msg)
                self.log_message.emit(f"❌ Error: {self.current_file} - {error_msg}", "danger")
                results["details"].append({
                    "file": str(filepath),
                    "success": False,
                    "error": error_msg,
                    "output": None
                })
        
        self.progress_updated.emit(100, "Complete!")
        self.finished.emit(results["successful"] > 0, results)
    
    def process_single_file(self, filepath: str):
        if not IMPORT_SUCCESS:
            return False, "Main script not available", []
        
        output_paths = []
        
        try:
            with open(filepath, "rb") as f:
                data = f.read()
            
            buffer = Buffer(data)
            file_type = detect_file_type(buffer, filepath)
            
            if self.options.get("force_version") != "auto":
                version = self.options["force_version"]
            else:
                if file_type == "MEF":
                    version = detect_mef_version(buffer)
                elif file_type == "MDL":
                    version = "MDL"
                elif file_type == "SMD":
                    version = "SMD"
                elif file_type == "OBJ":
                    version = "OBJ"
                else:
                    version = "IGI2"
            
            base_name = Path(filepath).stem
            output_subdir = os.path.join(self.output_dir, base_name)
            os.makedirs(output_subdir, exist_ok=True)
            
            debug_params = MefDebugParams(
                v_scale=self.options.get("scale", 0.01),
                swizzle_mode="XZY"
            )
            set_global_debug_params(debug_params)
            
            formats = self.options.get("formats", ["obj"])
            
            if version == "IGI2":
                model = MefModelIGI2(buffer, export_mode=self.options.get("mode", "multi"))
                model.export_all(output_subdir, formats, self.options.get("lightmap_format", "png"))
            elif version == "IGI1":
                model = MefModelIGI1(buffer, export_mode=self.options.get("mode", "multi"))
                model.export_all(output_subdir, formats, self.options.get("lightmap_format", "png"))
            elif version == "MDL":
                model = StudioHeader(buffer)
                model.export_all(output_subdir, formats)
            elif version == "SMD":
                convert_smd_to_formats(filepath, output_subdir, formats)
            elif version == "OBJ":
                convert_obj_to_formats(filepath, output_subdir, formats)
            else:
                return False, f"Unsupported file type: {file_type}", []
            
            # ========== جمع مسارات ملفات الإخراج بعد التصدير ==========
            output_paths = []
            
            # البحث عن ملفات OBJ
            obj_files = list(Path(output_subdir).glob("*.obj"))
            output_paths.extend([str(f) for f in obj_files])
            
            # البحث عن ملفات glTF
            gltf_files = list(Path(output_subdir).glob("*.gltf"))
            output_paths.extend([str(f) for f in gltf_files])
            
            # البحث عن ملفات DAE
            dae_files = list(Path(output_subdir).glob("*.dae"))
            output_paths.extend([str(f) for f in dae_files])
            
            # البحث عن ملفات JSON
            json_files = list(Path(output_subdir).glob("*.json"))
            output_paths.extend([str(f) for f in json_files])
            
            # البحث عن ملفات TXT
            txt_files = list(Path(output_subdir).glob("*.txt"))
            output_paths.extend([str(f) for f in txt_files])
            
            # البحث عن ملفات DirectX
            dx_files = list(Path(output_subdir).glob("*.x"))
            output_paths.extend([str(f) for f in dx_files])
            
            self.log_message.emit(f"📁 Found {len(output_paths)} output files in {output_subdir}", "info")
            
            return True, "", output_paths
            
        except Exception as e:
            return False, str(e), []
            
    def cancel(self):
        self.is_cancelled = True


# ============================================================
# النافذة الرئيسية - النسخة المحسنة
# ============================================================

class MEFConverterGUI(QMainWindow):
    """النافذة الرئيسية للتطبيق - نسخة محسنة مع دعم Blender"""
    
    def __init__(self):
        super().__init__()
        self.input_files = []
        self.output_dir = ""
        self.conversion_thread = None
        self.settings = QSettings("Tavrixender", "MEFConverter")
        
        self.init_ui()
        self.load_settings()
        self.setup_shortcuts()
        self.setup_animations()
        self.check_blender_installation()
    
    def check_blender_installation(self):
        """التحقق من وجود Blender 2.70"""
        blender_found = False
        blender_path = None
        
        # التحقق من المسار الافتراضي
        if os.path.exists(BLENDER_PATH):
            blender_found = True
            blender_path = BLENDER_PATH
        else:
            # التحقق من المسارات البديلة
            for alt_path in ALTERNATIVE_BLENDER_PATHS:
                if os.path.exists(alt_path):
                    blender_found = True
                    blender_path = alt_path
                    break
        
        if blender_found:
            self.blender_path = blender_path
            self.log_message(f"🎬 Blender found at: {blender_path}", "success")
            self.open_in_blender_action.setEnabled(True)
        else:
            self.blender_path = None
            self.log_message(f"⚠️ Blender 2.70 not found. 'Open in Blender' feature disabled.", "warning")
            self.open_in_blender_action.setEnabled(False)
    
    def init_ui(self):
        """تهيئة واجهة المستخدم"""
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION} - Professional Edition")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1200, 700)
        
        # تعيين أيقونة التطبيق
        self.setWindowIcon(self.create_window_icon())
        
        # تعيين لون الخلفية
        self.setStyleSheet(self.get_professional_stylesheet())
        
        # القائمة الرئيسية
        self.create_menu_bar()
        
        # شريط الأدوات
        self.create_tool_bar()
        
        # القطعة المركزية
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # التخطيط الرئيسي
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # استخدام QSplitter لتقسيم الواجهة
        main_splitter = QSplitter(Qt.Vertical)
        
        # الجزء العلوي (تبويبات)
        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.North)
        tabs.setDocumentMode(True)
        tabs.setElideMode(Qt.ElideRight)
        
        # تبويب الإدخال
        input_tab = self.create_input_tab()
        tabs.addTab(input_tab, "📁 INPUT")
        
        # تبويب الإعدادات
        settings_tab = self.create_settings_tab()
        tabs.addTab(settings_tab, "⚙️ SETTINGS")
        
        # تبويب التقدم
        progress_tab = self.create_progress_tab()
        tabs.addTab(progress_tab, "📊 PROGRESS")
        
        # تبويب المخرجات التفاعلي
        outputs_tab = self.create_outputs_tab()
        tabs.addTab(outputs_tab, "📦 OUTPUTS")
        
        # تبويب السجل المتقدم
        log_tab = self.create_advanced_log_tab()
        tabs.addTab(log_tab, "📝 LOG")
        
        # تبويب المعلومات
        info_tab = self.create_info_tab()
        tabs.addTab(info_tab, "ℹ️ INFO")
        
        main_splitter.addWidget(tabs)
        
        # شريط الحالة (Status Bar)
        self.create_status_bar()
        
        main_splitter.addWidget(self.status_bar_widget)
        
        main_splitter.setSizes([700, 80])
        
        main_layout.addWidget(main_splitter)
    
    def create_outputs_tab(self):
        """إنشاء تبويب المخرجات التفاعلي"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)
        
        # عنوان وشريط تحكم
        header_layout = QHBoxLayout()
        
        title_label = QLabel("📦 EXPORTED OUTPUTS")
        title_label.setStyleSheet(f"font-weight: bold; font-size: 14px; color: {COLORS['electric_blue']};")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # زر تصدير القائمة
        export_list_btn = QPushButton("💾 Export List")
        export_list_btn.clicked.connect(self.export_outputs_list)
        header_layout.addWidget(export_list_btn)
        
        # زر مسح القائمة
        clear_outputs_btn = QPushButton("🗑️ Clear")
        clear_outputs_btn.setObjectName("danger")
        clear_outputs_btn.clicked.connect(self.clear_outputs_list)
        header_layout.addWidget(clear_outputs_btn)
        
        layout.addLayout(header_layout)
        
        # شجرة عرض المخرجات
        self.outputs_tree = QTreeWidget()
        self.outputs_tree.setHeaderLabels(["📄 File", "🎨 Format", "📁 Path", "✅ Status"])
        self.outputs_tree.setAlternatingRowColors(True)
        self.outputs_tree.setIndentation(0)
        self.outputs_tree.setColumnWidth(0, 200)
        self.outputs_tree.setColumnWidth(1, 100)
        self.outputs_tree.setColumnWidth(2, 450)
        self.outputs_tree.setSelectionMode(QTreeWidget.ExtendedSelection)
        
        # إضافة قائمة السياق (Context Menu)
        self.outputs_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.outputs_tree.customContextMenuRequested.connect(self.show_outputs_context_menu)
        
        layout.addWidget(self.outputs_tree)
        
        # إحصائيات المخرجات
        stats_frame = QFrame()
        stats_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['charcoal']};
                border-radius: 8px;
                padding: 8px;
            }}
        """)
        stats_layout = QHBoxLayout(stats_frame)
        
        self.outputs_total_label = QLabel("📊 Total: 0 files")
        self.outputs_total_label.setStyleSheet(f"font-weight: bold; color: {COLORS['light_gray']};")
        stats_layout.addWidget(self.outputs_total_label)
        
        stats_layout.addStretch()
        
        self.outputs_models_label = QLabel("🎨 Models: 0")
        self.outputs_models_label.setStyleSheet(f"color: {COLORS['success_color']};")
        stats_layout.addWidget(self.outputs_models_label)
        
        self.outputs_textures_label = QLabel("🖼️ Textures: 0")
        self.outputs_textures_label.setStyleSheet(f"color: {COLORS['info_color']};")
        stats_layout.addWidget(self.outputs_textures_label)
        
        self.outputs_data_label = QLabel("📄 Data: 0")
        self.outputs_data_label.setStyleSheet(f"color: {COLORS['warning_color']};")
        stats_layout.addWidget(self.outputs_data_label)
        
        layout.addWidget(stats_frame)
        
        return widget
    
    def show_outputs_context_menu(self, position):
        """عرض قائمة السياق عند النقر بزر الفأرة الأيمن على المخرجات"""
        item = self.outputs_tree.itemAt(position)
        if not item:
            return
        
        menu = QMenu()
        
        # الحصول على المسار الكامل للملف
        file_path = item.text(2) if item.text(2) else item.data(0, Qt.UserRole)
        if not file_path:
            file_path = item.toolTip(2)
        
        format_name = item.text(1).lower()
        
        # إجراءات القائمة
        open_in_blender_action = QAction("🎬 Open in Blender", self)
        open_in_blender_action.triggered.connect(lambda: self.open_single_file_in_blender(file_path))
        menu.addAction(open_in_blender_action)
        
        menu.addSeparator()
        
        open_folder_action = QAction("📂 Open Containing Folder", self)
        open_folder_action.triggered.connect(lambda: self.open_containing_folder(file_path))
        menu.addAction(open_folder_action)
        
        copy_path_action = QAction("📋 Copy Full Path", self)
        copy_path_action.triggered.connect(lambda: self.copy_to_clipboard(file_path))
        menu.addAction(copy_path_action)
        
        menu.addSeparator()
        
        # فتح الملف بالنظام الافتراضي
        open_default_action = QAction("🖥️ Open with Default App", self)
        open_default_action.triggered.connect(lambda: self.open_with_default_app(file_path))
        menu.addAction(open_default_action)
        
        menu.exec_(self.outputs_tree.viewport().mapToGlobal(position))
    
    def add_output_files(self, source_file: str, output_files: list):
        """إضافة ملفات المخرجات إلى الشجرة بشكل منظم"""
        source_name = os.path.basename(source_file)
        
        # إنشاء العنصر الرئيسي للملف المصدر
        source_item = QTreeWidgetItem([source_name, "", "", "✅ Converted"])
        source_item.setForeground(0, QColor(COLORS['radiant_yellow']))
        source_item.setForeground(3, QColor(COLORS['success_color']))
        source_item.setExpanded(True)
        
        # إضافة المخرجات كأبناء
        for file_path in output_files:
            file_name = os.path.basename(file_path)
            ext = os.path.splitext(file_name)[1].lower().replace('.', '').upper()
            
            # تحديد أيقونة ونوع الملف
            if ext in ['OBJ', 'GLTF', 'DAE', 'X']:
                file_type = "🎨 Model"
                format_display = ext
            elif ext in ['PNG', 'TGA', 'DDS', 'JPG', 'JPEG', 'BMP']:
                file_type = "🖼️ Texture"
                format_display = ext
            elif ext in ['JSON', 'XML']:
                file_type = "📄 Data"
                format_display = ext
            elif ext in ['TXT', 'CSV', 'MD']:
                file_type = "📝 Text"
                format_display = ext
            else:
                file_type = "📦 Other"
                format_display = ext or "FILE"
            
            # إنشاء عنصر المخرجات
            child_item = QTreeWidgetItem([file_name, format_display, file_path, file_type])
            child_item.setToolTip(2, file_path)
            child_item.setData(0, Qt.UserRole, file_path)
            
            # تلوين حسب النوع
            if ext == 'OBJ':
                child_item.setForeground(1, QColor(COLORS['success_color']))
            elif ext == 'GLTF':
                child_item.setForeground(1, QColor(COLORS['electric_blue']))
            elif ext == 'PNG':
                child_item.setForeground(1, QColor(COLORS['radiant_yellow']))
            
            source_item.addChild(child_item)
        
        # إضافة العنصر الرئيسي إلى الشجرة
        self.outputs_tree.addTopLevelItem(source_item)
        
        # تحديث الإحصائيات
        self.update_outputs_statistics()
        
        # تمرير الشجرة إلى العنصر المضاف
        self.outputs_tree.scrollToItem(source_item)
    
    def update_outputs_statistics(self):
        """تحديث إحصائيات المخرجات"""
        total_files = 0
        models_count = 0
        textures_count = 0
        data_count = 0
        
        for i in range(self.outputs_tree.topLevelItemCount()):
            source_item = self.outputs_tree.topLevelItem(i)
            for j in range(source_item.childCount()):
                child = source_item.child(j)
                total_files += 1
                file_type = child.text(3)
                if "Model" in file_type:
                    models_count += 1
                elif "Texture" in file_type:
                    textures_count += 1
                elif "Data" in file_type or "Text" in file_type:
                    data_count += 1
        
        self.outputs_total_label.setText(f"📊 Total: {total_files} files")
        self.outputs_models_label.setText(f"🎨 Models: {models_count}")
        self.outputs_textures_label.setText(f"🖼️ Textures: {textures_count}")
        self.outputs_data_label.setText(f"📄 Data: {data_count}")
    
    def clear_outputs_list(self):
        """مسح قائمة المخرجات بالكامل"""
        reply = QMessageBox.question(self, "Clear Outputs", 
            "Are you sure you want to clear all exported outputs list?",
            QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.outputs_tree.clear()
            self.update_outputs_statistics()
            self.log_message("🗑️ Outputs list cleared.", "info")
    
    def export_outputs_list(self):
        """تصدير قائمة المخرجات إلى ملف"""
        filepath, _ = QFileDialog.getSaveFileName(self, "Export Outputs List", "", 
            "CSV Files (*.csv);;Text Files (*.txt);;JSON Files (*.json);;All Files (*.*)")
        if not filepath:
            return
        
        try:
            ext = os.path.splitext(filepath)[1].lower()
            
            if ext == '.csv':
                import csv
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Source File", "Output File", "Format", "Type", "Full Path"])
                    for i in range(self.outputs_tree.topLevelItemCount()):
                        source_item = self.outputs_tree.topLevelItem(i)
                        source_name = source_item.text(0)
                        for j in range(source_item.childCount()):
                            child = source_item.child(j)
                            writer.writerow([source_name, child.text(0), child.text(1), child.text(3), child.text(2)])
            
            elif ext == '.json':
                import json
                data = []
                for i in range(self.outputs_tree.topLevelItemCount()):
                    source_item = self.outputs_tree.topLevelItem(i)
                    source_data = {
                        "source_file": source_item.text(0),
                        "outputs": []
                    }
                    for j in range(source_item.childCount()):
                        child = source_item.child(j)
                        source_data["outputs"].append({
                            "file_name": child.text(0),
                            "format": child.text(1),
                            "path": child.text(2),
                            "type": child.text(3)
                        })
                    data.append(source_data)
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            
            else:  # txt
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write("=" * 80 + "\n")
                    f.write("MEF CONVERTER - EXPORTED OUTPUTS LIST\n")
                    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 80 + "\n\n")
                    for i in range(self.outputs_tree.topLevelItemCount()):
                        source_item = self.outputs_tree.topLevelItem(i)
                        f.write(f"[SOURCE] {source_item.text(0)}\n")
                        f.write("-" * 60 + "\n")
                        for j in range(source_item.childCount()):
                            child = source_item.child(j)
                            f.write(f"  {child.text(0)} ({child.text(1)}) - {child.text(2)}\n")
                        f.write("\n")
            
            self.log_message(f"💾 Outputs list exported to: {filepath}", "success")
            QMessageBox.information(self, "Export Complete", f"Outputs list exported to:\n{filepath}")
            
        except Exception as e:
            self.log_message(f"❌ Error exporting outputs list: {e}", "danger")
            QMessageBox.warning(self, "Export Error", f"Failed to export: {e}")
    
    def open_single_file_in_blender(self, file_path: str):
        """فتح ملف واحد في Blender"""
        import tempfile
        import ctypes
        from ctypes import wintypes
        
        self.log_message(f"🔍 Attempting to open in Blender: {file_path}", "info")
        
        if not os.path.exists(file_path):
            self.log_message(f"❌ File not found: {file_path}", "danger")
            QMessageBox.warning(self, "File Not Found", f"The file does not exist:\n{file_path}")
            return
        
        if not self.blender_path:
            self.log_message("⚠️ Blender not found. Please set Blender path.", "warning")
            reply = QMessageBox.question(self, "Blender Not Found",
                "Blender 2.70 was not found.\n\n"
                "Do you want to set the Blender path manually?",
                QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.set_blender_path()
            return
        
        # التحقق من صيغة الملف
        if not (file_path.endswith('.obj') or file_path.endswith('.gltf')):
            reply = QMessageBox.question(self, "Unsupported Format",
                f"'{os.path.basename(file_path)}' is not OBJ or glTF.\n\n"
                "Blender may not be able to open this file directly.\n"
                "Do you want to try anyway?",
                QMessageBox.Yes | QMessageBox.No)
            if reply != QMessageBox.Yes:
                return
        
        try:
            def get_short_path(long_path):
                try:
                    buffer = ctypes.create_unicode_buffer(260)
                    GetShortPathNameW = ctypes.windll.kernel32.GetShortPathNameW
                    GetShortPathNameW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
                    GetShortPathNameW.restype = wintypes.DWORD
                    result = GetShortPathNameW(long_path, buffer, 260)
                    if result > 0:
                        return buffer.value
                except:
                    pass
                return long_path
            
            short_path = get_short_path(file_path)
            self.log_message(f"📁 Short path: {short_path}", "info")
            
            # استخدام مسار قصير وتجنب المشاكل
            import_script = '''# MEF Converter - Open Single File
import bpy
import os
import sys

# إضافة مسار مؤقت للتصحيح
sys.path.append(os.path.dirname(__file__))

filepath = r"''' + short_path + '''"

print("=" * 50)
print("MEF Converter: Opening", os.path.basename(filepath))
print("Full path:", filepath)
print("=" * 50)

# محاولة استيراد الملف
try:
    if filepath.lower().endswith('.obj'):
        # محاولة استيراد OBJ مع خيارات إضافية
        bpy.ops.import_scene.obj(filepath=filepath, use_split_objects=False, use_split_groups=False)
        print("OBJ imported successfully!")
    elif filepath.lower().endswith('.gltf'):
        bpy.ops.import_scene.gltf(filepath=filepath)
        print("glTF imported successfully!")
    else:
        print("Unsupported file type: " + filepath)
        sys.exit(1)
except Exception as e:
    print("Import error:", str(e))
    import traceback
    traceback.print_exc()
    # محاولة بديلة: فتح Blender فقط بدون استيراد
    print("Will open Blender without importing")

# تحديث viewport إلى وضع المواد
try:
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.shading.type = 'MATERIAL'
                    break
            break
    print("Viewport updated to Material mode")
except Exception as e:
    print("Could not update viewport:", str(e))

print("=" * 50)
print("MEF Converter: Ready")
print("=" * 50)
'''
            
            # حفظ السكربت في ملف مؤقت
            temp_script = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='ascii', errors='replace')
            temp_script.write(import_script)
            temp_script.close()
            
            # تشغيل Blender مع السكربت
            process = subprocess.Popen([self.blender_path, "--python", temp_script.name], 
                                       stdout=subprocess.PIPE, 
                                       stderr=subprocess.PIPE,
                                       creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
            
            self.log_message(f"🎬 Opening in Blender: {os.path.basename(file_path)}", "success")
            
            # حذف الملف المؤقت بعد تأخير
            QTimer.singleShot(15000, lambda: self._cleanup_temp_script(temp_script.name))
            
        except Exception as e:
            self.log_message(f"❌ Failed to open in Blender: {e}", "danger")
            import traceback
            traceback.print_exc()
            QMessageBox.warning(self, "Error", f"Failed to open in Blender:\n{str(e)}")
            
    def open_containing_folder(self, file_path: str):
        """فتح المجلد الذي يحتوي على الملف"""
        folder_path = os.path.dirname(file_path)
        if os.path.exists(folder_path):
            if sys.platform == "win32":
                os.startfile(folder_path)
            else:
                os.system(f'open "{folder_path}"')
            self.log_message(f"📂 Opening folder: {folder_path}", "info")
        else:
            self.log_message(f"❌ Folder not found: {folder_path}", "danger")
    
    def copy_to_clipboard(self, text: str):
        """نسخ النص إلى الحافظة"""
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        self.log_message(f"📋 Copied to clipboard: {text}", "success")
    
    def open_with_default_app(self, file_path: str):
        """فتح الملف بالتطبيق الافتراضي للنظام"""
        if os.path.exists(file_path):
            if sys.platform == "win32":
                os.startfile(file_path)
            else:
                subprocess.Popen(['open', file_path])
            self.log_message(f"🖥️ Opening with default app: {os.path.basename(file_path)}", "info")
        else:
            self.log_message(f"❌ File not found: {file_path}", "danger")
            
    def create_status_bar(self):
        """إنشاء شريط الحالة بشكل صحيح"""
        self.status_bar_widget = QWidget()
        layout = QHBoxLayout(self.status_bar_widget)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # معلومات النظام
        sys_info = QLabel("💻 SYSTEM: ONLINE")
        sys_info.setStyleSheet(f"color: {COLORS['radiant_yellow']}; font-weight: bold;")
        layout.addWidget(sys_info)
        
        layout.addStretch()
        
        # معلومات الذاكرة المؤقتة
        cache_info = QLabel("💾 CACHE: ENABLED")
        cache_info.setStyleSheet(f"color: {COLORS['light_gray']};")
        layout.addWidget(cache_info)
        
        layout.addStretch()
        
        # معلومات المعالجة المتوازية
        parallel_info = QLabel("⚡ PARALLEL: ENABLED")
        parallel_info.setStyleSheet(f"color: {COLORS['light_gray']};")
        layout.addWidget(parallel_info)
        
        layout.addStretch()
        
        # شريط التقدم الصغير
        self.status_progress = QProgressBar()
        self.status_progress.setMaximumWidth(200)
        self.status_progress.setMaximumHeight(15)
        self.status_progress.setVisible(False)
        layout.addWidget(self.status_progress)
        
        # رسالة الحالة
        self.status_message = QLabel("Ready")
        self.status_message.setStyleSheet(f"color: {COLORS['success_color']}; font-weight: bold;")
        layout.addWidget(self.status_message)
        
        # شريط الحالة الرسمي لـ QMainWindow
        status_bar = self.statusBar()
        status_bar.setStyleSheet(f"""
            QStatusBar {{
                background-color: {COLORS['pure_black']};
                color: {COLORS['light_gray']};
                border-top: 1px solid {COLORS['dark_red']};
            }}
            QStatusBar::item {{
                border: none;
            }}
        """)
        status_bar.showMessage("Ready", 3000)
    
    def create_window_icon(self):
        """إنشاء أيقونة النافذة"""
        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor(COLORS['dark_red']))
        return QIcon(pixmap)
    
    def get_professional_stylesheet(self):
        """الحصول على أنماط CSS الاحترافية"""
        return f"""
            QMainWindow {{
                background-color: {COLORS['pure_black']};
            }}
            QWidget {{
                background-color: {COLORS['dark_black']};
                color: {COLORS['light_gray']};
                font-family: 'Segoe UI', 'Arial', 'Consolas', sans-serif;
                font-size: 12px;
            }}
            QPushButton {{
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {COLORS['electric_blue']}, stop:1 {COLORS['neon_blue']});
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 12px;
                color: {COLORS['pure_black']};
            }}
            QPushButton:hover {{
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {COLORS['cyan_blue']}, stop:1 {COLORS['electric_blue']});
                color: {COLORS['pure_black']};
            }}
            QPushButton:pressed {{
                background-color: {COLORS['dark_red']};
                color: {COLORS['radiant_yellow']};
            }}
            QPushButton:disabled {{
                background-color: {COLORS['charcoal']};
                color: {COLORS['medium_gray']};
            }}
            QPushButton#danger {{
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {COLORS['crimson']}, stop:1 {COLORS['dark_red']});
                color: {COLORS['white']};
            }}
            QPushButton#danger:hover {{
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {COLORS['dark_red']}, stop:1 {COLORS['blood_red']});
            }}
            QPushButton#success {{
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {COLORS['radiant_yellow']}, stop:1 {COLORS['gold']});
                color: {COLORS['pure_black']};
            }}
            QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit, QTextEdit {{
                background-color: {COLORS['charcoal']};
                border: 1px solid {COLORS['dark_red']};
                border-radius: 4px;
                padding: 6px;
                font-size: 12px;
                color: {COLORS['light_gray']};
            }}
            QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover, QLineEdit:hover {{
                border-color: {COLORS['electric_blue']};
            }}
            QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QLineEdit:focus {{
                border-color: {COLORS['radiant_yellow']};
                border-width: 2px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {COLORS['electric_blue']};
                margin-right: 5px;
            }}
            QListWidget, QTreeWidget, QTableWidget {{
                background-color: {COLORS['pure_black']};
                border: 1px solid {COLORS['dark_red']};
                border-radius: 6px;
                outline: none;
                alternate-background-color: {COLORS['dark_black']};
            }}
            QListWidget::item, QTreeWidget::item, QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {COLORS['charcoal']};
            }}
            QListWidget::item:selected, QTreeWidget::item:selected, QTableWidget::item:selected {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['dark_red']}, stop:1 {COLORS['crimson']});
                color: {COLORS['radiant_yellow']};
            }}
            QListWidget::item:hover, QTreeWidget::item:hover, QTableWidget::item:hover {{
                background-color: {COLORS['dark_red']};
            }}
            QGroupBox {{
                border: 2px solid {COLORS['dark_red']};
                border-radius: 8px;
                margin-top: 14px;
                padding-top: 10px;
                font-weight: bold;
                font-size: 13px;
                color: {COLORS['electric_blue']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px 0 8px;
                background-color: {COLORS['dark_black']};
            }}
            QCheckBox {{
                spacing: 10px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid {COLORS['dark_red']};
                background-color: {COLORS['charcoal']};
            }}
            QCheckBox::indicator:checked {{
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {COLORS['electric_blue']}, stop:1 {COLORS['neon_blue']});
                border-color: {COLORS['electric_blue']};
            }}
            QCheckBox::indicator:unchecked:hover {{
                border-color: {COLORS['radiant_yellow']};
            }}
            QTabWidget::pane {{
                border: 1px solid {COLORS['dark_red']};
                border-radius: 6px;
                background-color: {COLORS['dark_black']};
            }}
            QTabBar::tab {{
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {COLORS['charcoal']}, stop:1 {COLORS['dark_gray']});
                border: 1px solid {COLORS['dark_red']};
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 10px 20px;
                margin-right: 3px;
                font-weight: bold;
                font-size: 12px;
                color: {COLORS['light_gray']};
            }}
            QTabBar::tab:selected {{
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {COLORS['dark_red']}, stop:1 {COLORS['crimson']});
                border-bottom: 2px solid {COLORS['radiant_yellow']};
                color: {COLORS['radiant_yellow']};
            }}
            QTabBar::tab:hover {{
                background-color: {COLORS['dark_red']};
                color: {COLORS['white']};
            }}
            QProgressBar {{
                border: 1px solid {COLORS['dark_red']};
                border-radius: 6px;
                text-align: center;
                background-color: {COLORS['charcoal']};
                color: {COLORS['white']};
                font-weight: bold;
            }}
            QProgressBar::chunk {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['electric_blue']}, stop:1 {COLORS['neon_blue']});
                border-radius: 5px;
            }}
            QScrollBar:vertical {{
                background-color: {COLORS['charcoal']};
                width: 14px;
                border-radius: 7px;
            }}
            QScrollBar::handle:vertical {{
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {COLORS['dark_red']}, stop:1 {COLORS['crimson']});
                border-radius: 7px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {COLORS['electric_blue']};
            }}
            QMenuBar {{
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {COLORS['dark_black']}, stop:1 {COLORS['pure_black']});
                border-bottom: 1px solid {COLORS['dark_red']};
                color: {COLORS['light_gray']};
            }}
            QMenuBar::item {{
                padding: 6px 12px;
                background-color: transparent;
            }}
            QMenuBar::item:selected {{
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {COLORS['dark_red']}, stop:1 {COLORS['crimson']});
                color: {COLORS['radiant_yellow']};
            }}
            QMenu {{
                background-color: {COLORS['dark_black']};
                border: 1px solid {COLORS['dark_red']};
                border-radius: 6px;
            }}
            QMenu::item {{
                padding: 8px 25px;
                background-color: transparent;
            }}
            QMenu::item:selected {{
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {COLORS['dark_red']}, stop:1 {COLORS['crimson']});
                color: {COLORS['radiant_yellow']};
            }}
            QToolBar {{
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {COLORS['dark_black']}, stop:1 {COLORS['pure_black']});
                border-bottom: 1px solid {COLORS['dark_red']};
                spacing: 5px;
                padding: 4px;
            }}
            QHeaderView::section {{
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {COLORS['dark_red']}, stop:1 {COLORS['crimson']});
                padding: 8px;
                border: 1px solid {COLORS['pure_black']};
                font-weight: bold;
                color: {COLORS['radiant_yellow']};
            }}
            QLabel[level="title"] {{
                font-size: 18px;
                font-weight: bold;
                color: {COLORS['radiant_yellow']};
                padding: 10px;
            }}
            QLabel[level="subtitle"] {{
                font-size: 14px;
                font-weight: bold;
                color: {COLORS['electric_blue']};
                padding: 5px;
            }}
        """
    
    def create_menu_bar(self):
        """إنشاء شريط القوائم"""
        menubar = self.menuBar()
        
        # قائمة ملف
        file_menu = menubar.addMenu("&File")
        
        add_files_action = QAction("📁 &Add Files...", self)
        add_files_action.triggered.connect(self.add_files)
        add_files_action.setShortcut("Ctrl+A")
        file_menu.addAction(add_files_action)
        
        add_folder_action = QAction("📂 Add &Folder...", self)
        add_folder_action.triggered.connect(self.add_folder)
        add_folder_action.setShortcut("Ctrl+D")
        file_menu.addAction(add_folder_action)
        
        file_menu.addSeparator()
        
        clear_action = QAction("🗑️ &Clear List", self)
        clear_action.triggered.connect(self.clear_files)
        clear_action.setShortcut("Ctrl+L")
        file_menu.addAction(clear_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.triggered.connect(self.close)
        exit_action.setShortcut("Ctrl+Q")
        file_menu.addAction(exit_action)
        
        # قائمة تحويل
        convert_menu = menubar.addMenu("&Convert")
        
        start_action = QAction("🚀 &Start Conversion", self)
        start_action.triggered.connect(self.start_conversion)
        start_action.setShortcut("F5")
        convert_menu.addAction(start_action)
        
        stop_action = QAction("⏹️ &Stop", self)
        stop_action.triggered.connect(self.stop_conversion)
        stop_action.setShortcut("F6")
        convert_menu.addAction(stop_action)
        
        convert_menu.addSeparator()
        
        batch_action = QAction("📦 &Batch Convert Folder", self)
        batch_action.triggered.connect(self.batch_convert_folder)
        convert_menu.addAction(batch_action)
        
        # قائمة Blender
        blender_menu = menubar.addMenu("🎬 &Blender")
        
        self.open_in_blender_action = QAction("🚀 &Open Last Model in Blender", self)
        self.open_in_blender_action.triggered.connect(self.open_in_blender)
        self.open_in_blender_action.setShortcut("Ctrl+B")
        blender_menu.addAction(self.open_in_blender_action)
        
        blender_menu.addSeparator()
        
        set_blender_path_action = QAction("🔧 &Set Blender Path", self)
        set_blender_path_action.triggered.connect(self.set_blender_path)
        blender_menu.addAction(set_blender_path_action)
        
        # قائمة عرض
        view_menu = menubar.addMenu("&View")
        
        toggle_status_action = QAction("Status Bar", self)
        toggle_status_action.setCheckable(True)
        toggle_status_action.setChecked(True)
        toggle_status_action.triggered.connect(lambda: self.statusBar().setVisible(toggle_status_action.isChecked()))
        view_menu.addAction(toggle_status_action)
        
        # قائمة خيارات
        options_menu = menubar.addMenu("&Options")
        
        settings_action = QAction("⚙️ &Settings", self)
        settings_action.triggered.connect(self.show_settings_dialog)
        options_menu.addAction(settings_action)
        
        options_menu.addSeparator()
        
        clear_cache_action = QAction("🧹 &Clear Cache", self)
        clear_cache_action.triggered.connect(self.clear_cache)
        options_menu.addAction(clear_cache_action)
        
        # قائمة مساعدة
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("ℹ️ &About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        docs_action = QAction("📖 &Documentation", self)
        docs_action.triggered.connect(self.show_docs)
        help_menu.addAction(docs_action)
    
    def create_tool_bar(self):
        """إنشاء شريط الأدوات"""
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setIconSize(QtCore.QSize(24, 24))
        self.addToolBar(toolbar)
        
        add_files_btn = QAction("📁 Add Files", self)
        add_files_btn.triggered.connect(self.add_files)
        toolbar.addAction(add_files_btn)
        
        add_folder_btn = QAction("📂 Add Folder", self)
        add_folder_btn.triggered.connect(self.add_folder)
        toolbar.addAction(add_folder_btn)
        
        toolbar.addSeparator()
        
        clear_btn = QAction("🗑️ Clear", self)
        clear_btn.triggered.connect(self.clear_files)
        toolbar.addAction(clear_btn)
        
        toolbar.addSeparator()
        
        self.convert_btn = QAction("🚀 Start", self)
        self.convert_btn.triggered.connect(self.start_conversion)
        toolbar.addAction(self.convert_btn)
        
        self.stop_btn = QAction("⏹️ Stop", self)
        self.stop_btn.triggered.connect(self.stop_conversion)
        self.stop_btn.setEnabled(False)
        toolbar.addAction(self.stop_btn)
        
        toolbar.addSeparator()
        
        self.blender_btn = QAction("🎬 Open in Blender", self)
        self.blender_btn.triggered.connect(self.open_in_blender)
        toolbar.addAction(self.blender_btn)
        
        toolbar.addSeparator()
        
        spacer = QWidget()
        spacer.setSizePolicy(QWidget().sizePolicy().Expanding, QWidget().sizePolicy().Preferred)
        toolbar.addWidget(spacer)
        
        self.status_label = QLabel("● SYSTEM READY")
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['radiant_yellow']};
                font-weight: bold;
                font-size: 12px;
                padding: 5px 10px;
                background-color: {COLORS['dark_red']};
                border-radius: 10px;
            }}
        """)
        toolbar.addWidget(self.status_label)
    
    def create_input_tab(self):
        """إنشاء تبويب الإدخال المحسن"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)
        
        # منطقة السحب والإفلات المحسنة
        drop_area = QLabel()
        drop_area.setText("🎯\n\nDRAG & DROP FILES/FOLDERS HERE\n\nor click 'Add Files' button")
        drop_area.setAlignment(Qt.AlignCenter)
        drop_area.setMinimumHeight(140)
        drop_area.setStyleSheet(f"""
            QLabel {{
                border: 3px dashed {COLORS['dark_red']};
                border-radius: 15px;
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {COLORS['charcoal']}, stop:1 {COLORS['dark_black']});
                font-size: 14px;
                font-weight: bold;
                padding: 25px;
                color: {COLORS['light_gray']};
            }}
            QLabel:hover {{
                border-color: {COLORS['electric_blue']};
                background-color: {COLORS['dark_gray']};
            }}
        """)
        drop_area.setAcceptDrops(True)
        drop_area.dragEnterEvent = self.drag_enter_event
        drop_area.dropEvent = self.drop_event
        layout.addWidget(drop_area)
        
        # قائمة الملفات
        file_label = QLabel("📄 FILES TO CONVERT:")
        file_label.setStyleSheet(f"font-weight: bold; font-size: 12px; color: {COLORS['electric_blue']}; margin-top: 10px;")
        layout.addWidget(file_label)
        
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.file_list.setAlternatingRowColors(True)
        layout.addWidget(self.file_list)
        
        # أزرار التحكم في القائمة
        btn_layout = QHBoxLayout()
        
        remove_btn = QPushButton("🗑️ Remove Selected")
        remove_btn.setObjectName("danger")
        remove_btn.clicked.connect(self.remove_selected)
        btn_layout.addWidget(remove_btn)
        
        clear_btn = QPushButton("🧹 Clear All")
        clear_btn.clicked.connect(self.clear_files)
        btn_layout.addWidget(clear_btn)
        
        btn_layout.addStretch()
        
        self.file_count_label = QLabel("📊 0 files selected")
        self.file_count_label.setStyleSheet(f"color: {COLORS['radiant_yellow']}; font-weight: bold;")
        btn_layout.addWidget(self.file_count_label)
        
        layout.addLayout(btn_layout)
        
        # مجلد الإخراج
        output_group = QGroupBox("📁 OUTPUT DIRECTORY")
        output_layout = QHBoxLayout(output_group)
        
        self.output_label = QLabel("⚠️ No output directory selected")
        self.output_label.setStyleSheet(f"color: {COLORS['warning_color']}; font-weight: bold;")
        output_layout.addWidget(self.output_label, 1)
        
        browse_btn = QPushButton("📂 Browse...")
        browse_btn.clicked.connect(self.select_output_dir)
        output_layout.addWidget(browse_btn)
        
        open_output_btn = QPushButton("📁 Open Folder")
        open_output_btn.clicked.connect(self.open_output_folder)
        output_layout.addWidget(open_output_btn)
        
        layout.addWidget(output_group)
        
        # إحصائيات سريعة
        quick_stats = QFrame()
        quick_stats.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['charcoal']};
                border-radius: 8px;
                padding: 8px;
            }}
        """)
        stats_layout = QHBoxLayout(quick_stats)
        
        stats_layout.addWidget(QLabel("Supported Formats:"))
        stats_layout.addWidget(QLabel("MEF | MDL | SMD | OBJ"))
        stats_layout.addStretch()
        stats_layout.addWidget(QLabel("Output Formats:"))
        stats_layout.addWidget(QLabel("OBJ | glTF | DAE | JSON | TXT | DirectX"))
        
        layout.addWidget(quick_stats)
        
        return widget
    
    def create_settings_tab(self):
        """إنشاء تبويب الإعدادات المحسن"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f"QScrollArea {{ background-color: transparent; border: none; }}")
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(15)
        
        # مجموعة صيغ التصدير
        formats_group = QGroupBox("🎨 EXPORT FORMATS")
        formats_layout = QGridLayout(formats_group)
        formats_layout.setSpacing(10)
        
        self.format_obj = QCheckBox("📦 OBJ (Wavefront) - Universal 3D format")
        self.format_obj.setChecked(True)
        formats_layout.addWidget(self.format_obj, 0, 0)
        
        self.format_gltf = QCheckBox("🎮 glTF 2.0 - Modern web standard")
        self.format_gltf.setChecked(True)
        formats_layout.addWidget(self.format_gltf, 0, 1)
        
        self.format_dae = QCheckBox("📐 Collada DAE - Interchange format")
        self.format_dae.setChecked(False)
        formats_layout.addWidget(self.format_dae, 1, 0)
        
        self.format_json = QCheckBox("📄 JSON - Data export")
        self.format_json.setChecked(True)
        formats_layout.addWidget(self.format_json, 1, 1)
        
        self.format_txt = QCheckBox("📝 Text Info - Model statistics")
        self.format_txt.setChecked(True)
        formats_layout.addWidget(self.format_txt, 2, 0)
        
        self.format_directx = QCheckBox("🎮 DirectX (.X) - Full skeleton and animation support")
        self.format_directx.setChecked(False)
        formats_layout.addWidget(self.format_directx, 2, 1)
        
        scroll_layout.addWidget(formats_group)
        
        # مجموعة متقدمة
        advanced_group = QGroupBox("⚙️ ADVANCED SETTINGS")
        advanced_layout = QGridLayout(advanced_group)
        advanced_layout.setSpacing(10)
        
        advanced_layout.addWidget(QLabel("Model Type Detection:"), 0, 0)
        self.model_type = QComboBox()
        self.model_type.addItems(["🤖 Auto-detect", "🎮 IGI1", "🎮 IGI2", "🔫 Half-Life MDL", "📦 SMD", "📐 OBJ"])
        advanced_layout.addWidget(self.model_type, 0, 1)
        
        advanced_layout.addWidget(QLabel("Export Mode:"), 1, 0)
        self.export_mode = QComboBox()
        self.export_mode.addItems(["📄 Simple (Single File)", "📁 Multi (Separate Materials)"])
        advanced_layout.addWidget(self.export_mode, 1, 1)
        
        advanced_layout.addWidget(QLabel("Model Scale:"), 2, 0)
        self.scale_spin = QDoubleSpinBox()
        self.scale_spin.setRange(0.001, 100.0)
        self.scale_spin.setValue(0.01)
        self.scale_spin.setSingleStep(0.001)
        self.scale_spin.setDecimals(4)
        self.scale_spin.setSuffix(" units")
        advanced_layout.addWidget(self.scale_spin, 2, 1)
        
        advanced_layout.addWidget(QLabel("Lightmap Format:"), 3, 0)
        self.lightmap_format = QComboBox()
        self.lightmap_format.addItems(["🖼️ PNG (Recommended)", "🎨 TGA", "💾 DDS", "📦 Both"])
        advanced_layout.addWidget(self.lightmap_format, 3, 1)
        
        scroll_layout.addWidget(advanced_group)
        
        # مجموعة الميزات
        features_group = QGroupBox("✨ FEATURES")
        features_layout = QGridLayout(features_group)
        features_layout.setSpacing(10)
        
        self.atlas_check = QCheckBox("🖼️ Create Texture Atlas (merge textures)")
        self.atlas_check.setChecked(False)
        features_layout.addWidget(self.atlas_check, 0, 0, 1, 2)
        
        self.parallel_check = QCheckBox("⚡ Parallel Processing (faster on multi-core)")
        self.parallel_check.setChecked(True)
        features_layout.addWidget(self.parallel_check, 1, 0, 1, 2)
        
        self.cache_check = QCheckBox("💾 Enable Caching (reuse previous results)")
        self.cache_check.setChecked(True)
        features_layout.addWidget(self.cache_check, 2, 0, 1, 2)
        
        self.animations_check = QCheckBox("🎬 Extract Animations (from TXAN/MRPH)")
        self.animations_check.setChecked(True)
        features_layout.addWidget(self.animations_check, 3, 0, 1, 2)
        
        self.blender_check = QCheckBox("🎬 Open in Blender after conversion")
        self.blender_check.setChecked(False)
        features_layout.addWidget(self.blender_check, 4, 0, 1, 2)
        
        scroll_layout.addWidget(features_group)
        
        # مجموعة معاملات التصحيح
        debug_group = QGroupBox("🔧 DEBUG PARAMETERS (Advanced Users)")
        debug_layout = QGridLayout(debug_group)
        debug_layout.setSpacing(10)
        
        debug_layout.addWidget(QLabel("Swizzle Mode:"), 0, 0)
        self.swizzle_mode = QComboBox()
        self.swizzle_mode.addItems(["🔄 XZY (IGI->OpenGL)", "📐 XYZ", "🔄 YXZ", "🔄 ZXY", "🔄 YZX", "🔄 ZYX"])
        debug_layout.addWidget(self.swizzle_mode, 0, 1)
        
        debug_layout.addWidget(QLabel("Bone Mode:"), 1, 0)
        self.bone_mode = QComboBox()
        self.bone_mode.addItems(["🦴 REL (Relative to parent)", "🌍 ABS (Absolute)", "👑 ROOT (To root bone)"])
        debug_layout.addWidget(self.bone_mode, 1, 1)
        
        self.flip_x = QCheckBox("↔️ Flip X Axis")
        debug_layout.addWidget(self.flip_x, 2, 0)
        
        self.flip_y = QCheckBox("↕️ Flip Y Axis")
        debug_layout.addWidget(self.flip_y, 2, 1)
        
        self.flip_z = QCheckBox("🔄 Flip Z Axis")
        debug_layout.addWidget(self.flip_z, 3, 0)
        
        scroll_layout.addWidget(debug_group)
        
        scroll_layout.addStretch()
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        return widget
    
    def create_progress_tab(self):
        """إنشاء تبويب التقدم المحسن"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)
        
        # شريط التقدم الرئيسي
        progress_label = QLabel("📊 OVERALL PROGRESS")
        progress_label.setStyleSheet(f"font-weight: bold; color: {COLORS['electric_blue']};")
        layout.addWidget(progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p% - %v/%m files")
        layout.addWidget(self.progress_bar)
        
        # شريط تقدم ثانوي
        self.progress_bar2 = QProgressBar()
        self.progress_bar2.setValue(0)
        self.progress_bar2.setMaximum(0)
        self.progress_bar2.setVisible(False)
        self.progress_bar2.setFormat("Processing...")
        layout.addWidget(self.progress_bar2)
        
        # حالة الملفات
        file_status_label = QLabel("📋 FILE STATUS")
        file_status_label.setStyleSheet(f"font-weight: bold; color: {COLORS['electric_blue']}; margin-top: 10px;")
        layout.addWidget(file_status_label)
        
        self.file_status = QTreeWidget()
        self.file_status.setHeaderLabels(["📄 File Name", "✅ Status", "⚠️ Error Message"])
        self.file_status.setAlternatingRowColors(True)
        self.file_status.setColumnWidth(0, 350)
        self.file_status.setColumnWidth(1, 120)
        self.file_status.setIndentation(0)
        layout.addWidget(self.file_status)
        
        # إحصائيات محسنة
        stats_frame = QFrame()
        stats_frame.setStyleSheet(f"""
            QFrame {{
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {COLORS['charcoal']}, stop:1 {COLORS['dark_black']});
                border-radius: 10px;
                padding: 10px;
            }}
        """)
        stats_layout = QHBoxLayout(stats_frame)
        
        self.total_label = QLabel("📊 TOTAL: 0")
        self.total_label.setStyleSheet(f"font-weight: bold; color: {COLORS['light_gray']};")
        stats_layout.addWidget(self.total_label)
        
        self.success_label = QLabel("✅ SUCCESS: 0")
        self.success_label.setStyleSheet(f"font-weight: bold; color: {COLORS['success_color']};")
        stats_layout.addWidget(self.success_label)
        
        self.failed_label = QLabel("❌ FAILED: 0")
        self.failed_label.setStyleSheet(f"font-weight: bold; color: {COLORS['error_color']};")
        stats_layout.addWidget(self.failed_label)
        
        stats_layout.addStretch()
        
        self.time_label = QLabel("⏱️ TIME: --:--")
        self.time_label.setStyleSheet(f"font-weight: bold; color: {COLORS['electric_blue']};")
        stats_layout.addWidget(self.time_label)
        
        layout.addWidget(stats_frame)
        
        return widget
    
    def create_advanced_log_tab(self):
        """إنشاء تبويب السجل المتقدم مع خيارات الفلترة"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # شريط التحكم في السجل
        log_control_layout = QHBoxLayout()
        
        # أزرار السجل
        clear_log_btn = QPushButton("🗑️ Clear Log")
        clear_log_btn.clicked.connect(self.clear_log)
        log_control_layout.addWidget(clear_log_btn)
        
        copy_log_btn = QPushButton("📋 Copy Log")
        copy_log_btn.clicked.connect(self.copy_log)
        log_control_layout.addWidget(copy_log_btn)
        
        save_log_btn = QPushButton("💾 Save Log")
        save_log_btn.clicked.connect(self.save_log)
        log_control_layout.addWidget(save_log_btn)
        
        log_control_layout.addStretch()
        
        # فلتر السجل المتقدم
        filter_label = QLabel("🔍 Filter:")
        filter_label.setStyleSheet(f"color: {COLORS['light_gray']}; font-weight: bold;")
        log_control_layout.addWidget(filter_label)
        
        self.log_filter = QComboBox()
        self.log_filter.addItems(["📋 All", "✅ Success", "❌ Error", "⚠️ Warning", "ℹ️ Info", "🎬 Animation", "📦 Model"])
        self.log_filter.currentTextChanged.connect(self.filter_log)
        log_control_layout.addWidget(self.log_filter)
        
        # مربع بحث
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔎 Search in log...")
        self.search_input.textChanged.connect(self.search_log)
        self.search_input.setMaximumWidth(200)
        log_control_layout.addWidget(self.search_input)
        
        layout.addLayout(log_control_layout)
        
        # منطقة عرض السجل
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 10))
        self.log_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['pure_black']};
                color: {COLORS['light_gray']};
                border: 1px solid {COLORS['dark_red']};
                border-radius: 8px;
                font-family: 'Consolas', monospace;
            }}
        """)
        layout.addWidget(self.log_text)
        
        # رسائل ترحيب
        self.log_messages = []
        self.log_message(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "info")
        self.log_message(f"🔧 {APP_NAME} v{APP_VERSION} - Professional Edition", "primary")
        self.log_message(f"👤 DevEngineered_By: {APP_DevEngineered_By}", "info")
        self.log_message(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "info")
        self.log_message(f"✅ System ready. Waiting for input...", "success")
        
        return widget
    
    def create_info_tab(self):
        """إنشاء تبويب المعلومات المحسن"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)
        
        # شعار التطبيق
        title_label = QLabel("🎯 MEF MODEL CONVERTER")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 28px;
                font-weight: bold;
                color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {COLORS['radiant_yellow']}, stop:1 {COLORS['gold']});
                padding: 20px;
            }}
        """)
        layout.addWidget(title_label)
        
        subtitle_label = QLabel("Professional 3D Model Conversion Tool")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                color: {COLORS['electric_blue']};
                margin-bottom: 20px;
            }}
        """)
        layout.addWidget(subtitle_label)
        
        # فاصل
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet(f"background-color: {COLORS['dark_red']}; max-height: 2px;")
        layout.addWidget(line)
        
        # معلومات عن السكربت
        info_group = QGroupBox("📖 ABOUT")
        info_layout = QVBoxLayout(info_group)
        
        info_text = QLabel(
            f"<div style='line-height: 1.8;'>"
            f"<b>{APP_NAME}</b> is a powerful professional tool for converting 3D models from classic games.<br><br>"
            f"<b>🎮 SUPPORTED INPUT FORMATS:</b><br>"
            f"• <span style='color:{COLORS['radiant_yellow']}'>Project IGI 1</span> (MEF format)<br>"
            f"• <span style='color:{COLORS['radiant_yellow']}'>Project IGI 2</span> (MEF format)<br>"
            f"• <span style='color:{COLORS['radiant_yellow']}'>Half-Life / Counter-Strike 1.6</span> (MDL format)<br>"
            f"• <span style='color:{COLORS['radiant_yellow']}'>StudioMDL</span> (SMD format from Crowbar)<br>"
            f"• <span style='color:{COLORS['radiant_yellow']}'>Wavefront OBJ</span> (Standard 3D format)<br><br>"
            f"<b>📤 OUTPUT FORMATS:</b><br>"
            f"• OBJ (Wavefront) - Universal 3D format<br>"
            f"• glTF 2.0 - Modern web standard<br>"
            f"• Collada DAE - Interchange format<br>"
            f"• DirectX (.X) - Full skeleton support<br>"
            f"• JSON - Data export<br>"
            f"• TXT - Model statistics<br><br>"
            f"<b>✨ KEY FEATURES:</b><br>"
            f"• ✓ Full skeleton and animation support<br>"
            f"• ✓ Texture atlas generation<br>"
            f"• ✓ Parallel processing for speed<br>"
            f"• ✓ Batch conversion<br>"
            f"• ✓ Collision and shadow mesh extraction<br>"
            f"• ✓ Lightmap extraction<br>"
            f"• ✓ Morph target support<br>"
            f"• ✓ Direct import to Blender<br><br>"
            f"<b>👤 DevEngineered_By:</b> {APP_DevEngineered_By}<br>"
            f"<b>📅 VERSION:</b> {APP_VERSION}<br>"
            f"<b>⚖️ LICENSE:</b> MIT<br>"
            f"</div>"
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet(f"color: {COLORS['light_gray']}; font-size: 12px; padding: 10px;")
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_group)
        
        layout.addStretch()
        
        return widget
    
    # ========== دوال الأحداث ==========
    
    def drag_enter_event(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
    
    def drop_event(self, event):
        """معالجة السحب والإفلات المحسنة للملفات والمجلدات"""
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if os.path.isfile(path):
                self.add_single_file(path)
            elif os.path.isdir(path):
                self.add_folder_path(path)
        self.log_message(f"✓ Dragged and dropped items added", "success")
    
    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Model Files", "",
            "Model Files (*.mef *.MEF *.mdl *.MDL *.smd *.SMD *.obj *.OBJ);;All Files (*.*)"
        )
        for f in files:
            self.add_single_file(f)
    
    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.add_folder_path(folder)
    
    def add_folder_path(self, folder_path: str):
        """إضافة مجلد كامل مع دعم المجلدات الفرعية"""
        extensions = ('.mef', '.MEF', '.mdl', '.MDL', '.smd', '.SMD', '.obj', '.OBJ')
        count = 0
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(extensions):
                    self.add_single_file(os.path.join(root, file))
                    count += 1
        self.log_message(f"✓ Added {count} files from folder: {folder_path}", "success")
    
    def add_single_file(self, filepath: str):
        if filepath not in self.input_files:
            self.input_files.append(filepath)
            item = QListWidgetItem(os.path.basename(filepath))
            item.setToolTip(filepath)
            self.file_list.addItem(item)
            
            tree_item = QTreeWidgetItem([os.path.basename(filepath), "⏳ Pending", ""])
            self.file_status.addTopLevelItem(tree_item)
            
            self.file_count_label.setText(f"📊 {len(self.input_files)} files selected")
    
    def remove_selected(self):
        selected_indices = []
        for item in self.file_list.selectedItems():
            index = self.file_list.row(item)
            selected_indices.append(index)
        
        for index in sorted(selected_indices, reverse=True):
            self.file_list.takeItem(index)
            self.input_files.pop(index)
            self.file_status.takeTopLevelItem(index)
        
        self.file_count_label.setText(f"📊 {len(self.input_files)} files selected")
    
    def clear_files(self):
        self.file_list.clear()
        self.input_files.clear()
        self.file_status.clear()
        self.file_count_label.setText("📊 0 files selected")
        self.log_message("✓ File list cleared.", "info")
    
    def select_output_dir(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if directory:
            self.output_dir = directory
            self.output_label.setText(f"📁 {directory}")
            self.output_label.setStyleSheet(f"color: {COLORS['success_color']}; font-weight: bold;")
            self.log_message(f"✓ Output directory set to: {directory}", "success")
    
    def open_output_folder(self):
        if self.output_dir and os.path.exists(self.output_dir):
            os.startfile(self.output_dir) if sys.platform == "win32" else os.system(f'open "{self.output_dir}"')
        else:
            QMessageBox.warning(self, "No Output", "Please select an output directory first.")
    
    def start_conversion(self):
        if not self.input_files:
            QMessageBox.warning(self, "No Files", "Please add files to convert.")
            return
        
        if not self.output_dir:
            QMessageBox.warning(self, "No Output", "Please select an output directory.")
            return
        
        # جمع صيغ التصدير (محسن مع دعم DirectX)
        formats = []
        if self.format_obj.isChecked():
            formats.append("obj")
        if self.format_gltf.isChecked():
            formats.append("gltf")
        if self.format_dae.isChecked():
            formats.append("dae")
        if self.format_json.isChecked():
            formats.append("json")
        if self.format_txt.isChecked():
            formats.append("txt")
        if hasattr(self, 'format_directx') and self.format_directx.isChecked():
            formats.append("directx")
        
        if not formats:
            QMessageBox.warning(self, "No Format", "Please select at least one export format.")
            return
        
        swizzle_map = {
            "🔄 XZY (IGI->OpenGL)": "XZY",
            "📐 XYZ": "XYZ",
            "🔄 YXZ": "YXZ",
            "🔄 ZXY": "ZXY",
            "🔄 YZX": "YZX",
            "🔄 ZYX": "ZYX"
        }
        
        bone_mode_map = {
            "🦴 REL (Relative to parent)": "REL",
            "🌍 ABS (Absolute)": "ABS",
            "👑 ROOT (To root bone)": "ROOT"
        }
        
        debug_params = MefDebugParams(
            v_scale=self.scale_spin.value(),
            swizzle_mode=swizzle_map.get(self.swizzle_mode.currentText(), "XZY"),
            bone_mode=bone_mode_map.get(self.bone_mode.currentText(), "REL"),
            flip_x=self.flip_x.isChecked(),
            flip_y=self.flip_y.isChecked(),
            flip_z=self.flip_z.isChecked()
        )
        set_global_debug_params(debug_params)
        
        force_version_map = {
            "🤖 Auto-detect": "auto",
            "🎮 IGI1": "IGI1",
            "🎮 IGI2": "IGI2",
            "🔫 Half-Life MDL": "MDL",
            "📦 SMD": "SMD",
            "📐 OBJ": "OBJ"
        }
        
        options = {
            "mode": "multi" if self.export_mode.currentIndex() == 1 else "simple",
            "formats": formats,
            "force_version": force_version_map.get(self.model_type.currentText(), "auto"),
            "lightmap_format": self.lightmap_format.currentText().split()[0].lower(),
            "scale": self.scale_spin.value(),
            "atlas": self.atlas_check.isChecked(),
            "parallel": self.parallel_check.isChecked(),
            "cache": self.cache_check.isChecked(),
            "animations": self.animations_check.isChecked(),
            "open_in_blender": self.blender_check.isChecked()
        }
        
        self.convert_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.progress_bar2.setVisible(True)
        self.status_progress.setVisible(True)
        self.status_label.setText("● PROCESSING")
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['radiant_yellow']};
                font-weight: bold;
                font-size: 12px;
                padding: 5px 10px;
                background-color: {COLORS['dark_red']};
                border-radius: 10px;
            }}
        """)
        
        for i in range(self.file_status.topLevelItemCount()):
            item = self.file_status.topLevelItem(i)
            item.setText(1, "⏳ Pending")
            item.setText(2, "")
            item.setForeground(1, QColor(COLORS['light_gray']))
        
        self.log_message("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "info")
        self.log_message("🚀 STARTING CONVERSION PROCESS", "primary")
        self.log_message(f"📁 Input files: {len(self.input_files)}", "info")
        self.log_message(f"📂 Output directory: {self.output_dir}", "info")
        self.log_message(f"🎨 Export formats: {', '.join(formats)}", "info")
        self.log_message(f"🎬 Open in Blender after conversion: {self.blender_check.isChecked()}", "info")
        self.log_message("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "info")
        
        self.start_time = QTimer()
        self.last_output_paths = None
        
        self.conversion_thread = ConversionThread(self.input_files, self.output_dir, options)
        self.conversion_thread.progress_updated.connect(self.update_progress)
        self.conversion_thread.log_message.connect(self.log_message)
        self.conversion_thread.finished.connect(self.conversion_finished)
        self.conversion_thread.file_done.connect(self.update_file_status)
        self.conversion_thread.start()
    
    def stop_conversion(self):
        if self.conversion_thread and self.conversion_thread.isRunning():
            self.conversion_thread.cancel()
            self.log_message("⏹️ Stopping conversion...", "warning")
            self.status_label.setText("● STOPPING")
    
    def update_progress(self, value: int, text: str):
        self.progress_bar.setValue(value)
        self.statusBar().showMessage(text, 2000)
        self.progress_bar2.setValue(value)
        self.status_progress.setValue(value)
        self.status_message.setText(text)
    
    def log_message(self, message: str, level: str = "info"):
        """تسجيل رسالة مع دعم المستويات المختلفة"""
        colors = {
            "success": COLORS['success_color'],
            "danger": COLORS['error_color'],
            "error": COLORS['error_color'],
            "warning": COLORS['warning_color'],
            "info": COLORS['info_color'],
            "primary": COLORS['electric_blue'],
            "animation": COLORS['radiant_yellow'],
            "model": COLORS['neon_blue']
        }
        html_color = colors.get(level, COLORS['light_gray'])
        
        # أيقونة حسب المستوى
        icons = {
            "success": "✅",
            "danger": "❌",
            "error": "❌",
            "warning": "⚠️",
            "info": "ℹ️",
            "primary": "🔧",
            "animation": "🎬",
            "model": "📦"
        }
        icon = icons.get(level, "•")
        
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        formatted_msg = f'<span style="color:#666;">[{timestamp}]</span> <span style="color:{html_color}">{icon} {message}</span>'
        self.log_text.append(formatted_msg)
        self.log_text.moveCursor(QTextCursor.End)
        
        # تخزين الرسالة للفلترة
        self.log_messages.append({
            "timestamp": timestamp, 
            "message": message, 
            "level": level, 
            "html": formatted_msg,
            "searchable": message.lower()
        })
        
        # تحديث شريط الحالة للرسائل الهامة
        if level in ["danger", "error", "warning"]:
            self.statusBar().showMessage(message, 5000)
    
    def filter_log(self, filter_text: str):
        """فلترة رسائل السجل المتقدمة"""
        self.log_text.clear()
        
        # تحويل نص الفلتر إلى مستوى
        filter_map = {
            "📋 All": None,
            "✅ Success": "success",
            "❌ Error": "error",
            "⚠️ Warning": "warning",
            "ℹ️ Info": "info",
            "🎬 Animation": "animation",
            "📦 Model": "model"
        }
        target_level = filter_map.get(filter_text, None)
        
        for msg in self.log_messages:
            if target_level is None or msg["level"] == target_level:
                self.log_text.append(msg["html"])
        
        self.log_text.moveCursor(QTextCursor.End)
        self.log_message(f"🔍 Filter applied: {filter_text} ({len([m for m in self.log_messages if target_level is None or m['level'] == target_level])} messages)", "info")
    
    def search_log(self, search_text: str):
        """البحث في رسائل السجل"""
        if not search_text.strip():
            # إذا كان البحث فارغاً، أعد عرض الرسائل المفلترة
            self.filter_log(self.log_filter.currentText())
            return
        
        self.log_text.clear()
        search_lower = search_text.lower()
        count = 0
        
        for msg in self.log_messages:
            if search_lower in msg["searchable"]:
                # تمييز النص المبحوث عنه
                highlighted = msg["html"].replace(
                    search_text, 
                    f'<span style="background-color:{COLORS['radiant_yellow']}; color:{COLORS['pure_black']};">{search_text}</span>'
                )
                self.log_text.append(highlighted)
                count += 1
        
        self.log_text.moveCursor(QTextCursor.End)
        self.log_message(f"🔎 Search found {count} results for '{search_text}'", "info")
    
    def update_file_status(self, filename: str, success: bool, error_msg: str):
        for i in range(self.file_status.topLevelItemCount()):
            item = self.file_status.topLevelItem(i)
            if item.text(0) == filename:
                if success:
                    item.setText(1, "✅ SUCCESS")
                    item.setForeground(1, QColor(COLORS['success_color']))
                else:
                    item.setText(1, "❌ FAILED")
                    item.setText(2, error_msg[:150] if error_msg else "")
                    item.setForeground(1, QColor(COLORS['error_color']))
                break
    
    def conversion_finished(self, success: bool, results: dict):
        self.convert_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar2.setVisible(False)
        self.status_progress.setVisible(False)
        
        self.total_label.setText(f"📊 TOTAL: {results['total']}")
        self.success_label.setText(f"✅ SUCCESS: {results['successful']}")
        self.failed_label.setText(f"❌ FAILED: {results['failed']}")
        
        self.log_message("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "info")
        
        if success:
            self.log_message(f"✅ CONVERSION COMPLETED! {results['successful']}/{results['total']} files converted successfully.", "success")
            self.status_label.setText("● READY")
            self.status_label.setStyleSheet(f"""
                QLabel {{
                    color: {COLORS['success_color']};
                    font-weight: bold;
                    font-size: 12px;
                    padding: 5px 10px;
                    background-color: {COLORS['dark_red']};
                    border-radius: 10px;
                }}
            """)
            
            # ========== التعديل هنا ==========
            # حفظ آخر مخرجات للفتح في Blender
            self.last_output_paths = []
            for detail in results['details']:
                if detail.get('success', False):
                    output_files = detail.get('output', [])
                    if output_files:
                        self.last_output_paths.extend(output_files)
                        self.log_message(f"📁 Output files from {detail.get('file', 'unknown')}: {output_files}", "info")
            # ================================
            
            # إضافة المخرجات إلى تبويب OUTPUTS
            for detail in results['details']:
                if detail.get('success', False):
                    output_files = detail.get('output', [])
                    if output_files:
                        self.add_output_files(detail.get('file', 'unknown'), output_files)
                        
            # فتح في Blender تلقائياً إذا تم تفعيل الخيار
            if self.blender_check.isChecked() and self.last_output_paths:
                self.open_in_blender()
            
            QMessageBox.information(self, "Complete", 
                f"✅ Conversion completed successfully!\n\n"
                f"📊 Total files: {results['total']}\n"
                f"✅ Successful: {results['successful']}\n"
                f"❌ Failed: {results['failed']}\n\n"
                f"📂 Output directory: {self.output_dir}")
        else:
            self.log_message("⚠️ CONVERSION COMPLETED WITH ERRORS", "warning")
            self.status_label.setText("● WARNING")
            self.status_label.setStyleSheet(f"""
                QLabel {{
                    color: {COLORS['warning_color']};
                    font-weight: bold;
                    font-size: 12px;
                    padding: 5px 10px;
                    background-color: {COLORS['dark_red']};
                    border-radius: 10px;
                }}
            """)
            
            if results['failed'] > 0:
                reply = QMessageBox.question(self, "Errors Occurred",
                    f"⚠️ {results['failed']} files failed to convert.\n\n"
                    "Do you want to see the error log?",
                    QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.Yes:
                    self.show_error_log(results)
        
        self.log_message("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "info")
        
    def show_error_log(self, results: dict):
        error_window = QMainWindow(self)
        error_window.setWindowTitle("Error Log")
        error_window.setGeometry(200, 200, 900, 600)
        error_window.setStyleSheet(f"background-color: {COLORS['dark_black']};")
        
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setFont(QFont("Consolas", 10))
        text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['pure_black']};
                color: {COLORS['light_gray']};
                border: 1px solid {COLORS['dark_red']};
            }}
        """)
        
        for detail in results['details']:
            if not detail['success']:
                error = detail.get('error', 'Unknown error')
                text_edit.append(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                text_edit.append(f"📄 FILE: {detail['file']}")
                text_edit.append(f"❌ ERROR: {error}")
                text_edit.append(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                text_edit.append("")
        
        error_window.setCentralWidget(text_edit)
        error_window.show()
    
    def clear_log(self):
        self.log_text.clear()
        self.log_messages.clear()
        self.log_message("📝 Log cleared.", "info")
        self.log_message(f"🔧 {APP_NAME} v{APP_VERSION} - Professional Edition", "primary")
        self.log_message("✅ System ready.", "success")
    
    def copy_log(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.log_text.toPlainText())
        self.log_message("📋 Log copied to clipboard.", "success")
    
    def save_log(self):
        filepath, _ = QFileDialog.getSaveFileName(self, "Save Log", "", "Text Files (*.txt);;All Files (*.*)")
        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(self.log_text.toPlainText())
            self.log_message(f"💾 Log saved to {filepath}", "success")
    
    def batch_convert_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Convert")
        if folder:
            self.clear_files()
            self.add_folder_path(folder)
            
            output_folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
            if output_folder:
                self.output_dir = output_folder
                self.output_label.setText(f"📁 {output_folder}")
                self.start_conversion()
    
    def open_in_blender(self):
        """فتح آخر نموذج تم تصديره في Blender"""
        import tempfile
        
        # سطر تشخيصي
        self.log_message(f"🔍 Debug: last_output_paths = {self.last_output_paths}", "info")
        
        if not self.last_output_paths:
            QMessageBox.warning(self, "No Model", "No model has been converted yet. Please convert a model first.")
            return
        
        if not self.blender_path:
            self.log_message("⚠️ Blender not found. Please set Blender path in the Blender menu.", "warning")
            reply = QMessageBox.question(self, "Blender Not Found",
                "Blender 2.70 was not found.\n\n"
                "Do you want to set the Blender path manually?",
                QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.set_blender_path()
            return
        
        # البحث عن ملف OBJ أو glTF - نفضل ملف الـ render على الـ col
        model_file = None
        render_file = None
        col_file = None
        gltf_file = None
        
        for path in self.last_output_paths:
            if path.endswith('.obj'):
                if '_render' in path or 'render' in path.lower():
                    render_file = path
                elif '_col' in path or 'col' in path.lower():
                    col_file = path
            elif path.endswith('.gltf'):
                if '_render' in path or 'render' in path.lower():
                    gltf_file = path
        
        # اختيار أفضل ملف
        if render_file:
            model_file = render_file
            self.log_message(f"🎯 Found main render model: {os.path.basename(render_file)}", "success")
        elif gltf_file:
            model_file = gltf_file
            self.log_message(f"🎯 Found glTF model: {os.path.basename(gltf_file)}", "success")
        elif col_file:
            model_file = col_file
            self.log_message(f"⚠️ Using collision mesh: {os.path.basename(col_file)}", "warning")
            reply = QMessageBox.question(self, "Using Collision Mesh", 
                "Only collision mesh was found.\n\n"
                "Do you want to open it in Blender?",
                QMessageBox.Yes | QMessageBox.No)
            if reply != QMessageBox.Yes:
                return
        
        if not model_file:
            QMessageBox.warning(self, "No Valid Model", 
                "No OBJ or glTF file found.\n\nAvailable files:\n" + 
                "\n".join([os.path.basename(p) for p in self.last_output_paths[:5]]))
            return
        
        try:
            # الحصول على المسار القصير لتجنب المسافات
            import ctypes
            from ctypes import wintypes
            
            def get_short_path(long_path):
                """تحويل مسار طويل إلى مسار قصير (8.3)"""
                try:
                    buffer = ctypes.create_unicode_buffer(260)
                    GetShortPathNameW = ctypes.windll.kernel32.GetShortPathNameW
                    GetShortPathNameW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
                    GetShortPathNameW.restype = wintypes.DWORD
                    
                    result = GetShortPathNameW(long_path, buffer, 260)
                    if result > 0:
                        return buffer.value
                except:
                    pass
                return long_path
            
            short_model_path = get_short_path(model_file)
            self.log_message(f"📁 Short path: {short_model_path}", "info")
            
            # ========== استخدام Python 2.7 متوافق (بدون f-strings) ==========
            import_script = '''# MEF Converter Auto-Import Script (Python 2.7 compatible)
import bpy
import sys
import os

filepath = r"''' + short_model_path + '''"

print("=" * 50)
print("MEF Converter: Importing " + os.path.basename(filepath))
print("Full path: " + filepath)
print("=" * 50)

# محاولة استيراد الملف
try:
    if filepath.lower().endswith('.obj'):
        bpy.ops.import_scene.obj(filepath=filepath)
        print("OBJ imported successfully!")
    elif filepath.lower().endswith('.gltf'):
        bpy.ops.import_scene.gltf(filepath=filepath)
        print("glTF imported successfully!")
    else:
        print("Unsupported file type: " + filepath)
        
except Exception as e:
    print("Import error: " + str(e))
    import traceback
    traceback.print_exc()

# محاولة تحديث viewport
try:
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.shading.type = 'MATERIAL'
                    break
            break
    print("Viewport updated to Material mode")
except:
    pass

print("=" * 50)
print("MEF Converter: Ready")
print("=" * 50)
'''
            
            # حفظ السكربت (استخدام ترميز ascii بسيط)
            temp_script = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='ascii', errors='replace')
            temp_script.write(import_script)
            temp_script.close()
            
            # تشغيل Blender مع السكربت
            subprocess.Popen([self.blender_path, "--python", temp_script.name])
            self.log_message(f"🎬 Opening Blender with: {os.path.basename(model_file)}", "success")
            
            # حذف الملف المؤقت بعد تأخير
            QTimer.singleShot(10000, lambda: self._cleanup_temp_script(temp_script.name))
            
        except Exception as e:
            self.log_message(f"❌ Failed to open Blender: {e}", "danger")
            import traceback
            traceback.print_exc()
            QMessageBox.warning(self, "Error", f"Failed to open Blender: {e}")
            
    def _cleanup_temp_script(self, script_path: str):
        """حذف ملف السكربت المؤقت"""
        try:
            if os.path.exists(script_path):
                os.unlink(script_path)
                print(f"Cleaned up temp script: {script_path}")
        except Exception:
            pass
            
    def set_blender_path(self):
        """تعيين مسار Blender يدوياً"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Select Blender Executable", 
            r"C:\Users\T88M00\Downloads\blender-2.70-windows64\blender-2.70-windows64",
            "Executable Files (*.exe);;All Files (*.*)"
        )
        if filepath and os.path.exists(filepath):
            self.blender_path = filepath
            self.open_in_blender_action.setEnabled(True)
            self.blender_btn.setEnabled(True)
            self.log_message(f"🎬 Blender path set to: {filepath}", "success")
            QMessageBox.information(self, "Blender Path Set", f"Blender path set to:\n{filepath}")
    
    def show_settings_dialog(self):
        QMessageBox.information(self, "Settings", 
            "<h3>⚙️ Settings Information</h3>"
            "<p>All settings are available in the <b>SETTINGS</b> tab.</p>"
            "<p><b>You can configure:</b></p>"
            "<ul>"
            "<li>🎨 Export formats (OBJ, glTF, DAE, JSON, TXT, DirectX)</li>"
            "<li>📏 Model scale</li>"
            "<li>🖼️ Texture atlas creation</li>"
            "<li>⚡ Parallel processing</li>"
            "<li>💾 Caching</li>"
            "<li>🎬 Animation extraction</li>"
            "<li>🎬 Open in Blender after conversion</li>"
            "<li>🔧 Debug parameters (swizzle, bone mode, etc.)</li>"
            "</ul>"
            "<p>Settings are automatically saved and restored.</p>")
    
    def clear_cache(self):
        try:
            cache = MefCache(enabled=True)
            cache.clear_cache()
            self.log_message("🧹 Cache cleared successfully.", "success")
            QMessageBox.information(self, "Cache Cleared", "The cache has been cleared successfully.")
        except Exception as e:
            self.log_message(f"❌ Error clearing cache: {e}", "danger")
            QMessageBox.warning(self, "Error", f"Failed to clear cache: {e}")
    
    def show_about(self):
        QMessageBox.about(self, f"About {APP_NAME}",
            f"<h2 style='color:{COLORS['radiant_yellow']};'>{APP_NAME}</h2>"
            f"<p><b>Version {APP_VERSION}</b></p>"
            f"<p>A powerful professional tool for converting IGI1/IGI2 MEF models<br>"
            f"and Half-Life MDL models to modern 3D formats.</p>"
            f"<p><b>✨ Features:</b></p>"
            f"<ul>"
            f"<li>Convert to OBJ, glTF, Collada, DirectX, JSON, TXT</li>"
            f"<li>Full skeleton and animation support</li>"
            f"<li>Texture atlas generation</li>"
            f"<li>Parallel processing for speed</li>"
            f"<li>Batch conversion</li>"
            f"<li>Direct import to Blender 2.70</li>"
            f"<li>Dark Red & Electric Blue professional theme</li>"
            f"</ul>"
            f"<p><b>👤 DevEngineered_By:</b> {APP_DevEngineered_By}</p>"
            f"<p><b>⚖️ License:</b> MIT</p>")
    
    def show_docs(self):
        QMessageBox.information(self, "Documentation",
            "<h3>📖 Quick Start Guide</h3>"
            "<ol>"
            "<li>📁 Add files or folders using the buttons or drag & drop</li>"
            "<li>📂 Select output directory</li>"
            "<li>⚙️ Choose export formats in Settings tab</li>"
            "<li>🎬 Optional: Enable 'Open in Blender' for automatic import</li>"
            "<li>🚀 Click Start to begin conversion</li>"
            "</ol>"
            "<h3>⌨️ Keyboard Shortcuts</h3>"
            "<ul>"
            "<li><b>Ctrl+A</b> - Add files</li>"
            "<li><b>Ctrl+D</b> - Add folder</li>"
            "<li><b>Ctrl+L</b> - Clear list</li>"
            "<li><b>F5</b> - Start conversion</li>"
            "<li><b>F6</b> - Stop conversion</li>"
            "<li><b>Ctrl+E</b> - Export</li>"
            "<li><b>Ctrl+B</b> - Open in Blender</li>"
            "<li><b>F1</b> - Help</li>"
            "</ul>"
            "<h3>💻 Command Line Usage</h3>"
            "<code>python import_mef_standalone_with_x_w.py input -o output -F all</code>")
    
    def load_settings(self):
        self.output_dir = self.settings.value("output_dir", "")
        if self.output_dir:
            self.output_label.setText(f"📁 {self.output_dir}")
            self.output_label.setStyleSheet(f"color: {COLORS['success_color']}; font-weight: bold;")
        
        self.format_obj.setChecked(self.settings.value("format_obj", True, type=bool))
        self.format_gltf.setChecked(self.settings.value("format_gltf", True, type=bool))
        self.format_dae.setChecked(self.settings.value("format_dae", False, type=bool))
        self.format_json.setChecked(self.settings.value("format_json", True, type=bool))
        self.format_txt.setChecked(self.settings.value("format_txt", True, type=bool))
        
        if hasattr(self, 'format_directx'):
            self.format_directx.setChecked(self.settings.value("format_directx", False, type=bool))
        
        self.scale_spin.setValue(float(self.settings.value("scale", 0.01)))
        self.atlas_check.setChecked(self.settings.value("atlas", False, type=bool))
        self.parallel_check.setChecked(self.settings.value("parallel", True, type=bool))
        self.cache_check.setChecked(self.settings.value("cache", True, type=bool))
        self.animations_check.setChecked(self.settings.value("animations", True, type=bool))
        self.blender_check.setChecked(self.settings.value("blender", False, type=bool))
        
        swizzle_index = self.settings.value("swizzle_mode", 0, type=int)
        if 0 <= swizzle_index < self.swizzle_mode.count():
            self.swizzle_mode.setCurrentIndex(swizzle_index)
        
        bone_index = self.settings.value("bone_mode", 0, type=int)
        if 0 <= bone_index < self.bone_mode.count():
            self.bone_mode.setCurrentIndex(bone_index)
        
        self.flip_x.setChecked(self.settings.value("flip_x", False, type=bool))
        self.flip_y.setChecked(self.settings.value("flip_y", False, type=bool))
        self.flip_z.setChecked(self.settings.value("flip_z", False, type=bool))
        
        # تحميل مسار Blender المحفوظ
        saved_blender_path = self.settings.value("blender_path", "")
        if saved_blender_path and os.path.exists(saved_blender_path):
            self.blender_path = saved_blender_path
            self.open_in_blender_action.setEnabled(True)
            self.blender_btn.setEnabled(True)
    
    def save_settings(self):
        self.settings.setValue("output_dir", self.output_dir)
        self.settings.setValue("format_obj", self.format_obj.isChecked())
        self.settings.setValue("format_gltf", self.format_gltf.isChecked())
        self.settings.setValue("format_dae", self.format_dae.isChecked())
        self.settings.setValue("format_json", self.format_json.isChecked())
        self.settings.setValue("format_txt", self.format_txt.isChecked())
        
        if hasattr(self, 'format_directx'):
            self.settings.setValue("format_directx", self.format_directx.isChecked())
        
        self.settings.setValue("scale", self.scale_spin.value())
        self.settings.setValue("atlas", self.atlas_check.isChecked())
        self.settings.setValue("parallel", self.parallel_check.isChecked())
        self.settings.setValue("cache", self.cache_check.isChecked())
        self.settings.setValue("animations", self.animations_check.isChecked())
        self.settings.setValue("blender", self.blender_check.isChecked())
        self.settings.setValue("swizzle_mode", self.swizzle_mode.currentIndex())
        self.settings.setValue("bone_mode", self.bone_mode.currentIndex())
        self.settings.setValue("flip_x", self.flip_x.isChecked())
        self.settings.setValue("flip_y", self.flip_y.isChecked())
        self.settings.setValue("flip_z", self.flip_z.isChecked())
        
        if hasattr(self, 'blender_path') and self.blender_path:
            self.settings.setValue("blender_path", self.blender_path)
    
    def setup_shortcuts(self):
        """إعداد اختصارات لوحة المفاتيح"""
        QAction("Ctrl+N", self, triggered=self.add_files).setShortcut("Ctrl+N")
        QAction("Ctrl+O", self, triggered=self.open_output_folder).setShortcut("Ctrl+O")
        QAction("Ctrl+E", self, triggered=self.start_conversion).setShortcut("Ctrl+E")
        QAction("Ctrl+B", self, triggered=self.open_in_blender).setShortcut("Ctrl+B")
        QAction("Ctrl+Shift+C", self, triggered=self.clear_cache).setShortcut("Ctrl+Shift+C")
        QAction("F1", self, triggered=self.show_docs).setShortcut("F1")
    
    def setup_animations(self):
        """إعداد الرسوم المتحركة"""
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(500)
        self.animation.setStartValue(0.95)
        self.animation.setEndValue(1.0)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.animation.start()
    
    def closeEvent(self, event):
        if self.conversion_thread and self.conversion_thread.isRunning():
            reply = QMessageBox.question(self, "Conversion in Progress",
                "⚠️ A conversion is currently in progress.\n\n"
                "Do you want to stop it and exit?",
                QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.conversion_thread.cancel()
                self.conversion_thread.wait()
                self.save_settings()
                event.accept()
            else:
                event.ignore()
        else:
            self.save_settings()
            event.accept()


# ============================================================
# تشغيل التطبيق
# ============================================================

def run_gui():
    """تشغيل واجهة المستخدم الرسومية الاحترافية"""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = MEFConverterGUI()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    run_gui()