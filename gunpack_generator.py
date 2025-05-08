import os
import json

# --- Core Structure Generation (adapted from previous create_gunpack_structure.py) --- #

def create_tacz_gunpack_structure(base_dir, gunpack_root_name, namespace):
    """Creates the TACZ gunpack directory structure and a minimal gunpack_info.json."""
    root_path = os.path.join(base_dir, gunpack_root_name)

    paths = [
        f"assets/{namespace}/animations",
        f"assets/{namespace}/display/ammo",
        f"assets/{namespace}/display/attachments",
        f"assets/{namespace}/display/blocks",
        f"assets/{namespace}/display/guns",
        f"assets/{namespace}/geo_models/ammo",
        f"assets/{namespace}/geo_models/ammo_entity",
        f"assets/{namespace}/geo_models/attachment/lod",
        f"assets/{namespace}/geo_models/block",
        f"assets/{namespace}/geo_models/gun/lod",
        f"assets/{namespace}/geo_models/shell",
        f"assets/{namespace}/lang",
        f"assets/{namespace}/player_animator",
        f"assets/{namespace}/scripts",
        f"assets/{namespace}/tacz_sounds", # Sounds per weapon will be subdirs here
        f"assets/{namespace}/textures/ammo/slot",
        f"assets/{namespace}/textures/ammo/uv",
        f"assets/{namespace}/textures/ammo_entity",
        f"assets/{namespace}/textures/attachment/lod",
        f"assets/{namespace}/textures/attachment/slot",
        f"assets/{namespace}/textures/attachment/uv",
        f"assets/{namespace}/textures/block/uv",
        f"assets/{namespace}/textures/crosshair",
        f"assets/{namespace}/textures/flash",
        f"assets/{namespace}/textures/gun/hud",
        f"assets/{namespace}/textures/gun/lod",
        f"assets/{namespace}/textures/gun/slot",
        f"assets/{namespace}/textures/gun/uv",
        f"assets/{namespace}/textures/shell",
        f"data/{namespace}/data/attachments",
        f"data/{namespace}/data/blocks",
        f"data/{namespace}/data/guns",
        f"data/{namespace}/index/ammo",
        f"data/{namespace}/index/attachments",
        f"data/{namespace}/index/blocks",
        f"data/{namespace}/index/guns",
        f"data/{namespace}/recipes/ammo",
        f"data/{namespace}/recipes/attachments",
        f"data/{namespace}/recipes/gun",
        f"data/{namespace}/recipe_filters",
        f"data/{namespace}/scripts",
        f"data/{namespace}/tacz_tags/attachments/allow_attachments",
    ]

    if not os.path.exists(root_path):
        os.makedirs(root_path)
    
    for path_suffix in paths:
        full_path = os.path.join(root_path, path_suffix)
        os.makedirs(full_path, exist_ok=True)

    # Create minimal gunpack_info.json
    gunpack_info_path = os.path.join(root_path, f"assets/{namespace}/gunpack_info.json")
    if not os.path.exists(gunpack_info_path):
        gunpack_info_content = {
            "pack_format": 1, # Check TACZ wiki for current pack_format for 1.1.4
            "name": gunpack_root_name,
            "author": "YourName",
            "description": "A new TACZ gunpack created with the viewer tool.",
            "namespace": namespace 
        }
        with open(gunpack_info_path, 'w') as f:
            json.dump(gunpack_info_content, f, indent=4)
    
    return root_path

# --- Template File Creation --- #

