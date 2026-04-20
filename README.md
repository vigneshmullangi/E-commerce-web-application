# 🛒 FreshMart — E-Commerce Web App
### Django + MySQL (XAMPP) + HTML/CSS/JS

---

## 📂 Project Structure

```
freshmart/
├── manage.py
├── requirements.txt
├── freshmart/                 ← Django project package
│   ├── settings.py            ← MySQL config lives here
│   ├── urls.py                ← all routes
│   ├── wsgi.py
│   └── asgi.py
└── store/                     ← main app
    ├── models.py              ← Category, Product, Order, OrderItem
    ├── views.py               ← all page & AJAX views
    ├── admin.py               ← admin panel registrations
    ├── management/
    │   └── commands/
    │       └── seed_products.py   ← fills DB with 24 products
    ├── templates/store/
    │   ├── base.html          ← shared layout (navbar, cart drawer, toast)
    │   ├── signup.html
    │   ├── login.html
    │   ├── home.html          ← carousel offers
    │   ├── products.html      ← product grid with filters
    │   ├── about.html         ← story, location, customer count
    │   └── order_confirm.html ← thank-you page
    └── static/store/
        ├── css/style.css
        └── js/main.js
```

---

## ⚡ Setup Steps (do these in order)

### 1. Start XAMPP
- Open **XAMPP Control Panel**
- Start **Apache** and **MySQL**

### 2. Create the Database
- Open **phpMyAdmin** → `http://127.0.0.1/phpmyadmin/`
- Click **Databases** tab
- Type `freshmart_db` in the name field
- Choose collation: **utf8mb4_general_ci**
- Click **Create**

### 3. Install Python Dependencies
Open a terminal/command prompt inside the `freshmart/` folder:

```bash
pip install -r requirements.txt
```

> 💡 On Windows you may need **Visual C++ Build Tools** for `mysqlclient`.
> Alternative: replace `mysqlclient` with `PyMySQL` and add this to `settings.py`:
> ```python
> import pymysql
> pymysql.install_as_MySQLdb()
> ```

### 4. Run Migrations (creates tables in MySQL)
```bash
python manage.py migrate
```

### 5. Seed Products (fills categories + 24 products)
```bash
python manage.py seed_products
```

### 6. Start the Development Server
```bash
python manage.py runserver
```

### 7. Open the App
Go to: **http://127.0.0.1:8000/**

---

## 🧭 How It Works

| Page | URL | Description |
|------|-----|-------------|
| Sign Up | `/signup/` | Create account (name, email, phone, password) |
| Login | `/login/` | Login with email + password |
| Home | `/` | 5-slide auto-scrolling offer carousel |
| Products | `/products/` | All 24 products with category filters |
| Products (filtered) | `/products/?cat=1` | Filter by category ID |
| About | `/about/` | Story, location, live customer count |
| Cart | (drawer) | Click 🛒 icon — AJAX-powered |
| Order Confirm | `/order/confirm/` | Shows after checkout |
| Admin | `/admin/` | Manage products, orders, users |

---

## 💰 Delivery Logic
- Cart subtotal **< ₹500** → **₹50 delivery charge**
- Cart subtotal **≥ ₹500** → **Free delivery**

---

## 🏷️ Unit System
Products support mixed units automatically:
- **Oils** → 250ml, 500ml, 1L  (price stored per litre)
- **Dry Fruits / Spices** → 50g, 100g, 250g, 500g  (price per kg)
- **Rice** → 250g, 500g, 1kg, 5kg
- **Dairy (milk)** → 500ml, 1L, 2L
- **Vegetables** → 250g, 500g, 1kg, 2kg

Price updates live when you select a different unit.

---

## 🔧 Admin Panel
Go to `http://127.0.0.1:8000/admin/` and log in with a superuser.
Create one with:
```bash
python manage.py createsuperuser
```
From admin you can add/edit/delete products, categories, and view all orders.
