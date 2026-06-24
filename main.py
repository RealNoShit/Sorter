import os
import shutil
import json
import subprocess
import re
from pathlib import Path

import customtkinter as ctk
from tkinter import filedialog, messagebox, simpledialog
from PIL import Image


SETTINGS_FILE = Path("settings.json")

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class DownloadSorter:
    def __init__(self, root):
        self.root = root
        self.root.title("Downloads Sorter")
        self.root.geometry("1300x750")

        self.source_folder = None
        self.files = []
        self.current_index = 0
        self.last_move = None
        self.last_destination = None
        self.favorite_folders = []
        self.preview_size = 330

        self.active_series_prefix = None
        self.active_series_number = None

        self.load_settings()

        self.extensions = {
            ".png": ctk.BooleanVar(value=True),
            ".jpg": ctk.BooleanVar(value=True),
            ".jpeg": ctk.BooleanVar(value=True),
            ".mp4": ctk.BooleanVar(value=True),
            ".pdf": ctk.BooleanVar(value=False),
            ".zip": ctk.BooleanVar(value=False),
        }

        self.root.bind("<Return>", self.enter_pressed)
        self.build_ui()
        self.refresh_favorites()

    def build_ui(self):
        self.sidebar = ctk.CTkFrame(self.root, width=220)
        self.sidebar.pack(side="left", fill="y", padx=10, pady=10)

        self.main = ctk.CTkFrame(self.root)
        self.main.pack(side="left", fill="both", expand=True, padx=5, pady=10)

        self.folder_panel = ctk.CTkFrame(self.root, width=340)
        self.folder_panel.pack(side="right", fill="y", padx=10, pady=10)

        ctk.CTkLabel(self.sidebar, text="Downloads Sorter", font=("Arial", 22, "bold")).pack(pady=20)

        ctk.CTkButton(self.sidebar, text="Select Source Folder", command=self.select_folder).pack(fill="x", padx=15)

        self.folder_label = ctk.CTkLabel(self.sidebar, text="No folder selected", wraplength=190)
        self.folder_label.pack(padx=15, pady=15)

        ctk.CTkLabel(self.sidebar, text="File Types", font=("Arial", 16, "bold")).pack(pady=(25, 8))

        for ext, var in self.extensions.items():
            ctk.CTkCheckBox(self.sidebar, text=ext.upper(), variable=var).pack(anchor="w", padx=30, pady=4)

        ctk.CTkButton(self.sidebar, text="Start / Resume", command=self.start_process).pack(fill="x", padx=15, pady=25)

        self.stats_label = ctk.CTkLabel(self.sidebar, text="No session started")
        self.stats_label.pack(pady=10)

        ctk.CTkLabel(self.sidebar, text="Preview Size", font=("Arial", 14, "bold")).pack(pady=(25, 5))

        self.preview_slider = ctk.CTkSlider(
            self.sidebar,
            from_=200,
            to=520,
            command=self.change_preview_size
        )
        self.preview_slider.set(self.preview_size)
        self.preview_slider.pack(fill="x", padx=20, pady=5)

        self.preview_size_label = ctk.CTkLabel(self.sidebar, text=f"{self.preview_size}px")
        self.preview_size_label.pack()

        ctk.CTkLabel(self.main, text="Current File", font=("Arial", 24, "bold")).pack(pady=(20, 5))

        self.count_label = ctk.CTkLabel(self.main, text="No file loaded", font=("Arial", 15))
        self.count_label.pack(pady=5)

        self.preview_label = ctk.CTkLabel(
            self.main,
            text="Preview will appear here",
            width=650,
            height=self.preview_size
        )
        self.preview_label.pack(padx=25, pady=15)

        self.name_entry = ctk.CTkEntry(self.main, height=42, font=("Arial", 16))
        self.name_entry.pack(fill="x", padx=40, pady=10)

        self.extension_label = ctk.CTkLabel(self.main, text="")
        self.extension_label.pack()

        self.path_label = ctk.CTkLabel(self.main, text="", wraplength=700)
        self.path_label.pack(pady=5)

        self.last_folder_label = ctk.CTkLabel(self.main, text="Last folder: none")
        self.last_folder_label.pack(pady=5)

        ctk.CTkButton(self.main, text="Open File", height=40, command=self.open_current_file).pack(fill="x", padx=40, pady=10)

        row = ctk.CTkFrame(self.main)
        row.pack(fill="x", padx=40, pady=10)

        ctk.CTkButton(row, text="Move To Folder", command=self.move_to_folder).pack(side="left", expand=True, fill="x", padx=5)
        ctk.CTkButton(row, text="Create Folder + Move", command=self.create_folder_and_move).pack(side="left", expand=True, fill="x", padx=5)

        row2 = ctk.CTkFrame(self.main)
        row2.pack(fill="x", padx=40, pady=10)

        ctk.CTkButton(row2, text="Skip", command=self.skip_file).pack(side="left", expand=True, fill="x", padx=5)
        ctk.CTkButton(row2, text="Undo", command=self.undo_last_move).pack(side="left", expand=True, fill="x", padx=5)

        ctk.CTkLabel(
            self.main,
            text="Tip: type a new name, then press ENTER to move to the last used folder.",
            text_color="gray"
        ).pack(pady=10)

        ctk.CTkLabel(self.folder_panel, text="Favorite Folders", font=("Arial", 20, "bold")).pack(pady=20)

        ctk.CTkButton(self.folder_panel, text="+ Add Favorite Folder", command=self.add_favorite_folder).pack(fill="x", padx=15, pady=8)

        self.favorites_frame = ctk.CTkScrollableFrame(self.folder_panel)
        self.favorites_frame.pack(fill="both", expand=True, padx=15, pady=15)

        ctk.CTkButton(
        self.folder_panel,
        text="Auto Sort A-Z",
        command=self.auto_sort_favorites


).pack(fill="x", padx=15, pady=8)

    def load_settings(self):
        if not SETTINGS_FILE.exists():
            return

        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)

            self.favorite_folders = [Path(folder) for folder in data.get("favorites", [])]

            last_destination = data.get("last_destination")
            if last_destination:
                self.last_destination = Path(last_destination)

            self.preview_size = data.get("preview_size", self.preview_size)

        except Exception as error:
            print(f"Could not load settings: {error}")

    def save_settings(self):
        try:
            data = {
                "favorites": [str(folder) for folder in self.favorite_folders],
                "last_destination": str(self.last_destination) if self.last_destination else None,
                "preview_size": self.preview_size
            }

            with open(SETTINGS_FILE, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4)

        except Exception as error:
            print(f"Could not save settings: {error}")

    def select_folder(self):
        folder = filedialog.askdirectory(title="Select Downloads Folder")

        if folder:
            self.source_folder = Path(folder)
            self.folder_label.configure(text=str(self.source_folder))

    def start_process(self):
        if not self.source_folder:
            messagebox.showerror("Error", "Select a folder first.")
            return

        selected_extensions = {ext for ext, var in self.extensions.items() if var.get()}

        self.files = [
            file
            for file in self.source_folder.iterdir()
            if file.is_file() and file.suffix.lower() in selected_extensions
        ]

        self.files.sort(key=lambda file: file.stat().st_mtime)
        self.current_index = 0

        if not self.files:
            messagebox.showinfo("Done", "No matching files found.")
            return

        self.show_current_file()

    def show_current_file(self):
        if self.current_index >= len(self.files):
            self.count_label.configure(text="Done! No more files.")
            self.name_entry.delete(0, "end")
            self.preview_label.configure(text="Finished", image=None)
            self.stats_label.configure(text="Finished")
            return

        current = self.files[self.current_index]

        self.count_label.configure(text=f"{self.current_index + 1} of {len(self.files)}")
        self.path_label.configure(text=str(current))
        self.extension_label.configure(text=f"Extension: {current.suffix}")
        self.stats_label.configure(text=f"Remaining: {len(self.files) - self.current_index}")

        self.name_entry.delete(0, "end")

        if self.active_series_prefix and self.active_series_number and self.last_destination:
            suggested_name, suggested_number = self.get_next_available_series_name(
                self.last_destination,
                self.active_series_prefix,
                self.active_series_number,
                current.suffix
            )

            self.name_entry.insert(0, suggested_name)
            self.active_series_number = suggested_number
        else:
            self.name_entry.insert(0, current.stem)

        self.load_preview(current)
        self.root.after(100, self.focus_name_box)

    def focus_name_box(self):
        self.name_entry.focus_set()
        self.name_entry.select_range(0, "end")

    def change_preview_size(self, value):
        self.preview_size = int(value)
        self.preview_size_label.configure(text=f"{self.preview_size}px")
        self.preview_label.configure(height=self.preview_size)

        if self.files and self.current_index < len(self.files):
            self.load_preview(self.files[self.current_index])

        self.save_settings()

    
    def load_preview(self, file):
        extension = file.suffix.lower()

        # Clear old preview first
        self.preview_label.configure(image=None, text="")
        self.preview_label.image = None

        if extension in [".png", ".jpg", ".jpeg"]:
            try:
                image = Image.open(file)
                image.thumbnail((700, self.preview_size))

                preview = ctk.CTkImage(
                    light_image=image,
                    dark_image=image,
                    size=image.size
                )

                self.preview_label.configure(image=preview, text="")
                self.preview_label.image = preview

            except Exception as error:
                self.preview_label.configure(
                    image=None,
                    text=f"Could not load image preview.\n{error}"
                )
                self.preview_label.image = None
        else:
            self.preview_label.configure(
                image=None,
                text=f"No preview for {extension.upper()}\nUse Open File."
            )
            self.preview_label.image = None

    def parse_series_name(self, name):
        match = re.fullmatch(r"([a-zA-Z]+)(\d+)", name)

        if not match:
               return None, None

        prefix = match.group(1)
        number = int(match.group(2))

        return prefix, number


    def get_next_available_series_name(self, folder, prefix, start_number, suffix):
        number = start_number

        while True:
           candidate = f"{prefix}{number}"
           target = Path(folder) / f"{candidate}{suffix}"

           if not target.exists():
               return candidate, number

           number += 1

    def open_current_file(self):
        if self.current_index >= len(self.files):
            return

        file = self.files[self.current_index]

        try:
            if os.name == "nt":
                os.startfile(file)
            else:
                opener = "open" if os.uname().sysname == "Darwin" else "xdg-open"
                subprocess.call([opener, file])
        except Exception as error:
            messagebox.showerror("Error", f"Could not open file:\n{error}")

    def enter_pressed(self, event=None):
        if self.last_destination:
            self.rename_and_move_current_file(self.last_destination)
        else:
            messagebox.showinfo(
                "No last folder",
                "Move one file manually first. Then ENTER will reuse that folder."
            )

    def move_to_folder(self):
        destination = filedialog.askdirectory(title="Choose Destination Folder")

        if destination:
            self.rename_and_move_current_file(Path(destination))

    def create_folder_and_move(self):
        parent = filedialog.askdirectory(title="Choose Parent Folder")

        if not parent:
            return

        folder_name = simpledialog.askstring("New Folder", "Folder name:")

        if not folder_name:
            return

        destination = Path(parent) / folder_name
        destination.mkdir(exist_ok=True)

        self.rename_and_move_current_file(destination)

    def rename_and_move_current_file(self, destination):
        if self.current_index >= len(self.files):
            return

        current = self.files[self.current_index]
        new_stem = self.name_entry.get().strip()

        if not new_stem:
            messagebox.showerror("Error", "Filename cannot be empty.")
            return

        new_name = new_stem + current.suffix
        target = destination / new_name

        if target.exists():
            prefix, number = self.parse_series_name(new_stem)

            if prefix and number:
                suggested_name, suggested_number = self.get_next_available_series_name(
                    destination,
                    prefix,
                    number + 1,
                    current.suffix
                )

                self.name_entry.delete(0, "end")
                self.name_entry.insert(0, suggested_name)
                self.active_series_prefix = prefix
                self.active_series_number = suggested_number

                messagebox.showerror(
                    "Name already used",
                    f"{new_name} already exists.\nSuggested next name: {suggested_name}{current.suffix}"
                )
                return

            messagebox.showerror("Error", "A file with that name already exists.")
            return

        try:
            shutil.move(str(current), str(target))

            self.last_move = (target, current)
            self.last_destination = destination

            self.last_folder_label.configure(text=f"Last folder: {destination.name}")

            self.add_favorite_if_missing(destination)
            self.save_settings()

            prefix, number = self.parse_series_name(new_stem)

            if prefix and number:
                self.active_series_prefix = prefix
                self.active_series_number = number + 1

            self.current_index += 1
            self.show_current_file()

        except Exception as error:
            messagebox.showerror("Error", f"Could not move file:\n{error}")

    def skip_file(self):
        self.current_index += 1
        self.show_current_file()

    def undo_last_move(self):
        if not self.last_move:
            messagebox.showinfo("Undo", "Nothing to undo.")
            return

        moved_file, original_file = self.last_move

        try:
            shutil.move(str(moved_file), str(original_file))

            self.current_index = max(0, self.current_index - 1)
            self.last_move = None

            self.show_current_file()

        except Exception as error:
            messagebox.showerror("Error", f"Could not undo:\n{error}")

    def add_favorite_folder(self):
        folder = filedialog.askdirectory(title="Add Favorite Folder")

        if folder:
            self.add_favorite_if_missing(Path(folder))
            self.save_settings()

    def add_favorite_if_missing(self, folder):
        folder = Path(folder)

        if folder not in self.favorite_folders:
            self.favorite_folders.append(folder)
            self.refresh_favorites()
            self.save_settings()

    def remove_favorite_folder(self, folder):
        folder = Path(folder)

        if folder in self.favorite_folders:
            self.favorite_folders.remove(folder)
            self.refresh_favorites()
            self.save_settings()

    def move_favorite_up(self, folder):
        folder = Path(folder)

        if folder not in self.favorite_folders:
            return

        index = self.favorite_folders.index(folder)

        if index > 0:
            self.favorite_folders[index], self.favorite_folders[index - 1] = (
                self.favorite_folders[index - 1],
                self.favorite_folders[index],
            )
            self.refresh_favorites()
            self.save_settings()

    def move_favorite_down(self, folder):
        folder = Path(folder)

        if folder not in self.favorite_folders:
            return

        index = self.favorite_folders.index(folder)

        if index < len(self.favorite_folders) - 1:
            self.favorite_folders[index], self.favorite_folders[index + 1] = (
                self.favorite_folders[index + 1],
                self.favorite_folders[index],
            )
            self.refresh_favorites()
            self.save_settings()

    def refresh_favorites(self):
        for widget in self.favorites_frame.winfo_children():
            widget.destroy()

        for folder in self.favorite_folders:
            row = ctk.CTkFrame(self.favorites_frame)
            row.pack(fill="x", pady=6)

            up_button = ctk.CTkButton(
                row,
                text="↑",
                width=28,
                height=40,
                command=lambda selected_folder=folder: self.move_favorite_up(selected_folder)
            )

            down_button = ctk.CTkButton(
                row,
                text="↓",
                width=28,
                height=40,
                command=lambda selected_folder=folder: self.move_favorite_down(selected_folder)
            )

            delete_button = ctk.CTkButton(
                row,
                text="X",
                width=35,
                height=40,
                fg_color="darkred",
                hover_color="red",
                command=lambda selected_folder=folder: self.remove_favorite_folder(selected_folder)
            )

            move_button = ctk.CTkButton(
                row,
                text=folder.name,
                height=40,
                command=lambda selected_folder=folder: self.rename_and_move_current_file(selected_folder)
            )

            up_button.pack(side="left")
            down_button.pack(side="left")

            delete_button.pack(side="right")

            move_button.pack(
                side="left",
                fill="x",
                expand=True,
                padx=4
            )

    def auto_sort_favorites(self):
        self.favorite_folders.sort(
             key=lambda folder: folder.name.casefold()
            )
        self.refresh_favorites()
        self.save_settings()


if __name__ == "__main__":
    app = ctk.CTk()
    DownloadSorter(app)
    app.mainloop()
