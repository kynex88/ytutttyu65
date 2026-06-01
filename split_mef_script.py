#!/usr/bin/env python3
"""
================================================================================
ADVANCED MEF SCRIPT SPLITTER - Professional Code Divider
================================================================================
Purpose: Split the massive import_mef_standalone_with_x_w.py (20k+ lines)
         into organized, maintainable modules WITHOUT altering any functionality.
         
Usage:   python split_mef_script.py

Output:  mef_converter/  (organized package with all modules)
================================================================================
"""

import os
import re
import ast
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional
from dataclasses import dataclass, field
from collections import defaultdict

# =============================================================================
# Configuration
# =============================================================================

INPUT_SCRIPT = "import_mef_standalone_with_x_w.py"  # The massive script
OUTPUT_DIR = "mef_converter_split"                  # Output directory

# Automated distribution rules for unassigned items
AUTO_DISTRIBUTE_RULES = {
    # Functions that should go to specific modules
    "function_rules": {
        # DirectX functions
        "export_to_directx": "exporters/mef_igi2/export_directx.py",
        "fixed_export_to_directx": "exporters/mef_igi2/export_directx.py",
        "fix_export_to_directx_in_main": "exporters/mef_igi2/export_directx.py",
        "from_mef_model_fixed": "exporters/mef_igi2/export_directx.py",
        "from_mdl_model_fixed": "exporters/mdl/export_directx.py",
        "_extract_mesh_from_mef_fixed": "exporters/mef_igi2/export_directx.py",
        "_extract_mesh_from_mdl_fixed": "exporters/mdl/export_directx.py",
        
        # Atlas functions
        "export_all_with_atlas": "exporters/mef_igi2/export_atlas.py",
        "export_gltf_with_atlas": "exporters/mef_igi2/export_atlas.py",
        "export_obj_with_atlas": "exporters/mef_igi2/export_atlas.py",
        "create_texture_atlas_igi1": "exporters/mef_igi1/export_atlas.py",
        "apply_texture_atlas_igi1": "exporters/mef_igi1/export_atlas.py",
        "update_mtl_with_atlas_igi1": "exporters/mef_igi1/export_atlas.py",
        "create_texture_atlas": "exporters/mef_igi2/export_atlas.py",
        "apply_texture_atlas_igi2": "exporters/mef_igi2/export_atlas.py",
        "update_mtl_with_atlas": "exporters/mef_igi2/export_atlas.py",
        
        # IGI2 specific functions
        "bake_skinning_improved": "exporters/mef_igi2/export_extra.py",
        "build_bone_matrices": "exporters/mef_igi2/export_extra.py",
        "build_parent_indices": "exporters/mef_igi2/export_extra.py",
        "create_bone": "exporters/mef_igi2/export_extra.py",
        "debug_uv_transform": "exporters/mef_igi2/export_extra.py",
        "prepare_skinned_vertices_for_gltf": "exporters/mef_igi2/export_gltf.py",
        "_transform_vertices_optimized": "exporters/mef_igi2/export_extra.py",
        "_export_render_mesh_fast": "exporters/mef_igi2/export_obj.py",
        "export_render_mesh_optimized": "exporters/mef_igi2/export_obj.py",
        "export_obj_multi_material": "exporters/mef_igi2/export_obj.py",
        "export_obj_material_group": "exporters/mef_igi2/export_obj.py",
        
        # MDL functions
        "get_texture_names_from_mdl": "exporters/mdl/export_extra.py",
        "_export_gltf": "exporters/mdl/export_gltf.py",
        "_export_collada": "exporters/mdl/export_collada.py",
        "_export_json": "exporters/mdl/export_json.py",
        "_export_txt": "exporters/mdl/export_txt.py",
        
        # OBJ functions
        "batch_convert_obj_fixed": "exporters/obj/export_extra.py",
        "convert_obj_to_formats_fixed": "exporters/obj/export_extra.py",
        
        # SMD functions
        "batch_convert_smd_fixed": "exporters/smd/export_extra.py",
        "convert_smd_to_formats_fixed": "exporters/smd/export_extra.py",
        
        # IGI1 specific functions
        "export_mtl": "exporters/mef_igi1/export_obj.py",
        "export_obj": "exporters/mef_igi1/export_obj.py",
        "export_render_mesh_simple": "exporters/mef_igi1/export_obj.py",
        "export_render_mesh": "exporters/mef_igi1/export_obj.py",
        "export_collision_mesh": "exporters/mef_igi1/export_extra.py",
        "export_lightmaps": "exporters/mef_igi1/export_extra.py",
        "export_attachments": "exporters/mef_igi1/export_extra.py",
        "export_collision_materials": "exporters/mef_igi1/export_extra.py",
        "export_collision_spheres": "exporters/mef_igi1/export_extra.py",
        "export_magic_vertices_improved": "exporters/mef_igi1/export_extra.py",
        "export_portals_as_mesh": "exporters/mef_igi1/export_extra.py",
        "export_glow_sprites_improved": "exporters/mef_igi1/export_extra.py",
        "export_hsem_info_igi1": "exporters/mef_igi1/export_extra.py",
        "export_d3dr_info_igi1": "exporters/mef_igi1/export_extra.py",
        "export_mrph_info_igi1": "exporters/mef_igi1/export_extra.py",
        "export_txan_info_igi1": "exporters/mef_igi1/export_extra.py",
        
        # IGI2 OBJ exports
        "export_obj": "exporters/mef_igi2/export_obj.py",
    },
    # Classes that should go to specific modules
    "class_rules": {
        "DateTime": "core/types.py",
        "TextureAtlas": "exporters/mef_igi2/export_atlas.py",
        "DXFrame": "exporters/mef_igi2/export_directx.py",
        "DXSkinWeight": "exporters/mef_igi2/export_directx.py",
        "DXAnimationKey": "exporters/mef_igi2/export_directx.py",
        "DXAnimation": "exporters/mef_igi2/export_directx.py",
        "DirectXExporter": "exporters/mef_igi2/export_directx.py",
        "AnimationExporter": "animation/anim_exporter.py",
        "Animation": "animation/anim_exporter.py",
        "AnimationKeyframe": "animation/anim_exporter.py",
        "BoneAnimationTrack": "animation/txan_analyzer.py",
        "AdvancedAnimation": "animation/txan_analyzer.py",
        "AdvancedAnimationAnalyzer": "animation/txan_analyzer.py",
    }
}

