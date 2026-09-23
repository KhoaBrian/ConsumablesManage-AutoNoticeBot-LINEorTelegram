import calendar
import ctypes
import logging
import os
import sqlite3
from collections import defaultdict
from datetime import datetime

import bcrypt
import pandas as pd
import utils

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_DIR = utils.get_base_path(__file__)
STABLE_DATABASE_FILE = os.path.join(BASE_DIR, 'lab_chemicals.db')
DATABASE_FILE = STABLE_DATABASE_FILE
logging.info("Using database file: %s", DATABASE_FILE)


def get_stock_and_last_fillin(chemical_name):
    """Return current stock and the latest FillIn details for a chemical."""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    result = {
        'name': None,
        'current_stock': None,
        'last_fillin_by': None,
        'last_fillin_qty': None,
        'last_fillin_date': None
    }

    try:
        cursor.execute("SELECT chemical_id, name, current_stock FROM Chemicals WHERE LOWER(name) = LOWER(?)", (chemical_name.strip(),))
        chem_data = cursor.fetchone()

        if not chem_data:
            return None

        result['name'] = chem_data['name']
        result['current_stock'] = chem_data['current_stock']
        chemical_id = chem_data['chemical_id']

        cursor.execute("""
            SELECT timestamp, username_logged, quantity
            FROM Transactions
            WHERE chemical_id = ? AND transaction_type = 'FillIn'
            ORDER BY timestamp DESC
            LIMIT 1
        """, (chemical_id,))
        
        last_fillin_data = cursor.fetchone()

        if last_fillin_data:
            result['last_fillin_date'] = last_fillin_data['timestamp']
            result['last_fillin_by'] = last_fillin_data['username_logged']
            result['last_fillin_qty'] = last_fillin_data['quantity']

        return result

    except Exception as e:
        logging.error(f"Error in get_stock_and_last_fillin for '{chemical_name}': {e}", exc_info=True)
        return None
    finally:
        conn.close()

def get_monthly_chemical_summary(start_year, start_month, end_year, end_month):
    """Return monthly FillIn and TakeOut totals grouped by chemical."""
    summary_data = []
                                 
    try:
         start_dt_str = f"{start_year}-{start_month:02d}-01 00:00:00"
                                            
         end_day = calendar.monthrange(end_year, end_month)[1]
         end_dt_str = f"{end_year}-{end_month:02d}-{end_day:02d} 23:59:59"
         logging.info(f"Fetching monthly summary from {start_dt_str} to {end_dt_str}")
    except ValueError:
         logging.error("Invalid year/month provided for summary report.")
         return None                                          

    conn = sqlite3.connect(DATABASE_FILE)
                                      
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
                                                 
                                       
        cursor.execute("""
            SELECT
                strftime('%Y', timestamp) as Year,
                strftime('%m', timestamp) as Month,
                chemical_name_logged as Chemical,
                transaction_type as Type,
                SUM(quantity) as TotalQuantity
            FROM Transactions
            WHERE timestamp BETWEEN ? AND ?
              AND transaction_type IN ('FillIn', 'TakeOut')
              AND quantity > 0
            GROUP BY Year, Month, Chemical, Type
            ORDER BY Year, Month, Chemical, Type
        """, (start_dt_str, end_dt_str))

        summary_data = [dict(row) for row in cursor.fetchall()]
        logging.info(f"Found {len(summary_data)} summary entries.")

    except Exception as e:
        logging.error(f"Error fetching monthly chemical summary: {e}", exc_info=True)
        summary_data = None                         
    finally:
        conn.close()

    return summary_data

def update_user_password(user_id, new_password):
    """Update the password for the current user."""
    if not new_password:
        return False, "New password cannot be empty."

    new_hashed_pw = hash_password(new_password)
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE Users SET password_hash = ? WHERE user_id = ?", (new_hashed_pw, user_id))
        conn.commit()
        if cursor.rowcount > 0:
            logging.info(f"Password updated successfully for user ID {user_id}")
            return True, "Password updated successfully."
        else:
                                                                                           
            logging.warning(f"Attempted to update password for non-existent user ID {user_id}")
            return False, "User not found."
    except Exception as e:
        conn.rollback()
        logging.error(f"Error updating password for user ID {user_id}: {e}", exc_info=True)
        return False, f"Database error: {e}"
    finally:
        conn.close()

