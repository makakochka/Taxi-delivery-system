# routes/delivery.py
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models import (
    view_unassigned_requests,
    view_my_deliveries,
    accept_delivery,
    resign_delivery,
    complete_delivery,
    get_connection,
    return_connection,
)
from datetime import datetime
import psycopg2
from psycopg2.extras import DictCursor
import logging

delivery = Blueprint("delivery", __name__)


@delivery.route("/unassigned_requests")
@login_required
def view_unassigned_requests_route():
    requests = view_unassigned_requests(current_user.id)  # Pass current_user.id
    return render_template("unassigned_requests.html", requests=requests)


@delivery.route("/my_deliveries")
@login_required
def view_my_deliveries_route():
    my_deliveries = view_my_deliveries(current_user.id)
    return render_template("my_deliveries.html", my_deliveries=my_deliveries)


@delivery.route("/accept_delivery/<int:request_id>")
@login_required
def accept_delivery_route(request_id):
    if accept_delivery(current_user.id, request_id):
        flash("Delivery accepted successfully!", "success")
    else:
        flash("Failed to accept delivery.", "error")
    return redirect(url_for("dashboard"))


@delivery.route("/resign_delivery/<int:request_id>")
@login_required
def resign_delivery_route(request_id):
    if resign_delivery(current_user.id, request_id):
        flash("Delivery resigned successfully!", "success")
    else:
        flash("Failed to resign from delivery.", "error")
    return redirect(url_for("dashboard"))


@delivery.route("/complete_delivery/<int:request_id>")
@login_required
def complete_delivery_route(request_id):
    if complete_delivery(current_user.id, request_id):
        flash("Delivery completed successfully!", "success")
    else:
        flash("Failed to complete delivery.", "error")
    return redirect(url_for("dashboard"))


@delivery.route("/order_tracking")
@login_required
def order_tracking():
    """View all orders with their current status"""
    conn = get_connection()
    if not conn:
        flash("Failed to connect to the database. Please try again later.", "error")
        return redirect(url_for("stock.dashboard"))

    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:  # Use DictCursor
            # Fetch unassigned requests (pending)
            cur.execute(
                """
                SELECT request_id, NULL AS driver_id, dropoff_address, quantity, ordered_at, NULL AS completed_at, 'pending' AS status
                FROM delivery_requests
                WHERE status = 'pending'
                """
            )
            unassigned_requests = cur.fetchall()
            logging.info(f"Fetched unassigned requests: {unassigned_requests}")

            # Fetch active deliveries (in-progress)
            cur.execute(
                """
                SELECT request_id, assigned_driver_id AS driver_id, dropoff_address, quantity, ordered_at, NULL AS completed_at, 'in-progress' AS status
                FROM delivery_requests
                WHERE status = 'in-progress'
                """
            )
            active_deliveries = cur.fetchall()
            logging.info(f"Fetched active deliveries: {active_deliveries}")

            # Fetch completed deliveries from order_tracking
            cur.execute(
                """
                SELECT request_id, driver_id, dropoff_address, quantity, ordered_at, completed_at, status
                FROM order_tracking
                """
            )
            completed_deliveries = cur.fetchall()
            logging.info(f"Fetched completed deliveries: {completed_deliveries}")

            # Combine all results
            all_orders = unassigned_requests + active_deliveries + completed_deliveries
            logging.info(f"All orders: {all_orders}")

            # Pass the current time to the template for elapsed time calculation
            now = datetime.now()
            return render_template("order_tracking.html", orders=all_orders, now=now)
    except psycopg2.Error as e:
        logging.error(f"Error fetching order tracking data: {e}")
        flash("An error occurred while fetching order data. Please try again later.", "error")
        return redirect(url_for("stock.dashboard"))
    finally:
        return_connection(conn)