def create_template_json(file_path, content):
    """Creates a JSON file with the given content if it doesn't exist."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            json.dump(content, f, indent=4)
        return True
    return False # File already existed

def add_new_weapon_files(gunpack_root_path, namespace, weapon_id):
    """Creates template JSON files for a new weapon."""
    if not weapon_id: return False, "Weapon ID cannot be empty."

    # Template content (minimal)
    index_content = {"id": f"{namespace}:{weapon_id}"}
    data_content = {
        "type": "rifle", # Example, user should change
        "ammunition": f"{namespace}:your_ammo_id",
        "rpm": 600,
        "damage": {"head": 20, "body": 10, "limb": 5},
        # Add other common fields as placeholders
    }
    display_content = {
        "model": f"tacz:{namespace}/{weapon_id}.geo.json",
        "texture": f"tacz:{namespace}/{weapon_id}.png",
        # Add other common display fields
    }

    base_paths = {
        "index": os.path.join(gunpack_root_path, f"data/{namespace}/index/guns/{weapon_id}.json"),
        "data": os.path.join(gunpack_root_path, f"data/{namespace}/data/guns/{weapon_id}.json"),
        "display": os.path.join(gunpack_root_path, f"assets/{namespace}/display/guns/{weapon_id}_display.json")
    }
    
    created_files = []
    if create_template_json(base_paths["index"], index_content): created_files.append(base_paths["index"])
    if create_template_json(base_paths["data"], data_content): created_files.append(base_paths["data"])
    if create_template_json(base_paths["display"], display_content): created_files.append(base_paths["display"])
    
    # Create sound directory
    sound_dir = os.path.join(gunpack_root_path, f"assets/{namespace}/tacz_sounds/{weapon_id}")
    os.makedirs(sound_dir, exist_ok=True)
    created_files.append(sound_dir + " (directory)")

    return True, f"Created template files/dirs for weapon 	'{weapon_id}	': {', '.join(created_files)}"

def add_new_ammo_files(gunpack_root_path, namespace, ammo_id):
    """Creates template JSON files for new ammo."""
    if not ammo_id: return False, "Ammo ID cannot be empty."

    index_content = {"id": f"{namespace}:{ammo_id}"}
    display_content = {"texture": f"tacz:{namespace}/{ammo_id}.png"}
    # Data for ammo is usually simpler or part of gun data, but an index is key.

    base_paths = {
        "index": os.path.join(gunpack_root_path, f"data/{namespace}/index/ammo/{ammo_id}.json"),
        "display": os.path.join(gunpack_root_path, f"assets/{namespace}/display/ammo/{ammo_id}_display.json")
    }

    created_files = []
    if create_template_json(base_paths["index"], index_content): created_files.append(base_paths["index"])
    if create_template_json(base_paths["display"], display_content): created_files.append(base_paths["display"])

    return True, f"Created template files for ammo 	'{ammo_id}	': {', '.join(created_files)}"

def add_new_attachment_files(gunpack_root_path, namespace, attachment_id):
    """Creates template JSON files for a new attachment."""
    if not attachment_id: return False, "Attachment ID cannot be empty."

    index_content = {"id": f"{namespace}:{attachment_id}"}
    data_content = {"type": "scope"} # Example
    display_content = {"model": f"tacz:{namespace}/{attachment_id}.geo.json"}

    base_paths = {
        "index": os.path.join(gunpack_root_path, f"data/{namespace}/index/attachments/{attachment_id}.json"),
        "data": os.path.join(gunpack_root_path, f"data/{namespace}/data/attachments/{attachment_id}.json"),
        "display": os.path.join(gunpack_root_path, f"assets/{namespace}/display/attachments/{attachment_id}_display.json")
    }

    created_files = []
    if create_template_json(base_paths["index"], index_content): created_files.append(base_paths["index"])
    if create_template_json(base_paths["data"], data_content): created_files.append(base_paths["data"])
    if create_template_json(base_paths["display"], display_content): created_files.append(base_paths["display"])

    return True, f"Created template files for attachment 	'{attachment_id}	': {', '.join(created_files)}"


if __name__ == "__main__":
    # Example Usage (for testing this module)
    test_base_dir = "/home/ubuntu/tacz_gui_project/test_generator_output"
    test_project_name = "my_new_gunpack"
    test_namespace = "mynewguns"

    import shutil
    if os.path.exists(os.path.join(test_base_dir, test_project_name)):
        shutil.rmtree(os.path.join(test_base_dir, test_project_name))
    os.makedirs(test_base_dir, exist_ok=True)

    print(f"Creating structure in: {os.path.join(test_base_dir, test_project_name)}")
    created_root = create_tacz_gunpack_structure(test_base_dir, test_project_name, test_namespace)
    print(f"Gunpack structure created at: {created_root}")

    if created_root:
        success, msg = add_new_weapon_files(created_root, test_namespace, "super_rifle")
        print(f"Add Weapon: {success} - {msg}")
        
        success, msg = add_new_weapon_files(created_root, test_namespace, "cool_pistol")
        print(f"Add Weapon: {success} - {msg}")

        success, msg = add_new_ammo_files(created_root, test_namespace, "super_ammo_762")
        print(f"Add Ammo: {success} - {msg}")

        success, msg = add_new_attachment_files(created_root, test_namespace, "holo_sight_mk1")
        print(f"Add Attachment: {success} - {msg}")

        print("\nListing created files for super_rifle:")
        for f_type in ["index", "data", "display"]:
            p = os.path.join(created_root, f"data/{test_namespace}/{'index' if f_type == 'index' else 'data'}/guns/super_rifle.json")
            if f_type == "display":
                 p = os.path.join(created_root, f"assets/{test_namespace}/display/guns/super_rifle_display.json")
            if os.path.exists(p):
                print(f"{f_type.upper()} file exists: {p}")
            else:
                print(f"{f_type.upper()} file MISSING: {p}")
        sound_p = os.path.join(created_root, f"assets/{test_namespace}/tacz_sounds/super_rifle")
        if os.path.isdir(sound_p):
            print(f"Sound directory exists: {sound_p}")
        else:
            print(f"Sound directory MISSING: {sound_p}")

    print("\nTest complete. Check the test_generator_output directory.")

