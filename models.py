import psycopg2
from psycopg2 import pool
from typing import Optional, List, Tuple
from config import DB_CONFIG
from flask_login import UserMixin
import bcrypt
import logging
import re
from psycopg2.extras import DictCursor, DictRow
from functools import wraps


class User(UserMixin):
    def __init__(self, driver_id, name):
        self.id = driver_id  # Required by Flask-Login
        self.name = name

    # Flask-Login requires these properties
    @property
    def is_active(self):
        return True  # Assuming all users are active

    @property
    def is_authenticated(self):
        return True  # Assuming the user is authenticated

    @property
    def is_anonymous(self):
        return False  # Assuming this is not an anonymous user


def with_db_connection(func):
    """
    Decorator to handle database connections automatically.
    Provides connection object as first argument to the decorated function.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        conn = get_connection()
        if not conn:
            logging.error(f"Failed to get database connection in {func.__name__}")
            return None
        try:
            result = func(conn, *args, **kwargs)
            return result
        except psycopg2.Error as e:
            logging.error(f"Database error in {func.__name__}: {e}")
            conn.rollback()
            return None
        finally:
            return_connection(conn)
    return wrapper


# Configure logging
logging.basicConfig(filename="app.log", level=logging.ERROR)

# Database connection pool
# conn_pool = psycopg2.pool.SimpleConnectionPool(1, 10, **DB_CONFIG)
try:
    conn_pool = psycopg2.pool.SimpleConnectionPool(1, 10, **DB_CONFIG)
    logging.debug("Database connection pool initialized successfully.")
except psycopg2.Error as e:
    logging.error(f"Failed to initialize database connection pool: {e}")
    conn_pool = None


def get_connection() -> Optional[psycopg2.extensions.connection]:
    """Get a database connection from the pool or create a new one"""
    if conn_pool is None:
        logging.warning("Connection pool is not initialized. Creating a single connection.")
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            logging.debug("Successfully created a single database connection.")
            return conn
        except psycopg2.Error as e:
            logging.error(f"Failed to create a database connection: {e}")
            return None

    try:
        conn = conn_pool.getconn()
        if conn:
            logging.debug("Successfully retrieved a database connection from the pool.")
            return conn
        else:
            logging.error("Failed to get a database connection: Connection pool is empty.")
            return None
    except psycopg2.Error as e:
        logging.error(f"Failed to get database connection: {e}")
        return None


def return_connection(conn: psycopg2.extensions.connection) -> None:
    """Return a database connection to the pool or close it"""
    if conn_pool is None:
        logging.warning("Connection pool is not initialized. Closing the single connection.")
        try:
            conn.close()
            logging.debug("Successfully closed the single database connection.")
        except psycopg2.Error as e:
            logging.error(f"Failed to close the database connection: {e}")
        return

    try:
        conn_pool.putconn(conn)
        logging.debug("Successfully returned the database connection to the pool.")
    except psycopg2.Error as e:
        logging.error(f"Failed to return database connection: {e}")


def hash_password(password: str) -> bytes:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt)


def check_password(hashed_password: bytes, user_password: str) -> bool:
    """Check if a password matches the hashed password"""
    if isinstance(hashed_password, memoryview):
        # Convert memoryview to bytes
        hashed_password = hashed_password.tobytes()
    elif isinstance(hashed_password, str):
        # Convert string to bytes
        hashed_password = hashed_password.encode("utf-8")
    return bcrypt.checkpw(user_password.encode("utf-8"), hashed_password)


def validate_driver_id(driver_id: str) -> bool:
    """Validate driver ID format"""
    pattern = r"^[a-zA-Z][a-zA-Z0-9_]{3,31}$"
    return bool(driver_id and re.match(pattern, driver_id))


@with_db_connection
def register_driver(conn, driver_id: str, name: str, password: str) -> bool:
    try:
        hashed_password = hash_password(password)
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM drivers WHERE driver_id = %s", (driver_id,))
            if cur.fetchone():
                return False
            cur.execute(
                """
                INSERT INTO drivers (driver_id, name, password_hash, current_stock)
                VALUES (%s, %s, %s, %s)
                """,
                (driver_id, name, hashed_password, 0),  # New drivers start with 0 stock
            )
            conn.commit()
            return True
    except psycopg2.Error as e:
        logging.error(f"Registration error: {e}")
        conn.rollback()
        return False


@with_db_connection
def login_driver(conn, driver_id: str, password: str) -> Optional[User]:
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT name, password_hash FROM drivers WHERE driver_id = %s", (driver_id,))
            result = cur.fetchone()
            if result and result[1] and check_password(result[1], password):
                return User(driver_id, result[0])
        return None
    except psycopg2.Error as e:
        logging.error(f"Login error: {e}")
        return None


@with_db_connection
def update_stock(conn, driver_id: str, new_stock: int) -> bool:
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE drivers SET current_stock = %s WHERE driver_id = %s", (new_stock, driver_id))
            conn.commit()
            return True
    except psycopg2.Error as e:
        logging.error(f"Update stock error: {e}")
        return False


@with_db_connection
def view_my_stock(conn, driver_id: str) -> int:
    """View current stock level"""
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT current_stock FROM drivers WHERE driver_id = %s", (driver_id,))
            result = cur.fetchone()
            return result[0] if result else 0
    except psycopg2.Error as e:
        logging.error(f"View stock error: {e}")
        return 0


@with_db_connection
def view_unassigned_requests(conn, driver_id: str) -> List[DictRow]:
    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:  # Use DictCursor
            # Fetch unassigned requests (pending) from delivery_requests
            cur.execute(
                """
                SELECT request_id, NULL AS driver_id, dropoff_address, quantity, ordered_at, 'pending' AS status
                FROM delivery_requests
                WHERE status = 'pending'
                AND request_id NOT IN (
                    SELECT request_id
                    FROM order_tracking
                    WHERE status = 'pending(*)' AND driver_id = %s
                )
                """,
                (driver_id,),
            )
            unassigned_requests = cur.fetchall()

            cur.execute(
                """
                SELECT request_id, driver_id, dropoff_address, quantity, ordered_at, 'pending(*)' AS status
                FROM order_tracking
                WHERE status = 'pending(*)' AND driver_id != %s
                """,
                (driver_id,),
            )
            resigned_requests = cur.fetchall()

            # Combine unassigned and resigned requests
            all_requests = unassigned_requests + resigned_requests

            # Remove duplicates (keep the latest status for each request_id)
            unique_requests = {}
            for req in all_requests:
                request_id = req["request_id"]
                if request_id not in unique_requests or req["status"] == "pending(*)":
                    unique_requests[request_id] = req

            return list(unique_requests.values())
    except psycopg2.Error as e:
        logging.error(f"View unassigned requests error: {e}")
        return []


@with_db_connection
def count_active_deliveries(conn, driver_id: str) -> int:
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM delivery_requests
                WHERE assigned_driver_id = %s AND status = 'in-progress'
                """,
                (driver_id,),
            )
            result = cur.fetchone()
            return result[0] if result else 0
    except psycopg2.Error as e:
        logging.error(f"Error counting active deliveries: {e}")
        return 0


