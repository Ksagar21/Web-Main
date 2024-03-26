
from flask import Flask, render_template, request, redirect, flash, session, url_for
from datetime import datetime
import pyrebase
import os
import random 



# Replace with your actual Firebase project configuration
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



#Main Routes 


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
  session.pop('username', None)  # Remove username from session
  return redirect(url_for('index'))  # Redirect to the 'index' route



@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['username'] = username
            return redirect('/product.html')  # Assuming this is your admin panel route
        else:
            flash('Invalid username or password', 'danger')
            return render_template('admin_login.html')
    else:
        return render_template('admin_login.html')



@app.route('/product.html', methods=['GET', 'POST'])
def product():
    if 'username' in session and session['username'] == ADMIN_USERNAME:
        if request.method == 'POST':
            # Get the form data (modify field names as needed)
            product_category = request.form['product_category']
            product_brand = request.form['product_brand']
            product_model = request.form['product_model']
            product_price = request.form['product_price']
            product_image = request.files['product_image']

            # Save the image to Firebase Storage
            try:
                storage = firebase.storage()
                storage.child("product_images/" + product_image.filename).put(product_image)
                image_url = storage.child("product_images/" + product_image.filename).get_url(None)
            except Exception as e:
                # Handle storage error (e.g., display error message)
                return render_template('product.html', message='Error uploading image')

            # Create a dictionary to store product data
            product_data = {
                'category': product_category,
                'brand': product_brand,
                'model': product_model,
                'price': product_price,
                'image_url': image_url
            }

            # Push product data to Firebase Database
            try:
                db.child("products").push(product_data)
            except Exception as e:
                # Handle database push error (e.g., display error message)
                return render_template('product.html', message='Error saving product')

            # Fetch all products from the database
            products = db.child("products").get().val()

            return render_template('product.html', message='Product added successfully', products=products)
        else:
            # Fetch all products from the database
            products = db.child("products").get().val()

            return render_template('product.html', products=products)  # Use products=products
    else:
        return redirect('/admin/login')





# CRUD Operations


