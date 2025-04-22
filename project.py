from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy import UniqueConstraint
from datetime import datetime

app = Flask(__name__)
ma = Marshmallow(app)


app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:ILoveMoe@localhost/ecommerce_api'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)



class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200))
    email = db.Column(db.String(100), unique=True, nullable=False)

    orders = db.relationship('Order', backref='user', cascade='all, delete-orphan')

class Order(db.Model):
    __tablename__ = 'order'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    products = db.relationship('Product', secondary='order_product', backref='orders')


class Product(db.Model):
    __tablename__ = 'product'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)

class OrderProduct(db.Model):
    __tablename__ = 'order_product'
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), primary_key=True) 

class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        include_fk = True
        load_instance = True

class OrderSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Order
        include_fk = True
        load_instance = True

class ProductSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Product
        include_fk = True
        load_instance = True

user_schema = UserSchema()
users_schema = UserSchema(many=True)
product_schema = ProductSchema()
products_schema = ProductSchema(many=True)
order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)

@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return users_schema.jsonify(users)

@app.route('/users/<int:id>', methods=['GET'])
def get_user(id):
    user = User.query.get_or_404(id)
    return user_schema.jsonify(user)

@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    new_user = User(**data)
    db.session.add(new_user)
    db.session.commit()
    return user_schema.jsonify(new_user), 201

@app.route('/users/<int:id>', methods=['PUT'])
def update_user(id):
    user = User.query.get_or_404(id)
    data = request.get_json()
    for key, value in data.items():
        setattr(user, key, value)
    db.session.commit()
    return user_schema.jsonify(user)

@app.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    return '', 204

@app.route('/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    return products_schema.jsonify(products)

@app.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    product = Product.query.get_or_404(id)
    return product_schema.jsonify(product)

@app.route('/products', methods=['POST'])
def create_product():
    data = request.get_json()
    new_product = Product(**data)
    db.session.add(new_product)
    db.session.commit()
    return product_schema.jsonify(new_product), 201

@app.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    product = Product.query.get_or_404(id)
    data = request.get_json()
    for key, value in data.items():
        setattr(product, key, value)
    db.session.commit()
    return product_schema.jsonify(product)

@app.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    return '', 204

@app.route('/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    new_order = Order(**data)
    db.session.add(new_order)
    db.session.commit()
    return order_schema.jsonify(new_order), 201

@app.route('/orders/<int:order_id>/add_product/<int:product_id>', methods=['PUT'])
def add_product_to_order(order_id, product_id):
    existing = OrderProduct.query.filter_by(order_id=order_id, product_id=product_id).first()
    if existing:
        return jsonify({'error': 'Product already in order'}), 400
    assoc = OrderProduct(order_id=order_id, product_id=product_id)
    db.session.add(assoc)
    db.session.commit()
    return jsonify({'message': 'Product added to order'})

@app.route('/orders/<int:order_id>/remove_product/<int:product_id>', methods=['DELETE'])
def remove_product_from_order(order_id, product_id):
    assoc = OrderProduct.query.filter_by(order_id=order_id, product_id=product_id).first_or_404()
    db.session.delete(assoc)
    db.session.commit()
    return jsonify({'message': 'Product removed from order'})

@app.route('/orders/user/<int:user_id>', methods=['GET'])
def get_orders_by_user(user_id):
    orders = Order.query.filter_by(user_id=user_id).all()
    return orders_schema.jsonify(orders)

@app.route('/orders/<int:order_id>/products', methods=['GET'])
def get_products_by_order(order_id):
    product_ids = db.session.query(OrderProduct.product_id).filter_by(order_id=order_id).all()
    product_ids = [pid[0] for pid in product_ids]
    products = Product.query.filter(Product.id.in_(product_ids)).all()
    return products_schema.jsonify(products)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)