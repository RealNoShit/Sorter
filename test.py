import customtkinter as ctk

app = ctk.CTk()
app.geometry("400x300")
app.title("Test")

label = ctk.CTkLabel(app, text="CustomTkinter works!")
label.pack(pady=50)

app.mainloop()