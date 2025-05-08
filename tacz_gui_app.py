import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import os
import json
from gunpack_parser import GunpackParser 

class TaczGunpackViewerApp:
    def __init__(self, root_window):
        self.root = root_window
        self.root.title("TACZ Gunpack Viewer")
        self.root.geometry("1200x600")

        self.parser = None
        self.gunpack_path_var = tk.StringVar()

        top_frame = ttk.Frame(self.root, padding="10")
        top_frame.pack(fill=tk.X)

        ttk.Label(top_frame, text="Gunpack Path:").pack(side=tk.LEFT, padx=(0, 5))
        self.path_entry = ttk.Entry(top_frame, textvariable=self.gunpack_path_var, width=60)
        self.path_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        self.browse_button = ttk.Button(top_frame, text="Browse...", command=self.browse_gunpack)
        self.browse_button.pack(side=tk.LEFT, padx=5)
        self.load_button = ttk.Button(top_frame, text="Load Pack", command=self.load_gunpack)
        self.load_button.pack(side=tk.LEFT)

        main_paned_window = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned_window.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        weapons_frame = ttk.Labelframe(main_paned_window, text="Weapons", padding="5")
        main_paned_window.add(weapons_frame, weight=1)

        self.weapons_listbox = tk.Listbox(weapons_frame, exportselection=False)
        self.weapons_listbox.pack(expand=True, fill=tk.BOTH)
        self.weapons_listbox.bind("<<ListboxSelect>>", self.on_weapon_select)
        
        assets_frame = ttk.Labelframe(main_paned_window, text="Weapon Assets", padding="5")
        main_paned_window.add(assets_frame, weight=3)

        self.assets_tree = ttk.Treeview(assets_frame, columns=("path",), show="tree headings")
        self.assets_tree.heading("#0", text="Asset Type / File")
        self.assets_tree.heading("path", text="Full Path")
        self.assets_tree.column("path", width=300, stretch=tk.YES)
        self.assets_tree.pack(expand=True, fill=tk.BOTH)
        self.assets_tree.bind("<Double-1>", self.on_asset_double_click)
        
        self.status_var = tk.StringVar()
        self.status_var.set("Ready. Please select a gunpack.")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, padding="2")
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def browse_gunpack(self):
        path = filedialog.askdirectory(title="Select Gunpack Folder")
        if not path:
            path = filedialog.askopenfilename(
                title="Select Gunpack ZIP File",
                filetypes=(("ZIP files", "*.zip"), ("All files", "*.*"))
            )
        if path:
            self.gunpack_path_var.set(path)
            self.status_var.set(f"Selected: {path}. Click 'Load Pack'.")

    def load_gunpack(self):
        pack_path = self.gunpack_path_var.get()
        if not pack_path:
            messagebox.showerror("Error", "Please select a gunpack path first.")
            return

        self.status_var.set(f"Loading gunpack: {pack_path}...")
        self.root.update_idletasks() 

        if self.parser:
            self.parser.cleanup() 
        
        try:
            self.parser = GunpackParser(pack_path)
            weapons_data = self.parser.get_weapons_data()
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load or parse gunpack: {e}")
            self.status_var.set("Error loading gunpack.")
            if self.parser: self.parser.cleanup()
            self.parser = None
            return

        self.weapons_listbox.delete(0, tk.END)
        self.assets_tree.delete(*self.assets_tree.get_children())

        if not self.parser.namespace:
            messagebox.showerror("Load Error", "Could not determine gunpack namespace. The pack might be invalid or not structured as expected.")
            self.status_var.set("Failed to determine namespace.")
            self.parser.cleanup()
            self.parser = None
            return

        if weapons_data:
            for weapon_id in sorted(weapons_data.keys()):
                self.weapons_listbox.insert(tk.END, weapon_id)
            self.status_var.set(f"Loaded {len(weapons_data)} weapons from namespace '{self.parser.namespace}'. Select a weapon.")
        else:
            self.status_var.set("No weapons found in the gunpack or error during parsing.")
            messagebox.showinfo("Info", "No weapons found in the specified gunpack or an error occurred during parsing.")

    def on_weapon_select(self, event):
        selection = event.widget.curselection()
        if not selection:
            return
        
        weapon_id_index = selection[0]
        weapon_id = event.widget.get(weapon_id_index)
        self.status_var.set(f"Displaying assets for: {weapon_id}")

        self.assets_tree.delete(*self.assets_tree.get_children())

        if self.parser and weapon_id in self.parser.weapons_data:
            weapon_info = self.parser.weapons_data[weapon_id]
            assets = weapon_info.get("assets", {})
            
            for asset_key, asset_paths in sorted(assets.items()):
                category_node = self.assets_tree.insert("", tk.END, text=asset_key.replace("_", " ").title(), open=True, values=("N/A",))
                
                if isinstance(asset_paths, list):
                    for path in asset_paths:
                        file_name = os.path.basename(path)
                        self.assets_tree.insert(category_node, tk.END, text=file_name, values=(path,))
                elif isinstance(asset_paths, str): # Single path
                    file_name = os.path.basename(asset_paths)
                    self.assets_tree.insert(category_node, tk.END, text=file_name, values=(asset_paths,))
        else:
            self.status_var.set(f"No asset data found for {weapon_id}")

    def on_asset_double_click(self, event):
        item_id = self.assets_tree.focus() 
        if not item_id:
            return
        
        item_values = self.assets_tree.item(item_id, "values")
        if item_values and len(item_values) > 0:
            file_path = item_values[0]
            if file_path and file_path != "N/A" and os.path.exists(file_path):
                try:
                    self.status_var.set(f"Attempting to open: {file_path}")
                    GunpackParser.open_file_externally(file_path)
                except Exception as e:
                    messagebox.showerror("Error Opening File", f"Could not open file {file_path}:\n{e}")
                    self.status_var.set(f"Error opening {file_path}")
            elif file_path == "N/A":
                pass 
            else:
                messagebox.showwarning("File Not Found", f"The file does not exist or path is invalid:\n{file_path}")
                self.status_var.set(f"File not found: {file_path}")

    def on_closing(self):
        if self.parser:
            self.parser.cleanup()
        self.root.destroy()

if __name__ == "__main__":
    app_root = tk.Tk()
    app = TaczGunpackViewerApp(app_root)
    app_root.protocol("WM_DELETE_WINDOW", app.on_closing) 
    app_root.mainloop()

