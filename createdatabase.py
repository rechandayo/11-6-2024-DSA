import sqlite3

conn = sqlite3.connect("job_applications.db")
cursor = conn.cursor()

# Create users table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
    );
''')

# Create applications table with user_id foreign key
cursor.execute('''
    CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        company TEXT NOT NULL,
        stage TEXT NOT NULL,
        salary INTEGER NOT NULL,
        date_applied TEXT NOT NULL,
        deadline TEXT,
        role_type TEXT,
        priority INTEGER,
        user_id INTEGER,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
''')

conn.commit()
conn.close()