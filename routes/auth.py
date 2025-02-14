from flask import Blueprint, request, session, redirect, url_for, flash, render_template
from flask_login import LoginManager, login_user, logout_user, login_required
from models import login_driver

auth = Blueprint("auth", __name__)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.login_view = "auth.login"


@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        driver_id = request.form["driver_id"]
        password = request.form["password"]
        user = login_driver(driver_id, password)  # This now returns a User object
        if user:
            login_user(user)  # Pass the User object to login_user
            session["driver_id"] = driver_id  # Store driver_id in session
            session["driver_name"] = user.name  # Store driver_name in session
            flash("Login successful!", "success")  # Flash success message
            return redirect(url_for("dashboard"))  # Redirect to dashboard
        else:
            flash("Login failed. Please check your credentials.", "error")  # Flash error message
    return render_template("login.html")


@auth.route("/logout")
@login_required
def logout():
    logout_user()  # Log out the user
    session.clear()  # Clear the session
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


# @auth.route("/register", methods=["GET", "POST"])
# def register():
#     if request.method == "POST":
#         driver_id = request.form["driver_id"]
#         name = request.form["name"]
#         password = request.form["password"]
#         if register_driver(driver_id, name, password):  # Now this will work
#             flash("Registration successful!", "success")
#             return redirect(url_for("login"))
#         flash("Registration failed. Please check your inputs.", "error")
#     return render_template("register.html")