@app.route('/edit_product/<product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    if 'username' in session and session['username'] == ADMIN_USERNAME:
        if request.method == 'GET':
            # Fetch the specific product data from the database
            product_data = db.child("products").child(product_id).get().val()
            if product_data:
                return render_template('edit_product.html', product=product_data)
            else:
                flash('Product not found!', 'danger')
                return redirect('/product.html')
        elif request.method == 'POST':
            # Get updated product data from the form
            product_category = request.form['product_category']
            product_brand = request.form['product_brand']
            product_model = request.form['product_model']
            product_price = request.form['product_price']
            # ... handle image update (if applicable)

            # Update the product data in the database
            db.child("products").child(product_id).update({
                'category': product_category,
                'brand': product_brand,
                'model': product_model,
                'price': product_price,
                # ... update image URL if changed
            })
            flash('Product updated successfully!', 'success')
            return redirect('/product.html')
    else:
        return redirect('/admin/login')





@app.route('/remove_product', methods=['POST'])
def remove_product():
    if 'username' in session and session['username'] == ADMIN_USERNAME:
        if request.method == 'POST':
            # Get the camera ID from the request
            product_id = request.form.get('product_id')
            
            if product_id:
                # Remove the specific camera from the database
                db.child("products").child(product_id).remove()
                
            # Redirect back to the add_camera.html page
            return redirect('/product.html')
    else:
        return redirect('/admin/login')


#View the products code



@app.route('/allview')  # Replace with '/allview' if you prefer
def allproducts():
  # Fetch all products from the database (similar to product.html)
  products = db.child("products").get().val()

  return render_template('allview.html', products=products)


@app.route('/cameraview')
def cameraview():
    # Fetch all products from the database
    products = db.child("products").get().val()

    # Filter products for the "camera" category
    cameras = {product_id: product for product_id, product in products.items() if product.get('category') == "camera"}

    return render_template('cameraview.html', products=cameras)  # Pass filtered cameras



@app.route('/lensesview')
def lensesview():
    # Fetch all products from the database
    products = db.child("products").get().val()

    # Filter products for the "lens" category (assuming your category is "lens")
    lenses = {product_id: product for product_id, product in products.items() if product.get('category') == "lenses"}

    return render_template('lensesview.html', products=lenses)  # Pass filtered lenses


@app.route('/accessoriesview')
def accessoriesview():
    # Fetch all products from the database
    products = db.child("products").get().val()

    # Filter products for the "accessories" category (assuming your category is "accessories")
    accessories = {product_id: product for product_id, product in products.items() if product.get('category') == "accessories"}

    return render_template('accessoriesview.html', products=accessories)  # Pass filtered accessories


# Cart and Check out code 


@app.route('/cart', methods=['GET', 'POST'])
def cart():
    if request.method == 'POST':
        product_id = request.form['product_id']
        cart = session.get('cart', [])  # Get existing cart or create an empty one
        cart.append(product_id)
        session['cart'] = cart  # Store the updated cart in the session
        return redirect('/cart')  # Refresh the cart page

    # Render the cart page
    # Fetch cart items from the database using product_ids in session['cart']
    cart_items = fetch_cart_items_from_database(session['cart'])
    return render_template('cart.html', cart_items=cart_items)

def fetch_cart_items_from_database(product_ids):
    # Retrieve cart items from the database using the provided product IDs
    cart_items = {}  # Initialize an empty dictionary to store cart items
    for product_id in product_ids:
        product_data = db.child("products").child(product_id).get().val()
        if product_data:  # Check if product exists
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

# Payment functions 
payment_confirmation = None  # Initialize payment_confirmation variable globally
cart_items = {}  # Initialize payment_confirmation variable globally

def create_payment(amount, currency, customer_data, product_data):
    # Payment Gateway Specific Code to create payment request
    payment_intent = "your_payment_intent"  # Placeholder value
    return payment_intent

def process_payment(card_number, expiry_date, cvv, name_on_card):
    # Payment Gateway Specific Code to process payment
    global payment_confirmation
    payment_confirmation = "success"  # Placeholder value, should be set based on actual payment processing
    return payment_confirmation

@app.route('/checkout', methods=['POST'])
def checkout_route():
    global cart_items  # Access the global cart_items variable

    # Process payment form submission
    card_number = request.form.get('card_number')
    expiry_date = request.form.get('expiry_date')
    cvv = request.form.get('cvv')
    name_on_card = request.form.get('name')

    # Validate payment details and process payment using your payment gateway's API
    payment_confirmation = process_payment(card_number, expiry_date, cvv, name_on_card)

    if payment_confirmation == "success":  # Assuming "success" is the payment confirmation status
        # Clear the cart after successful payment
        cart_items = {}

        # Redirect to confirmation route with payment confirmation status
        return redirect(url_for('confirmation', payment_confirmation=payment_confirmation))
    else:
        # Handle payment failure
        return "Payment failed. Please try again."

@app.route('/confirmation')
def confirmation():
    global payment_confirmation 
    payment_confirmation = request.args.get('payment_confirmation')
    payment_intent = request.args.get('payment_intent')
     # Access the global payment_confirmation variable

    if payment_confirmation == "success":
        # Render the confirmation template with payment confirmation details
        
        return render_template('confirmation.html', payment_confirmation=payment_confirmation , payment_intent=payment_intent)
    
    else:
        # Redirect to a failure page or handle payment failure
        return "Payment failed. Please try again."
    









# User registration route
@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user_data = {
            'email': email,
            'password': password,
        }
        db.child('users').push(user_data)
        return redirect(url_for('login'))  # Redirect to login after registration
    return render_template('register.html')  # Render the registration form

# User login route
@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        users = db.child('users').get().val()
        if users:
            for user_id, user_data in users.items():
                if user_data['email'] == email and user_data['password'] == password:
                    session['user_id'] = user_id
                    session['logged_in'] = True
                    return redirect(url_for('user_dashboard'))
        return render_template('login.html', message='Invalid credentials')
    return render_template('login.html', message='')

# User dashboard route
@app.route("/dashboard")
def user_dashboard():
    if 'logged_in' in session and session['logged_in']:
        user_id = session['user_id']
        user_data = db.child('users').child(user_id).get().val()
        return render_template('dashboard.html', user=user_data)
    else:
        return redirect(url_for('login'))  # Redirect to login if not logged in




@app.route("/search", methods=["GET"])
def search():
    search_query = request.args.get("searchInput")
    search_results = {}
    
    # Query the database for matching books based on search query
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

        # Validate user input (optional)

        # Create a dictionary to store contact information
        contact_data = {
            'name': name,
            'email': email,
            'message': message,
            'timestamp': datetime.now().strftime("%d/%m/%Y %H:%M:%S")  # Capture timestamp
        }

        # Push contact data to Firebase Realtime Database
        try:
            db.child('contacts').push(contact_data)
            flash('Your message has been sent successfully!', 'success')
        except Exception as e:
            # Handle database push error (e.g., display error message)
            flash('Error saving your message. Please try again later.', 'danger')

        return render_template('contact.html')

    return render_template('contact.html')



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000,debug=True)
