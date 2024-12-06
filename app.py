from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)

# Use environment variable for secret key or fallback to default for development
app.secret_key = os.getenv('SECRET_KEY', 'defaultsecretkey')

# Connect to SQLite DB
def get_db_connection():
    conn = sqlite3.connect('grocery_store.db')
    conn.row_factory = sqlite3.Row
    return conn

# Function to create the database and tables
def create_db():
    conn = sqlite3.connect('grocery_store.db')
    cursor = conn.cursor()

    # Create Users Table
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
    )''')

    # Create Products Table
    cursor.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL
    )''')

    # Create Orders Table
    cursor.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        total REAL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')

    conn.commit()
    conn.close()

# Uncomment the next line if you want to create the database when the app starts
if not os.path.exists('grocery_store.db'):
    create_db()

# Home route (Product listing)
@app.route('/')
def index():
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products').fetchall()
    conn.close()
    return render_template('index.html', products=products)

# User Registration route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        try:
            conn = get_db_connection()
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
            conn.commit()
            conn.close()

            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists. Please try another one.', 'danger')

    return render_template('signup.html')

# User Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials. Try again.', 'danger')

    return render_template('login.html')

# Cart Route
@app.route('/cart')
def cart():
    if 'user_id' not in session:
        flash('You must be logged in to view your cart', 'warning')
        return redirect(url_for('login'))
    return render_template('cart.html')

# Add product to cart route
@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    if 'cart' not in session:
        session['cart'] = []
    session['cart'].append(product_id)
    flash('Product added to cart!', 'success')
    return redirect(url_for('index'))

# Order Confirmation
@app.route('/checkout')
def checkout():
    if 'user_id' not in session:
        flash('You must be logged in to checkout', 'warning')
        return redirect(url_for('login'))

    cart_items = session.get('cart', [])
    if not cart_items:
        flash('Your cart is empty!', 'warning')
        return redirect(url_for('index'))

    conn = get_db_connection()
    total = 0
    for item in cart_items:
        product = conn.execute('SELECT price FROM products WHERE id = ?', (item,)).fetchone()
        if product:
            total += product['price']
    conn.close()

    # Clear cart after checkout (Optional)
    session.pop('cart', None)
    flash('Order placed successfully!', 'success')

    return render_template('order.html', total=total)

# Logout route
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# Run the application
if __name__ == '__main__':
    app.run(debug=True)
