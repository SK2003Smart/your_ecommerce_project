# your_ecommerce_project
This is a modern Flask-based E-commerce Store with essential shopping functionalities and a sleek user interface. It allows users to browse products, manage a shopping cart, and place orders with integrated payment gateway support (Razorpay example). The project also features an administrative panel for product management.

# My E-commerce Store 🛍️

A modern, full-featured e-commerce web application built with Flask, providing a seamless shopping experience for users and an intuitive admin panel for product management.

## ✨ Features

* **User Authentication:** Secure registration, login, and logout functionalities. 🔐
* **User Profiles:** Users can view and update their personal details, including delivery address and contact information. 👤
* **Product Catalog:** Browse a wide range of products with detailed descriptions, pricing, and real-time stock availability. 📦
* **Shopping Cart:** Effortlessly add, update quantities of, and remove products from the shopping cart. 🛒
* **Checkout Process:**
    * Cash on Delivery (COD) option available. 💵
    * Integrated Online Payment Gateway (Razorpay example) for secure and smooth transactions. 💳
* **Order Management:** Users can view a comprehensive history of all their placed orders with their current statuses (e.g., Pending, Confirmed, Shipped, Delivered, Cancelled). 🚚
* **Admin Panel:** A dedicated and secure administrative interface for full control over product inventory. 🛠️
    * Add new products with all necessary details (name, description, price, stock, image URL). ➕
    * Edit existing product information. 📝
    * Delete products from the store. 🗑️
* **Dynamic UI:** Responsive design ensures a consistent and enjoyable user experience across various devices (desktops, tablets, mobiles). 📱💻
* **High-Class Visuals:**
    * Prominent brand logo in the navigation bar for a professional identity. 🌟
    * Engaging hero video section on the homepage, creating a modern and immersive first impression. 🎬

## 💻 Tech Stack

* **Backend Framework:** Flask (Python) 🐍
* **Database:** SQLite (lightweight, file-based database) 🗄️
* **ORM (Object-Relational Mapper):** Flask-SQLAlchemy
* **Frontend:** HTML5, CSS3, JavaScript, Jinja2 (templating engine) 🌐
* **Password Hashing:** Werkzeug Security
* **Payment Gateway:** Razorpay (integrated for online payments) 💰
* **Development Tools:** Git, Virtual Environments (venv/conda) 🌿

## 🚀 Setup Instructions

### Prerequisites

Before you begin, ensure you have the following installed:

* **Python:** Version 3.10, 3.11, or 3.12 is recommended. (Note: Python 3.13 is currently incompatible with certain Flask-SQLAlchemy/SQLAlchemy versions.) 🐍
* **`pip`:** Python package installer.
* **`git`:** Version control system for cloning the repository.

### Installation Steps

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-username/your-ecommerce-project.git](https://github.com/your-username/your-ecommerce-project.git)
    cd your_ecommerce_project
    ```

2.  **Create and activate a virtual environment:**
    It's highly recommended to use a virtual environment to manage project dependencies isolation.
    ```bash
    python -m venv venv
    # On Windows:
    .\venv\Scripts\activate
    # On macOS/Linux:
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    Ensure your `requirements.txt` is up-to-date with the specified versions.
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set Environment Variables (Crucial for Security & Production):**
    Create a `.env` file in your project root, or set these as system environment variables. This is vital for securing sensitive information like secret keys and API credentials.
    ```
    # .env (for local development, ensure this file is NOT committed to Git for production!)
    SECRET_KEY='a_very_long_and_random_secret_key_here' # 🔑 GENERATE A UNIQUE, STRONG KEY!
    RAZORPAY_KEY_ID='rzp_test_YOUR_RAZORPAY_KEY_ID'   # 💳 Get this from your Razorpay Dashboard (use Test Mode first)
    RAZORPAY_KEY_SECRET='YOUR_RAZORPAY_KEY_SECRET' # 🤫 Keep this secret! Get from Razorpay Dashboard
    # STRIPE_PUBLIC_KEY='pk_test_...' # Uncomment and fill if you also integrate Stripe
    # STRIPE_SECRET_KEY='sk_test_...' # Uncomment and fill if you also integrate Stripe
    # STRIPE_WEBHOOK_SECRET='whsec_...' # Uncomment and fill if you also integrate Stripe
    ```
    *(If using a `.env` file, ensure you have `python-dotenv` installed: `pip install python-dotenv`, and add `from dotenv import load_dotenv; load_dotenv()` at the very top of your `app.py`)*

5.  **Initialize the Database:**
    The SQLite database (`ecommerce.db`) will be automatically created when `app.py` runs for the first time. If you encounter schema errors or want a fresh start, delete the existing database file.
    ```bash
    # (Optional, to delete existing database and create a fresh one)
    rm instance/ecommerce.db  # On Linux/macOS
    del instance\ecommerce.db # On Windows
    ```

6.  **Add Static Assets:**
    * **Images:** Place your product images (e.g., `mouse.jpg`, `keyboard.jpg`, `usbc_hub.
