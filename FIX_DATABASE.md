# How to Fix Database Connection Error

## Current Issue
Your DATABASE_URL is using placeholder values:
- Username: `username` (this is a placeholder)
- Password authentication is failing

## Solution Steps

### Step 1: Check Your PostgreSQL Users

Connect to PostgreSQL and see what users exist:
```bash
psql -U postgres
```

Then run:
```sql
\du
```

This will show all users. You should see something like:
- `postgres` (default superuser)
- Or your custom users

### Step 2: Update Your .env File

Open `c:\pcp\dratul\.env` and update the DATABASE_URL:

**Option A: Use the default postgres user**
```env
DATABASE_URL=postgresql://postgres:YOUR_POSTGRES_PASSWORD@localhost:5432/clinic_db
```

**Option B: Create a new user (Recommended)**
```sql
-- In psql, run:
CREATE USER clinic_user WITH PASSWORD 'your_secure_password';
CREATE DATABASE clinic_db;
GRANT ALL PRIVILEGES ON DATABASE clinic_db TO clinic_user;
```

Then in .env:
```env
DATABASE_URL=postgresql://clinic_user:your_secure_password@localhost:5432/clinic_db
```

### Step 3: If Password Has Special Characters

If your password contains special characters, URL-encode them:
- `@` → `%40`
- `#` → `%23`
- `$` → `%24`
- `%` → `%25`
- `&` → `%26`
- `+` → `%2B`
- `=` → `%3D`

Example: If password is `p@ss#word`, use `p%40ss%23word`

### Step 4: Test the Connection

Run the diagnostic tool:
```bash
python test_db_connection.py
```

### Step 5: Verify PostgreSQL is Running

**Windows:**
```powershell
Get-Service -Name postgresql*
```

If not running:
```powershell
Start-Service postgresql-x64-<version>
```

## Quick Fix Commands

**If you want to use the default postgres user:**
```sql
-- Connect as postgres user
psql -U postgres

-- Create database
CREATE DATABASE clinic_db;

-- Update .env file with:
-- DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/clinic_db
```

**If you want to create a dedicated user:**
```sql
-- Connect as postgres user
psql -U postgres

-- Create user and database
CREATE USER clinic_user WITH PASSWORD 'secure_password_123';
CREATE DATABASE clinic_db OWNER clinic_user;
GRANT ALL PRIVILEGES ON DATABASE clinic_db TO clinic_user;

-- Update .env file with:
-- DATABASE_URL=postgresql://clinic_user:secure_password_123@localhost:5432/clinic_db
```

## Common Issues

1. **"password authentication failed"**
   - Password in .env doesn't match PostgreSQL password
   - Password needs URL encoding for special characters

2. **"could not connect"**
   - PostgreSQL service is not running
   - Wrong hostname or port

3. **"database does not exist"**
   - Create the database first: `CREATE DATABASE clinic_db;`

4. **"role does not exist"**
   - Create the user first: `CREATE USER username WITH PASSWORD 'password';`

