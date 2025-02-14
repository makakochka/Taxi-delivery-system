from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_required, current_user
from models import update_stock, view_my_stock
from helpers import flash_error, flash_success, validate_stock_update, log_activity, log_error

stock = Blueprint("stock", __name__)


@stock.route("/update_stock", methods=["GET", "POST"])
@login_required
def update_stock_route():
    if request.method == "POST":
        try:
            new_stock = int(request.form["new_stock"])
            current_stock = view_my_stock(current_user.id)

            # Validate stock update
            is_valid, error_message = validate_stock_update(current_stock, new_stock)
            if not is_valid:
                flash_error(error_message)
                return redirect(url_for("stock.update_stock_route"))

            # Update stock
            if update_stock(current_user.id, current_stock + new_stock):
                log_activity("STOCK_UPDATE", current_user.id, f"Added {new_stock} items")
                flash_success(f"Stock updated successfully! New stock: {current_stock + new_stock}")
            else:
                log_error("STOCK_UPDATE_FAILED", current_user.id, f"Failed to add {new_stock} items")
                flash_error("Failed to update stock.")

            return redirect(url_for("dashboard"))

        except ValueError:
            flash_error("Please enter a valid number.")
            return redirect(url_for("update_stock_route"))

    # Handle GET request
    current_stock = view_my_stock(current_user.id)
    return render_template("update_stock.html", current_stock=current_stock)
