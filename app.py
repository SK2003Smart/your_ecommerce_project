# your_ecommerce_project/app.py

from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from functools import wraps
import json # Added for webhook handling

# Import Config from your config.py file
from config import Config

# Conceptual import for a payment gateway SDK (e.g., Stripe, if you choose to use it)
# pip install stripe
try:
    import stripe
except ImportError:
    stripe = None
    print("Warning: Stripe library not installed. Stripe payment gateway functionality will be limited.")

# Import Razorpay SDK (NEW)
# pip install razorpay
try:
    import razorpay
except ImportError:
    razorpay = None
    print("Warning: Razorpay library not installed. Razorpay payment gateway functionality will be limited.")


app = Flask(__name__)
# Load configurations from the Config class
app.config.from_object(Config)

# Initialize SQLAlchemy with the Flask app
db = SQLAlchemy(app)

# --- Database Models ---

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    address = db.Column(db.String(200), nullable=True)
    contact_number = db.Column(db.String(20), nullable=True)
    is_admin = db.Column(db.Boolean, default=False, nullable=False) # NEW FIELD for admin access control

    # Define relationships for User
    cart_items = db.relationship('CartItem', backref='user', lazy=True)
    orders = db.relationship('Order', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    # Default image URL if none provided for a product
    image_url = db.Column(db.String(200), default='/static/images/product_placeholder.png')

    def __repr__(self):
        return f'<Product {self.name}>'

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)

    # Establish relationship to Product model
    product = db.relationship('Product')

    def __repr__(self):
        return f'<CartItem User:{self.user_id} Product:{self.product_id} Qty:{self.quantity}>'

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    order_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='Pending', nullable=False) # e.g., Pending, Confirmed, Shipped, Delivered, Cancelled
    delivery_address = db.Column(db.String(255), nullable=False)
    contact_number = db.Column(db.String(20), nullable=False)
    payment_mode = db.Column(db.String(50), nullable=False) # e.g., UPI, Debit Card, COD
    transaction_id = db.Column(db.String(100), nullable=True) # To store payment gateway transaction ID (e.g., Razorpay Order ID)

    # Define relationship to OrderItem model
    order_items = db.relationship('OrderItem', backref='order', lazy=True)

    def __repr__(self):
        return f'<Order {self.id} User:{self.user_id} Status:{self.status}>'

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False) # Price at the time of order

    # Establish relationship to Product model
    product = db.relationship('Product')

    def __repr__(self):
        return f'<OrderItem Order:{self.order_id} Product:{self.product_id} Qty:{self.quantity}>'


# --- Helper Functions / Decorators ---

# This decorator ensures a user is logged in before accessing certain routes.
# It prevents redirect loops on login/register/public pages.
def login_required(f):
    @wraps(f) # Preserves original function's metadata
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            # Only redirect if the current endpoint is not a public one
            if request.endpoint not in ['login', 'register', 'index', 'static', 'product_detail']:
                return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# NEW: Decorator to restrict access to admin users only
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login')) # Not logged in

        user = User.query.get(user_id)
        if not user or not user.is_admin:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('index')) # Redirect non-admins to home or a forbidden page
        return f(*args, **kwargs)
    return decorated_function


# Context processor to inject global variables into all templates.
# 'current_year' and 'current_user' will be available in every template.
@app.context_processor
def inject_global_data():
    current_year = datetime.now().year
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id']) # Retrieve the full user object if logged in
    return dict(current_year=current_year, current_user=user)


# --- Routes ---

@app.route('/')
def index():
    products = Product.query.all()
    return render_template('index.html', products=products)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product_detail.html', product=product)

