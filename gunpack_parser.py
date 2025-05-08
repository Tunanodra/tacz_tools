import os
import json
import zipfile
import tempfile
import shutil
import glob
import subprocess
import sys

class GunpackParser:
    def __init__(self, gunpack_path):
        self.gunpack_path = os.path.abspath(gunpack_path)
        self.temp_dir = None
        self.pack_root = None
        self.namespace = None
        self.weapons_data = {}

        self._prepare_gunpack()
        if self.pack_root:
            self._determine_namespace()
            if self.namespace:
                self._find_weapons_and_assets()

    def _prepare_gunpack(self):
        if not os.path.exists(self.gunpack_path):
            print(f"Error: Gunpack path does not exist: {self.gunpack_path}")
            return

        if zipfile.is_zipfile(self.gunpack_path):
            self.temp_dir = tempfile.mkdtemp(prefix="tacz_gui_")
            try:
                with zipfile.ZipFile(self.gunpack_path, 'r') as zip_ref:
                    zip_infos = zip_ref.infolist()
                    if not zip_infos:
                        print("Error: Zip file is empty.")
                        return
                    
                    first_level_dirs = set()
                    for member in zip_infos:
                        parts = member.filename.split('/')
                        if len(parts) > 1:
                            first_level_dirs.add(parts[0])
                    
                    if len(first_level_dirs) == 1:
                        zip_ref.extractall(self.temp_dir)
                        self.pack_root = os.path.join(self.temp_dir, list(first_level_dirs)[0])
                        print(f"Extracted zip to temp directory: {self.pack_root}")
                    else:
                        zip_name_no_ext = os.path.splitext(os.path.basename(self.gunpack_path))[0]
                        extract_target_dir = os.path.join(self.temp_dir, zip_name_no_ext)
                        zip_ref.extractall(extract_target_dir)
                        self.pack_root = extract_target_dir
                        print(f"Extracted zip (no single root) to temp directory: {self.pack_root}")

            except Exception as e:
                print(f"Error extracting zip file: {e}")
                self.cleanup()
                return
        elif os.path.isdir(self.gunpack_path):
            self.pack_root = self.gunpack_path
            print(f"Using directory as gunpack root: {self.pack_root}")
        else:
            print(f"Error: Gunpack path is not a valid zip file or directory: {self.gunpack_path}")

    def _determine_namespace(self):
        if not self.pack_root:
            return
        # 尝试搜索命名空间内文件夹
        for base_folder in ["assets", "data"]:
            base_path = os.path.join(self.pack_root, base_folder)
            if os.path.isdir(base_path):
                subdirs = [d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))]
                if subdirs:
                    self.namespace = subdirs[0]
                    print(f"Determined namespace: {self.namespace}")
                    return
        meta_path = os.path.join(self.pack_root, "gunpack.meta.json")
        if os.path.exists(meta_path):
            try:
                with open(meta_path, 'r') as f:
                    meta_data = json.load(f)
                    if "namespace" in meta_data:
                        self.namespace = meta_data["namespace"]
                        print(f"Determined namespace from gunpack.meta.json: {self.namespace}")
                        return
            except Exception as e:
                print(f"Error reading gunpack.meta.json: {e}")
        
        if not self.namespace:
            print("Error: Could not determine namespace.")

    def _find_weapons_and_assets(self):
        if not self.namespace or not self.pack_root:
            return

        index_guns_path = os.path.join(self.pack_root, "data", self.namespace, "index", "guns")
        if not os.path.isdir(index_guns_path):
            print(f"Error: Gun index directory not found: {index_guns_path}")
            return

        for weapon_file in os.listdir(index_guns_path):
            if weapon_file.endswith(".json"):
                weapon_id = weapon_file[:-5] # Remove .json
                self.weapons_data[weapon_id] = {"id": weapon_id, "assets": {}}
                self._collect_assets_for_weapon(weapon_id)
        print(f"Found {len(self.weapons_data)} weapons.")

    def _get_asset_path(self, category_path_template, weapon_id, file_pattern_template, is_dir=False):
        """Helper to get asset paths, supporting wildcards in file_pattern_template."""
        base_asset_path = category_path_template.replace("[namespace]", self.namespace).replace("[weapon_id]", weapon_id)
        full_category_path = os.path.join(self.pack_root, base_asset_path)
        
        assets_found = []
        if os.path.isdir(full_category_path):
            if is_dir:
                assets_found.append(full_category_path)
            else:
                file_pattern = file_pattern_template.replace("[weapon_id]", weapon_id)
                for f_path in glob.glob(os.path.join(full_category_path, file_pattern)):
                    if os.path.isfile(f_path):
                         assets_found.append(f_path)
        elif os.path.isfile(full_category_path) and not is_dir: 
             assets_found.append(full_category_path)
        return assets_found

    def _collect_assets_for_weapon(self, weapon_id):
        assets = {}
        asset_map = {
            "index_file": ("data/[namespace]/index/guns", "[weapon_id].json"),
            "data_file": ("data/[namespace]/data/guns", "[weapon_id].json"),
            "model_main": ("assets/[namespace]/geo_models/gun", "[weapon_id].geo.json"), # Assuming .geo.json
            "model_lod": ("assets/[namespace]/geo_models/gun/lod", "[weapon_id]_lod*.geo.json"),
            "texture_uv": ("assets/[namespace]/textures/gun/uv", "[weapon_id].png"),
            "texture_hud": ("assets/[namespace]/textures/gun/hud", "[weapon_id]*.png"), # More flexible pattern
            "texture_slot": ("assets/[namespace]/textures/gun/slot", "[weapon_id]*.png"),
            "texture_lod": ("assets/[namespace]/textures/gun/lod", "[weapon_id]_lod*.png"),
            "display_json": ("assets/[namespace]/display/guns", "[weapon_id]_display.json"),
            "animation_bedrock": ("assets/[namespace]/animations", "[weapon_id].animation.json"),
            "animation_gltf": ("assets/[namespace]/animations", "[weapon_id].gltf"),
            "sounds_dir": ("assets/[namespace]/tacz_sounds/[weapon_id]", "*", True), # True indicates it's a directory
            "recipe_gun": ("data/[namespace]/recipes/gun", "[weapon_id].json"),
            "tags_allow_attachments": ("data/[namespace]/tacz_tags/attachments/allow_attachments", "[weapon_id].json"),
            "script_lua": ("data/[namespace]/scripts", f"{weapon_id}_gun_logic.lua") 
        }

        for key, (path_template, file_pattern, *is_dir_flag) in asset_map.items():
            is_dir = is_dir_flag[0] if is_dir_flag else False
            found_paths = self._get_asset_path(path_template, weapon_id, file_pattern, is_dir)
            if found_paths:
                assets[key] = found_paths if len(found_paths) > 1 or is_dir else found_paths[0]
        
        self.weapons_data[weapon_id]["assets"] = assets

    def get_weapons_data(self):
        return self.weapons_data

    def cleanup(self):
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
                print(f"Cleaned up temp directory: {self.temp_dir}")
            except Exception as e:
                print(f"Error cleaning up temp directory {self.temp_dir}: {e}")
        self.temp_dir = None
        self.pack_root = None

    @staticmethod
    def open_file_externally(file_path):
        try:
            if sys.platform == "win32":
                os.startfile(file_path)
            elif sys.platform == "darwin": # macOS
                subprocess.Popen(["open", file_path])
            else: # linux
                subprocess.Popen(["xdg-open", file_path])
            print(f"Attempting to open file: {file_path}")
        except Exception as e:
            print(f"Error opening file {file_path}: {e}")

