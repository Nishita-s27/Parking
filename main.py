import tkinter as tk
from tkinter import ttk, messagebox
from database import initialize_database
from login_page import LoginPage
from register_page import RegisterPage
from user_dashboard import UserDashboard
from provider_dashboard import ProviderDashboard


class ParkingSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Parking Management System")

        # Set window size and position
        window_width = 1000
        window_height = 700
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        center_x = int(screen_width / 2 - window_width / 2)
        center_y = int(screen_height / 2 - window_height / 2)

        self.root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')

        # Configure styles
        self.configure_styles()

        # Configure the grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Create main container
        self.main_container = ttk.Frame(self.root)
        self.main_container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Initialize the login page
        self.show_login_page()

    def configure_styles(self):
        """Configure ttk styles"""
        style = ttk.Style()

        # Configure basic styles
        style.configure('TLabel', font=('Helvetica', 12))
        style.configure('TButton', font=('Helvetica', 12))
        style.configure('TEntry', font=('Helvetica', 12))

        # Custom style for links
        style.configure('Link.TButton',
                        font=('Helvetica', 10, 'underline'),
                        foreground='blue',
                        borderwidth=0)

        # Custom style for headers
        style.configure('Header.TLabel',
                        font=('Helvetica', 24, 'bold'))

        # Custom style for error messages
        style.configure('Error.TLabel',
                        font=('Helvetica', 10),
                        foreground='red')

    def show_login_page(self):
        """Display the login page"""
        # Clear the main container
        for widget in self.main_container.winfo_children():
            widget.destroy()

        # Create login page
        self.login_page = LoginPage(
            self.main_container,
            self.login_callback,
            self.show_register_page
        )

    def show_register_page(self):
        """Display the registration page"""
        # Clear the main container
        for widget in self.main_container.winfo_children():
            widget.destroy()

        # Create register page
        self.register_page = RegisterPage(
            self.main_container,
            self.register_callback,
            self.show_login_page
        )

    def show_user_dashboard(self, user_data):
        """Display the user dashboard"""
        # Clear the main container
        for widget in self.main_container.winfo_children():
            widget.destroy()

        # Create user dashboard
        self.current_dashboard = UserDashboard(
            self.main_container,
            user_data,
            self.logout_callback
        )

    def show_provider_dashboard(self, user_data):
        """Display the provider dashboard"""
        # Clear the main container
        for widget in self.main_container.winfo_children():
            widget.destroy()

        # Create provider dashboard
        self.current_dashboard = ProviderDashboard(
            self.main_container,
            user_data,
            self.logout_callback
        )

    def login_callback(self, user_data):
        """Handle successful login"""
        if user_data:
            # Show appropriate dashboard based on user type
            if user_data['user_type'] == 'USER':
                self.show_user_dashboard(user_data)
            elif user_data['user_type'] == 'PROVIDER':
                self.show_provider_dashboard(user_data)
            elif user_data['user_type'] == 'ADMIN':
                messagebox.showinfo("Admin Login", "Admin dashboard is not implemented yet")
                return

            messagebox.showinfo("Success", f"Welcome {user_data['username']}!")
        else:
            messagebox.showerror("Error", "Invalid login credentials")

    def register_callback(self, success):
        """Handle registration result"""
        if success:
            messagebox.showinfo("Success", "Registration successful! Please login.")
            self.show_login_page()
        else:
            messagebox.showerror("Error", "Registration failed. Please try again.")

    def logout_callback(self):
        """Handle logout"""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.show_login_page()

    def handle_error(self, error_message):
        """Handle and display errors"""
        messagebox.showerror("Error", error_message)


    def unpark_vehicle(request_id):
        bill_details = calculate_bill(request_id)
        if bill_details:
            return jsonify({
                'status': 'success',
                'amount': bill_details['amount'],
                'duration': bill_details['duration'],
                'message': f'Your bill amount is ${bill_details["amount"]} for {bill_details["duration"]} hours'
            })
        return jsonify({'status': 'error', 'message': 'Error calculating bill'})


def main():
    # Initialize database
    try:
        if not initialize_database():
            messagebox.showerror("Error", "Failed to initialize database")
            return
    except Exception as e:
        messagebox.showerror("Error", f"Database initialization error: {str(e)}")
        return

    # Create main window
    root = tk.Tk()

    # Set theme
    style = ttk.Style()
    available_themes = style.theme_names()
    if 'clam' in available_themes:
        style.theme_use('clam')

    # Create application
    app = ParkingSystem(root)

    # Start the application
    try:
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Error", f"Application error: {str(e)}")


if __name__ == "__main__":
    main()