@with_db_connection
def view_active_deliveries(conn) -> List[Tuple]:
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT r.request_id, r.dropoff_address, r.quantity,
                       r.ordered_at, d.name as driver_name
                FROM delivery_requests r
                JOIN drivers d ON r.assigned_driver_id = d.driver_id
                WHERE r.status = 'in-progress'
                ORDER BY r.ordered_at
                """
            )
            return cur.fetchall()
    except psycopg2.Error as e:
        logging.error(f"View active deliveries error: {e}")
        return []


@with_db_connection
def view_my_deliveries(conn, driver_id: str) -> List[Tuple]:
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT request_id, dropoff_address, quantity, ordered_at
                FROM delivery_requests
                WHERE assigned_driver_id = %s AND status = 'in-progress'
                ORDER BY ordered_at
                """,
                (driver_id,),
            )
            return cur.fetchall()
    except psycopg2.Error as e:
        logging.error(f"View my deliveries error: {e}")
        return []


@with_db_connection
def accept_delivery(conn, driver_id: str, request_id: int) -> bool:
    try:
        with conn.cursor() as cur:
            # Check if request is still pending and driver has enough stock
            cur.execute(
                """
                SELECT r.quantity, d.current_stock
                FROM delivery_requests r, drivers d
                WHERE r.request_id = %s
                AND d.driver_id = %s
                AND r.status = 'pending'
                """,
                (request_id, driver_id),
            )

            # Check if the driver already has 3 or more active deliveries
            # active_deliveries = count_active_deliveries(conn, driver_id)  # Remove `conn` argument
            active_deliveries = count_active_deliveries(driver_id)
            if active_deliveries >= 3:
                logging.error(f"Driver {driver_id} already has 3 active deliveries.")
                return False

            result = cur.fetchone()
            if not result:
                return False

            needed_quantity, current_stock = result
            if current_stock < needed_quantity:
                return False

            # Update request and driver stock
            cur.execute(
                """
                UPDATE delivery_requests
                SET status = 'in-progress', assigned_driver_id = %s
                WHERE request_id = %s AND status = 'pending'
                """,
                (driver_id, request_id),
            )

            cur.execute(
                """
                UPDATE drivers
                SET current_stock = current_stock - %s
                WHERE driver_id = %s
                """,
                (needed_quantity, driver_id),
            )

            # Remove resigned order from order_tracking if it exists
            cur.execute(
                """
                DELETE FROM order_tracking
                WHERE request_id = %s AND status = 'pending(*)'
                """,
                (request_id,),
            )

            conn.commit()
            return True
    except psycopg2.Error as e:
        logging.error(f"Accept delivery error: {e}")
        return False


