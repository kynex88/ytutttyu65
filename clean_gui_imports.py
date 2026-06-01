#!/usr/bin/env python3
"""
================================================================================
MEF Smart Filter - Remove GUI Dependencies
================================================================================
إزالة ذكية للتبعيات على الواجهة الرسومية من الملفات المقسمة
"""

import os
import re
from pathlib import Path
from typing import Set, List, Tuple


class SmartImportFilter:
    """فلترة ذكية للاستيرادات والتبعيات"""
    
    # Modules that should NOT be imported in converter
    BLACKLIST_MODULES = {
        'mef_gui',
        'PyQt5',
        'PyQt6',
        'tkinter',
        'wx',
    }
    
    # Classes/functions that are GUI-related and should be removed
    GUI_CLASSES = {
        'MEFConverterGUI',
        'ConversionThread',
        'QThread',
        'QMainWindow',
        'QApplication',
    }
    
    def __init__(self, module_dir: str):
        self.module_dir = Path(module_dir)
        self.errors = []
        self.removed_items = []
    
    def is_gui_import(self, line: str) -> bool:
        """Check if line is a GUI import"""
        for module in self.BLACKLIST_MODULES:
            if module in line:
                return True
        return False
    
    def remove_gui_imports(self, content: str) -> str:
        """Remove GUI-related imports"""
        lines = content.split('\n')
        filtered_lines = []
        
        for line in lines:
            # Remove GUI imports
            if self.is_gui_import(line) and ('import' in line or 'from' in line):
                self.removed_items.append(f"Import: {line.strip()}")
                continue
            filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)
    
    def remove_gui_classes(self, content: str) -> str:
        """Remove GUI class definitions"""
        lines = content.split('\n')
        filtered_lines = []
        skip_class = False
        indent_level = 0
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check if this is a GUI class definition
            is_gui_class = False
            for gui_class in self.GUI_CLASSES:
                if re.match(rf'^class\s+{gui_class}\b', line):
                    is_gui_class = True
                    skip_class = True
                    indent_level = len(line) - len(line.lstrip())
                    self.removed_items.append(f"Class: {gui_class}")
                    break
            
            if skip_class:
                # Skip until we find the next class or function at same/lower indent
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    next_indent = len(next_line) - len(next_line.lstrip())
                    
                    # Check if next line is a new definition at same or lower level
                    if (next_line.strip() and not next_line.startswith(' ' * (indent_level + 1)) 
                        and (next_line.startswith('def ') or next_line.startswith('class '))):
                        skip_class = False
                i += 1
                continue
            
            filtered_lines.append(line)
            i += 1
        
        return '\n'.join(filtered_lines)
    
    def remove_gui_calls(self, content: str) -> str:
        """Remove GUI-related function calls"""
        lines = content.split('\n')
        filtered_lines = []
        
        gui_patterns = [
            r'QApplication\(',
            r'MEFConverterGUI\(',
            r'ConversionThread\(',
            r'\.show\(',
            r'\.exec_\(',
        ]
        
        for line in lines:
            skip = False
            for pattern in gui_patterns:
                if re.search(pattern, line):
                    # Only skip if it's not part of a docstring or comment
                    if not line.strip().startswith('#') and not line.strip().startswith('"""'):
                        self.removed_items.append(f"Call: {line.strip()[:50]}")
                        skip = True
                        break
            
            if not skip:
                filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)
    
    def clean_empty_imports(self, content: str) -> str:
        """Remove empty import blocks"""
        lines = content.split('\n')
        filtered_lines = []
        
        skip_section = False
        empty_comment = False
        
        for i, line in enumerate(lines):
            # Remove "# ========== Imports ==========" if followed by empty lines
            if '# ========== Imports ==========' in line:
                if i + 1 < len(lines) and lines[i + 1].strip() == '':
                    # Check if next non-empty line is another section
                    for j in range(i + 2, min(i + 5, len(lines))):
                        if lines[j].strip():
                            if '# ==========' in lines[j]:
                                empty_comment = True
                            break
                
                if empty_comment:
                    empty_comment = False
                    continue
            
            filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)
    
    def process_file(self, file_path: Path) -> bool:
        """Process a single Python file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_length = len(content)
            
            # Apply filters in order
            content = self.remove_gui_imports(content)
            content = self.remove_gui_classes(content)
            content = self.remove_gui_calls(content)
            content = self.clean_empty_imports(content)
            
            # Remove multiple consecutive blank lines
            content = re.sub(r'\n\n\n+', '\n\n', content)
            
            # Write back only if changed
            if content != original_length:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True
            
            return False
        
        except Exception as e:
            self.errors.append(f"Error processing {file_path}: {e}")
            return False
    
    def process_directory(self) -> int:
        """Process all Python files in directory"""
        if not self.module_dir.exists():
            print(f"❌ Directory not found: {self.module_dir}")
            return 0
        
        print(f"\n{'='*70}")
        print(f"🧹 MEF SMART FILTER - REMOVING GUI DEPENDENCIES")
        print(f"{'='*70}\n")
        
        python_files = list(self.module_dir.rglob('*.py'))
        modified_count = 0
        
        for py_file in python_files:
            print(f"🔍 Processing: {py_file.relative_to(self.module_dir)}")
            if self.process_file(py_file):
                print(f"   ✅ Cleaned")
                modified_count += 1
            else:
                print(f"   ⏭️ Skipped")
        
        print(f"\n{'='*70}")
        print(f"📊 Results:")
        print(f"{'='*70}")
        print(f"   📝 Files processed: {len(python_files)}")
        print(f"   ✅ Files modified: {modified_count}")
        
        if self.removed_items:
            print(f"\n🗑️ Removed items ({len(self.removed_items)} total):")
            for item in self.removed_items[:20]:
                print(f"   - {item}")
            if len(self.removed_items) > 20:
                print(f"   ... and {len(self.removed_items) - 20} more")
        
        if self.errors:
            print(f"\n❌ Errors ({len(self.errors)} total):")
            for error in self.errors[:10]:
                print(f"   - {error}")
        
        print(f"{'='*70}\n")
        
        return modified_count


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Clean MEF converter modules from GUI dependencies'
    )
    parser.add_argument('-d', '--directory', default='mef_converter',
                       help='Directory to clean (default: mef_converter)')
    
    args = parser.parse_args()
    
    filter_tool = SmartImportFilter(args.directory)
    result = filter_tool.process_directory()
    
    return 0 if result >= 0 else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