# Module structure (where each class/function should go)
MODULE_STRUCTURE = {
    # Core modules
    "core/buffer.py": {
        "classes": ["Buffer"],
        "functions": ["read", "read_uint8", "read_int8", "read_uint16", "read_int16",
                      "read_uint32", "read_int32", "read_float", "read_fmt", 
                      "read_ascii_string", "align", "size", "eof"],
        "constants": []
    },
    "core/constants.py": {
        "classes": ["ModelType"],
        "functions": [],
        "constants": ["SCALE", "INV_SCALE", "XTRV_STRIDE", "XTRV_POS_OFF", 
                      "XTRV_NORM_OFF", "XTRV_UV1_OFF", "DNER_STRIDE", "SEMS_STRIDE",
                      "XTVS_STRIDE", "CAFS_STRIDE", "EGDE_STRIDE", "MODEL_TYPE_NAMES_EXT",
                      "MAGIC_ILFF", "NEW_CHUNK_TAGS", "MDL_ID", "MDL_VERSION",
                      "BONE_HAS_POSITION", "BONE_HAS_ROTATION", "BONE_HAS_SCALE",
                      "ENABLE_TEXTURE_ATLAS", "ENABLE_TEXTURE_ATLAS_SMD", 
                      "ENABLE_TEXTURE_ATLAS_OBJ", "ENABLE_TEXTURE_ATLAS_MDL",
                      "ATLAS_MODE", "INPUT_DIR", "OUTPUT_DIR"]
    },
    "core/types.py": {
        "classes": ["Vector3", "Sphere", "MeshInfo", "Bone", "TextureReference", 
                    "XTRWEntry", "MefDebugParams", "Attachment", "AttachmentIGI1",
                    "MagicVertex", "Portal", "PortalVertex", "PortalFace", "GlowSprite",
                    "CollisionMaterialIGI1", "CollisionMaterialIGI2", "LightmapData",
                    "TXANData", "HSEMInfo", "TextureCoordinateSet"],
        "functions": [],
        "constants": []
    },
    "core/utils.py": {
        "classes": [],
        "functions": ["convert_to_json_serializable", "get_texture_name", "ensure_dir",
                      "make_translation_matrix", "apply_igi_swizzle", "apply_igi_swizzle_to_vector3",
                      "save_lightmap_as_png", "save_lightmap_as_dds", "set_global_debug_params",
                      "get_global_debug_params", "reset_global_debug_params", "quick_validate",
                      "detect_file_type", "detect_mef_version"],
        "constants": []
    },
    
    # Format modules - Parsers (Reading only)
    "formats/mef_base.py": {
        "classes": ["ChunkHeader", "Chunk", "LoopFile"],
        "functions": ["__bool__", "next_chunk", "expect_chunk", "has_chunk", "print_all_chunks"],
        "constants": []
    },
    "formats/mef_igi1_parser.py": {
        "classes": ["ModelInfoIGI1", "RenderMeshHeaderIGI1", "RenderMeshDataIGI1", 
                    "MefModelIGI1", "OptimizedMefModelIGI1"],
        "functions": ["_is_igi1_skinned", "_process_magic_vertices", "_process_portal",
                      "_process_portal_vertices", "_process_portal_faces", "_process_render_mesh",
                      "_process_collision_mesh", "_process_lightmap", "_process_txan",
                      "_post_process_igi1", "_infer_bones_from_vertices", "_enhance_materials",
                      "_collect_texture_references", "_export_enhanced_igi1_data", 
                      "_calculate_model_stats", "get_cache_key"],
        "constants": []
    },
    "formats/mef_igi2_parser.py": {
        "classes": ["ModelInfoIGI2", "RenderMeshHeader", "FaceGroup", "SkinnedFaceGroup",
                    "LightmapFaceGroup", "CollisionMeshSubHeader", "CollisionMeshHeader",
                    "ShadowMeshHeader", "RenderMeshDataIGI2", "CollisionMeshDataIGI2",
                    "ShadowMeshDataIGI2", "MefModelIGI2", "MefModelIGI2EnhancedPatch",
                    "MefModelIGI2_V2", "HsemHeaderIGI2_V2", "ReihChunkData", "SmesHeaderIGI2",
                    "CafsFaceIGI2", "EgdeEdgeIGI2", "OptimizedMefModelIGI2"],
        "functions": ["_process_hierarchy", "_process_collision_materials", 
                      "_process_collision_materials_mesh1", "_process_render_mesh",
                      "_process_collision_mesh", "_process_shadow_mesh", "_process_morph",
                      "_process_xtrw", "_process_xtxm", "_process_tcst", "_process_hprm",
                      "_process_xtrn", "_process_nhsa", "_process_llun", "_process_chunks_enhanced",
                      "_process_hierarchy_enhanced", "_process_bone_names_enhanced",
                      "_process_hprm_enhanced", "_process_glow_enhanced", 
                      "_process_attachments_enhanced", "_process_magic_vertices_enhanced",
                      "_process_portal_enhanced", "_process_portal_faces_enhanced",
                      "_process_portal_vertices_enhanced", "_process_xtrw_enhanced",
                      "_process_xtxm_enhanced", "_process_tcst_enhanced", "_process_xtrn_enhanced",
                      "_process_nhsa_enhanced", "_process_txan_enhanced", 
                      "_process_shadow_mesh_enhanced", "_process_render_mesh_enhanced",
                      "_process_collision_mesh_enhanced", "_process_collision_materials_enhanced",
                      "_build_bones", "_find_parent", "_load_attachments", "_load_magic_vertices",
                      "_load_portals", "_load_portal_faces", "_load_portal_vertices", "_load_xtrw", 
                      "_load_xtxm", "_load_tcst", "_load_render_header", "_load_render_groups",
                      "_load_vertices", "_load_faces", "_load_lightmaps", "_load_shadow_header",
                      "_load_shadow_vertices", "_load_shadow_faces", "_load_shadow_edges",
                      "_load_xtrn", "_load_nhsa", "ensure_dir"],
        "constants": []
    },
    "formats/mdl_parser.py": {
        "classes": ["MDLHeader", "StudioBone", "StudioBodyPart", "StudioModel", 
                    "StudioMesh", "StudioVertex", "StudioNormal", "StudioTriangle",
                    "StudioVertexInfo", "StudioNormalInfo", "StudioHeader", "MdlModel"],
        "functions": ["_parse_header", "_parse_bones", "_parse_textures", "_parse_bodyparts",
                      "_parse_vertices_and_triangles", "_parse_geometry", "_parse_triangle_commands",
                      "extract_textures", "debug_print_geometry", "ensure_dir"],
        "constants": []
    },
    "formats/smd_parser.py": {
        "classes": ["SMDNode", "SMDVertex", "SMDFace", "SMDTriangle", "SMDExporter"],
        "functions": ["from_file", "from_string", "to_vertices_array", "to_bones_list",
                      "get_material_for_triangle", "get_materials_list", "ensure_dir"],
        "constants": []
    },
    "formats/obj_parser.py": {
        "classes": ["OBJVertex", "OBJTextureVertex", "OBJNormal", "OBJFace", 
                    "OBJMaterial", "OBJObject", "OBJExporter"],
        "functions": ["from_file", "from_string", "parse_obj_content", "to_unified_vertices",
                      "to_smd", "to_mdl_format", "_new_object", "_parse_vertex",
                      "_parse_texture_vertex", "_parse_normal", "_parse_face", "_load_mtl_file",
                      "_parse_mtl_content", "_get_original_vertices_for_gltf", "ensure_dir"],
        "constants": []
    },
    
    # Exporters - MEF IGI1
    "exporters/mef_igi1/__init__.py": {"classes": [], "functions": [], "constants": []},
    "exporters/mef_igi1/export_obj.py": {
        "classes": [],
        "functions": ["export_obj", "export_mtl", "export_render_mesh_simple", "export_render_mesh"],
        "constants": []
    },
    "exporters/mef_igi1/export_gltf.py": {
        "classes": [],
        "functions": ["export_to_gltf", "export_to_gltf_full"],
        "constants": []
    },
    "exporters/mef_igi1/export_directx.py": {
        "classes": [],
        "functions": ["export_to_directx", "from_mef_model"],
        "constants": []
    },
    "exporters/mef_igi1/export_json.py": {
        "classes": [],
        "functions": ["export_hsem_info_igi1", "export_d3dr_info_igi1", "export_mrph_info_igi1",
                      "export_txan_info_igi1", "export_hsmc_info_igi1_improved", "export_xtvc_info_igi1",
                      "export_ecfc_info_igi1", "export_tamc_info_igi1", "export_hpsc_info_igi1"],
        "constants": []
    },
    "exporters/mef_igi1/export_txt.py": {
        "classes": [],
        "functions": ["export_hsem_info_igi1", "export_d3dr_info_igi1", "export_attachments",
                      "export_collision_materials", "export_collision_spheres", "export_magic_vertices_improved",
                      "export_portals_as_mesh", "export_glow_sprites_improved", "export_all_enhanced"],
        "constants": []
    },
    "exporters/mef_igi1/export_csv.py": {
        "classes": [],
        "functions": ["export_xtvc_info_igi1", "export_ecfc_info_igi1", "export_tamc_info_igi1", "export_hpsc_info_igi1"],
        "constants": []
    },
    "exporters/mef_igi1/export_collada.py": {
        "classes": [],
        "functions": ["export_to_collada"],
        "constants": []
    },
    "exporters/mef_igi1/export_atlas.py": {
        "classes": [],
        "functions": ["create_texture_atlas_igi1", "apply_texture_atlas_igi1", "update_mtl_with_atlas_igi1"],
        "constants": []
    },
    "exporters/mef_igi1/export_extra.py": {
        "classes": [],
        "functions": ["export_collision_mesh", "export_lightmaps", "export_attachments", "export_extra_data",
                      "export_collision_materials", "export_collision_spheres", "export_magic_vertices_improved",
                      "export_portals_as_mesh", "export_glow_sprites_improved", "export_all_collision_mesh_data_igi1",
                      "export_all_shadow_data_igi1", "export_sems_info_igi1", "export_xtvs_info_igi1",
                      "export_cafs_info_igi1", "export_egde_info_igi1"],
        "constants": []
    },
    
    # Exporters - MEF IGI2
    "exporters/mef_igi2/__init__.py": {"classes": [], "functions": [], "constants": []},
    "exporters/mef_igi2/export_obj.py": {
        "classes": [],
        "functions": ["export_obj", "export_mtl", "export_render_mesh", "export_render_mesh_simple",
                      "export_render_mesh_multi_material", "export_obj_multi_material", "export_obj_material_group",
                      "export_render_mesh_optimized"],
        "constants": []
    },
    "exporters/mef_igi2/export_gltf.py": {
        "classes": [],
        "functions": ["export_to_gltf", "export_to_gltf_full", "prepare_skinned_vertices_for_gltf"],
        "constants": []
    },
    "exporters/mef_igi2/export_directx.py": {
        "classes": ["DXFrame", "DXSkinWeight", "DXAnimationKey", "DXAnimation", "DirectXExporter"],
        "functions": ["export_to_directx", "fixed_export_to_directx", "fix_export_to_directx_in_main",
                      "from_mef_model_fixed", "_extract_mesh_from_mef_fixed", "_extract_materials_from_mef",
                      "_extract_animations_from_mef", "_find_parent_name", "fix_directx_bone_extraction",
                      "fix_directx_mesh_extraction", "fix_export_to_directx", "apply_all_directx_fixes",
                      "convert_to_directx", "batch_convert_to_directx", "export_to_file", "_write_frame_hierarchy",
                      "_write_materials", "_write_frames", "_write_child_frame", "_write_mesh", "_write_skin_weights",
                      "_write_animations"],
        "constants": []
    },
    "exporters/mef_igi2/export_json.py": {
        "classes": [],
        "functions": ["export_hsem_info", "export_d3dr_info", "export_manb_detailed", "export_reih_detailed",
                      "export_mrph_info", "export_txan_info", "export_hsmc_info", "export_xtvc_info",
                      "export_ecfc_info", "export_tamc_info", "export_hpsc_info", "export_xtrw_info",
                      "export_xtxm_info", "export_tcst_info", "export_hprm_info", "export_shadow_detailed",
                      "export_hprm_detailed", "export_external_refs", "export_skeleton_hints", "export_all_enhanced"],
        "constants": []
    },
    "exporters/mef_igi2/export_txt.py": {
        "classes": [],
        "functions": ["export_hsem_info", "export_d3dr_info", "export_manb_detailed", "export_reih_detailed",
                      "export_mrph_info", "export_txan_info", "export_hsmc_info", "export_xtvc_info",
                      "export_ecfc_info", "export_tamc_info", "export_hpsc_info", "export_attachments",
                      "export_collision_materials", "export_collision_spheres"],
        "constants": []
    },
    "exporters/mef_igi2/export_csv.py": {
        "classes": [],
        "functions": ["export_manb_detailed", "export_reih_detailed", "export_hsmc_info", "export_xtvc_info",
                      "export_ecfc_info", "export_tamc_info", "export_hpsc_info"],
        "constants": []
    },
    "exporters/mef_igi2/export_collada.py": {
        "classes": [],
        "functions": ["export_to_collada"],
        "constants": []
    },
    "exporters/mef_igi2/export_atlas.py": {
        "classes": ["TextureAtlas"],
        "functions": ["create_texture_atlas", "apply_texture_atlas_igi2", "update_mtl_with_atlas",
                      "export_all_with_atlas", "export_gltf_with_atlas", "export_obj_with_atlas",
                      "_next_power_of_two", "find_texture_file", "add_texture", "pack_textures",
                      "get_uv_transform", "get_texture_index", "save_atlas", "has_multiple_textures",
                      "collect_textures_from_materials", "create_atlas_for_model", "update_uvs_with_atlas",
                      "update_mtl_to_use_atlas", "enable_texture_atlas_for_all", "add_atlas_support_to_smd",
                      "add_atlas_support_to_obj", "add_atlas_support_to_mdl", "add_atlas_support_to_mdl_model",
                      "enable_atlas_for_all_formats", "add_directx_export_to_mef_model_igi1",
                      "add_directx_export_to_mef_model_igi2"],
        "constants": ["ENABLE_TEXTURE_ATLAS_SMD", "ENABLE_TEXTURE_ATLAS_OBJ", 
                      "ENABLE_TEXTURE_ATLAS_MDL", "ATLAS_MODE"]
    },
    "exporters/mef_igi2/export_extra.py": {
        "classes": [],
        "functions": ["export_collision_mesh", "export_shadow_mesh", "export_lightmaps", "export_attachments",
                      "export_extra_data", "export_collision_materials", "export_collision_spheres",
                      "export_magic_vertices_improved", "export_portals_as_mesh", "export_glow_sprites_improved",
                      "export_all_collision_mesh_data", "export_all_shadow_data", "export_sems_info",
                      "export_xtvs_info", "export_cafs_info", "export_egde_info", "bake_skinning_improved",
                      "build_bone_matrices", "build_parent_indices", "create_bone", "debug_uv_transform",
                      "_transform_vertices_optimized"],
        "constants": []
    },
    
    # Exporters - MDL
    "exporters/mdl/__init__.py": {"classes": [], "functions": [], "constants": []},
    "exporters/mdl/export_obj.py": {
        "classes": [],
        "functions": ["export_obj", "export_obj_as_points", "export_all"],
        "constants": []
    },
    "exporters/mdl/export_gltf.py": {
        "classes": [],
        "functions": ["export_gltf", "_export_gltf"],
        "constants": []
    },
    "exporters/mdl/export_directx.py": {
        "classes": [],
        "functions": ["export_to_directx", "from_mdl_model_fixed", "_extract_mesh_from_mdl_fixed"],
        "constants": []
    },
    "exporters/mdl/export_json.py": {
        "classes": [],
        "functions": ["export_json", "_export_json"],
        "constants": []
    },
    "exporters/mdl/export_txt.py": {
        "classes": [],
        "functions": ["export_txt", "_export_txt"],
        "constants": []
    },
    "exporters/mdl/export_collada.py": {
        "classes": [],
        "functions": ["_export_collada"],
        "constants": []
    },
    "exporters/mdl/export_extra.py": {
        "classes": [],
        "functions": ["get_texture_names_from_mdl", "extract_textures"],
        "constants": []
    },
    
    # Exporters - SMD
    "exporters/smd/__init__.py": {"classes": [], "functions": [], "constants": []},
    "exporters/smd/export_obj.py": {
        "classes": [],
        "functions": ["export_obj", "export_all"],
        "constants": []
    },
    "exporters/smd/export_gltf.py": {
        "classes": [],
        "functions": ["export_gltf"],
        "constants": []
    },
    "exporters/smd/export_directx.py": {
        "classes": [],
        "functions": ["export_to_directx", "from_smd_model", "_extract_mesh_from_smd"],
        "constants": []
    },
    "exporters/smd/export_json.py": {
        "classes": [],
        "functions": ["export_json"],
        "constants": []
    },
    "exporters/smd/export_txt.py": {
        "classes": [],
        "functions": ["export_txt"],
        "constants": []
    },
    "exporters/smd/export_extra.py": {
        "classes": [],
        "functions": ["convert_smd_to_formats", "batch_convert_smd", "batch_convert_smd_fixed",
                      "convert_smd_to_formats_fixed"],
        "constants": []
    },
    
    # Exporters - OBJ
    "exporters/obj/__init__.py": {"classes": [], "functions": [], "constants": []},
    "exporters/obj/export_obj.py": {
        "classes": [],
        "functions": ["export_obj", "export_all"],
        "constants": []
    },
    "exporters/obj/export_gltf.py": {
        "classes": [],
        "functions": ["export_gltf"],
        "constants": []
    },
    "exporters/obj/export_directx.py": {
        "classes": [],
        "functions": ["export_to_directx", "from_obj_model"],
        "constants": []
    },
    "exporters/obj/export_json.py": {
        "classes": [],
        "functions": ["export_json"],
        "constants": []
    },
    "exporters/obj/export_txt.py": {
        "classes": [],
        "functions": ["export_txt"],
        "constants": []
    },
    "exporters/obj/export_extra.py": {
        "classes": [],
        "functions": ["convert_obj_to_formats", "batch_convert_obj", "batch_convert_obj_fixed",
                      "convert_obj_to_formats_fixed"],
        "constants": []
    },
    
    # Animation modules
    "animation/__init__.py": {"classes": [], "functions": [], "constants": []},
    "animation/txan_analyzer.py": {
        "classes": ["BoneAnimationTrack", "AdvancedAnimation", "AdvancedAnimationAnalyzer"],
        "functions": ["analyze_txan", "euler_to_quaternion", "analyze_morph_targets",
                      "blend_animations", "slerp_quaternion", "export_to_mmd", "export_to_fbx_style"],
        "constants": []
    },
    "animation/anim_exporter.py": {
        "classes": ["AnimationExporter", "Animation", "AnimationKeyframe"],
        "functions": ["extract_from_txan", "export_to_gltf_animations", "export_to_json",
                      "add_animation_support_to_igi2", "extract_animations", "export_animations"],
        "constants": []
    },
    
    # Parallel processing modules
    "parallel/__init__.py": {"classes": [], "functions": [], "constants": []},
    "parallel/processor.py": {
        "classes": ["ParallelProcessor"],
        "functions": ["process_vertices_chunk", "process_skin_batch"],
        "constants": []
    },
    "parallel/cache.py": {
        "classes": ["MefCache"],
        "functions": ["_ensure_cache_dir", "_get_file_hash", "_get_cache_path",
                      "get_cached_result", "store_cached_result", "clear_cache", "get_cache_size"],
        "constants": []
    },
    
    # Performance monitoring
    "performance/monitor.py": {
        "classes": ["PerformanceMonitor"],
        "functions": ["measure", "print_report"],
        "constants": []
    },
    
    # Main module
    "main.py": {
        "classes": [],
        "functions": ["main", "main_optimized", "optimized_convert_file", 
                      "parallel_process_folder", "comprehensive_test", "test_enhanced_parser",
                      "test_animation_extraction", "create_addon_files", "create_blender_addon_script",
                      "create_gui_launcher_script", "launch_gui", "apply_all_fixes"],
        "constants": ["APP_NAME", "APP_VERSION", "APP_DEVELOPER", "APP_COPYRIGHT",
                      "BLENDER_PATH", "ALTERNATIVE_BLENDER_PATHS", "COLORS"]
    },
    
    # Blender addon
    "blender_addon.py": {
        "classes": ["ImportIGIModel"],
        "functions": ["menu_func_import", "register", "unregister"],
        "constants": ["bl_info"]
    },
    
    # GUI module
    "gui/__init__.py": {
        "classes": ["ConversionThread", "MEFConverterGUI"],
        "functions": ["run_gui"],
        "constants": []
    },
    "gui/styles.py": {
        "classes": [],
        "functions": ["get_professional_stylesheet"],
        "constants": ["COLORS", "APP_NAME", "APP_VERSION"]
    },
    
    # __init__.py for each package
    "__init__.py": {"classes": [], "functions": [], "constants": ["__version__"]},
    "core/__init__.py": {"classes": [], "functions": [], "constants": []},
    "formats/__init__.py": {"classes": [], "functions": [], "constants": []},
    "exporters/__init__.py": {"classes": [], "functions": [], "constants": []},
}