@app.route('/register', methods=['GET', 'POST'])
def register():
    # If user is already logged in, redirect to homepage
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        address = request.form.get('address', '') # Use .get for optional fields
        contact_number = request.form.get('contact_number', '')

        # Basic server-side validation
        if not username or not email or not password:
            flash('All fields are required!', 'danger')
            return redirect(url_for('register'))

        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'danger')
            return redirect(url_for('register'))
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('register'))

        # Create new user and hash password
        new_user = User(username=username, email=email, address=address, contact_number=contact_number)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit() # Save new user to database

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # If user is already logged in, redirect to homepage
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Find user by username
        user = User.query.filter_by(username=username).first()

        if user:
            if user.check_password(password):
                session['user_id'] = user.id # Set user ID in session
                flash('Logged in successfully!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Invalid username or password.', 'danger')
                return redirect(url_for('login'))
        else:
            flash('Invalid username or password.', 'danger')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None) # Remove user ID from session
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required # This page requires login
def profile():
    user_id = session.get('user_id')
    user = User.query.get(user_id) # Retrieve user from database
    if request.method == 'POST':
        user.username = request.form['username']
        user.email = request.form['email']
        # Update address and contact, gracefully handling empty submissions by setting them to empty string
        user.address = request.form.get('address', '')
        user.contact_number = request.form.get('contact_number', '')
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    return render_template('profile.html', user=user)

@app.route('/add_to_cart/<int:product_id>')
@login_required # This action requires login
def add_to_cart(product_id):
    user_id = session['user_id']
    product = Product.query.get_or_404(product_id)

    if product.stock <= 0:
        flash(f'Sorry, {product.name} is out of stock.', 'warning')
        return redirect(url_for('product_detail', product_id=product_id))

    cart_item = CartItem.query.filter_by(user_id=user_id, product_id=product_id).first()
    if cart_item:
        if cart_item.quantity >= product.stock:
            flash(f'Cannot add more {product.name}. Max stock reached in cart.', 'warning')
        else:
            cart_item.quantity += 1
            flash(f'{product.name} quantity updated in cart!', 'success')
    else:
        new_cart_item = CartItem(user_id=user_id, product_id=product_id, quantity=1)
        db.session.add(new_cart_item)
        flash(f'{product.name} added to cart!', 'success')
    db.session.commit()
    return redirect(url_for('view_cart'))

@app.route('/update_cart/<int:item_id>', methods=['POST'])
@login_required # This action requires login
def update_cart(item_id):
    cart_item = CartItem.query.get_or_404(item_id)
    if cart_item.user_id != session['user_id']:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('view_cart'))

    try:
        new_quantity = int(request.form['quantity'])
        product = cart_item.product # Get the product associated with the cart item

        if new_quantity < 0:
            flash('Quantity cannot be negative.', 'danger')
        elif new_quantity == 0:
            db.session.delete(cart_item)
            flash('Item removed from cart.', 'info')
        elif new_quantity > product.stock:
            flash(f'Only {product.stock} of {product.name} are available.', 'warning')
            cart_item.quantity = product.stock # Adjust to max available stock
        else:
            cart_item.quantity = new_quantity
            flash('Cart updated.', 'success')

        db.session.commit()
    except ValueError:
        flash('Invalid quantity.', 'danger')
    return redirect(url_for('view_cart'))


@app.route('/remove_from_cart/<int:item_id>')
@login_required # This action requires login
def remove_from_cart(item_id):
    cart_item = CartItem.query.get_or_404(item_id)
    if cart_item.user_id != session['user_id']:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('view_cart'))

    db.session.delete(cart_item)
    db.session.commit()
    flash('Item removed from cart.', 'info')
    return redirect(url_for('view_cart'))

@app.route('/cart')
@login_required # This page requires login
def view_cart():
    user_id = session['user_id']
    cart_items = CartItem.query.filter_by(user_id=user_id).all()
    total_cart_value = sum(item.product.price * item.quantity for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total_cart_value=total_cart_value)

