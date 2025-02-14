from flask import Flask, request, session, redirect, url_for, render_template, flash
from routes.auth import auth
from routes.delivery import delivery
from models import User, get_connection, return_connection
from routes.stock import stock
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from config import SECRET_KEY
from models import (
    register_driver,
    # login_driver,
    update_stock,
    view_my_stock,
    view_unassigned_requests,
    view_active_deliveries,
    view_my_deliveries,
    accept_delivery,
    complete_delivery,
)
import psycopg2
import logging
from datetime import timedelta
import os
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


logging.basicConfig(filename="security.log", level=logging.WARNING)

app = Flask(__name__)
app.secret_key = SECRET_KEY  # Use the secret key from the environment

app.config.update(
    SESSION_COOKIE_SECURE=True,  # Only send cookies over HTTPS
    SESSION_COOKIE_HTTPONLY=True,  # Prevent client-side JavaScript from accessing the cookie
    SESSION_COOKIE_SAMESITE="Lax",  # Prevent CSRF attacks
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),  # Session expires after 30 minutes
)

# Register Blueprints
app.register_blueprint(auth)
app.register_blueprint(delivery)
app.register_blueprint(stock)

# Initialize Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = "login"


# User loader callback for Flask-Login
@login_manager.user_loader
def load_user(driver_id):
    """Load a user from the database by driver_id."""
    conn = get_connection()
    if not conn:
        return None

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM drivers WHERE driver_id = %s", (driver_id,))
            result = cur.fetchone()
            if result:
                return User(driver_id, result[0])  # Return a User object
            return None
    except psycopg2.Error as e:
        logging.error(f"Error loading user: {e}")
        return None
    finally:
        return_connection(conn)


@app.route("/")
def index():
    if "driver_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        driver_id = request.form["driver_id"]
        name = request.form["name"]
        password = request.form["password"]
        if register_driver(driver_id, name, password):
            flash("Registration successful!", "success")
            return redirect(url_for("auth.login"))
        flash("Registration failed. Please check your inputs.", "error")
    return render_template("register.html")


@app.before_request
def clear_session():
    if not hasattr(app, "session_cleared"):
        session.clear()  # Clear the session on the first request
        app.session_cleared = True  # Mark the session as cleared


# @app.route("/login", methods=["GET", "POST"])
# def login():
#     if request.method == "POST":
#         driver_id = request.form["driver_id"]
#         password = request.form["password"]
#         user = login_driver(driver_id, password)  # This returns a User object
#         if user:
#             session.clear()  # Clear the old session
#             session["driver_id"] = driver_id  # Start a new session
#             session.permanent = True  # Make the session permanent
#             os.urandom(24)  # Regenerate session ID
#             login_user(user)  # Log in the user using Flask-Login
#             flash("Login successful!", "success")
#             return redirect(url_for("dashboard"))
#         flash("Login failed. Please check your credentials.", "error")
#     return render_template("login.html")


# @app.route("/logout")
# @login_required
# def logout():
#     logout_user()  # Log out the user
#     flash("You have been logged out.", "info")
#     return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    if "driver_id" not in session:
        return redirect(url_for("login"))
    stock = view_my_stock(session["driver_id"])  # Call the function here
    return render_template("dashboard.html", driver_name=session["driver_name"], stock=stock)


@app.route("/update_stock", methods=["POST"])
def update_stock_route():
    if "driver_id" not in session:
        return redirect(url_for("login"))
    new_stock = int(request.form["new_stock"])
    if update_stock(session["driver_id"], new_stock):
        flash("Stock updated successfully!", "success")
    else:
        flash("Failed to update stock.", "error")
    return redirect(url_for("dashboard"))


@app.route("/view_unassigned_requests")
def view_unassigned_requests_route():
    if "driver_id" not in session:
        return redirect(url_for("login"))
    requests = view_unassigned_requests(current_user.id)
    return render_template("unassigned_requests.html", requests=requests)


@app.route("/view_active_deliveries")
def view_active_deliveries_route():
    if "driver_id" not in session:
        return redirect(url_for("login"))
    deliveries = view_active_deliveries()
    return render_template("order_tracking.html", deliveries=deliveries)


@app.route("/view_my_deliveries")
def view_my_deliveries_route():
    if "driver_id" not in session:
        return redirect(url_for("login"))
    my_deliveries = view_my_deliveries(session["driver_id"])
    return render_template("my_deliveries.html", my_deliveries=my_deliveries)


@app.route("/accept_delivery/<int:request_id>")
def accept_delivery_route(request_id):
    if "driver_id" not in session:
        return redirect(url_for("login"))
    if accept_delivery(session["driver_id"], request_id):
        flash("Delivery accepted successfully!", "success")
    else:
        flash("Failed to accept delivery.", "error")
    return redirect(url_for("dashboard"))


@app.route("/complete_delivery/<int:request_id>")
def complete_delivery_route(request_id):
    if "driver_id" not in session:
        return redirect(url_for("login"))
    if complete_delivery(session["driver_id"], request_id):
        flash("Delivery completed successfully!", "success")
    else:
        flash("Failed to complete delivery.", "error")
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    app.run(host="127.0.0.1", debug=os.getenv("FLASK_DEBUG", "False").lower() == "true")
