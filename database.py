import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta
import bcrypt


def create_db_connection():
    """Create a connection to the database"""
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='nishi',
            database='parking_near'
        )
        return connection
    except Error as e:
        raise Exception(f"Error connecting to database: {e}")


def initialize_database():
    try:
        conn = create_db_connection()
        cursor = conn.cursor()

        # Add this bills table creation along with your other table creations
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bills (
                id INT AUTO_INCREMENT PRIMARY KEY,
                request_id INT,
                user_id INT,
                space_id INT,
                amount DECIMAL(10,2),
                due_date DATETIME,
                status VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (request_id) REFERENCES parking_requests(id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (space_id) REFERENCES parking_spaces(id)
            )
        """)

        conn.commit()
        return True

    except Error as e:
        print(f"Error creating database tables: {e}")
        return False
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()


def create_tables():
    """Create all necessary tables if they don't exist"""
    try:
        conn = create_db_connection()
        cursor = conn.cursor()

        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                full_name VARCHAR(100),
                user_type ENUM('USER', 'PROVIDER', 'ADMIN') NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Parking Spaces table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS parking_spaces (
                id INT AUTO_INCREMENT PRIMARY KEY,
                provider_id INT NOT NULL,
                address VARCHAR(255) NOT NULL,
                latitude DECIMAL(10, 8) NOT NULL,
                longitude DECIMAL(11, 8) NOT NULL,
                capacity INT NOT NULL,
                rate_per_hour DECIMAL(10, 2) NOT NULL,
                description TEXT,
                status ENUM('ACTIVE', 'INACTIVE') DEFAULT 'ACTIVE',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (provider_id) REFERENCES users(id)
            )
        """)

        # Parking Requests table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS parking_requests (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                space_id INT NOT NULL,
                request_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                status ENUM('PENDING', 'ACCEPTED', 'DENIED') NOT NULL,
                notification_shown BOOLEAN DEFAULT FALSE,
                duration_hours FLOAT,
                vehicle_number VARCHAR(20),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (space_id) REFERENCES parking_spaces(id)
            )
        """)

        # Bills table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bills (
                id INT AUTO_INCREMENT PRIMARY KEY,
                request_id INT,
                user_id INT,
                space_id INT,
                amount DECIMAL(10,2),
                due_date DATETIME,
                status VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (request_id) REFERENCES parking_requests(id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (space_id) REFERENCES parking_spaces(id)
            )
        """)

        # Payments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                bill_id INT NOT NULL,
                user_id INT NOT NULL,
                amount DECIMAL(10, 2) NOT NULL,
                payment_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                payment_method ENUM('CREDIT_CARD', 'DEBIT_CARD', 'UPI', 'NET_BANKING') NOT NULL,
                transaction_id VARCHAR(100) UNIQUE,
                status ENUM('SUCCESS', 'FAILED', 'PENDING') DEFAULT 'PENDING',
                FOREIGN KEY (bill_id) REFERENCES bills(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        conn.commit()
        print("Tables created successfully!")

    except Error as e:
        print(f"Error creating tables: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()


def hash_password(password):
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password, hashed):
    """Verify a password against its hash"""
    try:
        return bcrypt.checkpw(
            password.encode('utf-8'),
            hashed.encode('utf-8')
        )
    except ValueError:
        return False


def register_user(username, password, full_name, user_type='USER'):
    """Register a new user"""
    try:
        conn = create_db_connection()
        cursor = conn.cursor()

        # Hash the password before storing
        hashed_password = hash_password(password)

        cursor.execute("""
            INSERT INTO users (username, password, full_name, user_type)
            VALUES (%s, %s, %s, %s)
        """, (username, hashed_password, full_name, user_type))

        conn.commit()
        return True

    except Error as e:
        print(f"Error registering user: {e}")
        return False
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()


def verify_user(username, password):
    """Verify user credentials and return user data if valid"""
    try:
        conn = create_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT * FROM users WHERE username = %s
        """, (username,))

        user = cursor.fetchone()

        if user and verify_password(password, user['password']):
            return {
                'id': user['id'],
                'username': user['username'],
                'user_type': user['user_type'],
                'full_name': user['full_name']
            }
        return None

    except Error as e:
        print(f"Error verifying user: {e}")
        return None
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()


def add_parking_space(provider_id, address, latitude, longitude, capacity, rate_per_hour, description):
    """Add a new parking space"""
    try:
        conn = create_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO parking_spaces 
            (provider_id, address, latitude, longitude, capacity, rate_per_hour, description)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (provider_id, address, latitude, longitude, capacity, rate_per_hour, description))

        conn.commit()
        return True
    except Error as e:
        print(f"Error adding parking space: {e}")
        return False
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()


