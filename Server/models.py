from config import db, SerializerMixin, hybrid_property, bcrypt, datetime


class User(db.Model, SerializerMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120), unique=True)
    _password_hash = db.Column(db.String(), unique=True)


    @hybrid_property
    def password_hash(self):
        raise AttributeError('Cannot view password')

    @password_hash.setter
    def password_hash(self, password):
        hashed_password = bcrypt.generate_password_hash(password.encode('utf-8'))
        self._password_hash = hashed_password.decode('utf-8')
        
    def authenticate(self, password):
        return bcrypt.check_password_hash(self._password_hash, password.encode('utf-8'))

    #Relationships
    products = db.relationship('Product', back_populates="user", lazy='dynamic')
    orders = db.relationship('Order', back_populates="user", lazy='dynamic')
    reviews = db.relationship('Review', back_populates="user", lazy='dynamic')
    addresses = db.relationship('Address', back_populates='user', lazy=True)
    notifications = db.relationship('Notification', back_populates='user', lazy=True)
    cart = db.relationship('Cart', back_populates='user', lazy=True)

    #Serialization
    serialize_rules = ("-products.user", '-orders.user', '-reviews.user', '-addresses.user', '-notifications.user')
    

    def __repr__(self):
        return f'<User {self.username}, {self.email} of role {self._password_hash}>'



class TokenBlocklist(db.Model, SerializerMixin):
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String, nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False)


class Product(db.Model, SerializerMixin):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), unique=True)
    price = db.Column(db.Integer)
    description = db.Column(db.String())
    quantity = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    image_url = db.Column(db.String())

    # Relationships
    user = db.relationship('User', back_populates='products', lazy=True)
    orders = db.relationship('Order', back_populates='product', lazy=True)
    order_items = db.relationship('OrderItem', back_populates='product', lazy=True)
    category = db.relationship('ProductCategory', back_populates='products', lazy=True)
    reviews = db.relationship('Review', back_populates='product', lazy=True)
    # images = db.relationship('ProductImage', back_populates='product', lazy=True)

    # Serialization
    serialize_rules = ("-user.product", "-orders.product", "-order_items.product", "-category.product", "-reviews.product", "-images.product")

    def __repr__(self):
        return f'<Product {self.name}, {self.price} of category {self.category}>'


class Cart(db.Model, SerializerMixin):
    __tablename__ = "carts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    #Relationships
    user = db.relationship("User", back_populates="cart")
    cart_items = db.relationship("CartItem", back_populates="cart")

    #Serialization
    serialize_rules = ('-user.cart', '-cart_items.cart')

    def __repr__(self):
        return f'<Cart {self.id}>'

class CartItem(db.Model, SerializerMixin):
    __tablename__ = "cart_items"

    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('carts.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    quantity = db.Column(db.Integer, nullable=False)

    product = db.relationship("Product")
    cart = db.relationship("Cart", back_populates="cart_items")

    serialize_rules = ('-cart.cart_items', '-product')

    def __repr__(self):
        return f'<CartItem {self.id}>'

class Order(db.Model, SerializerMixin):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    quantity = db.Column(db.Integer)
    price = db.Column(db.Integer)
    status = db.Column(db.String(), nullable=False, default='pending')

    #Relationships
    user = db.relationship('User', back_populates='orders', lazy=True)
    product = db.relationship('Product', back_populates='orders', lazy=True)
    order_items = db.relationship('OrderItem', back_populates='order', lazy=True)

    #Serialization
    serialize_rules = ("-user", "-product", "-order_items")

    def __repr__(self):
        return f'<Order {self.id}, {self.user_id} of product {self.product_id } >'


class OrderItem(db.Model, SerializerMixin):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    quantity = db.Column(db.Integer)
    price = db.Column(db.Integer)
    status = db.Column(db.String(), nullable=False, default='pending')

    #Relationships
    order = db.relationship('Order', back_populates='order_items', lazy=True)
    product = db.relationship('Product', back_populates='order_items', lazy=True)

    #Serialization
    serialize_rules = ("-order.order_item", "-product.order_item")

    def __repr__(self):
        return f'<OrderItem {self.id}, {self.order_id} of product {self.product_id}>'


class ProductCategory(db.Model, SerializerMixin):
    __tablename__ = 'product_categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False, unique=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))

    #Relationships
    products = db.relationship('Product', back_populates='category', lazy=True)

    #Serialization
    serialize_rules = ("-products.product_category")

    def __repr__(self):
        return f'<ProductCategory {self.id}, {self.name}>'


class Review(db.Model, SerializerMixin):
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    rating = db.Column(db.Integer, nullable=False)
    review = db.Column(db.String(), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(), nullable=False, default='pending')

    #Relationships
    user = db.relationship('User', back_populates='reviews', lazy=True)
    product = db.relationship('Product', back_populates='reviews', lazy=True)

    #Serialization
    serialize_rules = ("-user.reviews", "-product.reviews")

    def __repr__(self):
        return f'<Review {self.id}, {self.user_id} of product {self.product_id}>'


class Address(db.Model, SerializerMixin):
    __tablename__ = 'addresses'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    address = db.Column(db.String(), nullable=False)
    city = db.Column(db.String(), nullable=False)
    state = db.Column(db.String(), nullable=False)
    zip_code = db.Column(db.String(), nullable=False)
    country = db.Column(db.String(), nullable=False)
    phone = db.Column(db.String(), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(), nullable=False, default='pending')

    #Relationships
    user = db.relationship('User', back_populates='addresses', lazy=True)

    #Serialization
    serialize_rules = ("-user.addresses")

    def __repr__(self):
        return f'<Address {self.id}, {self.user_id}>'


class Notification(db.Model, SerializerMixin):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    title = db.Column(db.String(), nullable=False)
    content = db.Column(db.String(), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(), nullable=False, default='pending')
    type = db.Column(db.String(), nullable=False)
    read = db.Column(db.Boolean, nullable=False, default=False)

    # Relationships
    user = db.relationship('User', back_populates='notifications', lazy=True)

    # Serialization
    serialize_rules = ("-user.notifications",)

    def __repr__(self):
        return f'<Notification {self.id}, {self.user_id}>'
