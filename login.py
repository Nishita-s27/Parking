import tkinter as tk
from tkinter import ttk, messagebox
from database import create_db_connection
from provider_dashboard import ProviderDashboard
from user_dashboard import UserDashboard


class LoginScreen:
    def __init__(self, root):
        self.root = root
        self.root.title("Parking System - Login")
        self.root.geometry("400x300")
        self.setup_login_screen()

    def setup_login_screen(self):
        self.frame = ttk.Frame(self.root, padding="20")
        self.frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        ttk.Label(self.frame, text="Login", font=('Helvetica', 16, 'bold')).grid(row=0, column=0, columnspan=2, pady=20)

        ttk.Label(self.frame, text="Username:").grid(row=1, column=0, pady=5)
        self.username = ttk.Entry(self.frame)
        self.username.grid(row=1, column=1, pady=5)

        ttk.Label(self.frame, text="Password:").grid(row=2, column=0, pady=5)
        self.password = ttk.Entry(self.frame, show="*")
        self.password.grid(row=2, column=1, pady=5)

        ttk.Button(self.frame, text="Login", command=self.login).grid(row=3, column=0, columnspan=2, pady=10)
        ttk.Button(self.frame, text="Register", command=self.show_register).grid(row=4, column=0, columnspan=2)

    def login(self):
        username = self.username.get()
        password = self.password.get()

        conn = create_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone()

        if user:
            self.frame.destroy()
            if user[3] == "provider":
                ProviderDashboard(self.root, user[0])
            else:
                UserDashboard(self.root, user[0])
        else:
            messagebox.showerror("Error", "Invalid credentials")

        conn.close()

    def show_register(self):
        register_window = tk.Toplevel(self.root)
        RegisterScreen(register_window)


class RegisterScreen:
    def __init__(self, window):
        self.window = window
        self.window.title("Register")
        self.window.geometry("400x350")
        self.setup_register_screen()

    def setup_register_screen(self):
        frame = ttk.Frame(self.window, padding="20")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        ttk.Label(frame, text="Register", font=('Helvetica', 16, 'bold')).grid(row=0, column=0, columnspan=2, pady=20)

        ttk.Label(frame, text="Username:").grid(row=1, column=0, pady=5)
        self.username = ttk.Entry(frame)
        self.username.grid(row=1, column=1, pady=5)

        ttk.Label(frame, text="Password:").grid(row=2, column=0, pady=5)
        self.password = ttk.Entry(frame, show="*")
        self.password.grid(row=2, column=1, pady=5)

        ttk.Label(frame, text="User Type:").grid(row=3, column=0, pady=5)
        self.user_type = ttk.Combobox(frame, values=["user", "provider"])
        self.user_type.grid(row=3, column=1, pady=5)
        self.user_type.set("user")

        ttk.Button(frame, text="Register", command=self.register).grid(row=4, column=0, columnspan=2, pady=10)

    def register(self):
        username = self.username.get()
        password = self.password.get()
        user_type = self.user_type.get()

        if not all([username, password, user_type]):
            messagebox.showerror("Error", "All fields are required")
            return

        conn = create_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("INSERT INTO users (username, password, user_type) VALUES (%s, %s, %s)",
                           (username, password, user_type))
            conn.commit()
            messagebox.showinfo("Success", "Registration successful!")
            self.window.destroy()
        except mysql.connector.Error as err:
            messagebox.showerror("Error", f"Registration failed: {err}")
        finally:
            conn.close()
