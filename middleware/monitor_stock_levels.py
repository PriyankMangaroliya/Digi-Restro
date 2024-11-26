from datetime import datetime
from bson import ObjectId
from flask import jsonify

from config import mongo
from email_utils import send_email


# Function to monitor stock levels
def monitor_stock_levels():
    from app import mongo, app
    print("Scheduler started.")

    # Fetch all products from the products collection
    products = mongo.db.products.find({})

    for product in products:
        # Fetch the latest stock entry for this product
        stock_record = mongo.db.stock.find_one(
            {'sku': product['sku']}, sort=[('date', -1)]
        )

        if not stock_record:
            # If there's no stock record, continue to the next product
            continue

        current_stock_qty = stock_record['total_qty']
        min_stock_threshold = product.get('min', 10)  # Fetch min threshold or default to 10
        notification_sent = product.get('notification_sent', False)  # Check if notification has already been sent

        # Check if current stock is below the threshold
        if current_stock_qty < min_stock_threshold:
            if not notification_sent:
                # Send notification only if it hasn't been sent already
                send_notification(product, current_stock_qty, min_stock_threshold)
                # Update the product to mark that the notification has been sent
                mongo.db.products.update_one(
                    {'_id': ObjectId(product['_id'])},
                    {'$set': {'notification_sent': True}}
                )
                print(f"Low stock notification sent for {product['product_name']} (SKU: {product['sku']}) (stock : {current_stock_qty}")
            else:
                print(f"Notification already sent for {product['product_name']} (SKU: {product['sku']})")
        else:
            # If stock is replenished, reset the notification_sent field
            if notification_sent:
                mongo.db.products.update_one(
                    {'_id': ObjectId(product['_id'])},
                    {'$set': {'notification_sent': False}}
                )
                print(f"Stock replenished for {product['product_name']} (SKU: {product['sku']}), notification flag reset.")
            else:
                print(f"Stock is sufficient for {product['product_name']} (SKU: {product['sku']})")
    print("Scheduler stopped.")

# Function to send the notification email
def send_notification(product, current_stock_qty, min_stock_threshold):
    from app import app

    subject = f"Low Stock Alert: {product['product_name']} (SKU: {product['sku']})"
    body = f"""
    Alert! The stock of {product['product_name']} (SKU: {product['sku']}) has dropped below the minimum threshold of {min_stock_threshold} units.

    Current Stock: {current_stock_qty}
    Minimum Stock Threshold: {min_stock_threshold}

    Please replenish the stock immediately.

    Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """
    try:
        with app.app_context():
            if send_email(subject, "shubhamlathiya2004@gmail.com", body):
                print(f"Low stock notification sent for {product['product_name']} (SKU: {product['sku']})")
                return jsonify({"message": "Notification sent successfully!"}), 200
            else:
                return jsonify({"error": "Failed to send email."}), 500
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
