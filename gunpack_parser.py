# gunpack_parser.py
import os
import zipfile
import tempfile
import json
import shutil
import subprocess
import sys

# Ensure gunpack_generator is importable for testing incremental add
from gunpack_generator import add_new_weapon_files, add_new_ammo_files, add_new_attachment_files

class GunpackParser:
    def __init__(self, pack_path):
        self.pack_path = pack_path
        self.temp_dir_obj = None
        self.gunpack_root_dir = None
        self.namespace = None
        self.is_loaded_from_zip = False
        self.weapons_data = {}
        self.ammo_data = {}
        self.attachment_data = {}

        self._load_pack()

    def _find_gunpack_root_and_namespace(self, base_search_path):
        for root, dirs, files in os.walk(base_search_path):
            if "gunpack_info.json" in files:
                if os.path.basename(os.path.dirname(root)) == "assets":
                    self.namespace = os.path.basename(root)
                    potential_gunpack_root = os.path.abspath(os.path.join(root, "..", ".."))
                    
                    # Check if potential_gunpack_root is consistent with base_search_path
                    # This logic ensures that if base_search_path is already the gunpack root, it's used.
                    # Or if base_search_path is one level above (e.g. extracted zip root), it's also handled.
                    if os.path.abspath(base_search_path) == potential_gunpack_root or \
                       os.path.abspath(os.path.dirname(potential_gunpack_root)) == os.path.abspath(base_search_path) and os.path.basename(potential_gunpack_root) == os.listdir(base_search_path)[0] and len(os.listdir(base_search_path))==1 :
                         self.gunpack_root_dir = potential_gunpack_root
                    elif "assets" in os.listdir(base_search_path) and os.path.join(base_search_path, "assets", self.namespace) == root:
                         self.gunpack_root_dir = os.path.abspath(base_search_path)
                    else:
                        # If gunpack_info.json is found deeper, but doesn't align with base_search_path as root or parent-of-root
                        # it might be a nested pack or incorrect structure. For now, we prioritize alignment.
                        # This could be an area for more sophisticated root detection if needed.
                        print(f"Debug: gunpack_info.json found at {root}, but its derived root {potential_gunpack_root} does not align well with base_search_path {base_search_path}. Skipping this instance.")
                        self.namespace = None
                        self.gunpack_root_dir = None
                        continue

                    try:
                        with open(os.path.join(root, "gunpack_info.json"), 'r', encoding='utf-8') as f_info:
                            info_data = json.load(f_info)
                        if 'namespace' in info_data and info_data['namespace'] != self.namespace:
                            print(f"Warning: Namespace in gunpack_info.json (	'{info_data['namespace']}	') differs from directory structure (	'{self.namespace}	'). Using directory structure derived namespace: 	'{self.namespace}	'.")
                        return True
                    except Exception as e:
                        print(f"Warning: Could not parse gunpack_info.json at {os.path.join(root, 'gunpack_info.json')}: {e}")
                        self.namespace = None
                        self.gunpack_root_dir = None
                        continue
        return False

    def _load_pack(self):
        if os.path.isdir(self.pack_path):
            self.is_loaded_from_zip = False
            if not self._find_gunpack_root_and_namespace(self.pack_path):
                self.gunpack_root_dir = self.pack_path # Fallback, might not have namespace
                print(f"Warning: Could not reliably determine namespace from {self.pack_path} via gunpack_info.json. Operations requiring namespace may fail or be limited.")
        elif os.path.isfile(self.pack_path) and self.pack_path.endswith(".zip"):
            self.is_loaded_from_zip = True
            self.temp_dir_obj = tempfile.TemporaryDirectory(prefix="tacz_viewer_")
            extracted_zip_path = self.temp_dir_obj.name
            try:
                with zipfile.ZipFile(self.pack_path, 'r') as zip_ref:
                    zip_ref.extractall(extracted_zip_path)
                
                if not self._find_gunpack_root_and_namespace(extracted_zip_path):
                    extracted_items = os.listdir(extracted_zip_path)
                    if len(extracted_items) == 1 and os.path.isdir(os.path.join(extracted_zip_path, extracted_items[0])):
                        potential_root_in_zip = os.path.join(extracted_zip_path, extracted_items[0])
                        if not self._find_gunpack_root_and_namespace(potential_root_in_zip):
                            self.gunpack_root_dir = potential_root_in_zip
                            print(f"Warning: Found single folder in zip but could not determine namespace from {self.gunpack_root_dir} via gunpack_info.json.")
                    else:
                        self.gunpack_root_dir = extracted_zip_path
                        print(f"Warning: Could not determine namespace from extracted zip contents of {self.pack_path} via gunpack_info.json.")
            except Exception as e:
                self.cleanup()
                raise Exception(f"Failed to extract or process zip file: {e}")
        else:
            raise Exception(f"Invalid pack path: {self.pack_path}. Must be a directory or .zip file.")

        if self.gunpack_root_dir and self.namespace:
            self._parse_all_items()
        elif self.gunpack_root_dir:
            print(f"Warning: Gunpack root is 	'{self.gunpack_root_dir}	' but namespace could not be determined. Viewer and modification features will be limited.")
        else:
             raise Exception("Could not determine gunpack root directory. Cannot load pack.")

    def _parse_item_category(self, category_name, data_dict):
        if not self.gunpack_root_dir or not self.namespace: return
        
        index_dir = os.path.join(self.gunpack_root_dir, f"data/{self.namespace}/index/{category_name}")
        data_dir = os.path.join(self.gunpack_root_dir, f"data/{self.namespace}/data/{category_name}")
        display_dir = os.path.join(self.gunpack_root_dir, f"assets/{self.namespace}/display/{category_name}")
        geo_dir_name = 'gun' if category_name == 'guns' else category_name # Handle 'gun' vs 'guns'
        geo_dir = os.path.join(self.gunpack_root_dir, f"assets/{self.namespace}/geo_models/{geo_dir_name}")
        texture_dir_uv_name = 'gun' if category_name == 'guns' else category_name
        texture_dir_uv = os.path.join(self.gunpack_root_dir, f"assets/{self.namespace}/textures/{texture_dir_uv_name}/uv")
        texture_dir_slot = os.path.join(self.gunpack_root_dir, f"assets/{self.namespace}/textures/{texture_dir_uv_name}/slot")
        sound_base_dir = os.path.join(self.gunpack_root_dir, f"assets/{self.namespace}/tacz_sounds")

        if os.path.isdir(index_dir):
            for fname in os.listdir(index_dir):
                if fname.endswith(".json"):
                    item_id = fname[:-5]
                    item_assets = {"json_files": [], "model_files": [], "texture_files": [], "sound_files": []}
                    
                    for d, n_suffix in [(index_dir, ""), (data_dir, ""), (display_dir, "_display")]:
                        p = os.path.join(d, f"{item_id}{n_suffix}.json")
                        if os.path.isfile(p): item_assets["json_files"].append(p)
                    
                    if os.path.isdir(geo_dir):
                        for m_fname in os.listdir(geo_dir):
                            if item_id in m_fname and m_fname.endswith(".json"): 
                                item_assets["model_files"].append(os.path.join(geo_dir, m_fname))
                    
                    for tex_d in [texture_dir_uv, texture_dir_slot]:
                        if os.path.isdir(tex_d):
                            for t_fname in os.listdir(tex_d):
                                if item_id in t_fname and t_fname.endswith(".png"): 
                                    item_assets["texture_files"].append(os.path.join(tex_d, t_fname))
                    
                    if category_name == "guns":
                        s_dir = os.path.join(sound_base_dir, item_id)
                        if os.path.isdir(s_dir):
                            for sf in os.listdir(s_dir):
                                if sf.endswith(".ogg") or sf.endswith(".wav"): 
                                    item_assets["sound_files"].append(os.path.join(s_dir, sf))
                    
                    data_dict[item_id] = {"id": item_id, "assets": item_assets}

    def _parse_all_items(self):
        self._parse_item_category("guns", self.weapons_data)
        self._parse_item_category("ammo", self.ammo_data)
        self._parse_item_category("attachments", self.attachment_data)

    def get_weapons_data(self):
        return self.weapons_data

    def cleanup(self):
        if self.temp_dir_obj:
            try:
                self.temp_dir_obj.cleanup()
            except Exception as e:
                print(f"Error cleaning up temporary directory {self.temp_dir_obj.name}: {e}")
            self.temp_dir_obj = None
            
    @staticmethod
    def open_file_externally(file_path):
        try:
            if sys.platform == "win32":
                os.startfile(file_path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", file_path])
            else: 
                subprocess.Popen(["xdg-open", file_path])
        except Exception as e:
            print(f"Error opening file {file_path}: {e}")

if __name__ == "__main__":
    test_pack_dir = "/tmp/dummy_gunpack_parser_test"
    if os.path.exists(test_pack_dir): shutil.rmtree(test_pack_dir)
    
    dummy_namespace = "testns"
    # Create a structure that matches what _find_gunpack_root_and_namespace expects
    # i.e. test_pack_dir IS the gunpack root.
    os.makedirs(os.path.join(test_pack_dir, f"assets/{dummy_namespace}/textures/gun/uv"), exist_ok=True)
    os.makedirs(os.path.join(test_pack_dir, f"data/{dummy_namespace}/index/guns"), exist_ok=True)
    os.makedirs(os.path.join(test_pack_dir, f"data/{dummy_namespace}/data/guns"), exist_ok=True)
    os.makedirs(os.path.join(test_pack_dir, f"assets/{dummy_namespace}/display/guns"), exist_ok=True)
    os.makedirs(os.path.join(test_pack_dir, f"assets/{dummy_namespace}/geo_models/gun"), exist_ok=True)
    os.makedirs(os.path.join(test_pack_dir, f"assets/{dummy_namespace}/tacz_sounds/test_gun"), exist_ok=True)

    with open(os.path.join(test_pack_dir, f"assets/{dummy_namespace}/gunpack_info.json"), "w") as f:
        json.dump({"namespace": dummy_namespace, "pack_format": 1, "name": "Dummy Test Pack"}, f)
    with open(os.path.join(test_pack_dir, f"data/{dummy_namespace}/index/guns/test_gun.json"), "w") as f:
        json.dump({"id": f"{dummy_namespace}:test_gun"}, f)
    with open(os.path.join(test_pack_dir, f"assets/{dummy_namespace}/geo_models/gun/test_gun.geo.json"), "w") as f: json.dump({},f)
    with open(os.path.join(test_pack_dir, f"assets/{dummy_namespace}/textures/gun/uv/test_gun.png"), "w") as f: f.write("dummy png")
    with open(os.path.join(test_pack_dir, f"assets/{dummy_namespace}/tacz_sounds/test_gun/fire.ogg"), "w") as f: f.write("dummy ogg")

    print(f"--- Testing with folder: {test_pack_dir} ---")
    parser = None
    try:
        parser = GunpackParser(test_pack_dir)
        print(f"Detected Namespace: {parser.namespace}")
        print(f"Gunpack Root: {parser.gunpack_root_dir}")
        print(f"Is from ZIP: {parser.is_loaded_from_zip}")
        print(f"Weapons Data: {json.dumps(parser.get_weapons_data(), indent=2)}")

        # Test incremental add to this loaded pack (folder)
        if parser and parser.gunpack_root_dir and parser.namespace:
            print("\n--- Testing incremental add (to folder) ---")
            new_rifle_id = "added_rifle"
            success, msg = add_new_weapon_files(parser.gunpack_root_dir, parser.namespace, new_rifle_id)
            print(f"Add new weapon 	'{new_rifle_id}	': {success} - {msg}")
            expected_rifle_index_path = os.path.join(parser.gunpack_root_dir, f"data/{parser.namespace}/index/guns/{new_rifle_id}.json")
            if os.path.exists(expected_rifle_index_path):
                print(f"SUCCESS: New rifle index file created at: {expected_rifle_index_path}")
            else:
                print(f"FAILURE: New rifle index file NOT found at: {expected_rifle_index_path}")
        else:
            print("Skipping incremental add test (folder) due to parser init issues.")
    except Exception as e:
        print(f"Error during folder test: {e}")
    finally:
        if parser: parser.cleanup() # Though for folder, this does nothing to original files

    # Test with a ZIP file
    zip_path = "/tmp/dummy_gunpack_parser_test.zip"
    if os.path.exists(zip_path): os.remove(zip_path)
    shutil.make_archive(zip_path[:-4], 'zip', test_pack_dir) # Zip the dummy pack
    
    print(f"\n--- Testing with ZIP: {zip_path} ---")
    parser_zip = None
    try:
        parser_zip = GunpackParser(zip_path)
        print(f"Detected Namespace (zip): {parser_zip.namespace}")
        print(f"Gunpack Root (zip, temp): {parser_zip.gunpack_root_dir}")
        print(f"Is from ZIP (zip): {parser_zip.is_loaded_from_zip}")
        print(f"Weapons Data (zip): {json.dumps(parser_zip.get_weapons_data(), indent=2)}")

        # Test incremental add to this loaded pack (from ZIP, so to temp dir)
        if parser_zip and parser_zip.gunpack_root_dir and parser_zip.namespace:
            print("\n--- Testing incremental add (to temp dir from ZIP) ---")
            new_pistol_id = "added_pistol_temp"
            success, msg = add_new_weapon_files(parser_zip.gunpack_root_dir, parser_zip.namespace, new_pistol_id)
            print(f"Add new weapon 	'{new_pistol_id}	': {success} - {msg}")
            expected_pistol_index_path = os.path.join(parser_zip.gunpack_root_dir, f"data/{parser_zip.namespace}/index/guns/{new_pistol_id}.json")
            if os.path.exists(expected_pistol_index_path):
                print(f"SUCCESS: New pistol index file created in temp dir at: {expected_pistol_index_path}")
            else:
                print(f"FAILURE: New pistol index file NOT found in temp dir at: {expected_pistol_index_path}")
        else:
            print("Skipping incremental add test (zip) due to parser init issues.")
    except Exception as e:
        print(f"Error during zip test: {e}")
    finally:
        if parser_zip: parser_zip.cleanup() # This will delete the temp dir
    
    if os.path.exists(test_pack_dir): shutil.rmtree(test_pack_dir)
    if os.path.exists(zip_path): os.remove(zip_path)
    print("\nParser tests complete.")