# Functions that should be added to __init__.py exports
INIT_EXPORTS = {
    "__init__.py": [
        "main", "optimized_convert_file", "parallel_process_folder", "Buffer",
        "MefModelIGI1", "MefModelIGI2", "StudioHeader", "SMDExporter", "OBJExporter",
        "SCALE", "ModelType", "MefDebugParams"
    ],
    "core/__init__.py": ["Buffer", "SCALE", "ModelType", "MefDebugParams", 
                          "Vector3", "Sphere", "convert_to_json_serializable",
                          "set_global_debug_params", "get_global_debug_params"],
    "formats/__init__.py": ["MefModelIGI1", "MefModelIGI2", "StudioHeader", 
                             "SMDExporter", "OBJExporter", "detect_file_type", "detect_mef_version"],
    "exporters/__init__.py": ["export_to_directx", "export_to_gltf", "export_to_collada", "TextureAtlas"],
    "parallel/__init__.py": ["ParallelProcessor", "MefCache"],
    "animation/__init__.py": ["AnimationExporter", "AdvancedAnimationAnalyzer"],
    "exporters/mef_igi1/__init__.py": ["export_obj", "export_to_gltf", "export_to_directx", "export_to_collada"],
    "exporters/mef_igi2/__init__.py": ["export_obj", "export_to_gltf", "export_to_directx", "export_to_collada", "TextureAtlas"],
    "exporters/mdl/__init__.py": ["export_obj", "export_gltf", "export_to_directx"],
    "exporters/smd/__init__.py": ["export_obj", "export_gltf", "export_to_directx"],
    "exporters/obj/__init__.py": ["export_obj", "export_gltf", "export_to_directx"],
}


