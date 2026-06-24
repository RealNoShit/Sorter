import os
import shutil
import subprocess
from pathlib import Path
import customtkinter as ctk
from tkinter import filedialog, messagebox, simpledialog


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class DownloadSorter:
    def __init__(self, root):
        self.root = root
        self.root.title("Downloads Sorter")
        self.root.geometry("1000x650")

        self.source_folder = None
        self.files = []
        self.current_index = 0
        self.last_move = None
        self.last_destination = None

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

    def build_ui(self):
        self.sidebar = ctk.CTkFrame(self.root, width=260)
        self.sidebar.pack(side="left", fill="y", padx=10, pady=10)

        self.main = ctk.CTkFrame(self.root)
        self.main.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(self.sidebar, text="Downloads Sorter", font=("Arial", 22, "bold")).pack(pady=20)

        ctk.CTkButton(self.sidebar, text="Select Source Folder", command=self.select_folder).pack(fill="x", padx=15, pady=8)

        self.folder_label = ctk.CTkLabel(self.sidebar, text="No folder selected", wraplength=220)
        self.folder_label.pack(padx=15, pady=8)

        ctk.CTkLabel(self.sidebar, text="File Types", font=("Arial", 16, "bold")).pack(pady=(25, 8))

        for ext, var in self.extensions.items():
            ctk.CTkCheckBox(self.sidebar, text=ext.upper(), variable=var).pack(anchor="w", padx=30, pady=4)

        ctk.CTkButton(self.sidebar, text="Start / Resume", command=self.start_process).pack(fill="x", padx=15, pady=25)

        self.stats_label = ctk.CTkLabel(self.sidebar, text="No session started")
        self.stats_label.pack(pady=10)

        ctk.CTkLabel(self.main, text="Current File", font=("Arial", 24, "bold")).pack(pady=(25, 10))

        self.file_label = ctk.CTkLabel(self.main, text="None", font=("Arial", 18))
        self.file_label.pack(pady=5)

        self.name_entry = ctk.CTkEntry(self.main, height=40, font=("Arial", 16))
        self.name_entry.pack(fill="x", padx=40, pady=10)

        self.path_label = ctk.CTkLabel(self.main, text="", wraplength=650)
        self.path_label.pack(pady=5)

        self.last_folder_label = ctk.CTkLabel(self.main, text="Last folder: none")
        self.last_folder_label.pack(pady=5)

        ctk.CTkButton(self.main, text="Open File", height=40, command=self.open_current_file).pack(fill="x", padx=40, pady=10)

        button_row = ctk.CTkFrame(self.main)
        button_row.pack(fill="x", padx=40, pady=15)

        ctk.CTkButton(button_row, text="Move To Folder", command=self.move_to_folder).pack(side="left", expand=True, fill="x", padx=5)
        ctk.CTkButton(button_row, text="Create Folder + Move", command=self.create_folder_and_move).pack(side="left", expand=True, fill="x", padx=5)

        bottom_row = ctk.CTkFrame(self.main)
        bottom_row.pack(fill="x", padx=40, pady=10)

        ctk.CTkButton(bottom_row, text="Skip", command=self.next_file).pack(side="left", expand=True, fill="x", padx=5)
        ctk.CTkButton(bottom_row, text="Undo", command=self.undo_last_move).pack(side="left", expand=True, fill="x", padx=5)

        ctk.CTkLabel(
            self.main,
            text="Tip: Rename the file, then press ENTER to move it to the last used folder.",
            text_color="gray"
        ).pack(pady=20)

    def select_folder(self):
        folder = filedialog.askdirectory(title="Select Downloads Folder")
        if folder:
            self.source_folder = Path(folder)
            self.folder_label.configure(text=str(self.source_folder))

    def start_process(self):
        if not self.source_folder:
            messagebox.showerror("Error", "Select a folder first.")
            return

        selected_exts = {ext for ext, var in self.extensions.items() if var.get()}

        self.files = [
            file for file in self.source_folder.iterdir()
            if file.is_file() and file.suffix.lower() in selected_exts
        ]

        self.files.sort(key=lambda file: file.stat().st_mtime)  # oldest first
        self.current_index = 0

        if not self.files:
            messagebox.showinfo("Done", "No matching files found.")
            return

        self.show_current_file()
        self.open_current_file()

    def show_current_file(self):
        if self.current_index >= len(self.files):
            self.file_label.configure(text="Done! No more files.")
            self.name_entry.delete(0, "end")
            self.path_label.configure(text="")
            self.stats_label.configure(text="Finished")
            return

        current = self.files[self.current_index]

        self.file_label.configure(text=f"{self.current_index + 1} of {len(self.files)}")
        self.path_label.configure(text=str(current))
        self.stats_label.configure(text=f"Remaining: {len(self.files) - self.current_index}")

        self.name_entry.delete(0, "end")
        self.name_entry.insert(0, current.name)

        self.root.after(100, self.focus_name_box)

    def focus_name_box(self):
        self.name_entry.focus_set()
        self.name_entry.select_range(0, "end")

    def open_current_file(self):
        if self.current_index >= len(self.files):
            return

        file = self.files[self.current_index]

        try:
            if os.name == "nt":
                os.startfile(file)
            elif os.name == "posix":
                opener = "open" if os.uname().sysname == "Darwin" else "xdg-open"
                subprocess.call([opener, file])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file:\n{e}")

    def enter_pressed(self, event=None):
        if self.last_destination:
            self.rename_and_move_current_file(self.last_destination)
        else:
            messagebox.showinfo("No last folder", "Move one file manually first. Then ENTER will reuse that folder.")

    def move_to_folder(self):
        if self.current_index >= len(self.files):
            return

        destination = filedialog.askdirectory(title="Choose Destination Folder")
        if destination:
            self.rename_and_move_current_file(Path(destination))

    def create_folder_and_move(self):
        if self.current_index >= len(self.files):
            return

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
        current = self.files[self.current_index]
        new_name = self.name_entry.get().strip()

        if not new_name:
            messagebox.showerror("Error", "Filename cannot be empty.")
            return

        if "." not in Path(new_name).name:
            new_name += current.suffix

        target = destination / new_name

        if target.exists():
            messagebox.showerror("Error", "A file with that name already exists in the destination.")
            return

        try:
            shutil.move(str(current), str(target))

            self.last_move = (target, current)
            self.last_destination = destination
            self.last_folder_label.configure(text=f"Last folder: {destination.name}")

            self.next_file()
            self.open_current_file()

        except Exception as e:
            messagebox.showerror("Error", f"Could not move file:\n{e}")

    def next_file(self):
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
        except Exception as e:
            messagebox.showerror("Error", f"Could not undo:\n{e}")


if __name__ == "__main__":
    app = ctk.CTk()
    DownloadSorter(app)
    app.mainloop()