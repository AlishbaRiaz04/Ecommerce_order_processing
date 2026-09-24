import json
from dataclasses import dataclass, asdict


# =========================
# JSON DATA VALIDATION
# =========================

def validate_data(data):

    if not isinstance(data, dict):
        raise ValueError("Data must be a dictionary")

    if not isinstance(data.get("orders"), list):
        raise ValueError("Orders must be a list")

    if not isinstance(data.get("products"), dict):
        raise ValueError("Products must be a dictionary")


# =========================
# DATA MODELS
# =========================

@dataclass
class Product:
    id: str
    name: str
    price: float
    category: str
    stock: int



@dataclass
class OrderItem:
    product_id: str
    quantity: int


@dataclass
class Order:
    order_id: str
    customer: str
    items: list[OrderItem]
    payment_status: str


# =========================
# ORDER VALIDATION
# =========================

def validate_order(order, products):

    if not order.items:
        return False, "Order has no items"

    payment_status = order.payment_status

    if payment_status not in {"paid", "pending"}:
        return False, "Invalid payment status"

    if not products:
        return False, "Product catalog is empty"

    for item in order.items:

        product_id = item.product_id
        quantity = item.quantity

        product = products.get(product_id)

        if product is None:
            return False, f"Unknown product ID: {product_id}"

        if quantity is None or quantity <= 0:
            return False, "Quantity must be positive"

        if quantity > product.stock:
            return False, f"Insufficient stock for {product_id}"

    return True, "Valid order"


# =========================
# CALCULATIONS
# =========================

def calculate_order_subtotal(order, products):

    subtotal = 0

    for item in order.items:

        product_id = item.product_id
        quantity = item.quantity
        price = products[product_id].price

        subtotal += price * quantity

    return subtotal


def calculate_discount(subtotal):

    if subtotal >= 1000:
        return subtotal * 0.15

    elif subtotal >= 500:
        return subtotal * 0.10

    elif subtotal >= 200:
        return subtotal * 0.05

    return 0


def calculate_shipping(subtotal):

    if subtotal >= 500:
        return 0

    return 20


def calculate_total(*amounts):

    return sum(amounts)


# =========================
# ORDER PROCESSING
# =========================

def process_order(order, products, **options):

    include_shipping = options.get("include_shipping", True)
    apply_discount = options.get("apply_discount", True)

    is_valid, reason = validate_order(order, products)

    if not is_valid:

        return {
            "order_id": order.order_id,
            "customer": order.customer,
            "payment_status": order.payment_status,
            "processing_status": "rejected",
            "items": order.items,
            "reason": reason
        }

    subtotal = calculate_order_subtotal(order, products)

    if apply_discount:
        discount_amount = calculate_discount(subtotal)
    else:
        discount_amount = 0

    if include_shipping:
        shipping_fee = calculate_shipping(subtotal)
    else:
        shipping_fee = 0

    grand_total = calculate_total(
        subtotal,
        shipping_fee,
        -discount_amount
    )

    if order.payment_status == "paid":

        for item in order.items:

            product_id = item.product_id
            quantity = item.quantity

            products[product_id].stock -= quantity

        processing_status = "completed"

    else:
        processing_status = "pending"

    return {
        "order_id": order.order_id,
        "customer": order.customer,
        "payment_status": order.payment_status,
        "processing_status": processing_status,
        "items": order.items,
        "subtotal": subtotal,
        "discount_amount": discount_amount,
        "shipping_fee": shipping_fee,
        "grand_total": grand_total
    }


def process_all_orders(orders, products, **options):

    processed_orders = []

    for order in orders:

        result = process_order(
            order,
            products,
            **options
        )

        processed_orders.append(result)

    return processed_orders


# =========================
# CUSTOMER REPORT
# =========================

def generate_customer_report(processed_orders):

    unique_customers = {
        order["customer"]
        for order in processed_orders
    }

    customer_orders = {
        customer: sum(
            1
            for order in processed_orders
            if order["customer"] == customer
        )
        for customer in unique_customers
    }

    if not customer_orders:
        return None, 0, unique_customers

    sorted_customers = sorted(
        customer_orders.items(),
        key=lambda item: item[1],
        reverse=True
    )

    top_customer, highest_orders = sorted_customers[0]

    return top_customer, highest_orders, unique_customers


# =========================
# PRODUCT REPORT
# =========================

def generate_product_report(
    processed_orders,
    products,
    low_stock_threshold=20
):

    units_sold = {}

    for order in processed_orders:

        if order["processing_status"] != "completed":
            continue

        for item in order["items"]:

            product_id = item.product_id
            quantity = item.quantity

            units_sold[product_id] = (
                units_sold.get(product_id, 0) + quantity
            )

    if units_sold:

        highest_units = max(units_sold.values())

        top_selling = [
            product_id
            for product_id, units in units_sold.items()
            if units == highest_units
        ]

        top_selling.sort(
            key=lambda product_id: product_id
        )

    else:
        highest_units = 0
        top_selling = []

    low_stock = [
        (product_id, product.stock)
        for product_id, product in products.items()
        if product.stock < low_stock_threshold
    ]

    categories = {
        product.category
        for product in products.values()
    }

    return (
        top_selling,
        highest_units,
        low_stock,
        categories
    )


