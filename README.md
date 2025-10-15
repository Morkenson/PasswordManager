# Password Manager

A secure password manager web application with Two-Factor Authentication (2FA) using Duo Security.

## Features

- 🔐 Secure password storage with encryption
- 👤 User authentication with hashed passwords (PBKDF2)
- 📱 Two-Factor Authentication (2FA) via Duo Security
- 🛡️ Rate limiting to prevent brute-force attacks
- 👨‍💼 Admin user support
- 🔒 Security headers (CSP, X-Frame-Options, etc.)

## Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Duo Security account (for 2FA)

## Installation & Setup

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd PasswordManager
```

### 2. Create Virtual Environment

```bash
python -m venv env
```

**Activate the virtual environment:**

- Windows: `env\Scripts\activate`
- Linux/Mac: `source env/bin/activate`

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root directory:

```bash
# Copy the example file
cp .env.example .env
```

Edit the `.env` file and add your actual credentials:

```env
# Flask Configuration
FLASK_SECRET_KEY=your-generated-secret-key-here

# Database Configuration
DB_USER=postgres
DB_PASSWORD=your-secure-database-password
DB_NAME=passworddb
DB_HOST=127.0.0.1
DB_PORT=5432

# Duo Security API Credentials
DUO_IKEY=your-duo-integration-key
DUO_SKEY=your-duo-secret-key
DUO_HOST=api-xxxxxxxx.duosecurity.com

# Duo Client API Credentials
DUO_CLIENT_IKEY=your-duo-client-integration-key
DUO_CLIENT_SKEY=your-duo-client-secret-key
DUO_CLIENT_HOST=api-xxxxxxxx.duosecurity.com

# Application Settings
FLASK_ENV=production
DEBUG=False
```

**Generate a secure Flask secret key:**

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 5. Set Up Database

Create the PostgreSQL database:

```bash
createdb passworddb
```

Import the database schema:

```bash
psql -U postgres -d passworddb -f PasswordManagerDatabaseScript.sql
```

### 6. Generate Encryption Key

Run the key generation script:

```bash
python key.py
```

This creates a `key.key` file used for encrypting stored passwords. **NEVER commit this file to git!**

### 7. Configure Duo Security

1. Sign up for a [Duo Security account](https://duo.com/)
2. Create a new application in the Duo Admin Panel
3. Get your Integration Key (ikey), Secret Key (skey), and API hostname
4. Add these credentials to your `.env` file

## Running the Application

**Important for Production:**
- Set `DEBUG=False` in your `.env` file
- Use HTTPS (the app requires it for secure cookies)
- Set up proper firewall rules
- Use a reverse proxy (nginx, Apache)
- Keep all dependencies updated

### Password Security

- User passwords are hashed using PBKDF2 with SHA-256
- Each password has a unique salt
- Stored passwords are encrypted using Fernet (symmetric encryption)

### Additional Security Measures

1. **Rate Limiting**: Failed login attempts are tracked and limited
2. **Session Security**: Secure and SameSite cookies enabled
3. **Security Headers**: CSP, X-Frame-Options, X-Content-Type-Options
4. **2FA**: Duo Push notifications for all logins
5. **Input Validation**: Parameterized queries prevent SQL injection

## Project Structure

```
PasswordManager/
├── main.py                          # Main application entry point
├── PasswordManager2.py              # Core classes (User, PasswordManager, DatabaseHandler)
├── Duo.py                          # Duo Security integration
├── key.py                          # Encryption key generator
├── requirements.txt                 # Python dependencies
├── .env                            # Environment variables (NOT in git)
├── .env.example                    # Template for .env
├── .gitignore                      # Git ignore rules
├── PasswordManagerDatabaseScript.sql # Database schema
├── static/                         # Static files (CSS, images)
│   ├── duo_qr/                    # Generated QR codes (NOT in git)
│   └── *.css                      # Stylesheets
└── templates/                      # HTML templates
    ├── home.html
    ├── login.html
    ├── register.html
    ├── dashboard.html
    ├── add_password.html
    ├── view_password.html
    └── show_qr.html
```

## Usage

1. **Register**: Create a new account with username and password
2. **Enroll 2FA**: Scan the QR code with Duo Mobile app
3. **Login**: Enter credentials and approve Duo Push notification
4. **Add Passwords**: Store passwords for various services
5. **View Passwords**: Access your encrypted passwords

## Troubleshooting

### Database Connection Failed
- Verify PostgreSQL is running
- Check database credentials in `.env`
- Ensure database exists: `psql -l | grep passworddb`

### Duo API Errors
- Verify Duo credentials in `.env`
- Check Duo application is active in Admin Panel
- Ensure API hostname is correct

### Encryption Key Not Found
- Run `python key.py` to generate the key
- Ensure `key.key` exists in the project root

