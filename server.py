import json
import uuid
from datetime import datetime
from pathlib import Path
from mcp.server.mcpserver import MCPServer

DATA_DIR = Path(__file__).resolve().parent / "data"
MENU_FILE = DATA_DIR / "menu.json"
TABLES_FILE = DATA_DIR / "tables.json"
BOOKINGS_FILE = DATA_DIR / "bookings.json"

mcp = MCPServer("RestaurantService")

def _read_json(file_path: Path) -> list[dict]:
    if not file_path.exists():
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def _write_json(file_path: Path, data: list[dict]) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

@mcp.tool()
def get_restaurant_info() -> dict:
    """Returns general restaurant details, operating hours, address, and seating rules."""
    return {
        "name": "L'Aura Bistro",
        "address": "42 Market Street, Downtown",
        "phone": "+1-555-019-2834",
        "operating_hours": {
            "Tuesday-Sunday": "12:00 - 23:00",
            "Monday": "Closed"
        },
        "available_time_slots": [
            "12:00", "13:30", "15:00", "18:00", "19:30", "21:00"
        ],
        "cancellation_policy": "Cancellations allowed up to 2 hours before booking time."
    }

@mcp.tool()
def get_menu(category: str | None = None, dietary_tag: str | None = None) -> list[dict]:
    """Retrieve menu items. Can filter by category or dietary tags."""
    menu = _read_json(MENU_FILE)
    results = [item for item in menu if item.get("available", True)]

    if category:
        target_category = category.strip().lower()
        results = [item for item in results if item.get("category", "").lower() == target_category]

    if dietary_tag:
        target_tag = dietary_tag.strip().lower()
        results = [
            item for item in results
            if any(target_tag == d.lower() for d in item.get("dietary", []))
        ]

    return results

@mcp.tool()
def check_available_tables(date: str, time_slot: str, party_size: int) -> list[dict]:
    """Check for available tables matching party size, date (YYYY-MM-DD), and time_slot."""
    tables = _read_json(TABLES_FILE)
    bookings = _read_json(BOOKINGS_FILE)

    booked_table_ids = {
        b["table_id"]
        for b in bookings
        if b.get("date") == date
        and b.get("time_slot") == time_slot
        and b.get("status") == "confirmed"
    }

    available = [
        t for t in tables
        if t["capacity"] >= party_size and t["table_id"] not in booked_table_ids
    ]
    available.sort(key=lambda t: t["capacity"])
    return available

@mcp.tool()
def book_table(
    customer_name: str,
    customer_phone: str,
    party_size: int,
    date: str,
    time_slot: str,
    special_requests: str = ""
) -> dict:
    """Book an optimal table for a party on a given date and time_slot."""
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return {"status": "error", "message": "Date format must be YYYY-MM-DD."}

    available_tables = check_available_tables(date, time_slot, party_size)
    if not available_tables:
        return {
            "status": "unavailable",
            "message": f"No tables available for {party_size} guests on {date} at {time_slot}."
        }

    selected_table = available_tables[0]
    booking_id = f"BK-{uuid.uuid4().hex[:6].upper()}"

    new_booking = {
        "booking_id": booking_id,
        "table_id": selected_table["table_id"],
        "customer_name": customer_name,
        "customer_phone": customer_phone,
        "party_size": party_size,
        "date": date,
        "time_slot": time_slot,
        "location": selected_table["location"],
        "special_requests": special_requests,
        "status": "confirmed",
        "created_at": datetime.now().isoformat()
    }

    bookings = _read_json(BOOKINGS_FILE)
    bookings.append(new_booking)
    _write_json(BOOKINGS_FILE, bookings)

    return {
        "status": "confirmed",
        "booking_id": booking_id,
        "table_id": selected_table["table_id"],
        "location": selected_table["location"],
        "date": date,
        "time_slot": time_slot,
        "party_size": party_size,
        "message": f"Table reserved successfully under {customer_name}."
    }

@mcp.tool()
def get_booking_details(booking_id: str) -> dict:
    """Look up an existing reservation using its booking ID."""
    bookings = _read_json(BOOKINGS_FILE)
    for booking in bookings:
        if booking.get("booking_id") == booking_id:
            return {"status": "found", "booking": booking}
    return {"status": "not_found", "message": f"No booking found with ID {booking_id}."}

@mcp.tool()
def cancel_booking(booking_id: str) -> dict:
    """Cancel a confirmed booking by booking ID."""
    bookings = _read_json(BOOKINGS_FILE)
    target = None

    for b in bookings:
        if b.get("booking_id") == booking_id:
            target = b
            break

    if not target:
        return {"status": "not_found", "message": f"Booking ID {booking_id} not found."}

    if target.get("status") == "cancelled":
        return {"status": "already_cancelled", "message": f"Booking {booking_id} is already cancelled."}

    target["status"] = "cancelled"
    target["cancelled_at"] = datetime.now().isoformat()
    _write_json(BOOKINGS_FILE, bookings)

    return {
        "status": "success",
        "booking_id": booking_id,
        "message": f"Booking {booking_id} has been cancelled."
    }

# In server.py
if __name__ == "__main__":
    # In mcp 2.x, change transport="sse" to transport="streamable-http"
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)