from cryptography.fernet import Fernet
import datetime
import pyotp
import qrcode
import os
import random
import string
from hashlib import pbkdf2_hmac
import asyncpg
import random

# User Management
class User:
    def __init__(self, username, password=None, is_admin=False):
        self.username = username
        self.password = password
        self.is_admin = is_admin
        self.user_id = None

    async def fetch_user_id(self, db_handler):
        """Fetch user_id from the database."""
        conn = await db_handler.connect()
        try:
            query = "SELECT user_id FROM users WHERE username = $1"
            result = await conn.fetchval(query, self.username)
            if result:
                self.user_id = result  # Set the user_id if found
            else:
                raise ValueError("User not found in the database.")
        finally:
            await conn.close()

    async def register(self, db_handler):
        """
        Register the user by hashing the password and storing it in the database.
        """
        salt = os.urandom(16)  # Generate a 16-byte salt
        password_hash = salt + pbkdf2_hmac('sha256', self.password.encode('utf-8'), salt, 100000)
        self.user_id = random.randint(1000, 9999)
        await db_handler.insert_user(self.username, password_hash, self.is_admin, self.user_id)

    async def authenticate(self, password, db_handler):
        stored_hash = await db_handler.get_password_hash(self.username)
        if not stored_hash:
            return False
        return self.verify_password(stored_hash, password)

    @staticmethod
    def hash_password(password):
        salt = os.urandom(16)
        hash_ = pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return salt + hash_

    @staticmethod
    def verify_password(stored_hash, password):
        salt = stored_hash[:16]
        stored_hash = stored_hash[16:]
        hash_ = pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return hash_ == stored_hash


# Admin inherits from User
class Admin(User):
    def __init__(self, username, password):
        super().__init__(username, password, is_admin=True)

    def view_audit_logs(self, db_handler):
        return db_handler.get_audit_logs()


# Password Manager
class PasswordManager:
    def __init__(self, user, db_handler):
        self.user = user
        self.db_handler = db_handler

    async def get_all_services(self):
        query = """
        SELECT service_name, service_username, service_password
        FROM passwords
        WHERE user_id = $1
        """
        print("DEBUG: User ID ->", self.user.user_id)
        rows = await self.db_handler.fetch(query, self.user.user_id)
        print("DEBUG: Rows fetched ->", rows)

        decrypted_services = []

        for row in rows:
            service_name = row['service_name']
            service_username = row['service_username']
            encrypted_password = row['service_password']
            
            decrypted_password = PasswordManager.decrypt_password(encrypted_password)

            decrypted_services.append({
            "service_name": service_name,
            "service_username": service_username,
            "service_password": decrypted_password
        })

        return decrypted_services

    async def add_password(self, user_id, service, username, password):
        encrypted_password = self.encrypt_password(password)
        await self.db_handler.insert_password(user_id, service, username, encrypted_password)

    async def get_password(self, service):
        result = await self.db_handler.get_password(service, self.user.username)
        if result:
            return self.decrypt_password(result)
        return None

    @staticmethod
    def encrypt_password(password):
        key = PasswordManager.load_key()
        f = Fernet(key)
        return f.encrypt(password.encode()).decode()

    @staticmethod
    def decrypt_password(encrypted_password):
        key = PasswordManager.load_key()
        f = Fernet(key)
        return f.decrypt(encrypted_password).decode()

    @staticmethod
    def load_key():
        try:
            with open("key.key", "rb") as key_file:
                return key_file.read()
        except FileNotFoundError:
            raise Exception("Encryption key file 'key.key' not found!")


# Rate Limiting
class RateLimiter:
    def __init__(self, max_attempts, time_window):
        self.max_attempts = max_attempts
        self.time_window = time_window

    async def is_rate_limited(self, username, db_handler):
        recent_attempts = await db_handler.get_recent_login_attempts(username, self.time_window)
        return len(recent_attempts) >= self.max_attempts

    async def record_attempt(self, username, db_handler):
        await db_handler.insert_login_attempt(username, False)


