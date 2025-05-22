import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from database import create_db_connection


class UserPaymentFrame(ttk.Frame):
    def __init__(self, master, user_id):
        super().__init__(master)
        self.user_id = user_id
        self.setup_payment_ui()

    def setup_payment_ui(self):
        # Main payment frame setup
        self.grid(row=0, column=0, sticky='nsew', padx=20, pady=20)

        # Title
        ttk.Label(self, text="Payment Management", font=('Helvetica', 16, 'bold')).grid(row=0, column=0, columnspan=2,
                                                                                        pady=10)

        # Pending Bills Section
        ttk.Label(self, text="Pending Bills", font=('Helvetica', 12, 'bold')).grid(row=1, column=0, columnspan=2,
                                                                                   pady=5)

        # Bills Treeview
        self.bills_tree = ttk.Treeview(self, columns=('Bill ID', 'Space', 'Amount', 'Date', 'Status'), show='headings',
                                       height=8)
        self.bills_tree.heading('Bill ID', text='Bill ID')
        self.bills_tree.heading('Space', text='Parking Space')
        self.bills_tree.heading('Amount', text='Amount')
        self.bills_tree.heading('Date', text='Date')
        self.bills_tree.heading('Status', text='Status')

        self.bills_tree.column('Bill ID', width=100)
        self.bills_tree.column('Space', width=200)
        self.bills_tree.column('Amount', width=100)
        self.bills_tree.column('Date', width=150)
        self.bills_tree.column('Status', width=100)

        self.bills_tree.grid(row=2, column=0, columnspan=2, pady=5)

        # Scrollbar
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.bills_tree.yview)
        scrollbar.grid(row=2, column=2, sticky='ns')
        self.bills_tree.configure(yscrollcommand=scrollbar.set)

        # Buttons Frame
        buttons_frame = ttk.Frame(self)
        buttons_frame.grid(row=3, column=0, columnspan=2, pady=10)

        ttk.Button(buttons_frame, text="Pay Selected Bill", command=self.process_payment).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Refresh", command=self.load_bills).pack(side=tk.LEFT, padx=5)

        # Payment History Section
        ttk.Label(self, text="Payment History", font=('Helvetica', 12, 'bold')).grid(row=4, column=0, columnspan=2,
                                                                                     pady=5)

        # Payment History Treeview
        self.history_tree = ttk.Treeview(self, columns=('Payment ID', 'Amount', 'Method', 'Date'), show='headings',
                                         height=8)
        self.history_tree.heading('Payment ID', text='Payment ID')
        self.history_tree.heading('Amount', text='Amount')
        self.history_tree.heading('Method', text='Payment Method')
        self.history_tree.heading('Date', text='Date')

        self.history_tree.column('Payment ID', width=100)
        self.history_tree.column('Amount', width=100)
        self.history_tree.column('Method', width=150)
        self.history_tree.column('Date', width=150)

        self.history_tree.grid(row=5, column=0, columnspan=2, pady=5)

        # History Scrollbar
        history_scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.history_tree.yview)
        history_scrollbar.grid(row=5, column=2, sticky='ns')
        self.history_tree.configure(yscrollcommand=history_scrollbar.set)

        # Load initial data
        self.load_bills()
        self.load_payment_history()

    def load_bills(self):
        conn = create_db_connection()
        cursor = conn.cursor()

        # Clear existing items
        for item in self.bills_tree.get_children():
            self.bills_tree.delete(item)

        cursor.execute("""
            SELECT b.id, ps.address, b.amount, b.created_at, b.status
            FROM bills b
            JOIN parking_requests pr ON b.parking_request_id = pr.id
            JOIN parking_spaces ps ON pr.space_id = ps.id
            WHERE pr.user_id = %s AND b.status = 'PENDING'
            ORDER BY b.created_at DESC
        """, (self.user_id,))

        for row in cursor.fetchall():
            self.bills_tree.insert('', 'end', values=(
                row[0],
                row[1],
                f"${row[2]:.2f}",
                row[3].strftime('%Y-%m-%d %H:%M'),
                row[4]
            ))

        conn.close()

    def load_payment_history(self):
        conn = create_db_connection()
        cursor = conn.cursor()

        # Clear existing items
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)

        cursor.execute("""
            SELECT p.id, p.amount, p.payment_method, p.payment_date
            FROM payments p
            JOIN bills b ON p.bill_id = b.id
            JOIN parking_requests pr ON b.parking_request_id = pr.id
            WHERE pr.user_id = %s
            ORDER BY p.payment_date DESC
        """, (self.user_id,))

        for row in cursor.fetchall():
            self.history_tree.insert('', 'end', values=(
                row[0],
                f"${row[1]:.2f}",
                row[2],
                row[3].strftime('%Y-%m-%d %H:%M')
            ))

        conn.close()

    def process_payment(self):
        selected_item = self.bills_tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a bill to pay")
            return

        bill_id = self.bills_tree.item(selected_item)['values'][0]
        amount = float(self.bills_tree.item(selected_item)['values'][2].replace('$', ''))

        # Create payment window
        payment_window = tk.Toplevel(self)
        payment_window.title("Payment Processing")
        payment_window.geometry("400x300")

        # Payment form
        payment_frame = ttk.Frame(payment_window, padding="20")
        payment_frame.grid(row=0, column=0, sticky='nsew')

        ttk.Label(payment_frame, text="Payment Details", font=('Helvetica', 12, 'bold')).grid(row=0, column=0,
                                                                                              columnspan=2, pady=10)
        ttk.Label(payment_frame, text=f"Amount to Pay: ${amount:.2f}", font=('Helvetica', 10)).grid(row=1, column=0,
                                                                                                    columnspan=2,
                                                                                                    pady=5)

        # Payment method selection
        ttk.Label(payment_frame, text="Payment Method:").grid(row=2, column=0, pady=5)
        payment_method = tk.StringVar(value="credit_card")
        ttk.Radiobutton(payment_frame, text="Credit Card", variable=payment_method, value="credit_card").grid(row=3,
                                                                                                              column=0)
        ttk.Radiobutton(payment_frame, text="Debit Card", variable=payment_method, value="debit_card").grid(row=3,
                                                                                                            column=1)

        # Card details
        ttk.Label(payment_frame, text="Card Number:").grid(row=4, column=0, pady=5)
        card_number = ttk.Entry(payment_frame)
        card_number.grid(row=4, column=1, pady=5)

        ttk.Label(payment_frame, text="Expiry Date:").grid(row=5, column=0, pady=5)
        expiry = ttk.Entry(payment_frame)
        expiry.grid(row=5, column=1, pady=5)

        ttk.Label(payment_frame, text="CVV:").grid(row=6, column=0, pady=5)
        cvv = ttk.Entry(payment_frame, show="*")
        cvv.grid(row=6, column=1, pady=5)

        def confirm_payment():
            # Validate card details (basic validation)
            if not all([card_number.get(), expiry.get(), cvv.get()]):
                messagebox.showerror("Error", "Please fill in all card details")
                return

            conn = create_db_connection()
            cursor = conn.cursor()

            try:
                # Update bill status
                cursor.execute("""
                    UPDATE bills 
                    SET status = 'PAID', paid_at = %s 
                    WHERE id = %s
                """, (datetime.now(), bill_id))

                # Create payment record
                cursor.execute("""
                    INSERT INTO payments (bill_id, amount, payment_method, transaction_id, payment_date)
                    VALUES (%s, %s, %s, %s, %s)
                """, (bill_id, amount, payment_method.get(),
                      f"TXN-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                      datetime.now()))

                # Notify provider
                cursor.execute("""
                    SELECT ps.provider_id
                    FROM bills b
                    JOIN parking_requests pr ON b.parking_request_id = pr.id
                    JOIN parking_spaces ps ON pr.space_id = ps.id
                    WHERE b.id = %s
                """, (bill_id,))

                provider_id = cursor.fetchone()[0]

                cursor.execute("""
                    INSERT INTO notifications (user_id, message, type, created_at)
                    VALUES (%s, %s, %s, %s)
                """, (provider_id, f"Payment received for Bill ID: {bill_id}", "PAYMENT", datetime.now()))

                conn.commit()
                messagebox.showinfo("Success", "Payment processed successfully!")
                payment_window.destroy()

                # Refresh lists
                self.load_bills()
                self.load_payment_history()

            except Exception as e:
                conn.rollback()
                messagebox.showerror("Error", f"Payment failed: {str(e)}")
            finally:
                conn.close()

        ttk.Button(payment_frame, text="Confirm Payment", command=confirm_payment).grid(row=7, column=0, columnspan=2,
                                                                                        pady=20)
