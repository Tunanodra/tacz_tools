import tkinter as tk
from tkinter import filedialog, ttk, messagebox, simpledialog
import os
import json
import shutil # For cleaning up test directories

from gunpack_parser import GunpackParser # For opening files externally
from gunpack_generator import (
    create_tacz_gunpack_structure,
    add_new_weapon_files,
    add_new_ammo_files,
    add_new_attachment_files
)
# Assuming tacz_utils.py is in the same directory or PYTHONPATH
# If not, the function needs to be copied or path adjusted.
try:
    from tacz_utils import is_valid_tacz_namespace
except ImportError:
    # Fallback if tacz_utils.py is not directly importable (e.g. during packaging)
    # This is a simplified version for direct inclusion.
    import re
    def is_valid_tacz_namespace(namespace_str):
        if not namespace_str:
            return False, "Namespace cannot be empty."
        if not re.match("^[a-z0-9_]+$", namespace_str):
            return False, ("Namespace contains invalid characters. "
                          "Only lowercase English letters, numbers, and underscores are allowed.")
        return True, "Namespace is valid."

class TaczGunpackToolApp:
    def __init__(self, root_window):
        self.root = root_window
        self.root.title("TACZ Gunpack Tool")
        self.root.geometry("900x700")

        self.parser = None
        self.gunpack_path_var = tk.StringVar()
        
        # Variables for the creator tab
        self.creator_project_name_var = tk.StringVar()
        self.creator_namespace_var = tk.StringVar()
        self.creator_base_dir_var = tk.StringVar()
        self.created_gunpack_root_path = None # Store path of newly created gunpack
        self.created_gunpack_namespace = None

        # Main notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

        # --- Viewer Tab --- 
        self.viewer_tab = ttk.Frame(self.notebook, padding="5")
        self.notebook.add(self.viewer_tab, text="Gunpack Viewer")
        self.setup_viewer_tab()

        # --- Creator Tab --- 
        self.creator_tab = ttk.Frame(self.notebook, padding="5")
        self.notebook.add(self.creator_tab, text="Create New Gunpack")
        self.setup_creator_tab()
        
        # Status Bar (shared or individual? For now, one main status bar)
        self.status_var = tk.StringVar()
        self.status_var.set("Ready. Select a tab and proceed.")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, padding="2")
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    # --- VIEWER TAB SETUP AND LOGIC --- #
    def setup_viewer_tab(self):
        top_frame = ttk.Frame(self.viewer_tab, padding="5")
        top_frame.pack(fill=tk.X)

        ttk.Label(top_frame, text="Gunpack Path:").pack(side=tk.LEFT, padx=(0, 5))
        self.viewer_path_entry = ttk.Entry(top_frame, textvariable=self.gunpack_path_var, width=60)
        self.viewer_path_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        self.viewer_browse_button = ttk.Button(top_frame, text="Browse...", command=self.browse_gunpack_for_viewer)
        self.viewer_browse_button.pack(side=tk.LEFT, padx=5)
        self.viewer_load_button = ttk.Button(top_frame, text="Load Pack", command=self.load_gunpack_for_viewer)
        self.viewer_load_button.pack(side=tk.LEFT)

        main_paned_window = ttk.PanedWindow(self.viewer_tab, orient=tk.HORIZONTAL)
        main_paned_window.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

        weapons_frame = ttk.Labelframe(main_paned_window, text="Weapons", padding="5")
        main_paned_window.add(weapons_frame, weight=1)
        self.weapons_listbox = tk.Listbox(weapons_frame, exportselection=False)
        self.weapons_listbox.pack(expand=True, fill=tk.BOTH)
        self.weapons_listbox.bind("<<ListboxSelect>>", self.on_weapon_select_viewer)
        
        assets_frame = ttk.Labelframe(main_paned_window, text="Weapon Assets (Viewer)", padding="5")
        main_paned_window.add(assets_frame, weight=3)
        self.assets_tree_viewer = ttk.Treeview(assets_frame, columns=("path",), show="tree headings")
        self.assets_tree_viewer.heading("#0", text="Asset Type / File")
        self.assets_tree_viewer.heading("path", text="Full Path")
        self.assets_tree_viewer.column("path", width=300, stretch=tk.YES)
        self.assets_tree_viewer.pack(expand=True, fill=tk.BOTH)
        self.assets_tree_viewer.bind("<Double-1>", lambda e: self.on_asset_double_click(self.assets_tree_viewer))

    def browse_gunpack_for_viewer(self):
        path = filedialog.askdirectory(title="Select Gunpack Folder")
        if not path:
            path = filedialog.askopenfilename(title="Select Gunpack ZIP File", filetypes=(("ZIP files", "*.zip"), ("All files", "*.*")))
        if path:
            self.gunpack_path_var.set(path)
            self.status_var.set(f"Viewer: Selected {path}. Click \'Load Pack\'.")

    def load_gunpack_for_viewer(self):
        pack_path = self.gunpack_path_var.get()
        if not pack_path:
            messagebox.showerror("Error", "Viewer: Please select a gunpack path first.")
            return
        self.status_var.set(f"Viewer: Loading gunpack: {pack_path}...") ; self.root.update_idletasks()
        if self.parser: self.parser.cleanup()
        try:
            self.parser = GunpackParser(pack_path)
            weapons_data = self.parser.get_weapons_data()
        except Exception as e:
            messagebox.showerror("Load Error", f"Viewer: Failed to load/parse: {e}")
            self.status_var.set("Viewer: Error loading gunpack.")
            if self.parser: self.parser.cleanup() ; self.parser = None
            return
        self.weapons_listbox.delete(0, tk.END)
        self.assets_tree_viewer.delete(*self.assets_tree_viewer.get_children())
        if not self.parser.namespace:
            messagebox.showerror("Load Error", "Viewer: Could not determine namespace.")
            self.status_var.set("Viewer: Failed to determine namespace.")
            if self.parser: self.parser.cleanup(); self.parser = None
            return
        if weapons_data:
            for weapon_id in sorted(weapons_data.keys()): self.weapons_listbox.insert(tk.END, weapon_id)
            self.status_var.set(f"Viewer: Loaded {len(weapons_data)} weapons from 	'{self.parser.namespace}	'.")
        else:
            self.status_var.set("Viewer: No weapons found or error parsing.")
            messagebox.showinfo("Info", "Viewer: No weapons found.")

    def on_weapon_select_viewer(self, event):
        selection = event.widget.curselection()
        if not selection: return
        weapon_id = event.widget.get(selection[0])
        self.status_var.set(f"Viewer: Displaying assets for: {weapon_id}")
        self.assets_tree_viewer.delete(*self.assets_tree_viewer.get_children())
        if self.parser and weapon_id in self.parser.weapons_data:
            assets = self.parser.weapons_data[weapon_id].get("assets", {})
            for asset_key, asset_paths in sorted(assets.items()):
                cat_node = self.assets_tree_viewer.insert("", tk.END, text=asset_key.replace("_", " ").title(), open=True, values=("N/A",))
                if isinstance(asset_paths, list):
                    for p in asset_paths: self.assets_tree_viewer.insert(cat_node, tk.END, text=os.path.basename(p), values=(p,))
                elif isinstance(asset_paths, str):
                    self.assets_tree_viewer.insert(cat_node, tk.END, text=os.path.basename(asset_paths), values=(asset_paths,))
        else: self.status_var.set(f"Viewer: No asset data for {weapon_id}")

    # --- CREATOR TAB SETUP AND LOGIC --- #
    def setup_creator_tab(self):
        # Initialization Frame
        init_frame = ttk.Labelframe(self.creator_tab, text="1. Initialize Gunpack", padding="10")
        init_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(init_frame, text="Project Name:").grid(row=0, column=0, sticky=tk.W, padx=2, pady=2)
        self.creator_project_name_entry = ttk.Entry(init_frame, textvariable=self.creator_project_name_var, width=40)
        self.creator_project_name_entry.grid(row=0, column=1, sticky=tk.EW, padx=2, pady=2)

        ttk.Label(init_frame, text="Namespace:").grid(row=1, column=0, sticky=tk.W, padx=2, pady=2)
        self.creator_namespace_entry = ttk.Entry(init_frame, textvariable=self.creator_namespace_var, width=40)
        self.creator_namespace_entry.grid(row=1, column=1, sticky=tk.EW, padx=2, pady=2)

        ttk.Label(init_frame, text="Create In (Base Dir):").grid(row=2, column=0, sticky=tk.W, padx=2, pady=2)
        self.creator_base_dir_entry = ttk.Entry(init_frame, textvariable=self.creator_base_dir_var, width=40, state="readonly")
        self.creator_base_dir_entry.grid(row=2, column=1, sticky=tk.EW, padx=2, pady=2)
        self.creator_browse_base_dir_button = ttk.Button(init_frame, text="Browse...", command=self.browse_creator_base_dir)
        self.creator_browse_base_dir_button.grid(row=2, column=2, padx=5, pady=2)

        self.create_structure_button = ttk.Button(init_frame, text="Create Gunpack Structure", command=self.execute_create_gunpack_structure)
        self.create_structure_button.grid(row=3, column=0, columnspan=3, pady=10)
        init_frame.columnconfigure(1, weight=1)

        # Structure Management & Guidance Frame (Paned Window)
        manage_paned = ttk.PanedWindow(self.creator_tab, orient=tk.HORIZONTAL)
        manage_paned.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

        # Directory Tree View Frame
        tree_frame = ttk.Labelframe(manage_paned, text="2. Gunpack Structure", padding="5")
        manage_paned.add(tree_frame, weight=2)
        self.creator_dir_tree = ttk.Treeview(tree_frame, columns=("fullpath",), show="tree headings")
        self.creator_dir_tree.heading("#0", text="File/Folder")
        self.creator_dir_tree.heading("fullpath", text="Full Path (hidden)")
        self.creator_dir_tree.column("fullpath", width=0, stretch=tk.NO, anchor="w") # Hide fullpath column visually
        self.creator_dir_tree.pack(expand=True, fill=tk.BOTH)
        self.creator_dir_tree.bind("<Double-1>", lambda e: self.on_creator_tree_double_click(self.creator_dir_tree))

        # Guided Actions Frame
        guided_actions_frame = ttk.Labelframe(manage_paned, text="3. Guided Actions", padding="10")
        manage_paned.add(guided_actions_frame, weight=1)

        ttk.Button(guided_actions_frame, text="Edit gunpack_info.json", command=self.edit_gunpack_info).pack(fill=tk.X, pady=3)
        ttk.Separator(guided_actions_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        
        ttk.Label(guided_actions_frame, text="Add New Weapon:").pack(anchor=tk.W)
        self.creator_weapon_id_var = tk.StringVar()
        weapon_id_entry = ttk.Entry(guided_actions_frame, textvariable=self.creator_weapon_id_var)
        weapon_id_entry.pack(fill=tk.X, pady=(0,3))
        ttk.Button(guided_actions_frame, text="Add Weapon Files", command=self.add_weapon_from_creator).pack(fill=tk.X, pady=3)
        ttk.Separator(guided_actions_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)

        ttk.Label(guided_actions_frame, text="Add New Ammo:").pack(anchor=tk.W)
        self.creator_ammo_id_var = tk.StringVar()
        ammo_id_entry = ttk.Entry(guided_actions_frame, textvariable=self.creator_ammo_id_var)
        ammo_id_entry.pack(fill=tk.X, pady=(0,3))
        ttk.Button(guided_actions_frame, text="Add Ammo Files", command=self.add_ammo_from_creator).pack(fill=tk.X, pady=3)
        ttk.Separator(guided_actions_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)

        ttk.Label(guided_actions_frame, text="Add New Attachment:").pack(anchor=tk.W)
        self.creator_attachment_id_var = tk.StringVar()
        attachment_id_entry = ttk.Entry(guided_actions_frame, textvariable=self.creator_attachment_id_var)
        attachment_id_entry.pack(fill=tk.X, pady=(0,3))
        ttk.Button(guided_actions_frame, text="Add Attachment Files", command=self.add_attachment_from_creator).pack(fill=tk.X, pady=3)
        
        self.toggle_creator_actions_panel(False) # Initially disabled

    def toggle_creator_actions_panel(self, enable=True):
        state = tk.NORMAL if enable else tk.DISABLED
        for child in self.creator_tab.winfo_children():
            if isinstance(child, ttk.PanedWindow):
                for pane_child in child.winfo_children():
                    if pane_child.cget("text") == "3. Guided Actions": # Fragile, better to store ref
                        for action_widget in pane_child.winfo_children():
                            try: action_widget.config(state=state)
                            except: pass # Labels etc.
                        break
                break

    def browse_creator_base_dir(self):
        path = filedialog.askdirectory(title="Select Base Directory for New Gunpack")
        if path:
            self.creator_base_dir_var.set(path)
            self.status_var.set(f"Creator: Base directory set to {path}")

    def execute_create_gunpack_structure(self):
        project_name = self.creator_project_name_var.get().strip()
        namespace = self.creator_namespace_var.get().strip()
        base_dir = self.creator_base_dir_var.get().strip()

        if not all([project_name, namespace, base_dir]):
            messagebox.showerror("Input Error", "Project Name, Namespace, and Base Directory are required.")
            return
        
        is_valid, msg = is_valid_tacz_namespace(namespace)
        if not is_valid:
            messagebox.showerror("Namespace Error", msg)
            return

        try:
            self.created_gunpack_root_path = create_tacz_gunpack_structure(base_dir, project_name, namespace)
            self.created_gunpack_namespace = namespace # Store for later use
            self.status_var.set(f"Creator: Gunpack 	'{project_name}	' created at {self.created_gunpack_root_path}")
            messagebox.showinfo("Success", f"Gunpack structure for 	'{project_name}	' created successfully!")
            self.populate_creator_dir_tree(self.created_gunpack_root_path)
            self.toggle_creator_actions_panel(True)
        except Exception as e:
            messagebox.showerror("Creation Error", f"Failed to create gunpack structure: {e}")
            self.status_var.set(f"Creator: Error creating structure: {e}")
            self.toggle_creator_actions_panel(False)
            self.created_gunpack_root_path = None
            self.created_gunpack_namespace = None

    def populate_creator_dir_tree(self, root_path):
        self.creator_dir_tree.delete(*self.creator_dir_tree.get_children())
        self._add_to_tree(self.creator_dir_tree, "", root_path, root_path)

    def _add_to_tree(self, tree_widget, parent_node_id, current_path, root_display_path):
        for item in sorted(os.listdir(current_path)):
            item_full_path = os.path.join(current_path, item)
            # Display relative path for root, then just item name
            display_name = os.path.relpath(item_full_path, os.path.dirname(root_display_path)) if parent_node_id == "" else item
            node_id = tree_widget.insert(parent_node_id, tk.END, text=display_name, values=(item_full_path,), open=(parent_node_id==""))
            if os.path.isdir(item_full_path):
                self._add_to_tree(tree_widget, node_id, item_full_path, root_display_path)

    def on_creator_tree_double_click(self, tree_widget):
        item_id = tree_widget.focus()
        if not item_id: return
        item_values = tree_widget.item(item_id, "values")
        if item_values and len(item_values) > 0:
            file_path = item_values[0]
            if file_path and os.path.exists(file_path):
                if os.path.isfile(file_path):
                    self.open_file_external_handler(file_path, "Creator")
                elif os.path.isdir(file_path):
                    # Open directory in system file explorer
                    try:
                        if hasattr(os, 'startfile'): # Windows
                            os.startfile(file_path)
                        elif sys.platform == 'darwin': # macOS
                            subprocess.Popen(['open', file_path])
                        else: # Linux
                            subprocess.Popen(['xdg-open', file_path])
                        self.status_var.set(f"Creator: Opened directory {file_path}")
                    except Exception as e:
                        messagebox.showerror("Error", f"Could not open directory {file_path}: {e}")
                        self.status_var.set(f"Creator: Error opening directory {file_path}")

    def _handle_add_item(self, item_type_str, id_var, add_function):
        if not self.created_gunpack_root_path or not self.created_gunpack_namespace:
            messagebox.showerror("Error", f"Please create a gunpack structure first before adding a {item_type_str.lower()}.")
            return
        item_id = id_var.get().strip()
        if not item_id:
            messagebox.showerror("Input Error", f"{item_type_str} ID cannot be empty.")
            return
        
        is_valid_id, msg = is_valid_tacz_namespace(item_id) # Use same validation for IDs
        if not is_valid_id:
            messagebox.showerror(f"{item_type_str} ID Error", msg)
            return

        try:
            success, message = add_function(self.created_gunpack_root_path, self.created_gunpack_namespace, item_id)
            if success:
                self.status_var.set(f"Creator: {message}")
                messagebox.showinfo("Success", message)
                self.populate_creator_dir_tree(self.created_gunpack_root_path) # Refresh tree
                id_var.set("") # Clear input
            else:
                messagebox.showerror("Error", message)
                self.status_var.set(f"Creator: Error adding {item_type_str.lower()}: {message}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add {item_type_str.lower()} files: {e}")
            self.status_var.set(f"Creator: Exception adding {item_type_str.lower()}: {e}")

    def add_weapon_from_creator(self):
        self._handle_add_item("Weapon", self.creator_weapon_id_var, add_new_weapon_files)

    def add_ammo_from_creator(self):
        self._handle_add_item("Ammo", self.creator_ammo_id_var, add_new_ammo_files)

    def add_attachment_from_creator(self):
        self._handle_add_item("Attachment", self.creator_attachment_id_var, add_new_attachment_files)

    def edit_gunpack_info(self):
        if not self.created_gunpack_root_path or not self.created_gunpack_namespace:
            messagebox.showerror("Error", "Please create a gunpack structure first.")
            return
        file_path = os.path.join(self.created_gunpack_root_path, f"assets/{self.created_gunpack_namespace}/gunpack_info.json")
        if os.path.exists(file_path):
            self.open_file_external_handler(file_path, "Creator")
        else:
            messagebox.showerror("Error", f"gunpack_info.json not found at {file_path}. Try creating structure again.")

    # --- COMMON UTILITY METHODS --- #
    def on_asset_double_click(self, tree_widget):
        item_id = tree_widget.focus()
        if not item_id: return
        item_values = tree_widget.item(item_id, "values")
        if item_values and len(item_values) > 0:
            file_path = item_values[0]
            if file_path and file_path != "N/A" and os.path.exists(file_path) and os.path.isfile(file_path):
                self.open_file_external_handler(file_path, "Viewer")
            elif file_path == "N/A": pass # Category node
            else: messagebox.showwarning("File Error", f"File does not exist or path invalid: {file_path}")

    def open_file_external_handler(self, file_path, tab_name="Application"):
        try:
            self.status_var.set(f"{tab_name}: Attempting to open: {file_path}")
            GunpackParser.open_file_externally(file_path) # Use static method
        except Exception as e:
            messagebox.showerror("Error Opening File", f"Could not open file {file_path}:\n{e}")
            self.status_var.set(f"{tab_name}: Error opening {file_path}")

    def on_closing(self):
        if self.parser:
            self.parser.cleanup()
        # Clean up test directories if they exist from gunpack_generator.py's __main__
        test_gen_output_dir = "/home/ubuntu/tacz_gui_project/test_generator_output"
        if os.path.exists(test_gen_output_dir):
            try: shutil.rmtree(test_gen_output_dir)
            except Exception as e: print(f"Note: Could not clean up test dir {test_gen_output_dir}: {e}")
        self.root.destroy()

if __name__ == "__main__":
    app_root = tk.Tk()
    app = TaczGunpackToolApp(app_root)
    app_root.protocol("WM_DELETE_WINDOW", app.on_closing)
    app_root.mainloop()