@with_db_connection
def resign_delivery(conn, driver_id: str, request_id: int) -> bool:
    try:
        with conn.cursor() as cur:
            # Fetch the delivery details
            cur.execute(
                """
                SELECT dropoff_address, quantity, ordered_at
                FROM delivery_requests
                WHERE request_id = %s
                AND assigned_driver_id = %s
                AND status = 'in-progress'
                """,
                (request_id, driver_id),
            )

            result = cur.fetchone()
            if not result:
                return False

            dropoff_address, quantity, ordered_at = result

            # Restore the driver's stock
            cur.execute(
                """
                UPDATE drivers
                SET current_stock = current_stock + %s
                WHERE driver_id = %s
                """,
                (quantity, driver_id),
            )

            # Insert the delivery into order_tracking with status 'pending(*)'
            cur.execute(
                """
                INSERT INTO order_tracking (request_id, driver_id, dropoff_address, quantity, ordered_at, completed_at, status)
                VALUES (%s, %s, %s, %s, %s, NULL, 'pending(*)')
                """,
                (request_id, driver_id, dropoff_address, quantity, ordered_at),
            )

            # Update the delivery_requests table to set status back to 'pending'
            cur.execute(
                """
                UPDATE delivery_requests
                SET status = 'pending', assigned_driver_id = NULL
                WHERE request_id = %s
                AND assigned_driver_id = %s
                AND status = 'in-progress'
                """,
                (request_id, driver_id),
            )

            conn.commit()
            return True
    except psycopg2.Error as e:
        logging.error(f"Resign delivery error: {e}")
        conn.rollback()


@with_db_connection
def complete_delivery(conn, driver_id: str, request_id: int) -> bool:
    try:
        with conn.cursor() as cur:
            # Fetch the delivery details
            cur.execute(
                """
                SELECT dropoff_address, quantity, ordered_at
                FROM delivery_requests
                WHERE request_id = %s
                AND assigned_driver_id = %s
                AND status = 'in-progress'
                """,
                (request_id, driver_id),
            )

            result = cur.fetchone()
            if not result:
                return False

            dropoff_address, quantity, ordered_at = result

            # Insert the delivery into order_tracking
            cur.execute(
                """
                INSERT INTO order_tracking (request_id, driver_id, dropoff_address, quantity, ordered_at, completed_at, status)
                VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP, 'completed')
                """,
                (request_id, driver_id, dropoff_address, quantity, ordered_at),
            )

            # Delete the delivery from delivery_requests
            cur.execute(
                """
                DELETE FROM delivery_requests
                WHERE request_id = %s
                AND assigned_driver_id = %s
                AND status = 'in-progress'
                """,
                (request_id, driver_id),
            )

            conn.commit()
            return True
    except psycopg2.Error as e:
        logging.error(f"Complete delivery error: {e}")
        conn.rollback()
        return False
