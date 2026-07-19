"""
Mock customer and order data for the e-commerce support agent.

This module contains fictional data for one customer (Aarti Sharma, C-1001)
with three orders demonstrating different states (delivered, shipped, processing).
No PII or real account data.
"""

CUSTOMERS = {
    "C-1001": {
        "customer_id": "C-1001",
        "name": "Aarti Sharma",
        "tier": "Gold",
        "email": "aarti.sharma@example.com",
        "phone": "+1-555-0123",
        "address": "123 Main St, Springfield, IL 62701"
    }
}

ORDERS = {
    "O-9001": {
        "order_id": "O-9001",
        "customer_id": "C-1001",
        "status": "Delivered",
        "placed_on": "2024-01-15",
        "delivered_on": "2024-01-20",
        "total": 129.99,
        "items": [
            {"sku": "SKU-001", "name": "Wireless Mouse", "quantity": 1, "price": 29.99},
            {"sku": "SKU-002", "name": "USB-C Cable", "quantity": 2, "price": 15.00},
            {"sku": "SKU-003", "name": "Laptop Stand", "quantity": 1, "price": 70.00}
        ],
        "shipping_address": "123 Main St, Springfield, IL 62701",
        "tracking_number": "TRK-9001-XYZ"
    },
    "O-9002": {
        "order_id": "O-9002",
        "customer_id": "C-1001",
        "status": "Shipped",
        "placed_on": "2024-02-01",
        "shipped_on": "2024-02-03",
        "total": 89.99,
        "items": [
            {"sku": "SKU-010", "name": "Bluetooth Headphones", "quantity": 1, "price": 89.99}
        ],
        "shipping_address": "123 Main St, Springfield, IL 62701",
        "tracking_number": "TRK-9002-ABC"
    },
    "O-9003": {
        "order_id": "O-9003",
        "customer_id": "C-1001",
        "status": "Processing",
        "placed_on": "2024-02-10",
        "total": 249.99,
        "items": [
            {"sku": "SKU-020", "name": "Mechanical Keyboard", "quantity": 1, "price": 149.99},
            {"sku": "SKU-021", "name": "Gaming Mouse Pad", "quantity": 1, "price": 25.00},
            {"sku": "SKU-022", "name": "Monitor Arm", "quantity": 1, "price": 75.00}
        ],
        "shipping_address": "123 Main St, Springfield, IL 62701"
    }
}


def get_orders_for_customer(customer_id: str) -> list:
    """
    Retrieve all orders for a given customer.

    Returns a list of order dicts. In a real system this would hit a database
    and return hundreds of rows with dozens of columns each — exactly the
    bloat that Demo 2's optimizer is built to handle.
    """
    return [order for order in ORDERS.values() if order["customer_id"] == customer_id]


def get_open_orders_for_customer(customer_id: str) -> list:
    """
    Retrieve only open orders (not Delivered) for a customer.

    Used in Demo 3 to set up an ambiguous scenario: two open orders means
    "cancel my order" requires clarification.
    """
    all_orders = get_orders_for_customer(customer_id)
    return [o for o in all_orders if o["status"] != "Delivered"]


def get_customer(customer_id: str) -> dict:
    """Get customer details by ID."""
    return CUSTOMERS.get(customer_id, {})
