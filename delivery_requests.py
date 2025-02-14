# import csv
# # from datetime import datetime
# import random

# # Define addresses in both cities
# MITAKA_ADDRESSES = [
#     "三鷹市下連雀1-1-1",
#     "三鷹市下連雀2-2-2",
#     "三鷹市下連雀3-3-3",
#     "三鷹市井の頭1-4-4",
#     "三鷹市井の頭2-5-5",
#     "三鷹市牟礼1-6-6",
#     "三鷹市牟礼2-7-7",
#     "三鷹市北野1-8-8",
#     "三鷹市北野2-9-9",
#     "三鷹市新川1-10-10",
#     "三鷹市新川2-11-11",
#     "三鷹市中原1-12-12",
#     "三鷹市中原2-13-13",
#     "三鷹市深大寺1-14-14",
#     "三鷹市深大寺2-15-15",
# ]

# MUSASHINO_ADDRESSES = [
#     "武蔵野市吉祥寺本町1-1-1",
#     "武蔵野市吉祥寺本町2-2-2",
#     "武蔵野市吉祥寺南町1-3-3",
#     "武蔵野市吉祥寺南町2-4-4",
#     "武蔵野市中町1-5-5",
#     "武蔵野市中町2-6-6",
#     "武蔵野市御殿山1-7-7",
#     "武蔵野市御殿山2-8-8",
#     "武蔵野市桜堤1-9-9",
#     "武蔵野市桜堤2-10-10",
#     "武蔵野市境1-11-11",
#     "武蔵野市境2-12-12",
#     "武蔵野市境南町1-13-13",
#     "武蔵野市境南町2-14-14",
#     "武蔵野市関前1-15-15",
# ]


# # Generate random datetime on 2025-02-13
# def random_datetime():
#     hour = random.randint(0, 23)
#     minute = random.randint(0, 59)
#     second = random.randint(0, 59)
#     microsecond = random.randint(0, 999999)
#     return f"2025-02-13 {hour:02d}:{minute:02d}:{second:02d}.{microsecond:06d}"


# # Write to CSV with explicit NULL values
# with open("delivery_requests.csv", "w", newline="", encoding="utf-8") as f:
#     writer = csv.writer(f)
#     # Write header
#     writer.writerow(
#         [
#             "request_id",
#             "dropoff_address",
#             "quantity",
#             "status",
#             "assigned_driver_id",
#             "ordered_at",
#             "start_time",
#         ]
#     )

#     # Write 30 requests
#     for i in range(1, 31):
#         writer.writerow(
#             [
#                 i,  # request_id
#                 random.choice(MITAKA_ADDRESSES + MUSASHINO_ADDRESSES),  # dropoff_address
#                 random.randint(1, 3),  # quantity
#                 "pending",  # status
#                 "NULL",  # assigned_driver_id
#                 random_datetime(),  # ordered_at
#                 "NULL",  # start_time
#             ]
#         )

# print("delivery_requests.csv has been generated successfully!")


import random
from datetime import datetime
import psycopg2

# Define addresses in both cities
MITAKA_ADDRESSES = [
    "三鷹市下連雀1-1-1",
    "三鷹市下連雀2-2-2",
    "三鷷市下連雀3-3-3",
    "三鷹市井の頭1-4-4",
    "三鷹市井の頭2-5-5",
    "三鷹市牟礼1-6-6",
    "三鷹市牟礼2-7-7",
    "三鷹市北野1-8-8",
    "三鷹市北野2-9-9",
    "三鷹市新川1-10-10",
    "三鷹市新川2-11-11",
    "三鷹市中原1-12-12",
    "三鷹市中原2-13-13",
    "三鷹市深大寺1-14-14",
    "三鷹市深大寺2-15-15",
]

MUSASHINO_ADDRESSES = [
    "武蔵野市吉祥寺本町1-1-1",
    "武蔵野市吉祥寺本町2-2-2",
    "武蔵野市吉祥寺南町1-3-3",
    "武蔵野市吉祥寺南町2-4-4",
    "武蔵野市中町1-5-5",
    "武蔵野市中町2-6-6",
    "武蔵野市御殿山1-7-7",
    "武蔵野市御殿山2-8-8",
    "武蔵野市桜堤1-9-9",
    "武蔵野市桜堤2-10-10",
    "武蔵野市境1-11-11",
    "武蔵野市境2-12-12",
    "武蔵野市境南町1-13-13",
    "武蔵野市境南町2-14-14",
    "武蔵野市関前1-15-15",
]


def random_datetime():
    hour = random.randint(0, 23)
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    microsecond = random.randint(0, 999999)
    return datetime(2025, 2, 13, hour, minute, second, microsecond)


try:
    # Connect to the database
    conn = psycopg2.connect(
        dbname="taxi", user="postgres", password="kakashka3kakashka4", host="localhost", port="5432"
    )
    cur = conn.cursor()

    # First, clear existing data (optional)
    cur.execute("TRUNCATE TABLE delivery_requests RESTART IDENTITY")

    # Insert 30 requests
    for i in range(1, 31):
        cur.execute(
            """
            INSERT INTO delivery_requests
            (request_id, dropoff_address, quantity, status, assigned_driver_id, ordered_at, start_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
            (
                i,  # request_id
                random.choice(MITAKA_ADDRESSES + MUSASHINO_ADDRESSES),  # dropoff_address
                random.randint(1, 3),  # quantity
                "pending",  # status
                None,  # assigned_driver_id
                random_datetime(),  # ordered_at
                None,  # start_time
            ),
        )

    # Commit the transaction
    conn.commit()
    print("Successfully inserted 30 delivery requests into the database!")

except psycopg2.Error as e:
    print(f"Database error: {e}")
    conn.rollback()
finally:
    if "cur" in locals():
        cur.close()
    if "conn" in locals():
        conn.close()