@app.route('/checkout', methods=['GET', 'POST'])
@login_required # This page requires login
def checkout():
    user_id = session['user_id']
    user = User.query.get(user_id)
    cart_items = CartItem.query.filter_by(user_id=user_id).all()

    if not cart_items:
        flash('Your cart is empty!', 'warning')
        return redirect(url_for('index'))

    total_amount = sum(item.product.price * item.quantity for item in cart_items)
    # Razorpay amounts are in the smallest currency unit (e.g., paise for INR)
    razorpay_amount = int(total_amount * 100) # Convert to paise for INR

    if request.method == 'POST':
        delivery_address = request.form['delivery_address']
        contact_number = request.form['contact_number']
        payment_mode = request.form['payment_mode']

        # Update user's default address/contact if they changed it
        user.address = delivery_address
        user.contact_number = contact_number
        db.session.commit()

        # Check stock for all items before creating the order
        for item in cart_items:
            product = item.product
            if item.quantity > product.stock:
                flash(f'Not enough stock for {product.name}. Available: {product.stock}, In cart: {item.quantity}. Please adjust your cart.', 'danger')
                return redirect(url_for('view_cart'))

        # Create new order record
        new_order = Order(
            user_id=user_id,
            total_amount=total_amount,
            delivery_address=delivery_address,
            contact_number=contact_number,
            payment_mode=payment_mode,
            status='Pending' # Initial status for the order
        )
        db.session.add(new_order)
        db.session.flush() # Get the new_order.id before committing

        # Move items from cart to order_items and reduce product stock
        for item in cart_items:
            order_item = OrderItem(
                order_id=new_order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price=item.product.price # Store price at time of order
            )
            db.session.add(order_item)
            item.product.stock -= item.quantity # Reduce product stock
            # Do NOT delete cart item yet if online payment is chosen.
            # Only delete if COD, or after successful payment via webhook.
            if payment_mode == 'COD':
                db.session.delete(item) # Remove item from cart for COD

        # Payment Gateway Integration for Razorpay (UPDATED)
        if payment_mode in ['UPI', 'Debit Card']:
            if razorpay and app.config.get('RAZORPAY_KEY_ID') and app.config.get('RAZORPAY_KEY_SECRET'):
                try:
                    client = razorpay.Client(auth=(app.config['RAZORPAY_KEY_ID'], app.config['RAZORPAY_KEY_SECRET']))
                    # Create a Razorpay Order
                    razorpay_order = client.order.create({
                        'amount': razorpay_amount, # amount in smallest currency unit (paise for INR)
                        'currency': 'INR', # or 'USD', etc.
                        'receipt': f'order_rcpt_{new_order.id}', # Unique receipt ID
                        'notes': { # These notes are passed back in the webhook
                            'internal_order_id': new_order.id, # Your internal order ID
                            'user_id': user_id,
                        }
                    })

                    new_order.transaction_id = razorpay_order['id'] # Store Razorpay Order ID
                    new_order.status = 'Payment Initiated' # Update status
                    db.session.commit() # Commit order and stock updates here

                    flash('Please complete your payment.', 'info')
                    return render_template(
                        'checkout_payment.html',
                        razorpay_key_id=app.config['RAZORPAY_KEY_ID'],
                        razorpay_order_id=razorpay_order['id'], # Pass Razorpay Order ID to frontend
                        total_amount=total_amount,
                        order_id=new_order.id, # Your internal order ID
                        customer_name=user.username,
                        customer_email=user.email,
                        customer_contact=user.contact_number
                    )

                except Exception as e:
                    db.session.rollback() # Rollback the new_order if Razorpay order creation fails
                    flash(f'Error initiating payment: {e}', 'danger')
                    return redirect(url_for('checkout'))
            else:
                flash('Online payment gateway (Razorpay) not configured or library not found.', 'warning')
                flash('Please select Cash on Delivery or contact support.', 'info')
                db.session.rollback() # Rollback the order if online payment can't be processed
                return redirect(url_for('checkout'))
        else: # Cash on Delivery
            db.session.commit() # Commit all changes, including cart item deletions for COD
            flash('Your order has been placed via Cash on Delivery.', 'success')
            return redirect(url_for('order_confirmation', order_id=new_order.id))

    return render_template('checkout.html', user=user, cart_items=cart_items, total_amount=total_amount)

