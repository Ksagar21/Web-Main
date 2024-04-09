from flask import Flask, render_template, request, redirect, flash, session, url_for
from datetime import datetime
import pyrebase
import os
from werkzeug.security import generate_password_hash, check_password_hash
import random 

config = {
    "apiKey": "AIzaSyBq_Icm0xUdz8e7L7ldRDfFsYan7I4hyZM",
    "authDomain": "capture-fec44.firebaseapp.com",
    "projectId": "capture-fec44",
    "storageBucket": "capture-fec44.appspot.com",
    "messagingSenderId": "139485255549",
    "appId": "1:139485255549:web:58507f26c72cefc38c5e14",
    "measurementId": "G-N470CCMS55",
    "databaseURL": "https://capture-fec44-default-rtdb.firebaseio.com"
}

firebase = pyrebase.initialize_app(config)
db = firebase.database()

app = Flask(__name__)
app.secret_key = '123456'  
storage = firebase.storage()

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin123'

def load_images():
    images_path = os.path.join(app.static_folder, "images")
    images = [
        os.path.join(images_path, filename)
        for filename in os.listdir(images_path)
        if filename.endswith(".jpg") or filename.endswith(".png")
    ]
    return images

@app.route('/')
def index():
    return render_template('index.html', cart_items=cart_items)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['username'] = username
            return redirect('/product.html')
        else:
            flash('Invalid username or password', 'danger')
            return render_template('admin_login.html')
    else:
        return render_template('admin_login.html')

@app.route('/product.html', methods=['GET', 'POST'])
def product():
    if 'username' in session and session['username'] == ADMIN_USERNAME:
        if request.method == 'POST':
            product_category = request.form['product_category']
            product_brand = request.form['product_brand']
            product_model = request.form['product_model']
            product_price = request.form['product_price']
            product_image = request.files['product_image']

            try:
                storage = firebase.storage()
                storage.child("product_images/" + product_image.filename).put(product_image)
                image_url = storage.child("product_images/" + product_image.filename).get_url(None)
            except Exception as e:
                return render_template('product.html', message='Error uploading image')

            product_data = {
                'category': product_category,
                'brand': product_brand,
                'model': product_model,
                'price': product_price,
                'image_url': image_url
            }

            try:
                db.child("products").push(product_data)
            except Exception as e:
                return render_template('product.html', message='Error saving product')

            products = db.child("products").get().val()

            return render_template('product.html', message='Product added successfully', products=products)
        else:
            products = db.child("products").get().val()

            return render_template('product.html', products=products)
    else:
        return redirect('/admin/login')

