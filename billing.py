import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
from decimal import Decimal
from database import create_db_connection



class ProviderBillingFrame(ttk.Frame):
    def __init__(self, master, provider_id):
        super().__init__(master)
        self.provider_id = provider_id
        self.setup_billing_ui()

    def setup_billing_ui(self):
        # Main billing frame setup
        self.grid(row=0, column=0, sticky='nsew', padx=20, pady=20)

        # Title
        ttk.Label(self, text="Billing Management", font=('Helvetica', 16, 'bold')).grid(row=0, column=0, columnspan=2,
                                                                                        pady=10)

        # Pending Requests Section
        ttk.Label(self, text="Completed Parking Requests", font=('Helvetica', 12, 'bold')).grid(row=1, column=0,
                                                                                                columnspan=2, pady=5)

        # Requests Treeview
        self.requests_tree = ttk.Treeview(self, columns=('Request ID', 'User', 'Space', 'Duration', 'Status'),
                                          show='headings', height=8)
        self.requests_tree.heading('Request ID', text='Request ID')
        self.requests_tree.heading('User', text='User')
        self.requests_tree.heading('Space', text='Parking Space')
        self.requests_tree.heading('Duration', text='Duration (hours)')
        self.requests_tree.heading('Status', text='Status')

        self.requests_tree.column('Request ID', width=100)
        self.requests_tree.column('User', width=150)
        self.requests_tree.column('Space', width=200)
        self.requests_tree.column('Duration', width=120)
        self.requests_tree.column('Status', width=100)

        self.requests_tree.grid(row=2, column=0, columnspan=2, pady=5)

        # Scrollbar for requests
        request_scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.requests_tree.yview)
        request_scrollbar.grid(row=2, column=2, sticky='ns')
        self.requests_tree.configure(yscrollcommand=request_scrollbar.set)

        # Buttons Frame
        buttons_frame = ttk.Frame(self)
        buttons_frame.grid(row=3, column=0, columnspan=2, pady=10)

        ttk.Button(buttons_frame, text="Send Bill", command=self.send_bill).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Refresh", command=self.load_requests).pack(side=tk.LEFT, padx=5)

        # Sent Bills Section
        ttk.Label(self, text="Sent Bills", font=('Helvetica', 12, 'bold')).grid(row=4, column=0, columnspan=2, pady=5)

        # Bills Treeview
        self.bills_tree = ttk.Treeview(self, columns=('Bill ID', 'User', 'Amount', 'Date', 'Status'), show='headings',
                                       height=8)
        self.bills_tree.heading('Bill ID', text='Bill ID')
        self.bills_tree.heading('User', text='User')
        self.bills_tree.heading('Amount', text='Amount')
        self.bills_tree.heading('Date', text='Date')
        self.bills_tree.heading('Status', text='Status')

        self.bills_tree.column('Bill ID', width=100)
        self.bills_tree.column('User', width=150)
        self.bills_tree.column('Amount', width=100)
        self.bills_tree.column('Date', width=150)
        self.bills_tree.column('Status', width=100)

        self.bills_tree.grid(row=5, column=0, columnspan=2, pady=5)

        # Scrollbar for bills
        bills_scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.bills_tree.yview)
        bills_scrollbar.grid(row=5, column=2, sticky='ns')
        self.bills_tree.configure(yscrollcommand=bills_scrollbar.set)

        # Load initial data
        self.load_requests()
        self.load_bills()

    def load_requests(self):
        conn = create_db_connection()
        cursor = conn.cursor()

        # Clear existing items
        for item in self.requests_tree.get_children():
            self.requests_tree.delete(item)

        cursor.execute("""
            SELECT pr.id, u.username, ps.address, pr.status
            FROM parking_requests pr
            JOIN users u ON pr.user_id = u.id
            JOIN parking_spaces ps ON pr.space_id = ps.id
            WHERE ps.provider_id = %s AND pr.status = 'COMPLETED'
            AND NOT EXISTS (SELECT 1 FROM bills b WHERE b.parking_request_id = pr.id)
        """, (self.provider_id,))

        for row in cursor.fetchall():
            self.requests_tree.insert('', 'end', values=(row[0], row[1], row[2], '', row[3]))

        conn.close()

    def load_bills(self):
        conn = create_db_connection()
        cursor = conn.cursor()

        # Clear existing items
        for item in self.bills_tree.get_children():
            self.bills_tree.delete(item)

        cursor.execute("""
            SELECT b.id, u.username, b.amount, b.created_at, b.status
            FROM bills b
            JOIN parking_requests pr ON b.parking_request_id = pr.id
            JOIN users u ON pr.user_id = u.id
            JOIN parking_spaces ps ON pr.space_id = ps.id
            WHERE ps.provider_id = %s
            ORDER BY b.created_at DESC
        """, (self.provider_id,))

        for row in cursor.fetchall():
            self.bills_tree.insert('', 'end', values=(
                row[0],
                row[1],
                f"${row[2]:.2f}",
                row[3].strftime('%Y-%m-%d %H:%M'),
                row[4]
            ))

        conn.close()

    def send_bill(self):
        selected_item = self.requests_tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a parking request")
            return

        request_id = self.requests_tree.item(selected_item)['values'][0]

        # Get duration from user
        hours = simpledialog.askfloat("Input", "Enter parking duration (hours):", parent=self)
        if not hours:
            return

        conn = create_db_connection()
        cursor = conn.cursor()

        try:
            # Get rate for the parking space
            cursor.execute("""
                SELECT ps.rate_per_hour, pr.user_id
                FROM parking_requests pr
                JOIN parking_spaces ps ON pr.space_id = ps.id
                WHERE pr.id = %s
            """, (request_id,))

            rate_per_hour, user_id = cursor.fetchone()
            amount = Decimal(hours) * Decimal(rate_per_hour)

            # Create bill
            cursor.execute("""
                INSERT INTO bills (parking_request_id, amount, status, created_at)
                VALUES (%s, %s, %s, %s)
            """, (request_id, amount, "PENDING", datetime.now()))

            bill_id = cursor.lastrowid

            # Create notification
            cursor.execute("""
                INSERT INTO notifications (user_id, message, type, created_at)
                VALUES (%s, %s, %s, %s)
            """, (user_id, f"New bill received: ${amount:.2f} for {hours} hours parking", "BILL", datetime.now()))

            conn.commit()
            messagebox.showinfo("Success", "Bill sent successfully!")

            # Refresh lists
            self.load_requests()
            self.load_bills()

        except Exception as e:
            conn.rollback()
            messagebox.showerror("Error", f"Failed to send bill: {str(e)}")
        finally:
            conn.close()

    def mark_bill_as_paid(bill_id, amount_paid):
        conn = create_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                UPDATE bills
                SET status = 'PAID', amount_payed = %s
                WHERE id = %s AND status = 'PENDING'
            """, (amount_paid, bill_id))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def get_pending_bills(user_id):
        conn = create_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT b.id, b.amount, b.created_at
                FROM bills b
                JOIN parking_requests pr ON b.parking_request_id = pr.id
                WHERE pr.user_id = %s AND b.status = 'PENDING'
                ORDER BY b.created_at DESC
            """, (user_id,))
            results = cursor.fetchall()

            bills = []
            for row in results:
                bills.append({
                    "id": row[0],
                    "amount": float(row[1]),
                    "due_date": row[2].strftime("%Y-%m-%d %H:%M")  # or just %Y-%m-%d
                })
            return bills
        except Exception as e:
            print("Error fetching pending bills:", e)
            return []
        finally:
            conn.close()


