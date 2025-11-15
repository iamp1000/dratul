# Database Setup Guide

## Quick Fix for Database URL Error

### Step 1: Create a `.env` file

Create a file named `.env` in the project root directory (`c:\pcp\dratul\.env`)

### Step 2: Add Database Configuration

Copy the following template and update with your actual database credentials:

```env
DATABASE_URL=postgresql://your_username:your_password@localhost:5432/your_database_name
SECRET_KEY=your-secret-key-minimum-32-characters-long
ENCRYPTION_KEY=your-encryption-key-minimum-32-characters-long
```

### Step 3: Database URL Format

The `DATABASE_URL` must follow this format:
```
postgresql://username:password@host:port/database_name
```

**Examples:**
- Local PostgreSQL: `postgresql://postgres:mypassword@localhost:5432/clinic_db`
- With different user: `postgresql://clinic_user:secret123@localhost:5432/clinic_db`
- Remote server: `postgresql://user:pass@192.168.1.100:5432/clinic_db`

### Step 4: Generate Security Keys

You need to generate secure keys for `SECRET_KEY` and `ENCRYPTION_KEY`. Run this command:

```bash
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32)); print('ENCRYPTION_KEY=' + secrets.token_urlsafe(32))"
```

Copy the output to your `.env` file.

## Setting Up PostgreSQL Database

### Option 1: Use Existing PostgreSQL

If you already have PostgreSQL installed:

1. **Create a database:**
   ```sql
   CREATE DATABASE clinic_db;
   ```

2. **Create a user (optional):**
   ```sql
   CREATE USER clinic_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE clinic_db TO clinic_user;
   ```

3. **Update your `.env` file:**
   ```env
   DATABASE_URL=postgresql://clinic_user:your_password@localhost:5432/clinic_db
   ```

### Option 2: Install PostgreSQL (Windows)

1. Download PostgreSQL from: https://www.postgresql.org/download/windows/
2. Install with default settings
3. Remember the password you set for the `postgres` user
4. Create your database:
   ```sql
   CREATE DATABASE clinic_db;
   ```
5. Use this in your `.env`:
   ```env
   DATABASE_URL=postgresql://postgres:your_postgres_password@localhost:5432/clinic_db
   ```

### Option 3: Use SQLite (For Development Only)

If you don't want to set up PostgreSQL, you can use SQLite for development:

1. Update your `.env`:
   ```env
   DATABASE_URL=sqlite:///./clinic.db
   ```

**Note:** SQLite is not recommended for production use.

## Verify Your Setup

1. **Check if PostgreSQL is running:**
   ```bash
   # Windows PowerShell
   Get-Service -Name postgresql*
   ```

2. **Test connection:**
   ```bash
   psql -U your_username -d your_database_name -h localhost
   ```

3. **Restart your application:**
   ```bash
   uvicorn app.main:app --reload
   ```

## Common Issues

### "Password authentication failed"
- Check your username and password are correct
- Verify the user exists in PostgreSQL
- Check if the password contains special characters (may need URL encoding)

### "Could not connect to server"
- Ensure PostgreSQL service is running
- Check the host and port are correct (default is localhost:5432)
- Verify firewall settings

### "Database does not exist"
- Create the database first: `CREATE DATABASE your_database_name;`

## URL Encoding Special Characters

If your password contains special characters, you need to URL-encode them:

- `@` becomes `%40`
- `#` becomes `%23`
- `$` becomes `%24`
- `%` becomes `%25`
- `&` becomes `%26`
- `+` becomes `%2B`
- `=` becomes `%3D`

Example: If password is `p@ss#word`, use `p%40ss%23word` in the URL.

