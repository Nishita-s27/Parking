import tkinter as tk
from tkinter import ttk, messagebox
from geopy.geocoders import Nominatim
from database import add_parking_space, get_all_parking_spaces, update_request_status, generate_bill, get_provider_requests
from map_view import MapView
from database import (
    add_parking_space,
    get_all_parking_spaces,
    update_request_status,
    generate_bill
)


class ProviderDashboard:
    def __init__(self, parent, user_data, logout_callback):
        self.parent = parent
        self.user_data = user_data
        self.logout_callback = logout_callback
        self.geolocator = Nominatim(user_agent="parking_app")
        self.create_widgets()
        self.load_requests()
        self.load_parking_spaces()

    def create_widgets(self):
        self.frame = ttk.Frame(self.parent, padding="20")
        self.frame.grid(row=0, column=0, sticky="nsew")

        # Configure grid weights
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_columnconfigure(1, weight=1)

        # Header
        header = ttk.Label(
            self.frame,
            text=f"Welcome, {self.user_data['full_name']} (Provider)",
            style='Header.TLabel'
        )
        header.grid(row=0, column=0, columnspan=2, pady=20)

        # Left Side - Add Parking Space Section
        left_frame = ttk.Frame(self.frame)
        left_frame.grid(row=1, column=0, sticky="nsew", padx=10)

        # Add Parking Space Section
        add_space_frame = ttk.LabelFrame(left_frame, text="Add Parking Space", padding="10")
        add_space_frame.pack(fill="x", pady=10)

        # Address
        ttk.Label(add_space_frame, text="Address:").grid(row=0, column=0, pady=5, sticky="e")
        self.address_var = tk.StringVar()
        self.address_entry = ttk.Entry(add_space_frame, textvariable=self.address_var, width=40)
        self.address_entry.grid(row=0, column=1, pady=5, padx=5, sticky="w")

        # Capacity
        ttk.Label(add_space_frame, text="Capacity:").grid(row=1, column=0, pady=5, sticky="e")
        self.capacity_var = tk.StringVar()
        self.capacity_entry = ttk.Entry(add_space_frame, textvariable=self.capacity_var)
        self.capacity_entry.grid(row=1, column=1, pady=5, padx=5, sticky="w")

        # Rate per Hour
        ttk.Label(add_space_frame, text="Rate per Hour:").grid(row=2, column=0, pady=5, sticky="e")
        self.rate_var = tk.StringVar()
        self.rate_entry = ttk.Entry(add_space_frame, textvariable=self.rate_var)
        self.rate_entry.grid(row=2, column=1, pady=5, padx=5, sticky="w")

        # Description
        ttk.Label(add_space_frame, text="Description:").grid(row=3, column=0, pady=5, sticky="e")
        self.description_var = tk.StringVar()
        self.description_entry = ttk.Entry(add_space_frame, textvariable=self.description_var)
        self.description_entry.grid(row=3, column=1, pady=5, padx=5, sticky="w")

        # Add Space Button
        add_button = ttk.Button(add_space_frame, text="Add Space", command=self.add_space)
        add_button.grid(row=4, column=0, columnspan=2, pady=10)

        # Map Frame
        self.map_frame = ttk.LabelFrame(left_frame, text="Parking Spaces Map")
        self.map_frame.pack(fill="both", expand=True, pady=10)

        # Create Map Widget
        self.map_view = MapView(self.map_frame, width=500, height=400)
        self.map_view.pack(fill="both", expand=True)

        # Set default position (Bangalore coordinates - change as needed)
        self.map_view.set_position(12.9716, 77.5946)

        # Right Side - Requests and Actions
        right_frame = ttk.Frame(self.frame)
        right_frame.grid(row=1, column=1, sticky="nsew", padx=10)

        # Pending Requests Section
        requests_frame = ttk.LabelFrame(right_frame, text="Parking Requests", padding="10")
        requests_frame.pack(fill="both", expand=True)

        # Requests Treeview
        self.requests_tree = ttk.Treeview(
            requests_frame,
            columns=("ID", "User", "Vehicle", "Duration", "Status"),
            show="headings",
            height=10
        )

        # Configure columns
        self.requests_tree.heading("ID", text="Request ID")
        self.requests_tree.heading("User", text="User Name")
        self.requests_tree.heading("Vehicle", text="Vehicle Number")
        self.requests_tree.heading("Duration", text="Duration (hrs)")
        self.requests_tree.heading("Status", text="Status")

        # Column widths
        self.requests_tree.column("ID", width=80)
        self.requests_tree.column("User", width=120)
        self.requests_tree.column("Vehicle", width=100)
        self.requests_tree.column("Duration", width=100)
        self.requests_tree.column("Status", width=100)

        self.requests_tree.pack(fill="both", expand=True, pady=5)

        # Request Action Buttons
        btn_frame = ttk.Frame(requests_frame)
        btn_frame.pack(fill="x", pady=5)

        ttk.Button(
            btn_frame,
            text="Accept Request",
            command=self.accept_request
        ).pack(side="left", padx=5)

        ttk.Button(
            btn_frame,
            text="Deny Request",
            command=self.deny_request
        ).pack(side="left", padx=5)

        ttk.Button(
            btn_frame,
            text="Generate Bill",
            command=self.show_bill_dialog
        ).pack(side="left", padx=5)

        # Logout Button
        logout_btn = ttk.Button(
            self.frame,
            text="Logout",
            command=self.logout_callback
        )
        logout_btn.grid(row=0, column=1, sticky="e", pady=20, padx=10)

    def add_space(self):
        """Add a new parking space"""
        address = self.address_var.get().strip()
        try:
            capacity = int(self.capacity_var.get())
            rate = float(self.rate_var.get())
        except ValueError:
            messagebox.showerror("Error", "Capacity and rate must be numbers")
            return

        if not address:
            messagebox.showerror("Error", "Please enter an address")
            return

        description = self.description_var.get().strip()

        # Geocode address
        try:
            location = self.geolocator.geocode(address)
            if location is None:
                messagebox.showerror("Error", "Could not find location")
                return
        except Exception as e:
            messagebox.showerror("Error", f"Geocoding error: {str(e)}")
            return

        # Add to database
        if add_parking_space(
                self.user_data['id'],
                address,
                location.latitude,
                location.longitude,
                capacity,
                rate,
                description
        ):
            messagebox.showinfo("Success", "Parking space added successfully!")
            self.clear_space_fields()

            # Add marker to map
            self.map_view.add_marker(
                location.latitude,
                location.longitude,
                f"Address: {address}\nRate: ${rate}/hr\nCapacity: {capacity}"
            )

            # Center map on new marker
            self.map_view.set_position(location.latitude, location.longitude)

            # Reload parking spaces
            self.load_parking_spaces()
        else:
            messagebox.showerror("Error", "Failed to add parking space")

    def load_parking_spaces(self):
        """Load and display all parking spaces on the map"""
        # Clear existing markers
        self.map_view.clear_markers()

        # Load spaces from database
        spaces = get_all_parking_spaces()
        for space in spaces:
            if space['provider_id'] == self.user_data['id']:
                # Add marker to map
                self.map_view.add_marker(
                    space['latitude'],
                    space['longitude'],
                    f"Address: {space['address']}\nRate: ${space['rate_per_hour']}/hr\nCapacity: {space['capacity']}"
                )

    def load_requests(self):
        """Load parking requests from database"""
        # Clear existing items
        for item in self.requests_tree.get_children():
            self.requests_tree.delete(item)

        # Load requests from database
        requests = get_provider_requests(self.user_data['id'])

        # Update the treeview with requests
        for request in requests:
            status_color = {
                'PENDING': 'orange',
                'ACCEPTED': 'green',
                'DENIED': 'red'
            }.get(request['status'], 'black')

            self.requests_tree.insert(
                "",
                "end",
                values=(
                    request['id'],
                    request['user_name'],
                    request['vehicle_number'],
                    f"{request['duration_hours']} hrs",
                    request['status']
                ),
                tags=(status_color,)
            )

        # Configure tag colors
        self.requests_tree.tag_configure('orange', foreground='orange')
        self.requests_tree.tag_configure('green', foreground='green')
        self.requests_tree.tag_configure('red', foreground='red')

        # If there are pending requests, show a notification
        pending_requests = [r for r in requests if r['status'] == 'PENDING']
        if pending_requests:
            messagebox.showinfo(
                "New Requests",
                f"You have {len(pending_requests)} pending parking request(s)"
            )

    def accept_request(self):
        """Accept selected parking request"""
        selected_item = self.requests_tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a request")
            return

        request_id = self.requests_tree.item(selected_item[0])['values'][0]

        # Check if request is already processed
        current_status = self.requests_tree.item(selected_item[0])['values'][4]
        if current_status != 'PENDING':
            messagebox.showinfo("Info", f"Request is already {current_status}")
            return

        if update_request_status(request_id, 'ACCEPTED'):
            messagebox.showinfo("Success", "Request accepted")
            self.load_requests()  # Refresh the list
        else:
            messagebox.showerror("Error", "Failed to accept request")

    def deny_request(self):
        """Deny selected parking request"""
        selected_item = self.requests_tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a request")
            return

        request_id = self.requests_tree.item(selected_item[0])['values'][0]

        # Check if request is already processed
        current_status = self.requests_tree.item(selected_item[0])['values'][4]
        if current_status != 'PENDING':
            messagebox.showinfo("Info", f"Request is already {current_status}")
            return

        if update_request_status(request_id, 'DENIED'):
            messagebox.showinfo("Success", "Request denied")
            self.load_requests()  # Refresh the list
        else:
            messagebox.showerror("Error", "Failed to deny request")

    def handle_unpark_payment(self, request_id):
        try:
            # Get the selected item from the requests tree
            selected_item = self.requests_tree.selection()[0]
            request_data = self.requests_tree.item(selected_item)['values']

            # Calculate amount (simplified - just duration * rate)
            duration = request_data[3]  # Assuming duration is in the 4th column
            rate = 50  # Fixed rate per hour - you can modify this
            amount = duration * rate

            # Show payment confirmation
            if messagebox.askyesno("Payment Confirmation",
                                   f"Confirm payment of ₹{amount} for {duration} hours?"):
                # Update request status
                cursor = self.conn.cursor()
                cursor.execute("""
                    UPDATE parking_requests 
                    SET status = 'COMPLETED', amount_paid = %s 
                    WHERE id = %s
                """, (amount, request_id))

                self.conn.commit()

                # Show success message
                messagebox.showinfo("Success", "Payment received and recorded!")

                # Refresh the requests list
                self.load_requests()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to process payment: {str(e)}")

    def show_bill_dialog(self):
        """Show dialog to generate bill"""
        selected_item = self.requests_tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a request")
            return

        request_data = self.requests_tree.item(selected_item[0])['values']
        request_id = request_data[0]  # Request ID

        # Create bill dialog
        dialog = tk.Toplevel(self.frame)
        dialog.title("Generate Bill")
        dialog.geometry("300x200")

        ttk.Label(dialog, text="Amount:").pack(pady=5)
        amount_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=amount_var).pack(pady=5)

        def submit_bill():
            try:
                amount = float(amount_var.get())

                # Debugging output
                print(f"Generating bill for Request ID: {request_id}, Amount: {amount}")

                if generate_bill(request_id, amount):
                    messagebox.showinfo("Success", "Bill generated successfully")
                    dialog.destroy()
                    self.load_requests()
                else:
                    messagebox.showerror("Error", "Failed to generate bill")
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid amount")

        ttk.Button(dialog, text="Generate", command=submit_bill).pack(pady=20)

    def clear_space_fields(self):
        """Clear all input fields"""
        self.address_var.set("")
        self.capacity_var.set("")
        self.rate_var.set("")
        self.description_var.set("")