@app.route('/order_confirmation/<int:order_id>')
@login_required # This page requires login
def order_confirmation(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != session['user_id']:
        flash('Unauthorized access to order.', 'danger')
        return redirect(url_for('index'))
    return render_template('order_confirmation.html', order=order)

@app.route('/my_orders')
@login_required # This page requires login
def my_orders():
    user_id = session['user_id']
    orders = Order.query.filter_by(user_id=user_id).order_by(Order.order_date.desc()).all()
    return render_template('my_orders.html', orders=orders)


# --- Admin Routes ---
# These routes are now protected by both login_required and admin_required decorators.
# Only logged-in users who are marked as administrators can access them.

@app.route('/admin/add_product', methods=['GET', 'POST'])
@login_required
@admin_required # Requires admin privileges
def admin_add_product():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        stock = int(request.form['stock'])
        # Ensure image_url uses the new static/images path if empty
        image_url = request.form.get('image_url')
        if not image_url:
            image_url = '/static/images/product_placeholder.png'

        new_product = Product(name=name, description=description, price=price, stock=stock, image_url=image_url)
        db.session.add(new_product)
        db.session.commit()
        flash(f'Product "{name}" added successfully!', 'success')
        return redirect(url_for('admin_products'))
    return render_template('admin/add_product.html')

@app.route('/admin/products')
@login_required
@admin_required # Requires admin privileges
def admin_products():
    products = Product.query.all()
    return render_template('admin/products.html', products=products)

@app.route('/admin/edit_product/<int:product_id>', methods=['GET', 'POST'])
@login_required
@admin_required # Requires admin privileges
def admin_edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    if request.method == 'POST':
        product.name = request.form['name']
        product.description = request.form['description']
        product.price = float(request.form['price'])
        product.stock = int(request.form['stock'])
        # Preserve existing image_url if new one is empty
        new_image_url = request.form.get('image_url')
        if new_image_url:
            product.image_url = new_image_url
        # If new_image_url is empty, it means the user didn't change it,
        # so we keep the existing product.image_url.

        db.session.commit()
        flash(f'Product "{product.name}" updated successfully!', 'success')
        return redirect(url_for('admin_products'))
    return render_template('admin/edit_product.html', product=product)

@app.route('/admin/delete_product/<int:product_id>', methods=['POST'])
@login_required
@admin_required # Requires admin privileges
def admin_delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash(f'Product "{product.name}" deleted.', 'info')
    return redirect(url_for('admin_products'))


# --- Webhook for Razorpay (NEW) ---
# IMPORTANT: You MUST configure this URL in your Razorpay Dashboard -> Webhooks.
# For local testing, use ngrok to expose your localhost.
@app.route('/webhook/razorpay', methods=['POST'])
def razorpay_webhook():
    import hashlib
    import hmac

    # Get webhook payload and signature
    payload = request.get_data(as_text=True)
    razorpay_signature = request.headers.get('x-razorpay-signature')

    if not razorpay_signature:
        print("Webhook Error: No Razorpay signature found.")
        return 'Unauthorized', 401

    key_secret = app.config.get('RAZORPAY_KEY_SECRET')
    if not key_secret:
        print("Webhook Error: Razorpay Key Secret not configured.")
        return 'Internal Server Error', 500

    # Verify webhook signature
    try:
        # Generate expected signature
        generated_signature = hmac.new(
            key_secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        if generated_signature == razorpay_signature:
            event = json.loads(payload)
            event_type = event['event']

            # Handle payment.captured event (successful payment)
            if event_type == 'payment.captured':
                payment_id = event['payload']['payment']['entity']['id']
                razorpay_order_id = event['payload']['payment']['entity']['order_id'] # Razorpay's order ID
                # Extract your internal order ID from notes
                internal_order_id = event['payload']['payment']['entity']['notes'].get('internal_order_id')
                user_id_from_notes = event['payload']['payment']['entity']['notes'].get('user_id')

                if internal_order_id and user_id_from_notes:
                    with app.app_context():
                        order = Order.query.filter_by(id=internal_order_id, transaction_id=razorpay_order_id).first()
                        if order and order.status == 'Payment Initiated':
                            order.status = 'Confirmed'
                            db.session.commit()

                            # Clear user's cart items after successful payment
                            # Ensure user_id from notes matches session user_id or stored user_id for order
                            CartItem.query.filter_by(user_id=user_id_from_notes).delete()
                            db.session.commit()

                            print(f"Webhook: Payment captured for order {internal_order_id} (User: {user_id_from_notes}). Cart cleared.")
                        else:
                            print(f"Webhook: Payment captured for already processed or invalid order: {internal_order_id}")
                else:
                    print(f"Webhook: Payment intent succeeded without complete metadata: {payment_id}")

            # Handle other events like payment.failed, order.paid etc.
            elif event_type == 'payment.failed':
                # Similar logic to handle failed payments
                payment_id = event['payload']['payment']['entity']['id']
                razorpay_order_id = event['payload']['payment']['entity']['order_id']
                internal_order_id = event['payload']['payment']['entity']['notes'].get('internal_order_id')

                if internal_order_id:
                    with app.app_context():
                        order = Order.query.filter_by(id=internal_order_id, transaction_id=razorpay_order_id).first()
                        if order and order.status == 'Payment Initiated':
                            order.status = 'Payment Failed'
                            db.session.commit()
                            print(f"Webhook: Payment failed for order {internal_order_id}.")
                else:
                    print(f"Webhook: Payment failed without internal_order_id in notes. Payment ID: {payment_id}")

            else:
                print(f"Unhandled Razorpay event type: {event_type}")

            return 'OK', 200 # Acknowledge success
        else:
            print("Webhook Error: Signature mismatch.")
            return 'Signature mismatch', 400

    except json.JSONDecodeError:
        print("Webhook Error: Invalid JSON payload.")
        return 'Invalid JSON', 400
    except Exception as e:
        print(f"Webhook processing error: {e}")
        return 'Internal Server Error', 500


# --- Initial Database Setup and Running the App ---

if __name__ == '__main__':
    with app.app_context():
        # Creates database tables if they don't exist (or updates them if using migrations)
        db.create_all()
        # Optional: Add some dummy data if the database is empty for initial testing
        if Product.query.count() == 0:
            print("Adding dummy products...")
            p1 = Product(name="Wireless Mouse", description="Ergonomic wireless mouse with long battery life.", price=25.99, stock=50, image_url='/static/images/mouse.jpg')
            p2 = Product(name="Mechanical Keyboard", description="RGB mechanical keyboard with brown switches.", price=79.99, stock=30, image_url='/static/images/keyboard.jpg')
            p3 = Product(name="USB-C Hub", description="7-in-1 USB-C hub with HDMI, USB 3.0, and PD.", price=39.50, stock=100, image_url='/static/images/usbc_hub.jpg')
            db.session.add_all([p1, p2, p3])
            db.session.commit()
            print("Dummy products added.")

        # Optional: Create an admin user if none exists
        if not User.query.filter_by(is_admin=True).first():
            print("Creating a default admin user...")
            admin_user = User(username='admin', email='admin@example.com', is_admin=True)
            admin_user.set_password('adminpassword') # CHANGE THIS PASSWORD IN PRODUCTION!
            db.session.add(admin_user)
            db.session.commit()
            print("Default admin user created (username: admin, password: adminpassword). Please change password immediately!")


    app.run(debug=True) # Run in debug mode (DO NOT use debug=True in production)