# =============================================================================
# Code Analysis Class
# =============================================================================

class CodeAnalyzer:
    """Analyzes Python code to extract classes, functions, and imports"""
    
    def __init__(self, source_code: str):
        self.source_code = source_code
        self.lines = source_code.splitlines()
        self.tree = ast.parse(source_code)
        
        # Add parent references to all nodes
        for node in ast.walk(self.tree):
            for child in ast.iter_child_nodes(node):
                child.parent = node
        
        self.classes: Dict[str, Dict] = {}
        self.functions: Dict[str, Dict] = {}
        self.imports: List[str] = []
        self.constants: List[str] = []
        self.global_vars: List[str] = []
        self.decorators: List[str] = []
        
        self._analyze()
    
    def _analyze(self):
        """Analyze the AST tree"""
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef):
                self._extract_class(node)
            elif isinstance(node, ast.FunctionDef):
                # Check if this is a method (has parent class) or global function
                if not hasattr(node, 'parent') or not isinstance(node.parent, ast.ClassDef):
                    self._extract_function(node)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    self.imports.append(f"import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                names = ", ".join([alias.name for alias in node.names])
                self.imports.append(f"from {module} import {names}")
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id.isupper():
                        self.constants.append(target.id)
            elif isinstance(node, ast.Global):
                for name in node.names:
                    self.global_vars.append(name)
    
    def _extract_class(self, node: ast.ClassDef):
        """Extract class information"""
        methods = []
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                methods.append(item.name)
        
        self.classes[node.name] = {
            "lineno": node.lineno,
            "methods": methods,
            "bases": [base.id for base in node.bases if isinstance(base, ast.Name)],
            "decorators": [d.id for d in node.decorator_list if isinstance(d, ast.Name)]
        }
    
    def _extract_function(self, node: ast.FunctionDef):
        """Extract function information"""
        self.functions[node.name] = {
            "lineno": node.lineno,
            "args": [arg.arg for arg in node.args.args],
            "decorators": [d.id for d in node.decorator_list if isinstance(d, ast.Name)]
        }
    
    def get_class_body(self, class_name: str) -> str:
        """Extract the full source of a class"""
        class_node = None
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                class_node = node
                break
        
        if class_node:
            # Get the line range of the class
            start_line = class_node.lineno - 1
            end_line = class_node.end_lineno if hasattr(class_node, 'end_lineno') else start_line + 1
            
            # Extract just the class lines
            lines = self.lines[start_line:end_line]
            return "\n".join(lines)
        return ""

    def get_function_body(self, function_name: str) -> str:
        """Extract the full source of a function"""
        func_node = None
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef) and node.name == function_name:
                # Check if this is a global function (not a method)
                if not hasattr(node, 'parent') or not isinstance(node.parent, ast.ClassDef):
                    func_node = node
                    break
        
        if func_node:
            # Get the line range of the function
            start_line = func_node.lineno - 1
            end_line = func_node.end_lineno if hasattr(func_node, 'end_lineno') else start_line + 1
            
            # Extract just the function lines
            lines = self.lines[start_line:end_line]
            return "\n".join(lines)
        return ""