# =========================
# SALES REPORT
# =========================

def generate_sales_report(
    processed_orders,
    products,
    top_customer,
    highest_orders,
    top_selling,
    highest_units,
    low_stock
):

    total_orders = len(processed_orders)

    paid_orders = sum(
        1
        for order in processed_orders
        if order["processing_status"] == "completed"
    )

    pending_orders = sum(
        1
        for order in processed_orders
        if order["processing_status"] == "pending"
    )

    rejected_orders = sum(
        1
        for order in processed_orders
        if order["processing_status"] == "rejected"
    )

    paid_results = [
        order
        for order in processed_orders
        if order["processing_status"] == "completed"
    ]

    total_revenue = sum(
        order["grand_total"]
        for order in paid_results
    )

    total_discount = sum(
        order["discount_amount"]
        for order in paid_results
    )

    shipping_collected = sum(
        order["shipping_fee"]
        for order in paid_results
    )

    print("\n========== SALES REPORT ==========")

    print(f"\nTotal Orders: {total_orders}")
    print(f"Paid Orders: {paid_orders}")
    print(f"Pending Orders: {pending_orders}")
    print(f"Rejected Orders: {rejected_orders}")

    print(f"\nTotal Revenue: ${total_revenue:.2f}")
    print(f"Total Discount: ${total_discount:.2f}")
    print(f"Total Shipping: ${shipping_collected:.2f}")

    print(f"\nTop Customer: {top_customer}")

    if top_selling:

        if len(top_selling) == 1:

            product_id = top_selling[0]
            product_name = products[product_id].name

            print(
                f"Top Selling Product: "
                f"{product_id} - {product_name} "
                f"({highest_units} units)"
            )

        else:

            print("Top Selling Product:")

            for product_id in top_selling:

                product_name = products[product_id].name

                print(
                    f"- {product_id} - "
                    f"{product_name}: "
                    f"{highest_units} units"
                )

    else:
        print("Top Selling Product: None")

    print("\nLow Stock Products:")

    if low_stock:

        for product_id, stock in low_stock:

            product_name = products[product_id].name

            print(
                f"- {product_id} - "
                f"{product_name}: "
                f"{stock} units"
            )

    else:
        print("- None")

    print("\n==================================")


# =========================
# MAIN PROGRAM
# =========================

def main():

    # Load and validate JSON data
    try:

        with open("data.json", "r") as file:
            data = json.load(file)

        validate_data(data)

    except FileNotFoundError:

        print("Error: data.json file not found.")
        return

    except json.JSONDecodeError:

        print("Error: Invalid JSON format in data.json.")
        return

    except ValueError as e:

        print(f"Error: {e}")
        return

    products = data["products"]
    orders = data["orders"]

    # Convert products to dataclass objects
    product_objects = {}

    for product_id, product_data in products.items():

        product = Product(
            product_id,
            product_data["name"],
            product_data["price"],
            product_data["category"],
            product_data["stock"]
        )

        product_objects[product_id] = product

    # Convert orders to dataclass objects
    order_objects = []

    for order_data in orders:

        item_objects = []

        for item_data in order_data["items"]:

            item = OrderItem(
                item_data["product_id"],
                item_data["quantity"]
            )

            item_objects.append(item)

        order = Order(
            order_data["order_id"],
            order_data["customer"],
            item_objects,
            order_data["payment_status"]
        )

        order_objects.append(order)

    # Process orders
    processed_orders = process_all_orders(
        order_objects,
        product_objects,
        include_shipping=True,
        apply_discount=True
    )

    # Generate reports
    top_customer, highest_orders, unique_customers = (
        generate_customer_report(processed_orders)
    )

    top_selling, highest_units, low_stock, categories = (
        generate_product_report(
            processed_orders,
            product_objects
        )
    )

    generate_sales_report(
        processed_orders,
        product_objects,
        top_customer,
        highest_orders,
        top_selling,
        highest_units,
        low_stock
    )

    # Convert dataclass objects to JSON-compatible dictionaries
    for order in processed_orders:

        order["items"] = [
            asdict(item)
            for item in order["items"]
        ]

    # Save processed orders
    try:

        with open("processed_data.json", "w") as file:
            json.dump(
                processed_orders,
                file,
                indent=4
            )

        print("\nProcessed orders saved to processed_data.json.")

    except OSError as e:

        print(f"Error saving processed data: {e}")


if __name__ == "__main__":
    main()