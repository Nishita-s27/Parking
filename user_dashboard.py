import tkinter as tk
from tkinter import ttk, messagebox

import mysql

from map_view import MapView
from database import (  # Import functions from database.py
    create_db_connection,
    get_all_parking_spaces,
    create_parking_request,
    get_pending_bills,
    process_payment
)


class UserDashboard:
    def __init__(self, parent, user_data, logout_callback):
        self.parent = parent
        self.user_data = user_data
        self.logout_callback = logout_callback
        self.selected_space = None
        self.create_widgets()
        self.load_pending_bills()
        self.bills = []
        self.load_parking_spaces()
        self.show_payment_window()
        bills = self.load_bills_from_db()  # however you load them
        self.show_payment_window(bills)

    def load_pending_bills(self):
        bills = get_pending_bills(self.user_data['id'])
        if bills:
            # If there are pending bills, show them
            total_amount = sum(bill['amount'] for bill in bills)
            message = f"You have {len(bills)} pending bills totaling ₹{total_amount}.\nWould you like to pay now?"
            if messagebox.askyesno("Pending Bills", message):
                self.show_payment_window(bills)  # This call now correctly passes 'bills'

    def create_widgets(self):
        # Create main container
        main_container = ttk.Frame(self.parent)
        main_container.pack(fill="both", expand=True, padx=10, pady=5)

        # Header frame
        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill="x", pady=(0, 10))

        # Welcome message and user info
        ttk.Label(
            header_frame,
            text=f"Welcome, {self.user_data['full_name']}",
            font=("Helvetica", 12)
        ).pack(side="left")

        # My Bookings button
        ttk.Button(
            header_frame,
            text="My Bookings",
            command=self.show_my_bookings
        ).pack(side="left", padx=10)

        # Logout button
        ttk.Button(
            header_frame,
            text="Logout",
            command=self.logout_callback
        ).pack(side="right")


        # Search frame
        search_frame = ttk.LabelFrame(main_container, text="Find Parking")
        search_frame.pack(fill="x", pady=(0, 10))

        # Vehicle details frame
        vehicle_frame = ttk.Frame(search_frame)
        vehicle_frame.pack(fill="x", pady=5)

        ttk.Label(vehicle_frame, text="Vehicle Number:").pack(side="left", padx=5)
        self.vehicle_number = ttk.Entry(vehicle_frame)
        self.vehicle_number.pack(side="left", padx=5)

        ttk.Label(vehicle_frame, text="Vehicle Type:").pack(side="left", padx=5)
        self.vehicle_type = ttk.Combobox(
            vehicle_frame,
            values=["Car", "Bike", "Other"],
            state="readonly"
        )
        self.vehicle_type.set("Car")
        self.vehicle_type.pack(side="left", padx=5)

        ttk.Button(
            vehicle_frame,
            text="Submit Request",
            command=self.submit_request
        ).pack(side="left", padx=5)

        # Available spaces frame
        spaces_frame = ttk.Frame(main_container)
        spaces_frame.pack(fill="both", expand=True)

        # Create Treeview for parking spaces
        columns = ("Location", "Rate", "Capacity", "Provider")
        self.spaces_tree = ttk.Treeview(spaces_frame, columns=columns, show="headings")

        # Configure columns
        for col in columns:
            self.spaces_tree.heading(col, text=col)
            self.spaces_tree.column(col, width=100)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(spaces_frame, orient="vertical", command=self.spaces_tree.yview)
        self.spaces_tree.configure(yscrollcommand=scrollbar.set)

        # Pack Treeview and scrollbar
        self.spaces_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Initialize map view
        self.map_view = MapView(main_container)
        self.map_view.pack(fill="both", expand=True)

        # Load initial parking spaces
        self.load_parking_spaces()

    def load_parking_spaces(self):
        try:
            # Clear existing items
            for item in self.spaces_tree.get_children():
                self.spaces_tree.delete(item)

            # Clear existing markers on map
            self.map_view.clear_markers()

            # Get spaces from database
            conn = create_db_connection()
            cursor = conn.cursor()

            # Simple query without any truncation
            cursor.execute("""
                SELECT 
                    ps.id,
                    ps.address,
                    ps.rate_per_hour,
                    ps.capacity,
                    ps.latitude,
                    ps.longitude,
                    u.full_name as provider_name
                FROM parking_spaces ps
                JOIN users u ON ps.provider_id = u.id
            """)

            spaces = cursor.fetchall()

            # Add spaces to tree and map with full data
            for space in spaces:
                space_id, address, rate, capacity, lat, lng, provider = space

                # Insert into tree view without truncation
                self.spaces_tree.insert(
                    "",
                    "end",
                    values=(
                        address,  # Full address without truncation
                        f"₹{rate}/hr",
                        capacity,
                        provider
                    ),
                    tags=(space_id,)
                )

                # Add marker to map if coordinates are valid
                if lat and lng:
                    self.map_view.add_marker(
                        float(lat),
                        float(lng),
                        f"{address}\nRate: ₹{rate}/hr\nCapacity: {capacity}"
                    )

            # If spaces were found, center map on first space
            if spaces:
                first_space = spaces[0]
                self.map_view.set_position(
                    float(first_space[4]),  # latitude
                    float(first_space[5])  # longitude
                )

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load parking spaces: {str(e)}")
        finally:
            if 'conn' in locals() and conn.is_connected():
                cursor.close()
                conn.close()

    def on_space_select(self, event):
        selected_items = self.spaces_tree.selection()
        if selected_items:
            # Get the selected item
            item = self.spaces_tree.item(selected_items[0])
            space_id = item['tags'][0]  # Get space_id from tags

            try:
                # Fetch detailed information about the selected space
                conn = create_db_connection()
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT 
                        ps.address,
                        ps.rate_per_hour,
                        ps.capacity,
                        ps.latitude,
                        ps.longitude,
                        u.full_name as provider_name
                    FROM parking_spaces ps
                    JOIN users u ON ps.provider_id = u.id
                    WHERE ps.id = %s
                """, (space_id,))

                space_details = cursor.fetchone()

                if space_details:
                    address, rate, capacity, lat, lng, provider = space_details

                    # Update selected space label with more details
                    details_text = f"Selected: {address}\nRate: ₹{rate}/hr\nCapacity: {capacity}\nProvider: {provider}"
                    self.selected_space_label.config(text=details_text)

                    # Center map on selected space
                    if lat and lng:
                        self.map_view.set_position(float(lat), float(lng))

                    # Enable submit button
                    self.submit_btn.config(state="normal")

                    # Store selected space info
                    self.selected_space = {
                        'id': space_id,
                        'address': address,
                        'rate': rate,
                        'capacity': capacity,
                        'provider': provider
                    }

            except Exception as e:
                messagebox.showerror("Error", f"Failed to get space details: {str(e)}")
            finally:
                if 'conn' in locals() and conn.is_connected():
                    cursor.close()
                    conn.close()
        else:
            self.selected_space = None
            self.selected_space_label.config(text="No space selected")
            self.submit_btn.config(state="disabled")

    def submit_request(self):
        vehicle_number = self.vehicle_number.get().strip()
        if not vehicle_number:
            messagebox.showerror("Error", "Please enter vehicle number")
            return

        try:
            selected_items = self.spaces_tree.selection()
            if not selected_items:
                messagebox.showerror("Error", "Please select a parking space")
                return

            space_id = self.spaces_tree.item(selected_items[0])['tags'][0]

            conn = create_db_connection()
            cursor = conn.cursor()

            # Insert the request with PENDING status
            cursor.execute("""
                INSERT INTO parking_requests 
                (user_id, space_id, vehicle_number, status) 
                VALUES (%s, %s, %s, 'PENDING')
            """, (self.user_data['id'], space_id, vehicle_number))

            conn.commit()
            request_id = cursor.lastrowid

            if request_id:
                self.current_request_id = request_id
                messagebox.showinfo("Request Submitted",
                                    f"Your parking request has been submitted!\n\n"
                                    f"Vehicle Number: {vehicle_number}\n"
                                    f"Status: Waiting for provider approval\n\n"
                                    f"Check 'My Bookings' for status updates.")

                self.vehicle_number.delete(0, 'end')
                self.check_current_booking()  # Add this method to check current booking status

            else:
                messagebox.showerror("Error", "Failed to submit parking request")

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        finally:
            if 'conn' in locals() and conn.is_connected():
                cursor.close()
                conn.close()

    def check_current_booking(self):
        try:
            conn = create_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT 
                    parking_requests.id,
                    vehicle_number,
                    parking_requests.status,
                    address,
                    rate_per_hour
                FROM parking_requests
                JOIN parking_spaces ON space_id = parking_spaces.id
                WHERE user_id = %s 
                AND parking_requests.status IN ('PENDING', 'APPROVED', 'ACTIVE')
                ORDER BY created_at DESC
                LIMIT 1
            """, (self.user_data['id'],))

            booking = cursor.fetchone()

            if booking:
                request_id, vehicle_number, status, address, rate = booking
                self.current_request_id = request_id

                status_text = f"Current Booking:\nVehicle: {vehicle_number}\nStatus: {status}\nLocation: {address}"
                self.status_label.config(text=status_text)

                # **Ensure buttons update correctly**
                if status == 'APPROVED':
                    self.park_button.config(state='normal')  # Enable Park button
                    self.unpark_button.config(state='disabled')
                elif status == 'ACTIVE':
                    self.park_button.config(state='disabled')
                    self.unpark_button.config(state='normal')
                else:  # PENDING
                    self.park_button.config(state='disabled')
                    self.unpark_button.config(state='disabled')
            else:
                self.current_request_id = None
                self.status_label.config(text="No active booking")
                self.park_button.config(state='disabled')
                self.unpark_button.config(state='disabled')

        except Exception as e:
            messagebox.showerror("Error", f"Failed to check current booking: {str(e)}")
        finally:
            if 'conn' in locals() and conn.is_connected():
                cursor.close()
                conn.close()

    def load_bookings(self, tree):
        # Clear existing items
        for item in tree.get_children():
            tree.delete(item)

        try:
            conn = create_db_connection()
            cursor = conn.cursor()

            query = """
                SELECT 
                    parking_spaces.address,
                    parking_requests.vehicle_number,
                    parking_requests.status,
                    parking_requests.request_date,  -- Updated column name
                    users.full_name AS provider_name
                FROM parking_requests
                INNER JOIN parking_spaces ON parking_requests.space_id = parking_spaces.id
                INNER JOIN users ON parking_spaces.provider_id = users.id
                WHERE parking_requests.user_id = %s
                ORDER BY parking_requests.request_date DESC  -- Updated column name
            """

            user_id = self.user_data['id']
            cursor.execute(query, (user_id,))

            bookings = cursor.fetchall()
            for booking in bookings:
                tree.insert("", "end", values=booking)

        except mysql.connector.Error as e:
            messagebox.showerror("Database Error", f"Failed to load bookings: {e}")
            print(f"SQL Error: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error: {e}")
            print(f"Unexpected Error: {e}")
        finally:
            if 'conn' in locals() and conn.is_connected():
                cursor.close()
                conn.close()

    # Update the `show_my_bookings` method to use the fixed function
    def show_my_bookings(self):
        bookings_window = tk.Toplevel(self.parent)
        bookings_window.title("My Bookings")
        bookings_window.geometry("800x600")

        # Create Treeview for bookings
        columns = ("Parking Space", "Vehicle Number", "Status", "Request Date", "Provider")
        bookings_tree = ttk.Treeview(bookings_window, columns=columns, show="headings", height=10)

        # Configure columns
        for col in columns:
            bookings_tree.heading(col, text=col)
            bookings_tree.column(col, width=150)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(bookings_window, orient="vertical", command=bookings_tree.yview)
        bookings_tree.configure(yscrollcommand=scrollbar.set)

        # Pack widgets
        bookings_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Buttons Frame
        button_frame = ttk.Frame(bookings_window)
        button_frame.pack(pady=10)

        self.load_bookings(bookings_tree)

        '''self.pay_button = ttk.Button(
            button_frame,
            text="Pay Bill",
            command=self.pay_bill,
            state="disabled"
        )
        self.pay_button.pack(side="left", padx=5)'''

    def start_status_checker(self):
        def check_status():
            if self.current_request_id:
                self.check_current_booking()
            self.parent.after(5000, check_status)  # Check every 5 seconds

        check_status()

    def park_vehicle(self):
        try:
            conn = create_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE parking_requests 
                SET status = 'ACTIVE'
                WHERE id = %s
            """, (self.current_request_id,))

            conn.commit()

            messagebox.showinfo("Success", "Vehicle parked successfully!")

            # Ensure UI updates
            self.check_current_booking()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to park vehicle: {e}")
        finally:
            if 'conn' in locals() and conn.is_connected():
                cursor.close()
                conn.close()

    def unpark_vehicle(self):
        try:
            if messagebox.askyesno("Payment", "Parking fee: ₹50\n\nProceed with payment?"):
                conn = create_db_connection()
                cursor = conn.cursor()

                cursor.execute("""
                    UPDATE parking_requests 
                    SET status = 'COMPLETED', amount_paid = 50
                    WHERE id = %s
                """, (self.current_request_id,))

                conn.commit()

                messagebox.showinfo("Success", "Payment successful! You can now leave the parking space.")

                # Reset status and update UI
                self.current_request_id = None
                self.check_current_booking()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to process payment: {e}")
        finally:
            if 'conn' in locals() and conn.is_connected():
                cursor.close()
                conn.close()

    def load_pending_bills(self):
        bills = get_pending_bills(self.user_data['id'])
        if bills:
            # If there are pending bills, show them
            total_amount = sum(bill['amount'] for bill in bills)
            message = f"You have {len(bills)} pending bills totaling ₹{total_amount}.\nWould you like to pay now?"
            if messagebox.askyesno("Pending Bills", message):
                self.show_payment_window(bills)

    def show_payment_window(self, bills):
        """Opens a window to display pending bills."""
        if not bills:
            messagebox.showinfo("No Bills", "There are no pending bills.")
            return

        payment_window = tk.Toplevel(self.parent)
        payment_window.title("Pending Bills")
        payment_window.geometry("400x300")
        payment_window.grab_set()  # Make it modal

        ttk.Label(payment_window, text="Pending Bills", font=("Helvetica", 12, "bold")).pack(pady=10)

        # Create Treeview for bills
        bills_tree = ttk.Treeview(payment_window, columns=("Date", "Amount"), show="headings", height=5)
        bills_tree.heading("Date", text="Date")
        bills_tree.heading("Amount", text="Amount")
        bills_tree.pack(pady=10, padx=10, fill="both", expand=True)

        # Populate bills in Treeview
        for bill in bills:
            bills_tree.insert("", "end", values=(bill['due_date'], f"₹{bill['amount']}"))

        ttk.Label(
            payment_window,
            text=f"Total Amount: ₹{sum(b['amount'] for b in bills)}",
            font=("Helvetica", 12, "bold")
        ).pack(pady=10)

        def pay_bill(self):
            selected_item = self.bookings_tree.selection()
            if not selected_item:
                messagebox.showwarning("Warning", "Please select a bill to pay.")
                return

            item = self.bookings_tree.item(selected_item[0])
            status_index = 2  # Assuming "Status" is the third column

            # Retrieve the bill ID and other relevant info
            bill_id = item['tags'][0]  # Assuming that the 'tags' field contains the bill's unique ID

            try:
                # Update the bill status in the database
                conn = create_db_connection()
                cursor = conn.cursor()

                # Update the status of the bill to 'PAID' or 'COMPLETED' in the database
                cursor.execute("""
                    UPDATE parking_requests
                    SET status = 'PAID'
                    WHERE id = %s
                """, (bill_id,))

                conn.commit()

                # Show success message
                messagebox.showinfo("Payment", "Payment received by the provider!")

                # Update the UI: Update the status in the treeview (visual update)
                self.bookings_tree.item(selected_item[0], values=(
                *item['values'][:status_index], "PAID", *item['values'][status_index + 1:]))

                # Reload the bookings to ensure the data is up-to-date
                self.load_bookings(self.bookings_tree)  # Optional, to refresh all bookings

                # Disable the Pay Bill button after paying
                self.pay_button.config(state="disabled")

            except mysql.connector.Error as e:
                messagebox.showerror("Database Error", f"Failed to update status: {e}")
            except Exception as e:
                messagebox.showerror("Error", f"Unexpected error: {e}")
            finally:
                if 'conn' in locals() and conn.is_connected():
                    cursor.close()
                    conn.close()

        ttk.Button(payment_window, text="Pay Bill", command=pay_bill).pack(pady=10)

    def load_bills_in_window(self):
        """Load bills into the Treeview in the payment window"""
        self.bills_tree.delete(*self.bills_tree.get_children())  # Clear existing entries
        self.bills = get_bills(self.user_data["id"])  # Fetch bills from the database

        if not self.bills:
            messagebox.showinfo("No Bills", "No pending bills found.")
            return

        for bill in self.bills:
            self.bills_tree.insert("", "end", values=(bill["date"], f"₹{bill['amount']}"))

        # Update the total amount
        total_amount = sum(b["amount"] for b in self.bills)
        self.total_label.config(text=f"Total Amount: ₹{total_amount}")





