
from flask import Flask, render_template, request, redirect, flash, session
from datetime import datetime
import pyrebase

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
app.secret_key = 'your_secret_key'  # Replace with a strong secret key

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin123'

@app.route('/')
def index():
    return render_template('index.html')

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
      # Get the form data (modify field names as needed for products)
      product_category = request.form['product_category']
      product_brand = request.form['product_brand']
      product_model = request.form['product_model']   # Replace 'brand' with 'name'
      product_price = request.form['product_price']
      product_image = request.files['product_image']

      # Save the image to Firebase Storage (assuming the same logic)
      storage = firebase.storage()
      storage.child("product_images/" + product_image.filename).put(product_image)
      image_url = storage.child("product_images/" + product_image.filename).get_url(None)

      # Create a dictionary to store product data
      product_data = {
          'category': product_category,
          'brand': product_brand,  # Replace 'brand' with 'name'
          'model': product_model,
          'price': product_price,
          'image_url': image_url
      }

      # Push product data to Firebase Database (assuming a "products" node)
      db.child("products").push(product_data)

      # Fetch all products from the database (modify node name)
      products = db.child("products").get().val()

      return render_template('product.html', message='Product added successfully', products=products)
    else:
      # Fetch all products from the database (modify node name)
      products = db.child("products").get().val()

      return render_template('product.html', product=products)
  else:
    return redirect('/admin/login')



@app.route("/camera")
def camera():
    cameras = db.child("products").get().val()
    return render_template('camera.html', camera=cameras)








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

# Your existing routes using the Firebase database can go here...

if __name__ == '__main__':
    app.run(debug=True)