@app.route('/edit_product/<product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    if 'username' in session and session['username'] == ADMIN_USERNAME:
        if request.method == 'GET':
            product_data = db.child("products").child(product_id).get().val()
            if product_data:
                return render_template('edit_product.html', product=product_data)
            else:
                flash('Product not found!', 'danger')
                return redirect('/product.html')
        elif request.method == 'POST':
            product_category = request.form['product_category']
            product_brand = request.form['product_brand']
            product_model = request.form['product_model']
            product_price = request.form['product_price']

            db.child("products").child(product_id).update({
                'category': product_category,
                'brand': product_brand,
                'model': product_model,
                'price': product_price,
            })
            flash('Product updated successfully!', 'success')
            return redirect('/product.html')
    else:
        return redirect('/admin/login')

@app.route('/remove_product', methods=['POST'])
def remove_product():
    if 'username' in session and session['username'] == ADMIN_USERNAME:
        if request.method == 'POST':
            product_id = request.form.get('product_id')
            
            if product_id:
                db.child("products").child(product_id).remove()
                
            return redirect('/product.html')
    else:
        return redirect('/admin/login')

@app.route('/allview')
def allproducts():
    products = db.child("products").get().val()
    return render_template('allview.html', products=products)

@app.route('/cameraview')
def cameraview():
    products = db.child("products").get().val()
    cameras = {product_id: product for product_id, product in products.items() if product.get('category') == "camera"}
    return render_template('cameraview.html', products=cameras)

@app.route('/lensesview')
def lensesview():
    products = db.child("products").get().val()
    lenses = {product_id: product for product_id, product in products.items() if product.get('category') == "lenses"}
    return render_template('lensesview.html', products=lenses)

@app.route('/accessoriesview')
def accessoriesview():
    products = db.child("products").get().val()
    accessories = {product_id: product for product_id, product in products.items() if product.get('category') == "accessories"}
    return render_template('accessoriesview.html', products=accessories)

@app.route('/cart', methods=['GET', 'POST'])
def cart():
    if request.method == 'POST':
        product_id = request.form['product_id']
        cart = session.get('cart', [])
        cart.append(product_id)
        session['cart'] = cart
        return redirect('/cart')

    cart_items = fetch_cart_items_from_database(session['cart'])
    return render_template('cart.html', cart_items=cart_items)

def fetch_cart_items_from_database(product_ids):
    cart_items = {}
    for product_id in product_ids:
        product_data = db.child("products").child(product_id).get().val()
        if product_data:
            cart_items[product_id] = product_data

    return cart_items

@app.route('/cart/remove/<product_id>', methods=['POST'])
def remove_from_cart(product_id):
    if 'cart' in session:
        cart = session['cart']
        if product_id in cart:
            cart.remove(product_id)
            session['cart'] = cart
            flash(f'Product removed from cart!', 'success')
        else:
            flash(f'Product (ID: {product_id}) not found in cart.', 'warning')
    else:
        flash('Cart is empty. Nothing to remove.', 'warning')

    return redirect('/cart')

payment_confirmation = None
cart_items = {}

def create_payment(amount, currency, customer_data, product_data):
    payment_intent = "your_payment_intent"
    return payment_intent

def process_payment(card_number, expiry_date, cvv, name_on_card):
    global payment_confirmation
    payment_confirmation = "success"
    return payment_confirmation

@app.route('/checkout', methods=['POST'])
def checkout_route():
    global cart_items

    card_number = request.form.get('card_number')
    expiry_date = request.form.get('expiry_date')
    cvv = request.form.get('cvv')
    name_on_card = request.form.get('name')

    payment_confirmation = process_payment(card_number, expiry_date, cvv, name_on_card)

    if payment_confirmation == "success":
        cart_items = {}
        return redirect(url_for('confirmation', payment_confirmation=payment_confirmation))
    else:
        return "Payment failed. Please try again."

@app.route('/confirmation')
def confirmation():
    global payment_confirmation 
    payment_confirmation = request.args.get('payment_confirmation')
    payment_intent = request.args.get('payment_intent')

    if payment_confirmation == "success":
        return render_template('confirmation.html', payment_confirmation=payment_confirmation , payment_intent=payment_intent)
    else:
        return "Payment failed. Please try again."

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        user_data = {
            'email': email,
            'password': hashed_password
        }
        db.child('users').push(user_data)
        flash('Registration successful! Please login.', 'success')
        return render_template('register.html', registration_complete=True)
    else:
        return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        users = db.child('users').get().val()
        for user_id, user_info in users.items():
            if user_info['email'] == email:
                if check_password_hash(user_info['password'], password):
                    session['user_id'] = user_id
                    session['logged_in'] = True
                    flash('Login successful!', 'success')
                    return redirect(url_for('dashboard'))
                else:
                    flash('Invalid password.', 'danger')
                    return render_template('login.html')
        flash('Invalid email or user not found.', 'danger')
        return render_template('login.html')
    else:
        return render_template('login.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        flash('A password reset link has been sent to your email (if applicable).', 'info')
        return redirect(url_for('login'))
    else:
        return render_template('forgot_password.html')

@app.route('/dashboard')
def dashboard():
    if 'logged_in' not in session or session['logged_in'] is False:
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    return render_template('dashboard.html', user_id=user_id) 

@app.route("/search", methods=["GET"])
def search():
    search_query = request.args.get("searchInput")
    search_results = {}
    
    if search_query:
        books_data = db.child("books").get().val() or {}
        for key, book in books_data.items():
            if search_query.lower() in book.get('title', '').lower() or search_query.lower() in book.get('author', '').lower():
                search_results[key] = book
    
    return render_template('search_results.html', search_results=search_results, search_query=search_query)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        contact_data = {
            'name': name,
            'email': email,
            'message': message,
            'timestamp': datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        }
        try:
            db.child('contacts').push(contact_data)
            flash('Your message has been sent successfully!', 'success')
        except Exception as e:
            flash('Error saving your message. Please try again later.', 'danger')

        return render_template('contact.html')

    return render_template('contact.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