# Database Handler
class DatabaseHandler:

    def load_key():
        try:
            with open("key.key", "rb") as key_file:
                return key_file.read()
        except FileNotFoundError:
            raise Exception("Encryption key file (key.key) not found! Make sure it exists.")

    def __init__(self):
        self.user = os.environ.get("DB_USER", "postgres")
        self.password = os.environ.get("DB_PASSWORD")
        self.database = os.environ.get("DB_NAME", "passworddb")
        self.host = os.environ.get("DB_HOST", "127.0.0.1")
        self.port = int(os.environ.get("DB_PORT", "5432"))
        
        if not self.password:
            raise Exception("DB_PASSWORD environment variable is not set. Please check your .env file.")

    async def connect(self):
        """
        Create an asynchronous connection to the PostgreSQL database.
        """
        try:
            conn = await asyncpg.connect(
                user=self.user,
                password=self.password,
                database=self.database,
                host=self.host,
            )
            print("Connected to the database.")  # Debugging
            return conn

        except Exception as e:
            print(f"Database connection failed: {e}")  # Debugging
            raise e

    async def insert_user(self, username, password_hash, is_admin, user_id):
        conn = await self.connect()
        try:
            query = """
            INSERT INTO users (user_id, username, password_hash, is_admin)
            VALUES ($1, $2, $3, $4);
        """
            # Execute the query with user_id, username, password_hash, and is_admin
            await conn.execute(query, user_id, username, password_hash, is_admin)
            print(f"User '{username}' added with User ID: {user_id}")
        except Exception as e:
            print(f"Error adding user: {e}")
            raise e
        finally:
            await conn.close()

    async def get_password_hash(self, username):
        """
        Retrieve the password hash for a user.
        """
        conn = await self.connect()
        try:
            query = "SELECT password_hash FROM users WHERE username = $1"
            result = await conn.fetchval(query, username)
            return result
        finally:
            await conn.close()

    async def insert_password(self, user_id, service_name, service_username, service_password):
        conn = await self.connect()
        try:
            # Insert encrypted password into the database
            query = """
                INSERT INTO passwords (user_id, service_name, service_username, service_password)
                VALUES ($1, $2, $3, $4)
            """
            await conn.execute(query, user_id, service_name, service_username, service_password.encode("utf-8"))
            print(f"Password for '{service_name}' added successfully!")  # Debugging
        except Exception as e:
            print(f"Error inserting password: {e}")
            raise e
        finally:
            await conn.close()

    async def get_password(self, password_id):
        conn = await self.connect()
        try:
            FERNET_KEY = DatabaseHandler.load_key()
            cipher = Fernet(FERNET_KEY)
            query = "SELECT service_name, service_username, service_password FROM passwords WHERE id = $1"
            result = await conn.fetchrow(query, password_id)
            if result:
                decrypted_password = cipher.decrypt(result["service_password"]).decode("utf-8")
                return {
                    "service_name": result["service_name"],
                    "service_username": result["service_username"],
                    "service_password": decrypted_password,
                }
            else:
                print(f"No password found for ID: {password_id}")
                return None
        except Exception as e:
            print(f"Error retrieving password: {e}")
            raise e
        finally:
            await conn.close()


    async def get_recent_login_attempts(self, username, time_window=None):
        conn = await self.connect()
        try:
            query = """
                SELECT attempt_time FROM login_attempts
                WHERE username = $1
            """
            rows = await conn.fetch(query, username)  # No time filtering
            return [row["attempt_time"] for row in rows]
        finally:
            await conn.close()

    async def get_audit_logs(self):
        conn = await self.connect()
        try:
            query = "SELECT * FROM audit_logs ORDER BY event_time DESC"
            rows = await conn.fetch(query)
            return rows
        finally:
            await conn.close()

    async def insert_login_attempt(self, username, success):
        """
        Insert a login attempt into the database.
        """
        conn = await self.connect()
        try:
            query = """
                INSERT INTO login_attempts (username, attempt_time, success)
                VALUES ($1, NOW(), $2)
            """
            await conn.execute(query, username, success)
        finally:
            await conn.close()

    async def get_is_admin(self, username):
        """
        Check if the user has admin privileges.
        """
        conn = await self.connect()
        try:
            query = "SELECT is_admin FROM users WHERE username = $1"
            result = await conn.fetchval(query, username)
            print(f"Admin status for {username}: {result}")  # Debugging
            return result  # This will return True, False, or None
        except Exception as e:
            print(f"Error fetching admin status: {e}")
            raise e
        finally:
            await conn.close()

    async def fetch(self, query, *args):
        conn = await self.connect()
        try:
            rows = await conn.fetch(query, *args)  # asyncpg fetches rows
            return rows
        finally:
            await conn.close()

