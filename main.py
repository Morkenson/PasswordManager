from quart import Quart, request, render_template, session, redirect, url_for, flash
from PasswordManager2 import User, Admin, PasswordManager, DatabaseHandler, RateLimiter
import datetime
import os
from Duo import enroll_user_with_duo
from Duo import send_duo_push

# Flask app initialization
app = Quart(__name__)

app.config.update(
    SESSION_COOKIE_SAMESITE='Strict',
    SESSION_COOKIE_SECURE=True  # Ensure HTTPS
)

@app.before_request
async def set_security_headers():
    headers = {
        "X-Frame-Options": "DENY",  # Block framing to prevent clickjacking
    }
    for header, value in headers.items():
        request.headers.add(header, value)

@app.before_request
async def set_security_headers2():
    headers = {
        "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'",
    }
    for header, value in headers.items():
        request.headers.add(header, value)

@app.before_request
async def set_security_headers3():
    headers = {
        "X-Content-Type-Options": "nosniff",
    }
    for header, value in headers.items():
        request.headers.add(header, value)


def load_env_file(file_path=".env"):
    try:
        with open(file_path) as f:
            for line in f:
                # Skip empty lines and comments
                if line.strip() and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    os.environ[key] = value
    except FileNotFoundError:
        raise Exception(f"Environment file {file_path} not found!")

load_env_file()
app.secret_key = os.environ.get("FLASK_SECRET_KEY")  # Replace with an actual secret key

# Instantiate helpers
db_handler = DatabaseHandler()
rate_limiter = RateLimiter(5, "15 minutes")

@app.route("/register", methods=["GET", "POST"])
async def register():
    if request.method == "POST":
        form = await request.form
        username = form.get("username")
        password = form.get("password")
        is_admin = "is_admin" in form

        if not username or not password:
            await flash("Username and password are required!", "danger")
            return await render_template("register.html")

        user = User(username, password, is_admin)

        try:
            await user.register(db_handler)  # Assuming this is async
            # If enroll_user_with_duo is synchronous, remove 'await'
            qr_path = await enroll_user_with_duo(username)

            # At this point, the user is successfully registered and enrolled.
            # Flash the success message before showing the QR.
            await flash("User registered successfully!", "success")
            
            # Return the template showing the QR code.
            return await render_template("show_qr.html", username=username)

            # The lines below won't be reached, so remove them.
            # return redirect(url_for("login"))
        except Exception as e:
            await flash(f"Error during Duo enrollment: {e}", "danger")
            return await render_template("register.html")

    # For GET requests, just render the registration page.
    return await render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
async def login():
    if request.method == "POST":
        form = await request.form
        username = form.get("username")
        password = form.get("password")

        print(f"Attempting login for user: {username}")  # Debugging output

        user = User(username, password)

        try:
            # Check rate limiting
            if await rate_limiter.is_rate_limited(username, db_handler):
                await flash("Too many failed attempts. Please try again later.", "danger")
                return redirect(url_for("login"))

            # Authenticate the user
            if await user.authenticate(password, db_handler):
                print("Login successful!")
                
                if await send_duo_push(username):
                    print("Duo Push approved!") # Debugging output

                # Set session variables
                session["username"] = username
                session["is_admin"] = await db_handler.get_is_admin(username)

                await flash("Login successful!", "success")
                return redirect(url_for("dashboard"))  # Redirect to dashboard
            else:
                # Record failed login attempt
                await rate_limiter.record_attempt(username, db_handler)
                await flash("Invalid credentials. Please try again.", "danger")
                return redirect(url_for("login"))

        except Exception as e:
            print(f"Error during login: {e}")  # Debugging output
            await flash(f"Error: {e}", "danger")
            return redirect(url_for("login"))

    return await render_template("login.html")

@app.route("/add_password", methods=["GET", "POST"])
async def add_password():
    if "username" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        form = await request.form

        service_name = form.get("service_name")
        service_username = form.get("service_username")
        service_password = form.get("service_password")

        user = User(session["username"])
        await user.fetch_user_id(db_handler)
        pm = PasswordManager(user, db_handler)
        await pm.add_password(user.user_id,service_name,service_username,service_password)  # Await the async function
        await flash("Password added successfully!", "success")
    return await render_template("add_password.html")

@app.route("/view_password", methods=["GET"])
async def view_password():
    if "username" not in session:
        return redirect(url_for("login"))

    user = User(session["username"])
    await user.fetch_user_id(db_handler)
    pm = PasswordManager(user, db_handler)

    # Fetch all services, usernames, and passwords
    all_services = await pm.get_all_services()
    print("DEBUG: All services ->", all_services)  # Debugging line
    
    return await render_template("view_password.html", services=all_services)


@app.route("/dashboard")
async def dashboard():
    if "username" not in session:
        await flash("Please log in to access the dashboard.", "warning")
        return redirect(url_for("login"))

    username = session["username"]
    is_admin = session.get("is_admin", False)

    return await render_template("dashboard.html", username=username, is_admin=is_admin)

@app.route("/")
async def home():
    """Render the home page."""
    return await render_template("home.html")

@app.route("/logout")
async def logout():
    """
    Logs out the user by clearing the session.
    """
    session.clear()  # Clear all session data
    await flash("You have been logged out.", "info")
    return redirect(url_for("home"))  # Redirect to login page



if __name__ == "__main__":
    # Get debug mode from environment variable, default to False for security
    debug_mode = os.environ.get("DEBUG", "False").lower() == "true"
    app.run(debug=debug_mode)
