import tkinter as tk
from tkinter import ttk, messagebox
from database import register_user


class RegisterPage:
    def __init__(self, parent, register_callback, show_login_callback):
        self.parent = parent
        self.register_callback = register_callback
        self.show_login_callback = show_login_callback

        self.create_widgets()

    def create_widgets(self):
        # Create main frame
        self.frame = ttk.Frame(self.parent, padding="20")
        self.frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Title
        title_label = ttk.Label(
            self.frame,
            text="Register New Account",
            font=('Helvetica', 24, 'bold')
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=20)

        # Username
        ttk.Label(self.frame, text="Username:").grid(row=1, column=0, pady=5, sticky='e')
        self.username_var = tk.StringVar()
        self.username_entry = ttk.Entry(self.frame, textvariable=self.username_var)
        self.username_entry.grid(row=1, column=1, pady=5, padx=5, sticky='w')

        # Password
        ttk.Label(self.frame, text="Password:").grid(row=2, column=0, pady=5, sticky='e')
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(
            self.frame,
            textvariable=self.password_var,
            show="*"
        )
        self.password_entry.grid(row=2, column=1, pady=5, padx=5, sticky='w')

        # Confirm Password
        ttk.Label(self.frame, text="Confirm Password:").grid(row=3, column=0, pady=5, sticky='e')
        self.confirm_password_var = tk.StringVar()
        self.confirm_password_entry = ttk.Entry(
            self.frame,
            textvariable=self.confirm_password_var,
            show="*"
        )
        self.confirm_password_entry.grid(row=3, column=1, pady=5, padx=5, sticky='w')

        # Full Name
        ttk.Label(self.frame, text="Full Name:").grid(row=4, column=0, pady=5, sticky='e')
        self.full_name_var = tk.StringVar()
        self.full_name_entry = ttk.Entry(self.frame, textvariable=self.full_name_var)
        self.full_name_entry.grid(row=4, column=1, pady=5, padx=5, sticky='w')

        # User Type
        ttk.Label(self.frame, text="User Type:").grid(row=5, column=0, pady=5, sticky='e')
        self.user_type_var = tk.StringVar(value="USER")
        user_type_frame = ttk.Frame(self.frame)
        user_type_frame.grid(row=5, column=1, pady=5, sticky='w')

        ttk.Radiobutton(
            user_type_frame,
            text="User",
            variable=self.user_type_var,
            value="USER"
        ).pack(side=tk.LEFT, padx=5)

        ttk.Radiobutton(
            user_type_frame,
            text="Provider",
            variable=self.user_type_var,
            value="PROVIDER"
        ).pack(side=tk.LEFT, padx=5)

        # Register Button
        register_button = ttk.Button(
            self.frame,
            text="Register",
            command=self.register
        )
        register_button.grid(row=6, column=0, columnspan=2, pady=20)

        # Login Link
        login_link = ttk.Button(
            self.frame,
            text="Already have an account? Login here",
            command=self.show_login_callback,
            style='Link.TButton'
        )
        login_link.grid(row=7, column=0, columnspan=2)

        # Center the frame
        self.parent.grid_rowconfigure(0, weight=1)
        self.parent.grid_columnconfigure(0, weight=1)

    def register(self):
        # Get all values
        username = self.username_var.get().strip()
        password = self.password_var.get()
        confirm_password = self.confirm_password_var.get()
        full_name = self.full_name_var.get().strip()
        user_type = self.user_type_var.get()

        # Validate inputs
        if not all([username, password, confirm_password, full_name]):
            messagebox.showerror("Error", "All fields are required")
            return

        if password != confirm_password:
            messagebox.showerror("Error", "Passwords do not match")
            return

        if len(password) < 6:
            messagebox.showerror("Error", "Password must be at least 6 characters long")
            return

        if len(username) < 4:
            messagebox.showerror("Error", "Username must be at least 4 characters long")
            return

        # Try to register
        success = register_user(username, password, full_name, user_type)

        if success:
            self.clear_fields()

        self.register_callback(success)

    def clear_fields(self):
        """Clear all input fields"""
        self.username_var.set("")
        self.password_var.set("")
        self.confirm_password_var.set("")
        self.full_name_var.set("")
        self.user_type_var.set("USER")
