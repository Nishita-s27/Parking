import tkinter as tk
from tkinter import ttk
from database import verify_user


class LoginPage:
    def __init__(self, parent, login_callback, register_callback):
        self.parent = parent
        self.login_callback = login_callback
        self.register_callback = register_callback

        self.create_widgets()

    def create_widgets(self):
        # Create main frame
        self.frame = ttk.Frame(self.parent, padding="20")
        self.frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Title
        title_label = ttk.Label(
            self.frame,
            text="Parking Management System",
            font=('Helvetica', 24, 'bold')
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=20)

        # Username
        ttk.Label(self.frame, text="Username:").grid(row=1, column=0, pady=5)
        self.username_var = tk.StringVar()
        self.username_entry = ttk.Entry(self.frame, textvariable=self.username_var)
        self.username_entry.grid(row=1, column=1, pady=5)

        # Password
        ttk.Label(self.frame, text="Password:").grid(row=2, column=0, pady=5)
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(
            self.frame,
            textvariable=self.password_var,
            show="*"
        )
        self.password_entry.grid(row=2, column=1, pady=5)

        # Login button
        login_button = ttk.Button(
            self.frame,
            text="Login",
            command=self.login
        )
        login_button.grid(row=3, column=0, columnspan=2, pady=20)

        # Register link
        register_link = ttk.Button(
            self.frame,
            text="New user? Register here",
            command=self.register_callback,
            style='Link.TButton'
        )
        register_link.grid(row=4, column=0, columnspan=2)

    def login(self):
        username = self.username_var.get()
        password = self.password_var.get()

        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return

        user_data = verify_user(username, password)
        self.login_callback(user_data)
