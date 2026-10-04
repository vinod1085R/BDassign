from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)

# SUNSHINE GIFTS STORE
# PRODUCTS TABLE

# SQLite database
DATABASE = os.path.join(os.path.dirname(__file__), "sunshine.db")


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# CREATE - Add Product
@app.route('/products', methods=['POST'])
def add_product():
    data = request.get_json()

    p_type = data['p_type']
    p_name = data['p_name']
    price = data['price']
    p_color = data['p_color']

    conn = get_db_connection()

    conn.execute(
        "INSERT INTO products (p_type, p_name, price, p_color) VALUES (?, ?, ?, ?)",
        (p_type, p_name, price, p_color)
    )

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Product added successfully"
    }), 201


# READ - Get All Products
@app.route('/products', methods=['GET'])
def get_products():
    conn = get_db_connection()

    products = conn.execute(
        "SELECT * FROM products"
    ).fetchall()

    conn.close()

    result = []

    for product in products:
        result.append({
            "p_id": product["p_id"],
            "p_type": product["p_type"],
            "p_name": product["p_name"],
            "price": product["price"],
            "p_color": product["p_color"]
        })

    return jsonify(result), 200


# UPDATE - Update Product
@app.route('/products/<int:p_id>', methods=['PUT'])
def update_product(p_id):
    data = request.get_json()

    p_type = data['p_type']
    p_name = data['p_name']
    price = data['price']
    p_color = data['p_color']

    conn = get_db_connection()

    conn.execute(
        """UPDATE products
           SET p_type = ?, p_name = ?, price = ?, p_color = ?
           WHERE p_id = ?""",
        (p_type, p_name, price, p_color, p_id)
    )

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Product updated successfully"
    }), 200


# DELETE - Delete Product
@app.route('/products/<int:p_id>', methods=['DELETE'])
def delete_product(p_id):
    conn = get_db_connection()

    conn.execute(
        "DELETE FROM products WHERE p_id = ?",
        (p_id,)
    )

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Product deleted successfully"
    }), 200


if __name__ == '__main__':
    app.run(debug=True)