# =============================================================================
# Main Splitter Class
# =============================================================================

class SmartSplitter:
    """Intelligent script splitter that preserves all functionality"""
    
    def __init__(self, input_path: str, output_dir: str):
        self.input_path = input_path
        self.output_dir = Path(output_dir)
        self.analyzer = None
        self.source_code = ""
        
        self.created_files: List[str] = []
        self.errors: List[str] = []
        
        # Auto-distribute unassigned items
        self.auto_distributed = {
            "classes": {},
            "functions": {}
        }
    
    def _auto_distribute_items(self, all_classes: set, all_functions: set, 
                                classes_written: set, functions_written: set) -> Tuple[Dict, Dict]:
        """Automatically distribute unassigned classes and functions based on rules"""
        
        # Find unassigned items
        unassigned_classes = all_classes - classes_written
        unassigned_functions = all_functions - functions_written
        
        # Apply rules for functions
        function_rules = AUTO_DISTRIBUTE_RULES.get("function_rules", {})
        for func_name, target_module in function_rules.items():
            if func_name in unassigned_functions:
                if target_module not in self.auto_distributed["functions"]:
                    self.auto_distributed["functions"][target_module] = []
                self.auto_distributed["functions"][target_module].append(func_name)
                functions_written.add(func_name)
        
        # Apply rules for classes
        class_rules = AUTO_DISTRIBUTE_RULES.get("class_rules", {})
        for class_name, target_module in class_rules.items():
            if class_name in unassigned_classes:
                if target_module not in self.auto_distributed["classes"]:
                    self.auto_distributed["classes"][target_module] = []
                self.auto_distributed["classes"][target_module].append(class_name)
                classes_written.add(class_name)
        
        # For remaining unassigned functions, try to infer from name patterns
        remaining_functions = all_functions - functions_written
        for func in remaining_functions:
            # Infer module based on function name patterns
            if "igi1" in func.lower() or "_igi1_" in func.lower():
                target = "exporters/mef_igi1/export_extra.py"
            elif "igi2" in func.lower() or "_igi2_" in func.lower():
                target = "exporters/mef_igi2/export_extra.py"
            elif "mdl" in func.lower():
                target = "exporters/mdl/export_extra.py"
            elif "smd" in func.lower():
                target = "exporters/smd/export_extra.py"
            elif "obj" in func.lower():
                target = "exporters/obj/export_extra.py"
            elif "directx" in func.lower() or "dx" in func.lower():
                target = "exporters/mef_igi2/export_directx.py"
            elif "gltf" in func.lower():
                target = "exporters/mef_igi2/export_gltf.py"
            elif "collada" in func.lower():
                target = "exporters/mef_igi2/export_collada.py"
            elif "atlas" in func.lower():
                target = "exporters/mef_igi2/export_atlas.py"
            elif "animation" in func.lower() or "txan" in func.lower():
                target = "animation/anim_exporter.py"
            elif "analyzer" in func.lower():
                target = "animation/txan_analyzer.py"
            elif "cache" in func.lower():
                target = "parallel/cache.py"
            elif "processor" in func.lower():
                target = "parallel/processor.py"
            elif "monitor" in func.lower():
                target = "performance/monitor.py"
            else:
                target = "core/utils.py"  # Default fallback
            
            if target not in self.auto_distributed["functions"]:
                self.auto_distributed["functions"][target] = []
            self.auto_distributed["functions"][target].append(func)
            functions_written.add(func)
        
        # For remaining unassigned classes
        remaining_classes = all_classes - classes_written
        for cls in remaining_classes:
            # Infer module based on class name patterns
            if "IGI1" in cls or "Igi1" in cls:
                target = "formats/mef_igi1_parser.py"
            elif "IGI2" in cls or "Igi2" in cls:
                target = "formats/mef_igi2_parser.py"
            elif "MDL" in cls or "Mdl" in cls:
                target = "formats/mdl_parser.py"
            elif "SMD" in cls or "Smd" in cls:
                target = "formats/smd_parser.py"
            elif "OBJ" in cls or "Obj" in cls:
                target = "formats/obj_parser.py"
            elif "DirectX" in cls or "DX" in cls:
                target = "exporters/mef_igi2/export_directx.py"
            elif "Atlas" in cls:
                target = "exporters/mef_igi2/export_atlas.py"
            else:
                target = "core/types.py"  # Default for types
            
            if target not in self.auto_distributed["classes"]:
                self.auto_distributed["classes"][target] = []
            self.auto_distributed["classes"][target].append(cls)
            classes_written.add(cls)
        
        return classes_written, functions_written
    
    def run(self) -> bool:
        """Execute the splitting process"""
        print("\n" + "=" * 80)
        print("🚀 ADVANCED MEF SCRIPT SPLITTER")
        print("=" * 80)
        
        # Step 1: Read source
        print("\n📖 Step 1: Reading source file...")
        try:
            with open(self.input_path, 'r', encoding='utf-8') as f:
                self.source_code = f.read()
            print(f"   ✅ Read {len(self.source_code)} characters")
        except Exception as e:
            print(f"   ❌ Error reading file: {e}")
            return False
        
        # Step 2: Analyze code
        print("\n🔍 Step 2: Analyzing code structure...")
        try:
            self.analyzer = CodeAnalyzer(self.source_code)
            print(f"   ✅ Found {len(self.analyzer.classes)} classes")
            print(f"   ✅ Found {len(self.analyzer.functions)} global functions")
            print(f"   ✅ Found {len(self.analyzer.imports)} imports")
            print(f"   ✅ Found {len(self.analyzer.constants)} constants")
        except Exception as e:
            print(f"   ❌ Error analyzing code: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Step 3: Create directory structure
        print("\n📁 Step 3: Creating directory structure...")
        try:
            self._create_directories()
            print(f"   ✅ Created directories under: {self.output_dir}")
        except Exception as e:
            print(f"   ❌ Error creating directories: {e}")
            return False
        
        # Step 4: Extract and write modules
        print("\n✂️ Step 4: Extracting and writing modules...")
        success = self._extract_modules()
        
        # Step 5: Generate __init__.py files
        print("\n🔗 Step 5: Generating __init__.py files...")
        self._generate_init_files()
        
        # Step 6: Create requirements.txt
        print("\n📦 Step 6: Creating requirements.txt...")
        self._create_requirements()
        
        # Step 7: Report auto-distributed items
        self._report_auto_distributed()
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 SPLIT COMPLETE")
        print("=" * 80)
        print(f"   ✅ Created: {len(self.created_files)} files")
        print(f"   ⚠️ Errors: {len(self.errors)}")
        print(f"   📂 Output: {self.output_dir.absolute()}")
        
        if self.errors:
            print("\n⚠️ Warnings:")
            for err in self.errors:
                print(f"   - {err}")
        
        print("\n" + "=" * 80)
        return True
    
    def _report_auto_distributed(self):
        """Report automatically distributed items"""
        if self.auto_distributed["classes"] or self.auto_distributed["functions"]:
            print("\n🤖 AUTO-DISTRIBUTED ITEMS:")
            
            if self.auto_distributed["classes"]:
                print("\n   📦 Classes automatically distributed:")
                for module, classes in self.auto_distributed["classes"].items():
                    print(f"      → {module}: {', '.join(classes)}")
            
            if self.auto_distributed["functions"]:
                print("\n   🔧 Functions automatically distributed:")
                for module, functions in self.auto_distributed["functions"].items():
                    print(f"      → {module}: {', '.join(functions)}")
    
    def _create_directories(self):
        """Create all necessary directories"""
        for module_path in MODULE_STRUCTURE.keys():
            dir_path = self.output_dir / Path(module_path).parent
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def _extract_modules(self) -> bool:
        """Extract and write each module"""
        all_classes = set(self.analyzer.classes.keys())
        all_functions = set(self.analyzer.functions.keys())
        all_constants = set(self.analyzer.constants)
        
        classes_written = set()
        functions_written = set()
        constants_written = set()
        
        # First pass: write explicitly defined modules
        for module_path, content in MODULE_STRUCTURE.items():
            file_path = self.output_dir / module_path
            
            classes_for_module = content.get("classes", [])
            functions_for_module = content.get("functions", [])
            constants_for_module = content.get("constants", [])
            
            if not classes_for_module and not functions_for_module and not constants_for_module:
                # Empty file - just create it
                file_path.write_text('"""\n' + module_path + '\n"""\n\n', encoding='utf-8')
                self.created_files.append(str(file_path))
                continue
            
            print(f"   📝 Creating: {module_path}")
            
            # Build module content
            module_content = []
            module_content.append(f'"""\n{module_path}\n"""\n')
            module_content.append("# ============================================================")
            module_content.append("# AUTO-GENERATED BY MEF SCRIPT SPLITTER")
            module_content.append("# DO NOT EDIT - ALL FUNCTIONALITY PRESERVED")
            module_content.append("# ============================================================\n")
            
            # Add imports
            module_content.append("# ========== Imports ==========")
            for imp in self.analyzer.imports:
                if any(cls in imp for cls in classes_for_module):
                    continue
                if "mef_converter" in imp:
                    imp = imp.replace("import_mef_standalone_with_x_w", "mef_converter")
                module_content.append(imp)
            module_content.append("")
            
            # Add constants
            if constants_for_module:
                module_content.append("# ========== Constants ==========")
                for const in constants_for_module:
                    if const in all_constants:
                        const_body = self._extract_constant(const)
                        if const_body:
                            module_content.append(const_body)
                            constants_written.add(const)
            module_content.append("")
            
            # Add classes
            if classes_for_module:
                module_content.append("# ========== Classes ==========")
                for cls_name in classes_for_module:
                    if cls_name in all_classes:
                        class_body = self.analyzer.get_class_body(cls_name)
                        if class_body:
                            module_content.append(class_body)
                            module_content.append("")
                            classes_written.add(cls_name)
                        else:
                            self.errors.append(f"Could not extract class '{cls_name}' for {module_path}")
            module_content.append("")
            
            # Add functions
            if functions_for_module:
                module_content.append("# ========== Functions ==========")
                for func_name in functions_for_module:
                    if func_name in all_functions:
                        func_body = self.analyzer.get_function_body(func_name)
                        if func_body:
                            module_content.append(func_body)
                            module_content.append("")
                            functions_written.add(func_name)
                        else:
                            self.errors.append(f"Could not extract function '{func_name}' for {module_path}")
            
            # Write file
            try:
                file_path.write_text("\n".join(module_content), encoding='utf-8')
                self.created_files.append(str(file_path))
            except Exception as e:
                self.errors.append(f"Error writing {module_path}: {e}")
        
        # Second pass: auto-distribute remaining items
        classes_written, functions_written = self._auto_distribute_items(
            all_classes, all_functions, classes_written, functions_written
        )
        
        # Write auto-distributed items to their respective modules
        for module_path, extra_classes in self.auto_distributed["classes"].items():
            file_path = self.output_dir / module_path
            if file_path.exists():
                # Append to existing file
                with open(file_path, 'r', encoding='utf-8') as f:
                    existing_content = f.read()
                
                # Add classes
                with open(file_path, 'a', encoding='utf-8') as f:
                    f.write("\n\n# ========== Auto-Distributed Classes ==========\n\n")
                    for cls_name in extra_classes:
                        class_body = self.analyzer.get_class_body(cls_name)
                        if class_body:
                            f.write(class_body)
                            f.write("\n\n")
                        else:
                            self.errors.append(f"Could not extract auto-distributed class '{cls_name}'")
            else:
                # Create new file with these classes
                content = [f'"""\n{module_path}\n"""\n\n']
                content.append("# ============================================================")
                content.append("# AUTO-GENERATED (AUTO-DISTRIBUTED)")
                content.append("# ============================================================\n\n")
                for cls_name in extra_classes:
                    class_body = self.analyzer.get_class_body(cls_name)
                    if class_body:
                        content.append(class_body)
                        content.append("\n\n")
                file_path.write_text("\n".join(content), encoding='utf-8')
                self.created_files.append(str(file_path))
        
        for module_path, extra_functions in self.auto_distributed["functions"].items():
            file_path = self.output_dir / module_path
            if file_path.exists():
                # Append to existing file
                with open(file_path, 'a', encoding='utf-8') as f:
                    f.write("\n\n# ========== Auto-Distributed Functions ==========\n\n")
                    for func_name in extra_functions:
                        func_body = self.analyzer.get_function_body(func_name)
                        if func_body:
                            f.write(func_body)
                            f.write("\n\n")
                        else:
                            self.errors.append(f"Could not extract auto-distributed function '{func_name}'")
            else:
                # Create new file with these functions
                content = [f'"""\n{module_path}\n"""\n\n']
                content.append("# ============================================================")
                content.append("# AUTO-GENERATED (AUTO-DISTRIBUTED)")
                content.append("# ============================================================\n\n")
                for func_name in extra_functions:
                    func_body = self.analyzer.get_function_body(func_name)
                    if func_body:
                        content.append(func_body)
                        content.append("\n\n")
                file_path.write_text("\n".join(content), encoding='utf-8')
                self.created_files.append(str(file_path))
        
        # Report missing items
        missing_classes = all_classes - classes_written
        missing_functions = all_functions - functions_written
        
        if missing_classes:
            print(f"\n   ⚠️ Classes still not assigned ({len(missing_classes)}):")
            for cls in sorted(missing_classes)[:10]:
                print(f"      - {cls}")
        
        if missing_functions:
            print(f"\n   ⚠️ Functions still not assigned ({len(missing_functions)}):")
            for func in sorted(missing_functions)[:20]:
                print(f"      - {func}")
        
        return True
    
    def _extract_constant(self, const_name: str) -> str:
        """Extract constant definition from source"""
        pattern = rf'^{const_name}\s*=\s*.+$'
        for line in self.analyzer.lines:
            if re.match(pattern, line.strip()):
                return line
        return f"{const_name} = None  # Value not extracted"
    
    def _generate_init_files(self):
        """Generate __init__.py files for all packages"""
        for init_path, exports in INIT_EXPORTS.items():
            file_path = self.output_dir / init_path
            parent_dir = file_path.parent
            parent_dir.mkdir(parents=True, exist_ok=True)
            
            content = []
            content.append('"""')
            content.append(f'{init_path} - Package initialization')
            content.append('"""')
            content.append("")
            content.append("# ============================================================")
            content.append("# AUTO-GENERATED BY MEF SCRIPT SPLITTER")
            content.append("# ============================================================\n")
            
            if exports:
                content.append(f"__all__ = {exports}\n")
            
            # Determine the correct import path
            if init_path == "__init__.py":
                # Root level - import directly from modules
                for export in exports:
                    content.append(f"from . import {export}")
            else:
                # Subpackage
                package_name = Path(init_path).stem
                for export in exports:
                    content.append(f"from .{package_name} import {export}")
            
            # Add version for main __init__.py
            if init_path == "__init__.py":
                content.append("")
                content.append('__version__ = "3.0.0"')
            
            file_path.write_text("\n".join(content), encoding='utf-8')
            self.created_files.append(str(file_path))
    
    def _create_requirements(self):
        """Create requirements.txt file"""
        requirements = """numpy>=1.19.0
pillow>=8.0.0
pygltflib>=1.16.0
PyQt5>=5.15.0
"""
        file_path = self.output_dir / "requirements.txt"
        file_path.write_text(requirements, encoding='utf-8')
        self.created_files.append(str(file_path))

# =============================================================================
# Verification Function
# =============================================================================
def verify_split(output_dir: Path) -> bool:
    """Verify that the split was successful by checking file integrity"""
    print("\n" + "=" * 80)
    print("🔍 VERIFYING SPLIT INTEGRITY")
    print("=" * 80)

    # Check all expected files exist
    expected_files = list(MODULE_STRUCTURE.keys()) + list(INIT_EXPORTS.keys()) + ["requirements.txt", "README.md"]
    expected_files = [f for f in expected_files if f] # Remove empty strings

    missing_files = []
    for expected in expected_files:
        if not (output_dir / expected).exists():
            missing_files.append(expected)

    if missing_files:
        print(f"\n⚠️ Missing files ({len(missing_files)}):")
        for f in missing_files[:20]:
            print(f" - {f}")
    else:
        print("\n✅ All expected files created!")

    # Check file sizes
    total_size = 0
    for py_file in output_dir.rglob("*.py"):
        size = py_file.stat().st_size
        total_size += size
        if size == 0:
            print(f" ⚠️ Empty file: {py_file}")

    print(f"\n📊 Total Python code size: {total_size:,} bytes")

    return len(missing_files) == 0

# =============================================================================
# Main Execution
# =============================================================================
def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Split massive MEF script into organized modules")
    parser.add_argument("--input", "-i", default=INPUT_SCRIPT, help="Input script path")
    parser.add_argument("--output", "-o", default=OUTPUT_DIR, help="Output directory")
    parser.add_argument("--verify", "-v", action="store_true", help="Verify split after completion")

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"❌ Input file not found: {args.input}")
        return 1

    splitter = SmartSplitter(args.input, args.output)
    success = splitter.run()

    if success and args.verify:
        verify_split(Path(args.output))

    return 0 if success else 1

if __name__ == "__main__":
    exit(main())