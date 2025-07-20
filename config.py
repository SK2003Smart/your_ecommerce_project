# your_ecommerce_project/config.py
import os

class Config:
    # IMPORTANT: For production, set this as an environment variable (e.g., export SECRET_KEY='your_super_secret_key')
    # For development, use a strong, randomly generated string. NEVER use a simple default in production.
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a_very_secret_and_complex_key_for_development_only'

    SQLALCHEMY_DATABASE_URI = 'sqlite:///ecommerce.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Configuration for payment gateway (Example: Stripe)
    # Get these from your Stripe Dashboard (publishable key is public, secret key must be kept secret!)
    # For production, set these as environment variables too.
    STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY') or 'pk_test_YOUR_STRIPE_PUBLIC_KEY'
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY') or 'sk_test_YOUR_STRIPE_SECRET_KEY'
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET') or 'whsec_YOUR_STRIPE_WEBHOOK_SECRET' # For verifying webhooks

    # Define a folder for product images
    # Make sure to create this folder: your_ecommerce_project/static/images
    UPLOAD_FOLDER = 'static/images'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}