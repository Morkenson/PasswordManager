# Quick Clean & Push Guide

## 🚨 STEP 1: Change Credentials FIRST (Critical!)

Before doing anything else:

### Change Database Password
```sql
-- In PostgreSQL:
ALTER USER postgres PASSWORD 'your-new-secure-password';
```

### Regenerate Duo API Keys
1. Go to https://admin.duosecurity.com/
2. Go to Applications → Your applications
3. Regenerate all keys
4. Save the new keys

---

## 🧹 STEP 2: Clean History (Choose ONE method)

### Option A: Fresh Start (EASIEST - Recommended)

This keeps your current code but removes all old history:

```powershell
# 1. Make sure all your changes are in the working directory
cd "C:\Github Projects\PasswordManager"

# 2. Make a backup just in case
cd ..
Copy-Item -Recurse PasswordManager PasswordManager-backup

# 3. Go back to your project
cd PasswordManager

# 4. Remove git history
Remove-Item -Recurse -Force .git

# 5. Initialize fresh repository
git init
git add .
git commit -m "Security: Clean repository with environment variables

- Removed all hardcoded credentials
- Implemented environment variable configuration
- Added comprehensive security documentation
- Updated .gitignore to prevent sensitive data commits"

# 6. Connect to GitHub
git remote add origin https://github.com/Morkenson/PasswordManager.git
git branch -M main

# 7. Force push (this replaces everything on GitHub)
git push -f origin main
```

**Pros:** Simple, fast, removes ALL old credentials  
**Cons:** Loses commit history, pull requests, and issues  

### Option B: Rewrite History (Keeps commit history)

If you want to keep your commit history:

```powershell
# Install git-filter-repo
pip install git-filter-repo

# Create a text file with strings to remove
@"
deadpool229
DITFYZ582OAJRRIEBO9Y
fTORaUv1ufXUlsxeDuADmiIZN3Z5m7fHqeUaYkbd
DI6NKM0NSARWX6J4K1IF
vtJBQJ7FuBVTSbUw1XPszL0ViikoJmFj0ykSJIZ3
api-99671107.duosecurity.com
"@ | Out-File -Encoding ASCII credentials.txt

# Run filter-repo
git filter-repo --replace-text credentials.txt --force

# Re-add remote
git remote add origin https://github.com/Morkenson/PasswordManager.git

# Force push
git push -f origin main
```

---

## ✅ STEP 3: Verify on GitHub

1. Go to https://github.com/Morkenson/PasswordManager
2. Click on various files (Duo.py, PasswordManager2.py)
3. Search for "deadpool229" - should not appear
4. Check commit history - old credentials should be gone

---

## 📝 STEP 4: Create .env File

Now create your `.env` file with the NEW credentials:

```env
FLASK_SECRET_KEY=your-new-generated-secret-key
DB_USER=postgres
DB_PASSWORD=your-new-database-password
DB_NAME=passworddb
DB_HOST=127.0.0.1
DB_PORT=5432
DUO_IKEY=your-new-duo-integration-key
DUO_SKEY=your-new-duo-secret-key
DUO_HOST=api-xxxxxxxx.duosecurity.com
DUO_CLIENT_IKEY=your-new-duo-client-integration-key
DUO_CLIENT_SKEY=your-new-duo-client-secret-key
DUO_CLIENT_HOST=api-xxxxxxxx.duosecurity.com
FLASK_ENV=development
DEBUG=True
```

Generate Flask secret:
```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 🧪 STEP 5: Test Everything

```powershell
# Activate virtual environment
env\Scripts\activate

# Generate encryption key
python key.py

# Test the application
python main.py
```

Test:
- [ ] User registration works
- [ ] Duo enrollment works
- [ ] Login with 2FA works
- [ ] Password storage works
- [ ] Password retrieval works

---

## 🎉 Done!

Your repository is now clean and your new credentials are secure!

**Remember:**
- ❌ The OLD credentials are compromised - never use them again
- ✅ Your NEW credentials are in `.env` (not committed)
- ✅ Future commits won't include sensitive data (thanks to `.gitignore`)

