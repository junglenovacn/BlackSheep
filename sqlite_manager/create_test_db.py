"""
Create a test SQLite database for demonstration.
"""
import sqlite3
import os


def create_test_database(path: str = "test_database.db"):
    """Create a test database with sample data."""
    
    # Remove existing file
    if os.path.exists(path):
        os.remove(path)
    
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL,
            age INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    
    # Create products table
    cursor.execute('''
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            stock INTEGER DEFAULT 0,
            category TEXT
        )
    ''')
    
    # Create orders table
    cursor.execute('''
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            total_price REAL NOT NULL,
            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')
    
    # Insert sample users
    users = [
        ('alice', 'alice@example.com', 28),
        ('bob', 'bob@example.com', 35),
        ('charlie', 'charlie@example.com', 22),
        ('diana', 'diana@example.com', 30),
        ('eve', 'eve@example.com', 27),
        ('frank', 'frank@example.com', 41),
        ('grace', 'grace@example.com', 33),
        ('henry', 'henry@example.com', 29),
    ]
    cursor.executemany(
        'INSERT INTO users (username, email, age) VALUES (?, ?, ?)',
        users
    )
    
    # Insert sample products
    products = [
        ('Laptop', 'High-performance laptop for work and gaming', 999.99, 50, 'Electronics'),
        ('Mouse', 'Wireless ergonomic mouse', 29.99, 200, 'Electronics'),
        ('Keyboard', 'Mechanical keyboard with RGB', 79.99, 150, 'Electronics'),
        ('Monitor', '27-inch 4K display', 399.99, 30, 'Electronics'),
        ('Headphones', 'Noise-cancelling wireless headphones', 199.99, 100, 'Audio'),
        ('Webcam', 'HD webcam for video conferencing', 49.99, 80, 'Electronics'),
        ('USB Hub', '7-port USB 3.0 hub', 34.99, 120, 'Accessories'),
        ('Desk Lamp', 'LED desk lamp with adjustable brightness', 25.99, 60, 'Office'),
    ]
    cursor.executemany(
        'INSERT INTO products (name, description, price, stock, category) VALUES (?, ?, ?, ?, ?)',
        products
    )
    
    # Insert sample orders
    orders = [
        (1, 1, 1, 999.99, 'completed'),
        (1, 2, 2, 59.98, 'completed'),
        (2, 3, 1, 79.99, 'pending'),
        (3, 4, 1, 399.99, 'shipped'),
        (4, 5, 1, 199.99, 'pending'),
        (5, 1, 1, 999.99, 'completed'),
        (6, 6, 2, 99.98, 'shipped'),
        (7, 7, 3, 104.97, 'pending'),
        (8, 8, 1, 25.99, 'completed'),
        (1, 3, 1, 79.99, 'pending'),
    ]
    cursor.executemany(
        '''INSERT INTO orders (user_id, product_id, quantity, total_price, status) 
           VALUES (?, ?, ?, ?, ?)''',
        orders
    )
    
    conn.commit()
    conn.close()
    
    print(f"Test database created: {os.path.abspath(path)}")
    print(f"Tables: users ({len(users)} rows), products ({len(products)} rows), orders ({len(orders)} rows)")


if __name__ == "__main__":
    create_test_database()