def update_transaction_note(transaction_id, new_note, performing_user_id):
    """Updates the notes for a specific transaction and logs the audit with username."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    success = False
    message = ""
    try:
        performing_username = get_username_by_id(performing_user_id)                                              

        cursor.execute("SELECT notes FROM Transactions WHERE transaction_id = ?", (transaction_id,))
        original_note_tuple = cursor.fetchone()
        original_note = original_note_tuple[0] if original_note_tuple else None

        conn.execute("BEGIN TRANSACTION")                      

        cursor.execute("UPDATE Transactions SET notes = ? WHERE transaction_id = ?",
                       (new_note, transaction_id))

        if cursor.rowcount == 0:
                                                    
            message = f"Transaction ID {transaction_id} not found."
            success = False
                                      
        else:
                                                                
            audit_details = f"User '{performing_username}' updated notes for transaction ID {transaction_id}. New note: '{new_note}'. Old note: '{original_note}'"
            log_success = log_audit_event(performing_user_id, 'Edit Transaction Note', 'Transactions', transaction_id, audit_details, cursor=cursor)
                                                                             

            conn.commit()                           
            logging.info(f"Note updated for transaction {transaction_id} by User '{performing_username}' (ID: {performing_user_id}). Audit log attempted.")
            message = "Transaction note updated successfully."
            success = True

    except Exception as e:
        conn.rollback()                                            
        logging.error(f"Error updating note for transaction {transaction_id}: {e}", exc_info=True)
        message = f"Database error during note update: {e}"
        success = False
    finally:
        conn.close()                          

    return success, message

                                 
def initialize_database():
    """Creates database tables if they don't exist and ensures a default admin exists if needed."""
                                                             
    db_existed = os.path.exists(DATABASE_FILE)

    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    try:
                    
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                is_admin INTEGER DEFAULT 0 NOT NULL CHECK(is_admin IN (0, 1))
            )
        ''')
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_username_nocase ON Users(username COLLATE NOCASE)")

                        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Chemicals (
                chemical_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL COLLATE NOCASE,
                current_stock REAL DEFAULT 0,
                threshold REAL DEFAULT 0
            )
        ''')
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chemical_name ON Chemicals(name)")

                                 
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Transactions (
                transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username_logged TEXT NOT NULL,
                chemical_id INTEGER NOT NULL,
                chemical_name_logged TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                transaction_type TEXT NOT NULL CHECK(transaction_type IN ('FillIn', 'TakeOut', 'Adjust', 'Edit', 'Delete')),
                quantity REAL NOT NULL,
                notes TEXT,
                FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE SET NULL,
                FOREIGN KEY (chemical_id) REFERENCES Chemicals(chemical_id) ON DELETE RESTRICT
            )
        ''')
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transaction_time ON Transactions(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transaction_chem ON Transactions(chemical_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transaction_user ON Transactions(user_id)")

                       
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS AuditLog (
                audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_user_id INTEGER NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                action_type TEXT NOT NULL,
                target_table TEXT,
                target_id INTEGER,
                details TEXT,
                FOREIGN KEY (admin_user_id) REFERENCES Users(user_id)
            )
        ''')

                                              
                                                                                                
                                                         
        cursor.execute("SELECT COUNT(*) FROM Users WHERE is_admin = 1")
        admin_count = cursor.fetchone()[0]

        if admin_count == 0:
            default_admin_user = 'admin'
            default_admin_pass = 'admin'                           
                                                                                  
            cursor.execute("SELECT user_id FROM Users WHERE LOWER(username) = LOWER(?) AND is_admin = 0", (default_admin_user,))
            non_admin_exists = cursor.fetchone()

            if non_admin_exists:
                 logging.warning(f"Username '{default_admin_user}' already exists as a non-admin user. Cannot create default admin.")
            else:
                                                                                                                                   
                try:
                                                                                                         
                    hashed_pw = hash_password(default_admin_pass)
                    cursor.execute("INSERT OR IGNORE INTO Users (username, password_hash, is_admin) VALUES (?, ?, ?)",
                                   (default_admin_user, hashed_pw, 1))
                    if cursor.rowcount > 0:                                    
                       conn.commit()                                        
                       logging.info(f"*** Default admin user '{default_admin_user}' created with password '{default_admin_pass}'. Please change it. ***")
                    else:
                                                                                                 
                       logging.info(f"Default admin user '{default_admin_user}' already exists or could not be created.")

                except Exception as e:
                    conn.rollback()                                    
                    logging.error(f"Failed to create default admin user: {e}", exc_info=True)
        else:
            logging.info("Admin user(s) already exist. Default admin creation skipped.")

        conn.commit()                                           
        
                                                                      
        if not db_existed and os.name == 'nt':                                                                
            try:
                                         
                attrs = ctypes.windll.kernel32.GetFileAttributesW(DATABASE_FILE)
                if attrs != -1:                                   
                                                                   
                    result = ctypes.windll.kernel32.SetFileAttributesW(DATABASE_FILE, attrs | 0x02)
                    if result:
                        logging.info(f"Successfully set hidden attribute for '{DATABASE_FILE}'.")
                    else:
                        logging.warning(f"Failed to set hidden attribute for '{DATABASE_FILE}'. Error code: {ctypes.get_last_error()}")
                else:
                     logging.warning(f"Could not get attributes for '{DATABASE_FILE}'. Error code: {ctypes.get_last_error()}")
            except Exception as e_hide:
                logging.error(f"Error attempting to hide database file: {e_hide}", exc_info=True)
                                       

        if not db_existed:
               logging.info("Database '%s' created and initialized.", DATABASE_FILE)
        else:
               logging.info("Database '%s' checked/initialized successfully.", DATABASE_FILE)

    except Exception as e:
        logging.error(f"Error during database initialization: {e}", exc_info=True)
        if conn: conn.rollback()                                   
    finally:
        if conn: conn.close()                    

def get_transaction_details(transaction_id):
    """Gets specific details of a transaction, including user_id."""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT t.transaction_id, t.user_id, t.username_logged, t.chemical_id,
                   t.chemical_name_logged, t.timestamp, t.transaction_type, t.quantity, t.notes
            FROM Transactions t
            WHERE t.transaction_id = ?
        """, (transaction_id,))
        transaction = cursor.fetchone()
        return dict(transaction) if transaction else None
    except Exception as e:
        logging.error(f"Error getting transaction details for ID {transaction_id}: {e}", exc_info=True)
        return None
    finally:
        conn.close()

def log_audit_event(performing_user_id, action_type, target_table, target_id, details, cursor=None):
    """Logs an action to the AuditLog table.
       Uses the provided cursor if available, otherwise creates a new connection.
       Does NOT commit if using a provided cursor.
    """
    conn = None                        
    internal_cursor = False                                         

    try:
        if cursor is None:
                                                                          
            conn = sqlite3.connect(DATABASE_FILE, timeout=10)                       
            cursor = conn.cursor()
            internal_cursor = True                                

                                                                              
        cursor.execute("""
            INSERT INTO AuditLog (admin_user_id, action_type, target_table, target_id, details, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (performing_user_id, action_type, target_table, target_id, details, datetime.now()))

        if internal_cursor:
                                                              
            conn.commit()
            logging.info(f"Audit log (new conn): UserID {performing_user_id} performed {action_type} on {target_table}({target_id}). Details: {details}")
        else:
                                                                    
            logging.info(f"Audit log (existing conn): UserID {performing_user_id} performed {action_type} on {target_table}({target_id}). Details: {details}")

        return True                                                       

    except sqlite3.OperationalError as e:
                                                           
        logging.error(f"Error logging audit event (OperationalError): {e}. Details: UserID {performing_user_id}, Action: {action_type}, Target: {target_table}({target_id})", exc_info=True)
        if internal_cursor and conn:
            conn.rollback()                                           
                                                                   
        return False                          
    except Exception as e:
        logging.error(f"Error logging audit event (General Exception): {e}", exc_info=True)
        if internal_cursor and conn:
            conn.rollback()
        return False
    finally:
                                                            
        if internal_cursor and conn:
            conn.close()

