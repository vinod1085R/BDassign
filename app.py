from datetime import date

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError


db = SQLAlchemy()


@event.listens_for(Engine, "connect")
def enable_sqlite_foreign_keys(connection, _record):
    if connection.__class__.__module__ == "sqlite3":
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


class Store(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    place = db.Column(db.String(20), nullable=False)


class Staff(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    store_id = db.Column(
        db.Integer, db.ForeignKey("store.id"), nullable=False, unique=True
    )


class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(20), nullable=False)
    store_id = db.Column(db.Integer, db.ForeignKey("store.id"), nullable=False)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(20), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    color = db.Column(db.String(20), nullable=False)
    store_id = db.Column(db.Integer, db.ForeignKey("store.id"), nullable=False)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_date = db.Column(db.Date, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("customer.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)


class Delivery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customer.id"), nullable=False)
    payments = db.Column(db.String(20), nullable=False)


RESOURCES = {
    "stores": {
        "model": Store,
        "fields": {"name": "text", "phone": "phone", "place": "text"},
    },
    "staff": {
        "model": Staff,
        "fields": {
            "name": "text",
            "gender": "text",
            "age": "int",
            "store_id": "int",
        },
    },
    "customers": {
        "model": Customer,
        "fields": {
            "name": "text",
            "phone": "phone",
            "address": "text",
            "store_id": "int",
        },
    },
    "products": {
        "model": Product,
        "fields": {
            "type": "text",
            "name": "text",
            "price": "int",
            "color": "text",
            "store_id": "int",
        },
    },
    "orders": {
        "model": Order,
        "fields": {
            "order_date": "date",
            "customer_id": "int",
            "product_id": "int",
        },
    },
    "deliveries": {
        "model": Delivery,
        "fields": {"customer_id": "int", "payments": "text"},
    },
}


def serialize(record):
    result = {
        column.name: getattr(record, column.name)
        for column in record.__table__.columns
    }

    for key, value in result.items():
        if isinstance(value, date):
            result[key] = value.isoformat()

    return result


def parse_payload(fields):
    if not request.is_json:
        return None, (jsonify(error="Content-Type must be application/json"), 415)

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return None, (jsonify(error="Request body must be a JSON object"), 400)

    unknown = sorted(set(payload) - set(fields))
    if unknown:
        return None, (jsonify(error="Unknown field(s)", fields=unknown), 400)

    missing = sorted(set(fields) - set(payload))
    if missing:
        return None, (jsonify(error="Missing required field(s)", fields=missing), 400)

    cleaned = {}

    for key, value in payload.items():
        kind = fields[key]

        if kind == "text":
            if not isinstance(value, str) or not value.strip():
                return None, (jsonify(error=f"'{key}' must be a non-empty string"), 400)
            if len(value.strip()) > 20:
                return None, (jsonify(error=f"'{key}' must be 20 characters or fewer"), 400)
            cleaned[key] = value.strip()

        elif kind == "phone":
            if not isinstance(value, (str, int)) or isinstance(value, bool):
                return None, (jsonify(error=f"'{key}' must be a phone number string"), 400)
            phone = str(value).strip()
            if not phone or len(phone) > 20:
                return None, (jsonify(error=f"'{key}' must contain 1 to 20 characters"), 400)
            cleaned[key] = phone

        elif kind == "int":
            if not isinstance(value, int) or isinstance(value, bool):
                return None, (jsonify(error=f"'{key}' must be an integer"), 400)
            if key in ("age", "price") and value < 0:
                return None, (jsonify(error=f"'{key}' cannot be negative"), 400)
            if key.endswith("_id") and value < 1:
                return None, (jsonify(error=f"'{key}' must be a positive integer"), 400)
            cleaned[key] = value

        elif kind == "date":
            if not isinstance(value, str):
                return None, (jsonify(error=f"'{key}' must use YYYY-MM-DD format"), 400)
            try:
                cleaned[key] = date.fromisoformat(value)
            except ValueError:
                return None, (jsonify(error=f"'{key}' must use YYYY-MM-DD format"), 400)

    return cleaned, None


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///sunshine_gifts.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    @app.get("/")
    def index():
        return jsonify(message="Sunshine Gifts Store API", base_url="/api")

    @app.get("/api")
    def api_index():
        return jsonify(resources=[f"/api/{name}" for name in RESOURCES])

    for resource_name, config in RESOURCES.items():
        model = config["model"]
        fields = config["fields"]
        label = {
            "stores": "Store",
            "staff": "Staff",
            "customers": "Customer",
            "products": "Product",
            "orders": "Order",
            "deliveries": "Delivery",
        }[resource_name]
        collection_url = f"/api/{resource_name}"

        def list_records(model=model):
            records = db.session.execute(
                db.select(model).order_by(model.id)
            ).scalars()
            return jsonify([serialize(record) for record in records])

        def create_record(model=model, fields=fields):
            values, error = parse_payload(fields)
            if error:
                return error

            record = model(**values)
            db.session.add(record)

            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                return jsonify(error="A related record does not exist, or a unique value is duplicated"), 409

            return jsonify(serialize(record)), 201

        def read_record(record_id, model=model, label=label):
            record = db.session.get(model, record_id)
            if record is None:
                return jsonify(error=f"{label} not found"), 404
            return jsonify(serialize(record))

        def update_record(record_id, model=model, fields=fields, label=label):
            record = db.session.get(model, record_id)
            if record is None:
                return jsonify(error=f"{label} not found"), 404

            values, error = parse_payload(fields)
            if error:
                return error

            for key, value in values.items():
                setattr(record, key, value)

            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                return jsonify(error="A related record does not exist, or a unique value is duplicated"), 409

            return jsonify(serialize(record))

        def delete_record(record_id, model=model, label=label):
            record = db.session.get(model, record_id)
            if record is None:
                return jsonify(error=f"{label} not found"), 404

            db.session.delete(record)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                return jsonify(error="Cannot delete this record while other records refer to it"), 409

            return "", 204

        app.add_url_rule(
            collection_url, f"list_{resource_name}", list_records, methods=["GET"]
        )
        app.add_url_rule(
            collection_url, f"create_{resource_name}", create_record, methods=["POST"]
        )
        app.add_url_rule(
            f"{collection_url}/<int:record_id>",
            f"read_{resource_name}",
            read_record,
            methods=["GET"],
        )
        app.add_url_rule(
            f"{collection_url}/<int:record_id>",
            f"update_{resource_name}",
            update_record,
            methods=["PUT"],
        )
        app.add_url_rule(
            f"{collection_url}/<int:record_id>",
            f"delete_{resource_name}",
            delete_record,
            methods=["DELETE"],
        )

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify(error="Route not found"), 404

    @app.errorhandler(405)
    def method_not_allowed(_error):
        return jsonify(error="Method not allowed for this route"), 405

    with app.app_context():
        db.create_all()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)