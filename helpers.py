from functools import wraps
from flask import flash, session, redirect, url_for
import logging
from typing import Optional, Callable, Any
import re


# Flash message helpers
def flash_error(message: str) -> None:
    """Flash an error message and log it."""
    flash(message, "error")
    logging.error(message)


def flash_success(message: str) -> None:
    """Flash a success message and log it."""
    flash(message, "success")
    logging.info(message)


def flash_info(message: str) -> None:
    """Flash an info message."""
    flash(message, "info")


# Validation helpers
def validate_driver_id(driver_id: str) -> bool:
    """Validate driver ID format (exactly 4 characters)."""
    return bool(driver_id and len(driver_id) == 4)


def validate_password(password: str) -> bool:
    """
    Validate password format:
    - 8-32 characters
    - Starts with a letter
    - Contains only alphanumeric and underscore
    """
    pattern = r"^[a-zA-Z][a-zA-Z0-9_]{7,31}$"
    return bool(re.match(pattern, password))


def validate_stock_update(current_stock: int, new_stock: int) -> tuple[bool, Optional[str]]:
    """
    Validate stock update request.
    Returns (is_valid, error_message)
    """
    if new_stock <= 0:
        return False, "Please enter a number greater than 0."
    if current_stock + new_stock > 9:
        return False, "The total stock cannot exceed 9."
    return True, None


# Authentication decorator
def login_required(f: Callable) -> Callable:
    """Custom login required decorator that checks session."""

    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if "driver_id" not in session:
            flash_error("Please log in to access this page.")
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


# Response formatting
def format_error_response(message: str) -> dict:
    """Format an error response."""
    return {"success": False, "message": message, "status": "error"}


def format_success_response(data: Any = None, message: str = "") -> dict:
    """Format a success response."""
    response = {"success": True, "status": "success"}
    if data is not None:
        response["data"] = data
    if message:
        response["message"] = message
    return response


# Address validation
def validate_address(address: str) -> bool:
    """
    Validate that address is in allowed areas
    (三鷹市 or 武蔵野市)
    """
    allowed_areas = ["三鷹市", "武蔵野市"]
    return any(area in address for area in allowed_areas)


# Delivery helpers
def can_accept_delivery(
    active_deliveries: int, stock: int, required_stock: int
) -> tuple[bool, Optional[str]]:
    """
    Check if a driver can accept a delivery.
    Returns (can_accept, error_message)
    """
    if active_deliveries >= 3:
        return False, "You can only handle up to 3 deliveries at a time."
    if stock < required_stock:
        return False, "Insufficient stock for this delivery."
    return True, None


# Logging helpers
def log_activity(activity_type: str, user_id: str, details: str) -> None:
    """Log user activity with standardized format."""
    logging.info(f"ACTIVITY: {activity_type} | USER: {user_id} | DETAILS: {details}")


def log_error(error_type: str, user_id: str, error_details: str) -> None:
    """Log errors with standardized format."""
    logging.error(f"ERROR: {error_type} | USER: {user_id} | DETAILS: {error_details}")


# Time formatting
def format_timestamp(timestamp) -> str:
    """Format timestamp for display."""
    return timestamp.strftime("%y-%m-%d %H:%M")