def get_all_users_details():
    """Return all users with IDs, usernames, and administrator status."""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    users = []
    try:
        cursor.execute("SELECT user_id, username, is_admin FROM Users ORDER BY username COLLATE NOCASE ASC")
        users = [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        logging.error(f"Error fetching all user details: {e}", exc_info=True)
    finally:
        conn.close()
    return users

def reset_user_password(user_id, new_password, admin_user_id):
    """Reset a user's password as an administrator."""
    if not new_password:
        return False, "New password cannot be empty."
    new_hashed_pw = hash_password(new_password)
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    success = False
    message = ""
    try:
        conn.execute("BEGIN TRANSACTION")                      
        cursor.execute("UPDATE Users SET password_hash = ? WHERE user_id = ?", (new_hashed_pw, user_id))

        if cursor.rowcount > 0:
                                                                
            log_success = log_audit_event(admin_user_id, 'Reset Password', 'Users', user_id, f"Password reset for user ID {user_id}", cursor=cursor)
            conn.commit()                     
            logging.info(f"Password reset successfully for user ID {user_id} by admin ID {admin_user_id}. Audit log attempted.")
            message = "Password reset successfully."
            success = True
        else:
                                                    
            message = "User not found."
            success = False
                                     
    except Exception as e:
        conn.rollback()                      
        logging.error(f"Error resetting password for user ID {user_id}: {e}", exc_info=True)
        message = f"Database error: {e}"
        success = False
    finally:
        conn.close()                    
    return success, message

def set_admin_status(user_id, is_admin_flag, admin_user_id):
    """Change a user's administrator status."""
    is_admin = 1 if is_admin_flag else 0
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    success = False
    message = ""
    try:
                                                                       
        if not is_admin_flag:
            cursor.execute("SELECT COUNT(*) FROM Users WHERE is_admin = 1")
            admin_count = cursor.fetchone()[0]
            cursor.execute("SELECT is_admin FROM Users WHERE user_id = ?", (user_id,))
            current_status = cursor.fetchone()
            if current_status and current_status[0] == 1 and admin_count <= 1:
                conn.close()                                
                return False, "Cannot remove the last admin."

        conn.execute("BEGIN TRANSACTION")                      
        cursor.execute("UPDATE Users SET is_admin = ? WHERE user_id = ?", (is_admin, user_id))

        if cursor.rowcount > 0:
            action = "Granted Admin" if is_admin_flag else "Revoked Admin"
                                                                
            log_success = log_audit_event(admin_user_id, action, 'Users', user_id, f"{action} status for user ID {user_id}", cursor=cursor)
            conn.commit()                     
            logging.info(f"{action} status successfully for user ID {user_id} by admin ID {admin_user_id}. Audit log attempted.")
            message = "Admin status updated successfully."
            success = True
        else:
                                
            message = "User not found."
            success = False
                          

    except Exception as e:
        conn.rollback()                      
        logging.error(f"Error setting admin status for user ID {user_id}: {e}", exc_info=True)
        message = f"Database error: {e}"
        success = False
    finally:
        conn.close()                    
    return success, message

def delete_user(user_id_to_delete, admin_user_id):
    """Delete a user as an administrator."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    success = False
    message = ""
    try:
                                                                                              
        cursor.execute("SELECT is_admin, username FROM Users WHERE user_id = ?", (user_id_to_delete,))                           
        user_to_delete = cursor.fetchone()
        if not user_to_delete:
            conn.close()
            return False, "User not found."
        is_admin_to_delete, username_to_delete = user_to_delete

        if user_id_to_delete == admin_user_id:
            conn.close()
            return False, "Admin cannot delete themselves."

        if is_admin_to_delete == 1:
            cursor.execute("SELECT COUNT(*) FROM Users WHERE is_admin = 1")
            admin_count = cursor.fetchone()[0]
            if admin_count <= 1:
                conn.close()
                return False, "Cannot delete the last admin user."

        conn.execute("BEGIN TRANSACTION")                      
        cursor.execute("DELETE FROM Users WHERE user_id = ?", (user_id_to_delete,))

        if cursor.rowcount > 0:
                                                                 
            log_success = log_audit_event(admin_user_id, 'Delete User', 'Users', user_id_to_delete, f"Deleted user '{username_to_delete}' (ID: {user_id_to_delete})", cursor=cursor)
            conn.commit()                     
            logging.info(f"User '{username_to_delete}' (ID: {user_id_to_delete}) deleted successfully by admin ID {admin_user_id}. Audit log attempted.")
            message = "User deleted successfully."
            success = True
        else:
                                 
             message = "User not found or could not be deleted."
             success = False
                           

    except Exception as e:
        conn.rollback()                      
        logging.error(f"Error deleting user ID {user_id_to_delete}: {e}", exc_info=True)
        message = f"Database error: {e}"
        success = False
    finally:
        conn.close()                    
    return success, message

def get_username_by_id(user_id):
    """Helper function to get username from user ID."""
                                                         
    if user_id is None:
        return "Unknown_User"                             

    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT username FROM Users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        return result[0] if result else f"UserID_{user_id}"                                                 
    except Exception as e:
        logging.error(f"Error getting username for ID {user_id}: {e}")
        return f"UserID_{user_id}"                       
    finally:
        conn.close()

def mark_transaction_deleted(transaction_id, performing_user_id, reason):
    """Marks a transaction as deleted, logs username, and adjusts stock."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    success = False
    message = ""
    try:
        performing_username = get_username_by_id(performing_user_id)                   

        cursor.execute("SELECT chemical_id, transaction_type, quantity, notes FROM Transactions WHERE transaction_id = ?", (transaction_id,))
        original_data = cursor.fetchone()
        if not original_data:
            return False, f"Transaction ID {transaction_id} not found."

        chemical_id, original_type, original_quantity, original_notes = original_data

        conn.execute("BEGIN TRANSACTION")                      

                                       
        current_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        delete_info = f"-- DELETED by '{performing_username}' on {current_time_str}. Reason: {reason} --"
        new_note = (original_notes + delete_info) if original_notes else delete_info.strip()
        cursor.execute("""
            UPDATE Transactions
            SET transaction_type = 'Delete', notes = ?
            WHERE transaction_id = ?
        """, (new_note, transaction_id))

                               
        stock_change = 0.0
        if original_type == 'TakeOut':
            stock_change = original_quantity
        elif original_type == 'FillIn':
            stock_change = -original_quantity

        if stock_change != 0:
            cursor.execute("UPDATE Chemicals SET current_stock = current_stock + ? WHERE chemical_id = ?",
                           (stock_change, chemical_id))
            logging.info(f"Stock adjusted by {stock_change} for chemical_id {chemical_id} due to deletion of transaction {transaction_id}")

                                                       
                                                            
        audit_details = f"Marked transaction as deleted (Orig Type: {original_type}, Qty: {original_quantity}). Reason: {reason}. Stock changed by: {stock_change}."
        log_success = log_audit_event(performing_user_id, 'Delete Transaction', 'Transactions', transaction_id, audit_details, cursor=cursor)

                                                                            
        conn.commit()
        logging.info(f"Transaction {transaction_id} marked as deleted by User '{performing_username}' (ID: {performing_user_id}). Audit log attempted.")
        message = f"Transaction {transaction_id} marked as deleted."
        success = True

    except Exception as e:
        conn.rollback()                                     
        logging.error(f"Error deleting transaction {transaction_id}: {e}", exc_info=True)
        message = f"Database error during deletion: {e}"
        success = False
    finally:
        conn.close()                          

    return success, message    
        
                             
def hash_password(password):
    """Hashes a password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')                  

def check_password(stored_hash, provided_password):
    """Checks a provided password against a stored hash."""
    if not stored_hash or not provided_password:
        return False
    try:
        return bcrypt.checkpw(provided_password.encode('utf-8'), stored_hash.encode('utf-8'))
    except ValueError:                                    
        return False

                         
def add_user(username, password, is_admin=0):
    """Adds a new user."""
    if not username or not password:
        logging.error("Username and password cannot be empty.")
        return False, "Username and password cannot be empty."

    hashed_pw = hash_password(password)
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO Users (username, password_hash, is_admin) VALUES (?, ?, ?)",
                       (username, hashed_pw, is_admin))
        conn.commit()
        logging.info("User '%s' added successfully.", username)
        return True, f"User '{username}' added."
    except sqlite3.IntegrityError:
        logging.error("Username '%s' already exists.", username)
        return False, f"Username '{username}' already exists."
    except Exception as e:
        logging.error("Error adding user: %s", e)
        return False, f"Error adding user: {e}"
    finally:
        conn.close()

def get_user(username):
    """Gets user info by username (case-insensitive)."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
                                                 
    cursor.execute("SELECT user_id, username, password_hash, is_admin FROM Users WHERE LOWER(username) = LOWER(?)", (username,))
    user_data = cursor.fetchone()
    conn.close()
                                                                         
    return user_data

def verify_user(username, password):
    """Verifies a user's credentials and returns user info if valid."""
    user_data = get_user(username)
    if user_data and check_password(user_data[2], password):
                                               
        return {'user_id': user_data[0], 'username': user_data[1], 'is_admin': bool(user_data[3])}
    return None

def get_all_user_names(include_admin=True):
    """Gets a list of all usernames."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    query = "SELECT username FROM Users"
    if not include_admin:
        query += " WHERE is_admin = 0"
    query += " ORDER BY username COLLATE NOCASE ASC"                        
    try:
        cursor.execute(query)
        names = [row[0] for row in cursor.fetchall()]
    except Exception as e:
        logging.error("Error fetching usernames: %s", e)
        names = []
    finally:
        conn.close()
    return names

                             
def add_chemical(name, initial_stock=0.0, threshold=0.0):
    """Adds a new chemical."""
    if not name:
        return False, "Chemical name cannot be empty."
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    try:
                                                                                         
        cursor.execute("INSERT OR IGNORE INTO Chemicals (name, current_stock, threshold) VALUES (?, ?, ?)",
                       (name.strip(), float(initial_stock), float(threshold)))
        conn.commit()
        if cursor.lastrowid:
            logging.info("Chemical '%s' added successfully with ID %s.", name, cursor.lastrowid)
            return True, f"Chemical '{name}' added."
        else:
                                                            
            logging.info("Chemical '%s' might already exist.", name)
            return True, f"Chemical '{name}' already exists or failed to add."

    except sqlite3.IntegrityError:                                                  
        logging.error("Chemical '%s' likely already exists.", name)
        return False, f"Chemical '{name}' already exists."
    except (ValueError, TypeError) as e:
         logging.error("Error adding chemical '%s': invalid stock or threshold format: %s", name, e)
         return False, "Invalid number format for stock or threshold."
    except Exception as e:
        logging.error("Error adding chemical '%s': %s", name, e)
        return False, f"Error adding chemical: {e}"
    finally:
        conn.close()


def get_chemical(name):
    """Gets chemical info by name (case-insensitive)."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
                                               
    cursor.execute("SELECT chemical_id, name, current_stock, threshold FROM Chemicals WHERE LOWER(name) = LOWER(?)", (name.strip(),))
    chem_data = cursor.fetchone()
    conn.close()
    if chem_data:
        return {'chemical_id': chem_data[0], 'name': chem_data[1], 'current_stock': chem_data[2], 'threshold': chem_data[3]}
    return None

def update_chemical_stock(chemical_id, change_amount):
    """Updates chemical stock. Returns new stock and threshold or None on error."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE Chemicals SET current_stock = current_stock + ? WHERE chemical_id = ?",
                       (change_amount, chemical_id))
        conn.commit()
                              
        cursor.execute("SELECT current_stock, threshold FROM Chemicals WHERE chemical_id = ?", (chemical_id,))
        updated_data = cursor.fetchone()
        return updated_data                                     
    except Exception as e:
        logging.error("Error updating stock for chemical_id %s: %s", chemical_id, e)
        conn.rollback()                             
        return None
    finally:
        conn.close()

def get_all_chemical_names():
    """Gets a list of all chemical names."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT name FROM Chemicals ORDER BY name COLLATE NOCASE ASC")                        
        names = [row[0] for row in cursor.fetchall()]
    except Exception as e:
        logging.error("Error fetching chemical names: %s", e)
        names = []
    finally:
        conn.close()
    return names