if __name__ == "__main__":
    test_pack_path = "test_gun_pack"
    if os.path.exists(test_pack_path):
        shutil.rmtree(test_pack_path)
    os.makedirs(os.path.join(test_pack_path, "assets/testns/geo_models/gun"), exist_ok=True)
    os.makedirs(os.path.join(test_pack_path, "assets/testns/textures/gun/uv"), exist_ok=True)
    os.makedirs(os.path.join(test_pack_path, "assets/testns/tacz_sounds/testgun1"), exist_ok=True)
    os.makedirs(os.path.join(test_pack_path, "data/testns/index/guns"), exist_ok=True)
    os.makedirs(os.path.join(test_pack_path, "data/testns/data/guns"), exist_ok=True)

    with open(os.path.join(test_pack_path, "data/testns/index/guns/testgun1.json"), 'w') as f: json.dump({"id": "testgun1"}, f)
    with open(os.path.join(test_pack_path, "data/testns/data/guns/testgun1.json"), 'w') as f: json.dump({"damage": 10}, f)
    with open(os.path.join(test_pack_path, "assets/testns/geo_models/gun/testgun1.geo.json"), 'w') as f: json.dump({}, f)
    with open(os.path.join(test_pack_path, "assets/testns/textures/gun/uv/testgun1.png"), 'w') as f: f.write("dummy png content")
    with open(os.path.join(test_pack_path, "assets/testns/tacz_sounds/testgun1/fire.ogg"), 'w') as f: f.write("dummy ogg content")
    
    print("--- Testing with dummy folder pack ---")
    parser_folder = GunpackParser(test_pack_path)
    data_folder = parser_folder.get_weapons_data()
    print(json.dumps(data_folder, indent=2))
    parser_folder.cleanup()

    zip_example_path = "your example gunpack zip file"
    if os.path.exists(zip_example_path):
        print("\n--- Testing with user example gunpack ---")
        parser_zip = GunpackParser(zip_example_path)
        data_zip = parser_zip.get_weapons_data()
        if "ak47" in data_zip:
            print("AK47 data found:")
            print(json.dumps(data_zip["ak47"], indent=2))
        else:
            print("AK47 not found in parsed zip data.")
        parser_zip.cleanup()
    else:
        print(f"\nSkipping zip test: {zip_example_path} not found.")