def get_all_parking_spaces():
    try:
        conn = create_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT ps.*, u.full_name as provider_name
            FROM parking_spaces ps
            JOIN users u ON ps.provider_id = u.id
        """)

        spaces = cursor.fetchall()
        # Convert Decimal to float for latitude and longitude
        for space in spaces:
            space['latitude'] = float(space['latitude'])
            space['longitude'] = float(space['longitude'])
        return spaces
    except Error as e:
        print(f"Error fetching parking spaces: {e}")
        return []
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()


def create_parking_request(user_id, space_id, vehicle_number):
    try:
        conn = create_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO parking_requests (user_id, space_id, vehicle_number, status)
            VALUES (%s, %s, %s, 'PENDING')
        """, (user_id, space_id, vehicle_number))

        conn.commit()
        return True

    except Error as e:
        print(f"Error creating parking request: {e}")
        return False
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()


def get_provider_requests(provider_id):
    """Get all parking requests for a provider's spaces"""
    try:
        conn = create_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT 
                pr.id,
                u.full_name as user_name,
                pr.vehicle_number,
                pr.duration_hours,
                pr.status,
                pr.request_time,
                ps.address as space_address,
                ps.rate_per_hour
            FROM parking_requests pr
            JOIN users u ON pr.user_id = u.id
            JOIN parking_spaces ps ON pr.space_id = ps.id
            WHERE ps.provider_id = %s
            ORDER BY pr.request_time DESC
        """, (provider_id,))

        return cursor.fetchall()
    except Error as e:
        print(f"Error fetching provider requests: {e}")
        return []
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()


def update_request_status(request_id, status):
    """Update parking request status"""
    try:
        conn = create_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE parking_requests 
            SET status = %s 
            WHERE id = %s
        """, (status, request_id))

        conn.commit()
        return True
    except Error as e:
        print(f"Error updating request: {e}")
        return False
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()


def generate_bill(request_id, amount):
    """Generate a bill for a parking request."""
    try:
        conn = create_db_connection()  # Establish DB connection
        cursor = conn.cursor()

        # Fetch user_id from parking_requests table
        cursor.execute("SELECT user_id FROM parking_requests WHERE id = %s", (request_id,))
        result = cursor.fetchone()

        if not result:
            print("Error: No matching request found.")
            return False

        user_id = result[0]  # Extract user_id

        # Insert the bill into the database with user_id
        cursor.execute("""
            INSERT INTO bills (request_id, user_id, amount, status) 
            VALUES (%s, %s, %s, 'PENDING')
        """, (request_id, user_id, amount))

        conn.commit()  # Save changes
        cursor.close()
        conn.close()  # Close connection

        return True
    except Exception as e:
        print(f"Error generating bill: {e}")  # Debugging output
        return False


def calculate_bill(request_id):
    try:
        conn = create_db_connection()
        cursor = conn.cursor()

        # Get request details
        cursor.execute("""
            SELECT duration_hours, rate_per_hour 
            FROM parking_requests pr
            JOIN parking_spaces ps ON pr.space_id = ps.id
            WHERE pr.id = %s
        """, (request_id,))
        request_data = cursor.fetchone()

        if not request_data:
            return False

        # Calculate amount
        duration = request_data[0]
        rate = request_data[1]
        amount = duration * rate

        return {
            'amount': amount,
            'duration': duration
        }

    except Error as e:
        print(f"Error calculating bill: {e}")
        return False
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()


def get_pending_bills(user_id):
    """Get all pending bills for a user"""
    try:
        conn = create_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT b.*, ps.address, ps.rate_per_hour 
            FROM bills b
            JOIN parking_spaces ps ON b.space_id = ps.id
            WHERE b.user_id = %s AND b.status = 'PENDING'
        """, (user_id,))

        return cursor.fetchall()
    except Error as e:
        print(f"Error fetching bills: {e}")
        return []
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()


def process_payment(bill_id, user_id, amount, payment_method):
    """Process a payment for a bill"""
    try:
        conn = create_db_connection()
        cursor = conn.cursor()

        # Create payment record
        cursor.execute("""
            INSERT INTO payments 
            (bill_id, user_id, amount, payment_method, status)
            VALUES (%s, %s, %s, %s, 'SUCCESS')
        """, (bill_id, user_id, amount, payment_method))

        # Update bill status
        cursor.execute("""
            UPDATE bills 
            SET status = 'PAID' 
            WHERE id = %s
        """, (bill_id,))

        conn.commit()
        return True
    except Error as e:
        print(f"Error processing payment: {e}")
        return False
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

def mark_bill_as_paid(user_id):
    conn = create_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE bills
            SET status = 'PAID'
            WHERE user_id = %s AND status = 'PENDING'
        """, (user_id,))
        conn.commit()
    finally:
        cursor.close()
        conn.close()



# Initialize database if this file is run directly
if __name__ == "__main__":
    initialize_database()
