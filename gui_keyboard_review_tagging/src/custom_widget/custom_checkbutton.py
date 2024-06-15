import tkinter as tk
from tkinter import ttk

class CustomCheckbutton(ttk.Checkbutton):
    def __init__(self, master=None, **kwargs):
        self.var = tk.BooleanVar()
        super().__init__(master, variable=self.var, **kwargs)

    def get(self):
        return self.var.get()

    def set(self, value):
        self.var.set(value)