def get_all_chemicals_details():
    """Return all chemicals with IDs, stock, and thresholds."""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row                              
    cursor = conn.cursor()
    chemicals = []
    try:
        cursor.execute("SELECT chemical_id, name, current_stock, threshold FROM Chemicals ORDER BY name COLLATE NOCASE ASC")
        chemicals = [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        logging.error(f"Error fetching all chemical details: {e}", exc_info=True)
    finally:
        conn.close()
    return chemicals

def get_chemical_by_id(chemical_id):
    """Gets chemical info by ID."""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT chemical_id, name, current_stock, threshold FROM Chemicals WHERE chemical_id = ?", (chemical_id,))
        chem_data = cursor.fetchone()
        return dict(chem_data) if chem_data else None
    except Exception as e:
         logging.error(f"Error getting chemical by ID {chemical_id}: {e}", exc_info=True)
         return None
    finally:
        conn.close()

def update_chemical_details(chemical_id, name, threshold, admin_user_id):
    """Updates chemical name and threshold (Admin only). Stock is NOT updated here."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    success = False
    message = ""
    try:
                                                       
        cursor.execute("SELECT chemical_id FROM Chemicals WHERE LOWER(name) = LOWER(?) AND chemical_id != ?", (name.strip(), chemical_id))
        existing = cursor.fetchone()
        if existing:
            conn.close()
            return False, f"Chemical name '{name.strip()}' already exists for another chemical (ID: {existing[0]})."

        conn.execute("BEGIN TRANSACTION")                      
        cursor.execute("""
            UPDATE Chemicals
            SET name = ?, threshold = ?
            WHERE chemical_id = ?
        """, (name.strip(), float(threshold), chemical_id))

        if cursor.rowcount > 0:
                                                                 
            log_success = log_audit_event(admin_user_id, 'Update Chemical Details', 'Chemicals', chemical_id, f"Updated Name='{name.strip()}', Threshold={threshold}", cursor=cursor)
            conn.commit()                     
            logging.info(f"Updated details for chemical_id {chemical_id}: Name='{name.strip()}', Threshold={threshold}. Audit log attempted.")
            message = "Chemical details (Name/Threshold) updated successfully."
            success = True
        else:
                                 
             message = "Chemical not found or no changes made."
             success = False
                           

    except sqlite3.IntegrityError:
         conn.rollback()                                
         logging.warning(f"Update failed for chemical_id {chemical_id}: Name '{name.strip()}' might already exist.")
         message = f"Update failed: Chemical name '{name.strip()}' likely already exists."
         success = False
    except (ValueError, TypeError) as e:
                                                                 
         logging.error(f"Update failed for chemical_id {chemical_id}: Invalid number format for threshold. {e}", exc_info=True)
         message = "Invalid number format for threshold."
         success = False
    except Exception as e:
        conn.rollback()                            
        logging.error(f"Error updating chemical details for ID {chemical_id}: {e}", exc_info=True)
        message = f"Database error during update: {e}"
        success = False
    finally:
        conn.close()                    
    return success, message


def delete_chemical(chemical_id, performing_user_id):
    """Delete a chemical when no related transactions exist."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    success = False
    message = ""
    try:
                                                         
        cursor.execute("SELECT COUNT(*) FROM Transactions WHERE chemical_id = ?", (chemical_id,))
        count = cursor.fetchone()[0]
        if count > 0:
            conn.close()
            return False, f"Cannot delete chemical: It has existing transaction records ({count}). Consider marking it as inactive instead."

                                     
        cursor.execute("SELECT name FROM Chemicals WHERE chemical_id = ?", (chemical_id,))
        chem_info = cursor.fetchone()
        chem_name_to_delete = chem_info[0] if chem_info else f"ID {chemical_id}"

        conn.execute("BEGIN TRANSACTION")                      
        cursor.execute("DELETE FROM Chemicals WHERE chemical_id = ?", (chemical_id,))

        if cursor.rowcount > 0:
                                                                
            log_success = log_audit_event(performing_user_id, 'Delete Chemical', 'Chemicals', chemical_id, f"Deleted chemical '{chem_name_to_delete}' (ID: {chemical_id})", cursor=cursor)
            conn.commit()                     
            logging.info(f"Chemical '{chem_name_to_delete}' (ID: {chemical_id}) deleted by UserID {performing_user_id}. Audit log attempted.")
            message = "Chemical deleted successfully."
            success = True
        else:
                                
            message = "Chemical not found or already deleted."
            success = False
                          

    except sqlite3.IntegrityError as e:
        conn.rollback()                                 
        logging.error(f"Integrity error deleting chemical {chemical_id}: {e}", exc_info=True)
        message = f"Cannot delete chemical due to existing references: {e}"
        success = False
    except Exception as e:
        conn.rollback()                            
        logging.error(f"Error deleting chemical {chemical_id}: {e}", exc_info=True)
        message = f"Database error during deletion: {e}"
        success = False
    finally:
        conn.close()                    
    return success, message


def get_low_stock_chemicals():
    """Return chemicals whose stock is at or below their thresholds."""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    low_stock = []
    try:
                                                                         
        cursor.execute("""
            SELECT name, current_stock, threshold
            FROM Chemicals
            WHERE threshold > 0 AND current_stock <= threshold
            ORDER BY name COLLATE NOCASE ASC
        """)
        low_stock = [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        logging.error(f"Error fetching low stock chemicals: {e}", exc_info=True)
    finally:
        conn.close()
    return low_stock

def get_monthly_usage_summary(year, month):
    """Return chemical usage totals for a specific month."""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    summary = []
    start_date = f"{year}-{month:02d}-01 00:00:00"
                          
    import calendar
    last_day = calendar.monthrange(year, month)[1]
    end_date = f"{year}-{month:02d}-{last_day:02d} 23:59:59"

    try:
        cursor.execute("""
            SELECT
                chemical_name_logged,
                SUM(CASE WHEN transaction_type = 'FillIn' THEN quantity ELSE 0 END) as total_fillin,
                SUM(CASE WHEN transaction_type = 'TakeOut' THEN quantity ELSE 0 END) as total_takeout
            FROM Transactions
            WHERE timestamp BETWEEN ? AND ? AND transaction_type IN ('FillIn', 'TakeOut')
            GROUP BY chemical_name_logged
            ORDER BY chemical_name_logged COLLATE NOCASE ASC
        """, (start_date, end_date))
        summary = [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        logging.error(f"Error fetching monthly summary for {year}-{month}: {e}", exc_info=True)
    finally:
        conn.close()
    return summary

                                                     
def get_user_activity_summary(year, month):
    """Return user activity totals for a specific month."""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    summary = {'users': {}, 'whoknows': {'takeout': 0.0, 'fillin': 0.0}}
    start_date = f"{year}-{month:02d}-01 00:00:00"
    last_day = calendar.monthrange(year, month)[1]
    end_date = f"{year}-{month:02d}-{last_day:02d} 23:59:59"

    try:
        cursor.execute("""
            SELECT
                username_logged,
                transaction_type,
                SUM(quantity) as total_quantity
            FROM Transactions
            WHERE timestamp BETWEEN ? AND ?
              AND transaction_type IN ('FillIn', 'TakeOut')
              AND username_logged IS NOT NULL
            GROUP BY username_logged, transaction_type
        """, (start_date, end_date))

        results = cursor.fetchall()

                          
        temp_users = {}
        for row in results:
            username = row['username_logged']
            ttype = row['transaction_type']
            total = row['total_quantity'] if row['total_quantity'] is not None else 0.0

                                  
            is_whoknows_variant = 'whoknows' in username.lower() or '(imported' in username.lower()

            if is_whoknows_variant:
                if ttype == 'TakeOut':
                    summary['whoknows']['takeout'] += total
                elif ttype == 'FillIn':
                    summary['whoknows']['fillin'] += total
            else:
                                   
                if username not in temp_users:
                    temp_users[username] = {'takeout': 0.0, 'fillin': 0.0}

                if ttype == 'TakeOut':
                    temp_users[username]['takeout'] += total
                elif ttype == 'FillIn':
                    temp_users[username]['fillin'] += total

                                       
        summary['users'] = {user: data for user, data in temp_users.items() if data['takeout'] > 0 or data['fillin'] > 0}

    except Exception as e:
        logging.error(f"Error fetching user activity summary for {year}-{month}: {e}", exc_info=True)
    finally:
        conn.close()

                                                          
    max_takeout = ('N/A', 0.0)
    min_takeout = ('N/A', float('inf'))
    max_fillin = ('N/A', 0.0)
    min_fillin = ('N/A', float('inf'))

    if summary['users']:                                 
                     
        max_takeout_user = max(summary['users'], key=lambda u: summary['users'][u]['takeout'])
        max_takeout = (max_takeout_user, summary['users'][max_takeout_user]['takeout'])

                                                                              
        active_takeout_users = {u: d['takeout'] for u, d in summary['users'].items() if d['takeout'] > 0}
        if active_takeout_users:
             min_takeout_user = min(active_takeout_users, key=active_takeout_users.get)
             min_takeout = (min_takeout_user, active_takeout_users[min_takeout_user])
        else:                           
             min_takeout = ('N/A', 0.0)                            


                    
        max_fillin_user = max(summary['users'], key=lambda u: summary['users'][u]['fillin'])
        max_fillin = (max_fillin_user, summary['users'][max_fillin_user]['fillin'])

                               
        active_fillin_users = {u: d['fillin'] for u, d in summary['users'].items() if d['fillin'] > 0}
        if active_fillin_users:
            min_fillin_user = min(active_fillin_users, key=active_fillin_users.get)
            min_fillin = (min_fillin_user, active_fillin_users[min_fillin_user])
        else:                          
             min_fillin = ('N/A', 0.0)        

    summary['stats'] = {
        'max_takeout': max_takeout,
        'min_takeout': min_takeout if min_takeout[1] != float('inf') else ('N/A', 0.0),                         
        'max_fillin': max_fillin,
        'min_fillin': min_fillin if min_fillin[1] != float('inf') else ('N/A', 0.0)                          
    }

    logging.info(f"User activity summary for {year}-{month} generated.")
    return summary


                                      
def add_transaction(user_id, username_logged, chemical_id, chemical_name_logged, transaction_type, quantity, notes=None):
    """Adds a new transaction and updates stock."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    change_amount = 0
    if transaction_type == 'FillIn':
        change_amount = quantity
    elif transaction_type == 'TakeOut':
        change_amount = -quantity
                                                                                   
                                                                   

    try:
                                         
        conn.execute("BEGIN TRANSACTION")

                                         
        cursor.execute("""
            INSERT INTO Transactions (user_id, username_logged, chemical_id, chemical_name_logged, transaction_type, quantity, notes, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, username_logged, chemical_id, chemical_name_logged, transaction_type, quantity, notes, datetime.now()))

                                               
        if transaction_type in ['FillIn', 'TakeOut']:
            cursor.execute("UPDATE Chemicals SET current_stock = current_stock + ? WHERE chemical_id = ?",
                           (change_amount, chemical_id))

        conn.commit()                               
        logging.info("Transaction logged: %s, %s %s %s", username_logged, transaction_type, quantity, chemical_name_logged)

                                                                
        cursor.execute("SELECT current_stock, threshold FROM Chemicals WHERE chemical_id = ?", (chemical_id,))
        stock_data = cursor.fetchone()
        conn.close()                                    

        if stock_data:
            is_low = stock_data[0] is not None and stock_data[1] is not None and stock_data[0] <= stock_data[1]
            return {'low_stock': is_low, 'chemical_name': chemical_name_logged, 'current_stock': stock_data[0]}
        else:
            return {'low_stock': False}                                            

    except Exception as e:
        logging.error("Error adding transaction: %s", e, exc_info=True)
        conn.rollback()                             
        conn.close()
        return {'error': str(e)}
                                                                            


def get_transaction_history(filters=None):
    """Fetches transaction history, optionally applying filters."""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row                                         
    cursor = conn.cursor()

                                                                                   
    query = """
        SELECT
            t.transaction_id,
            strftime('%Y-%m-%d %H:%M:%S', t.timestamp) as timestamp, -- Format timestamp
            t.username_logged,
            t.chemical_name_logged,
            t.transaction_type,
            t.quantity,
            t.notes
        FROM Transactions t
    """
    params = {}                                   
    where_clauses = []

                                       
    if filters:
        if filters.get('start_date'):
            where_clauses.append("t.timestamp >= :start_date")
            params['start_date'] = filters['start_date']                                    
        if filters.get('end_date'):
            where_clauses.append("t.timestamp <= :end_date")
            params['end_date'] = filters['end_date']
        if filters.get('username'):
            where_clauses.append("LOWER(t.username_logged) LIKE LOWER(:username)")
            params['username'] = f"%{filters['username']}%"                        
        if filters.get('chemical_name'):
            where_clauses.append("LOWER(t.chemical_name_logged) LIKE LOWER(:chemical_name)")
            params['chemical_name'] = f"%{filters['chemical_name']}%"
        if filters.get('transaction_type') and filters['transaction_type'] != 'All':
             where_clauses.append("t.transaction_type = :transaction_type")
             params['transaction_type'] = filters['transaction_type']
                                    

    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)

    query += " ORDER BY t.timestamp DESC"                       

    try:
        logging.debug("Executing transaction history query with params: %s", params)
        cursor.execute(query, params)
        history = cursor.fetchall()
                                                              
        return [dict(row) for row in history]
    except Exception as e:
        logging.error("Error fetching transaction history: %s", e, exc_info=True)
        return []                             
    finally:
        conn.close()


                     
def import_from_excel(excel_path):
    """Imports transaction data from the specified Excel format,
       including 'Notes' and handling 'Delete' type."""
    if not os.path.exists(excel_path):
        logging.error(f"Error: Import file not found at '{excel_path}'")
                                       
        return False, f"Import file not found: {excel_path}"

    try:
                                           
        df_check_cols = pd.read_excel(excel_path, sheet_name='Sheet1', nrows=0)
                                                                                            
                                                                                 
        expected_cols = ["Name", "Chemical", "Number", "Type", "Time"]                                     
        actual_cols = [col.strip() for col in df_check_cols.columns]

                                                               
        missing_cols = [col for col in expected_cols if col not in actual_cols]
        if missing_cols:
            error_msg = f"Missing essential columns in Excel file '{os.path.basename(excel_path)}': {', '.join(missing_cols)}"
            logging.error(error_msg)
            return False, error_msg

                                                                          
        dtype_map = {col: str for col in actual_cols}
        df = pd.read_excel(excel_path, sheet_name='Sheet1', dtype=dtype_map, keep_default_na=False)
        logging.info(f"Successfully read {len(df)} rows from {excel_path}")

    except Exception as e:
        error_msg = f"Error reading Excel file '{os.path.basename(excel_path)}': {e}"
        logging.error(error_msg, exc_info=True)
        return False, error_msg

    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

                                                                                
    chemicals_in_db = {row[0].lower(): row[1] for row in cursor.execute("SELECT name, chemical_id FROM Chemicals").fetchall()}
    users_in_db = {row[0].lower(): row[1] for row in cursor.execute("SELECT username, user_id FROM Users").fetchall()}

    imported_count = 0
    skipped_count = 0
    errors = []

                                                                 
    try:
        conn.execute("BEGIN TRANSACTION")
        for index, row in df.iterrows():
            row_num = index + 2                   
            try:
                                        
                name_raw = str(row.get('Name', '')).strip()
                chemical_raw = str(row.get('Chemical', '')).strip()
                number_val = row.get('Number', '')
                number_raw = str(number_val).strip()
                type_raw = str(row.get('Type', '')).strip()
                time_raw = str(row.get('Time', '')).strip()
                                                         
                note_raw = str(row.get('Notes', '')).strip()                             

                                                
                if (not name_raw or name_raw == '0' or name_raw.lower() == 'name') and \
                   (not chemical_raw or chemical_raw == '0' or chemical_raw.lower() == 'chemical') and \
                   (not number_raw or number_raw == '0'):
                    logging.info(f"Skipping empty/placeholder/header row {row_num}: {row.to_dict()}")
                    skipped_count += 1
                    continue
                if not name_raw or not chemical_raw or not number_raw:
                     logging.warning(f"Skipping row {row_num} due to missing essential data: {row.to_dict()}")
                     errors.append(f"Row {row_num}: Missing essential data (Name, Chemical, or Number)")
                     skipped_count += 1
                     continue

                                               
                try:
                    quantity = float(number_raw)
                except ValueError:
                    logging.warning(f"Invalid number format '{number_raw}' in row {row_num}. Skipping.")
                    errors.append(f"Row {row_num}: Invalid quantity format '{number_raw}'")
                    skipped_count += 1
                    continue

                                                                  
                type_clean = type_raw.lower()
                transaction_type = None                   
                if type_clean == "fillin":
                    transaction_type = "FillIn"
                elif type_clean == "takeout":
                    transaction_type = "TakeOut"
                elif type_clean == "delete":                          
                    transaction_type = "Delete"
                                                              
                                              
                                                 
                else:
                                                                                      
                    logging.warning(f"Row {row_num}: Unrecognized Type '{type_raw}', skipping row.")
                    errors.append(f"Row {row_num}: Unrecognized transaction type '{type_raw}'")
                    skipped_count += 1
                    continue                                        

                                 
                try:
                    timestamp_dt = pd.to_datetime(time_raw)
                    timestamp_str = timestamp_dt.strftime('%Y-%m-%d %H:%M:%S')
                except Exception as time_err:
                    logging.warning(f"Invalid timestamp '{time_raw}' in row {row_num}. Skipping. Error: {time_err}")
                    errors.append(f"Row {row_num}: Invalid timestamp '{time_raw}'")
                    skipped_count += 1
                    continue

                                                
                chemical_name_logged = chemical_raw                                  
                chemical_name_lower = chemical_name_logged.lower()
                if chemical_name_lower not in chemicals_in_db:
                                                                                               
                    cursor.execute("SELECT chemical_id FROM Chemicals WHERE LOWER(name) = ?", (chemical_name_lower,))
                    existing_chem = cursor.fetchone()
                    if not existing_chem:
                        cursor.execute("INSERT INTO Chemicals (name) VALUES (?)", (chemical_name_logged,))
                        chemical_id = cursor.lastrowid
                        chemicals_in_db[chemical_name_lower] = chemical_id
                        logging.info(f"  Added new chemical during import: '{chemical_name_logged}' (ID: {chemical_id})")
                    else:
                         chemical_id = existing_chem[0]
                         chemicals_in_db[chemical_name_lower] = chemical_id                          
                else:
                    chemical_id = chemicals_in_db[chemical_name_lower]

                                     
                user_id = None
                username_logged = name_raw                              
                username_lower = username_logged.lower()
                if username_lower not in ['whoknows', '0', ''] :                                   
                    if username_lower in users_in_db:
                        user_id = users_in_db[username_lower]
                    else:
                                                                               
                                                                              
                        logging.warning(f"  User '{username_logged}' not found in Users table for row {row_num}. Logging as Whoknows.")
                        user_id = None                         
                                                                                                                  
                else:
                    user_id = None                                                     

                                                              
                import_marker = "Imported from Excel"
                final_note = note_raw                             
                if note_raw:                                
                                                                                
                    if import_marker not in note_raw:
                        final_note = f"{note_raw} - {import_marker}"
                else:                          
                    final_note = import_marker


                                                                
                cursor.execute("""
                    INSERT INTO Transactions (user_id, username_logged, chemical_id, chemical_name_logged, timestamp, transaction_type, quantity, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (user_id, username_logged, chemical_id, chemical_name_logged, timestamp_str, transaction_type, quantity, final_note))                     
                imported_count += 1

            except Exception as row_err:
                error_msg = f"Row {row_num}: Error processing - {row_err}"
                errors.append(error_msg)
                logging.error(f"Error processing row {row_num}: {row.to_dict()}", exc_info=True)
                skipped_count += 1
                                            

                                                                          
        logging.info("Recalculating final stock levels...")
        cursor.execute("SELECT chemical_id, name FROM Chemicals")
        all_chemicals = cursor.fetchall()
        for chem_id, chem_name in all_chemicals:
                                                                                                
            cursor.execute("""
                SELECT SUM(CASE WHEN transaction_type = 'FillIn' THEN quantity ELSE 0 END) as total_fillin,
                       SUM(CASE WHEN transaction_type = 'TakeOut' THEN quantity ELSE 0 END) as total_takeout
                FROM Transactions
                WHERE chemical_id = ? AND transaction_type != 'Delete'
            """, (chem_id,))
            result = cursor.fetchone()
            total_fillin = result[0] if result[0] is not None else 0.0
            total_takeout = result[1] if result[1] is not None else 0.0
            current_stock = total_fillin - total_takeout
            cursor.execute("UPDATE Chemicals SET current_stock = ? WHERE chemical_id = ?", (current_stock, chem_id))
                                         
                                                                                                     


        conn.commit()                                
        final_message = f"Import finished. Imported: {imported_count}, Skipped: {skipped_count}."
        logging.info(final_message)
        if errors:
            logging.warning("Errors/Warnings encountered during import:")
            error_details_msg = "\n".join([f"  - {err}" for err in errors[:20]])
            if len(errors) > 20:
                 error_details_msg += f"\n  - ... ({len(errors) - 20} more errors)"
            logging.warning(error_details_msg)
            final_message += f"\nEncountered {len(errors)} errors/warnings (see console log for details)."

                                            
        logging.warning("Note: If importing into an existing database containing previous exports, duplicate entries might be created.")

        return True, final_message

    except Exception as e:
        conn.rollback()
        error_msg = f"Fatal error during import process: {e}"
        logging.error(error_msg, exc_info=True)
        return False, error_msg
    finally:
        if conn:
            conn.close()


def get_chemical_log_since_last_fillin(chemical_name):
    """
    Return the latest FillIn record and all later transactions for a chemical.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
                            
        cursor.execute("SELECT chemical_id, name FROM Chemicals WHERE LOWER(name) = LOWER(?)", (chemical_name.strip(),))
        chem_data = cursor.fetchone()
        if not chem_data:
            return None, []                                          

        chemical_id = chem_data['chemical_id']
        result_chem_name = chem_data['name']

                                                   
        cursor.execute("""
            SELECT timestamp, username_logged, quantity 
            FROM Transactions 
            WHERE chemical_id = ? AND transaction_type = 'FillIn' 
            ORDER BY timestamp DESC LIMIT 1
        """, (chemical_id,))
        last_fillin = cursor.fetchone()
        
        start_timestamp = "1970-01-01 00:00:00"                                     
        if last_fillin:
            start_timestamp = last_fillin['timestamp']

                                                                                 
        cursor.execute("""
            SELECT timestamp, username_logged, transaction_type, quantity, notes 
            FROM Transactions 
            WHERE chemical_id = ? AND timestamp >= ? 
            ORDER BY timestamp ASC
        """, (chemical_id, start_timestamp))
        
        transactions = [dict(row) for row in cursor.fetchall()]

                                                                                 
        return {'name': result_chem_name, 'last_fillin': dict(last_fillin) if last_fillin else None}, transactions

    except Exception as e:
        logging.error(f"Error in get_chemical_log_since_last_fillin for '{chemical_name}': {e}", exc_info=True)
        return None, []
    finally:
        conn.close()


def get_user_activity_since_last_fillin(username, chemical_name):
    """
    Return the latest FillIn record and a user's later activity for a chemical.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
                            
        cursor.execute("SELECT chemical_id, name FROM Chemicals WHERE LOWER(name) = LOWER(?)", (chemical_name.strip(),))
        chem_data = cursor.fetchone()
        if not chem_data:
            return None, []

        chemical_id = chem_data['chemical_id']
        result_chem_name = chem_data['name']
        
                                           
        cursor.execute("SELECT user_id FROM Users WHERE LOWER(username) = LOWER(?)", (username.strip(),))
        user_data = cursor.fetchone()
        if not user_data and username.lower() != 'whoknows':
                                                              
            return {'error': 'User not found'}, []

                                                                             
        cursor.execute("""
            SELECT timestamp, username_logged, quantity 
            FROM Transactions 
            WHERE chemical_id = ? AND transaction_type = 'FillIn' 
            ORDER BY timestamp DESC LIMIT 1
        """, (chemical_id,))
        last_fillin = cursor.fetchone()
        
        start_timestamp = "1970-01-01 00:00:00"
        if last_fillin:
            start_timestamp = last_fillin['timestamp']

                                                                          
        cursor.execute("""
            SELECT timestamp, transaction_type, quantity, notes 
            FROM Transactions 
            WHERE chemical_id = ? AND LOWER(username_logged) = LOWER(?) AND timestamp >= ? 
            ORDER BY timestamp ASC
        """, (chemical_id, username.strip(), start_timestamp))
        
        transactions = [dict(row) for row in cursor.fetchall()]

        return {'name': result_chem_name, 'last_fillin': dict(last_fillin) if last_fillin else None}, transactions

    except Exception as e:
        logging.error(f"Error in get_user_activity_since_last_fillin for '{username}/{chemical_name}': {e}", exc_info=True)
        return None, []
    finally:
        conn.close()
        
if __name__ == "__main__":
    if not os.path.exists(DATABASE_FILE):
        logging.info("Database file '%s' not found. Initializing.", DATABASE_FILE)
        initialize_database()
        logging.info("Database created. Use the GUI import action to load initial data if needed.")
    else:
        logging.info("Database file '%s' found.", DATABASE_FILE)