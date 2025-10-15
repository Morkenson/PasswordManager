import asyncio
import asyncpg
import os

# Load environment variables
def load_env_file(file_path=".env"):
    try:
        with open(file_path) as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    os.environ[key] = value
    except FileNotFoundError:
        raise Exception(f"Environment file {file_path} not found!")

load_env_file()

async def connect_to_db():
    try:
        # Connect to the PostgreSQL database using environment variables
        conn = await asyncpg.connect(
            user=os.environ.get("DB_USER", "postgres"),
            password=os.environ.get("DB_PASSWORD"),
            database=os.environ.get("DB_NAME", "passworddb"),
            host=os.environ.get("DB_HOST", "127.0.0.1")
        )
        print("Connected to the database!")

        # Fetch all rows from the 'users' table
        rows = await conn.fetch("SELECT * FROM users;")
        if rows:
            print("Users in the database:")
            for row in rows:
                print(dict(row))  # Convert row to a dictionary for better readability
        else:
            print("No users found in the database.")

        # Close the connection
        await conn.close()
    except Exception as e:
        print(f"Error: {e}")

# Run the async function
asyncio.run(connect_to_db())
