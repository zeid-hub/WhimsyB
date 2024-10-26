from config import app, db, current_user, get_jwt, set_access_cookies, create_access_token, jwt_required, jwt, datetime, timedelta, timezone, request, make_response, jsonify, Resource, api, get_jwt_identity
from models import User, TokenBlocklist, Product, ProductCategory, Order, OrderItem, Review, Address, Notification, Cart, CartItem


@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    return User.query.filter_by(username=identity).one_or_none()

@app.after_request
def refresh_expiring_jwts(response):
    try:
        exp_timestamp = get_jwt()["exp"]
        now = datetime.now(timezone.utc)
        target_timestamp = datetime.timestamp(now + timedelta(minutes=30))
        if target_timestamp > exp_timestamp:
            access_token = create_access_token(identity=get_jwt_identity())
            set_access_cookies(response, access_token)
        return response
    except (RuntimeError, KeyError):
        return response

@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload: dict) -> bool:
    jti = jwt_payload["jti"]
    token = db.session.query(TokenBlocklist.id).filter_by(jti=jti).scalar()
    return token is not None

class Home (Resource):
    def get(self):
        response = (
            {
                "Message": "Welcome to my Home Page"
            }
        )
        return make_response(
            response,
            200
        )
api.add_resource(Home, "/")

class AddUser(Resource):
    def post(self):
        data = request.get_json()
        
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        if not username or not email or not password:
            return jsonify({"error": "Username, email and password are required."}), 400

        new_user = User(username=username, email=email)
        new_user.password_hash = password
        db.session.add(new_user)
        db.session.commit()
        
        return make_response({"message": "The user has been created successfully"}, 201)

api.add_resource(AddUser, "/adduser")


class GetAllUsers(Resource):
    def get(self):
        users = User.query.all()
        user_list = [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email
            }
            for user in users
        ]
        response = make_response(jsonify(user_list), 200)
        return response

api.add_resource(GetAllUsers, "/getallusers")

class LoginUser(Resource):
    def post(self):
        data = request.get_json()

        new_user = User.query.filter_by(email=data['email']).first()
        if not new_user:
            return jsonify({"error": "email is incorrect."}), 400

        if new_user.authenticate(data['password']):
            given_token = create_access_token(identity=new_user.username)
            return make_response(
                jsonify(
                    {"message": "The user has been logged in successfully", "token": given_token}
                    ),
                    200
            )
        else:
            return make_response(
                jsonify(
                    {"error": "You have entered the Incorrect password"}
                ),
                400
            )

api.add_resource(LoginUser, "/login")

class LogoutUser(Resource):
    @jwt_required
    def delete(self):
        jti = get_jwt()["jti"]
        now = datetime.now(timezone.utc)
        token = TokenBlocklist(jti=jti, created_at=now)
        db.session.add(token)
        db.session.commit()
        return make_response(
            jsonify(
                {"message": "Successfully logged out"}
            ),
            200
        )
api.add_resource(LogoutUser, "/logout")


# class Products(Resource):
#     def get(self):
#         products = Product.query.all()
#         result = []
#         for product in products:
#             result.append({
#                 'id': product.id,
#                 'name': product.name,
#                 'price': product.price,
#                 'description': product.description,
#                 'quantity': product.quantity
#             })
#         response = make_response(jsonify(result), 200)
#         return response

#     def post(self):
#         data = request.get_json()
#         if not data:
#             response = make_response(jsonify(message='No input data provided'), 400)
#             return response

#         new_product = Product(
#             name=data.get('name'),
#             price=data.get('price'),
#             description=data.get('description'),
#             quantity=data.get('quantity'),
#         )

#         db.session.add(new_product)
#         db.session.commit()

#         response = make_response(jsonify(message='Product created successfully'), 201)
#         return response



class Products(Resource):
    def get(self):
        products = Product.query.all()
        result = []
        for product in products:
            product_data = {
                'id': product.id,
                'name': product.name,
                'price': product.price,
                'description': product.description,
                'quantity': product.quantity,
                'image_url': product.image_url  # Include image_url here
            }
            result.append(product_data)

        response = make_response(jsonify(result), 200)
        return response

    def post(self):
        data = request.get_json()
        if not data:
            response = make_response(jsonify(message='No input data provided'), 400)
            return response

        new_product = Product(
            name=data.get('name'),
            price=data.get('price'),
            description=data.get('description'),
            quantity=data.get('quantity'),
            image_url=data.get('image_url')  # Add image_url field
        )

        db.session.add(new_product)
        db.session.commit()

        response = make_response(jsonify(message='Product created successfully'), 201)
        return response
        
api.add_resource(Products, '/products')




class ProductById(Resource):
    def get(self, product_id):
        product = Product.query.filter_by(id=product_id).first()
        if product:
            response = {
                "id": product.id,
                "name": product.name,
                "price": product.price,
                "description": product.description,
                "quantity": product.quantity
                }
            return make_response(jsonify(response), 200)
        else:
            response = {"message": "Product not found"}
            return make_response(jsonify(response), 404)

    def patch(self, product_id):
        product = Product.query.filter_by(id=product_id).first()
        if product:
            data = request.get_json()
            for key, value in data.items():
                setattr(product, key, value)
            db.session.commit()
            return make_response(jsonify(product.to_dict()), 200)
        else:
            return make_response(jsonify({"error": "Product not found"}), 404)

    def delete(self, product_id):
        product = Product.query.filter_by(id=product_id).first()
        if product:
            db.session.delete(product)
            db.session.commit()
            return make_response(jsonify({"message": "Product deleted"}), 200)
        else:
            return make_response(jsonify({"error": "Product not found"}), 404)

api.add_resource(ProductById, "/products/<int:product_id>")


class Orders(Resource):
    # @jwt_required()
    def get(self):
        orders = Order.query.all()
        order_list = [
            {
                "id": order.id,
                "user_id": order.user_id,
                "product_id": order.product_id,
                "quantity": order.quantity,
                "price": order.price,
                "status": order.status
            }
            for order in orders
        ]
        return make_response(jsonify(order_list), 200)

    # @jwt_required()
    def post(self):
        data = request.get_json()
        if not data:
            response = {"message": "No input data provided"}
            return make_response(jsonify(response), 400)

        user_id = get_jwt_identity()

        # Ensure both user_id and product_id are provided
        if 'product_id' not in data:
            response = {"message": "product_id is required"}
            return make_response(jsonify(response), 400)

        # Check if the product exists
        product = Product.query.get(data['product_id'])
        if not product:
            response = {"message": "Product does not exist"}
            return make_response(jsonify(response), 404)

        new_order = Order(
            user_id=user_id,  # Assigning user_id from JWT token
            product_id=data['product_id'],  # Assigning product_id from request data
            quantity=data.get('quantity'),
            price=data.get('price'),
            status=data.get('status', 'pending')
        )

        db.session.add(new_order)
        db.session.commit()

        response = {"message": "Order created successfully"}
        return make_response(jsonify(response), 201)

api.add_resource(Orders, '/orders')


class OrderById(Resource):
    # @jwt_required()
    def get(self, order_id):
        order = Order.query.get(order_id)
        if not order:
            return make_response(jsonify({"error": "Order not found"}), 404)
        
        order_data = {
            "id": order.id,
            "user_id": order.user_id,
            "product_id": order.product_id,
            "quantity": order.quantity,
            "price": order.price,
            "status": order.status
        }
        return make_response(jsonify(order_data), 200)

    # @jwt_required()
    def patch(self, order_id):
        order = Order.query.get(order_id)
        if not order:
            return make_response(jsonify({"error": "Order not found"}), 404)
        
        data = request.get_json()
        if not data:
            return make_response(jsonify({"error": "No input data provided"}), 400)
        
        if 'quantity' in data:
            order.quantity = data['quantity']
        if 'price' in data:
            order.price = data['price']
        if 'status' in data:
            order.status = data['status']
        
        db.session.commit()
        
        return make_response(jsonify({"message": "Order updated successfully"}), 200)

    # @jwt_required()
    def delete(self, order_id):
        order = Order.query.get(order_id)
        if not order:
            return make_response(jsonify({"error": "Order not found"}), 404)
        
        db.session.delete(order)
        db.session.commit()
        
        return make_response(jsonify({"message": "Order deleted successfully"}), 200)

api.add_resource(OrderById, '/orders/<int:order_id>')


class OrderItems(Resource):
    # @jwt_required()
    def get(self):
        order_items = OrderItem.query.all()
        order_item_list = [
            {
                "id": order_item.id,
                "order_id": order_item.order_id,
                "product_id": order_item.product_id,
                "quantity": order_item.quantity,
                "price": order_item.price,
                "status": order_item.status
            }
            for order_item in order_items
        ]
        return make_response(jsonify(order_item_list), 200)

    # @jwt_required()
    def post(self):
        data = request.get_json()
        if not data:
            response = {"message": "No input data provided"}
            return make_response(jsonify(response), 400)

        new_order_item = OrderItem(
            order_id=data.get('order_id'),
            product_id=data.get('product_id'),
            quantity=data.get('quantity'),
            price=data.get('price'),
            status=data.get('status', 'pending')
        )

        db.session.add(new_order_item)
        db.session.commit()

        response = {"message": "Order item created successfully"}
        return make_response(jsonify(response), 201)

api.add_resource(OrderItems , "/order-items")


# class ShoppingCart(Resource):
#     # @jwt_required()
#     def get(self):
#         current_user_id = get_jwt_identity()
#         print(f'current_user_id (GET): {current_user_id}')

#         user_cart = CartItem.query.filter_by(cart_id=current_user_id).all()

#         if user_cart:
#             serialized_cart_items = []
#             for cart_item in user_cart:
#                 product = Product.query.get(cart_item.product_id)
#                 serialized_cart_items.append({
#                     'id': cart_item.id,
#                     'product_id': cart_item.product_id,
#                     'quantity': cart_item.quantity,
#                     'name': product.name,
#                     'price': product.price,
#                     'image_url': product.image_url
#                 })

#             response = jsonify(serialized_cart_items)
#             response.status_code = 200
#             return response
#         else:
#             return {'message': 'Cart not found'}, 404

#     # @jwt_required()
#     def post(self):
#         current_user_id = get_jwt_identity()
#         print(f'current_user_id (POST): {current_user_id}')
#         data = request.json

#         try:
#             product_id = data.get('product_id')
#             quantity = data.get('quantity', 1)  # Default quantity to 1

#             if product_id:
#                 if not Product.query.filter_by(id=product_id).first():
#                     raise ValueError('Product with provided ID not found')
#             else:
#                 raise ValueError('A product_id must be provided')

#             new_cart_item = CartItem(
#                 cart_id=current_user_id,
#                 product_id=product_id,
#                 quantity=quantity
#             )

#             db.session.add(new_cart_item)
#             db.session.commit()

#             return {'message': 'Cart item added successfully'}, 201

#         except Exception as e:
#             db.session.rollback()
#             return {'error': str(e)}, 400

#     # @jwt_required()
#     def patch(self, item_id):
#         current_user_id = get_jwt_identity()
#         print(f'current_user_id (PATCH): {current_user_id}')
#         data = request.json

#         try:
#             updated_quantity = data.get('quantity')
#             cart_item = CartItem.query.filter_by(id=item_id, cart_id=current_user_id).first()

#             if cart_item:
#                 cart_item.quantity = updated_quantity
#                 db.session.commit()
#                 return {'message': 'Cart item updated successfully'}, 200
#             else:
#                 return {'error': 'Cart item not found'}, 404

#         except Exception as e:
#             db.session.rollback()
#             return {'error': str(e)}, 400

#     # @jwt_required()
#     def delete(self, item_id):
#         current_user_id = get_jwt_identity()
#         print(f'current_user_id (DELETE): {current_user_id}')

#         try:
#             cart_item = CartItem.query.filter_by(id=item_id, cart_id=current_user_id).first()

#             if cart_item:
#                 db.session.delete(cart_item)
#                 db.session.commit()
#                 return {'message': 'Cart item deleted successfully'}, 200
#             else:
#                 return {'error': 'Cart item not found'}, 404

#         except Exception as e:
#             db.session.rollback()
#             return {'error': str(e)}, 400

# api.add_resource(ShoppingCart, '/userCart', '/userCart/<int:item_id>')


class ShoppingCart(Resource):
    def get(self):
        current_user_id = 1  # Placeholder for the current user ID
        print(f'current_user_id (GET): {current_user_id}')

        user_cart = CartItem.query.filter_by(cart_id=current_user_id).all()

        if user_cart:
            serialized_cart_items = []
            for cart_item in user_cart:
                product = Product.query.get(cart_item.product_id)
                serialized_cart_items.append({
                    'id': cart_item.id,
                    'product_id': cart_item.product_id,
                    'quantity': cart_item.quantity,
                    'name': product.name,
                    'price': product.price,
                    'image_url': product.image_url
                })

            response = jsonify(serialized_cart_items)
            response.status_code = 200
            return response
        else:
            return {'message': 'Cart not found'}, 404

    def post(self):
        current_user_id = 1  # Placeholder for the current user ID
        print(f'current_user_id (POST): {current_user_id}')
        data = request.json

        try:
            product_id = data.get('product_id')
            quantity = data.get('quantity', 1)  # Default quantity to 1

            if product_id:
                if not Product.query.filter_by(id=product_id).first():
                    raise ValueError('Product with provided ID not found')
            else:
                raise ValueError('A product_id must be provided')

            new_cart_item = CartItem(
                cart_id=current_user_id,
                product_id=product_id,
                quantity=quantity
            )

            db.session.add(new_cart_item)
            db.session.commit()

            return {'message': 'Cart item added successfully'}, 201

        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 400

    def patch(self, item_id):
        current_user_id = 1  # Placeholder for the current user ID
        print(f'current_user_id (PATCH): {current_user_id}')
        data = request.json

        try:
            updated_quantity = data.get('quantity')
            cart_item = CartItem.query.filter_by(id=item_id, cart_id=current_user_id).first()

            if cart_item:
                cart_item.quantity = updated_quantity
                db.session.commit()
                return {'message': 'Cart item updated successfully'}, 200
            else:
                return {'error': 'Cart item not found'}, 404

        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 400

    def delete(self, item_id):
        current_user_id = 1  # Placeholder for the current user ID
        print(f'current_user_id (DELETE): {current_user_id}')

        try:
            cart_item = CartItem.query.filter_by(id=item_id, cart_id=current_user_id).first()

            if cart_item:
                db.session.delete(cart_item)
                db.session.commit()
                return {'message': 'Cart item deleted successfully'}, 200
            else:
                return {'error': 'Cart item not found'}, 404

        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 400

api.add_resource(ShoppingCart, '/userCart', '/userCart/<int:item_id>')


class ProductCategories(Resource):
    @jwt_required()
    def get(self):
        categories = ProductCategory.query.all()
        category_list = [
            {
                "id": category.id,
                "name": category.name,
                "product_id": category.product_id
            }
            for category in categories
        ]
        return make_response(jsonify(category_list), 200)

    @jwt_required()
    def post(self):
        data = request.get_json()
        if not data:
            response = {"message": "No input data provided"}
            return make_response(jsonify(response), 400)

        new_category = ProductCategory(
            name=data.get('name'),
            product_id=data.get('product_id')
        )

        db.session.add(new_category)
        db.session.commit()

        response = {"message": "Product category created successfully"}
        return make_response(jsonify(response), 201)

api.add_resource(ProductCategories , "/product-categories")



class Reviews(Resource):
    @jwt_required()
    def get(self):
        reviews = Review.query.all()
        review_list = [
            {
                "id": review.id,
                "user_id": review.user_id,
                "product_id": review.product_id,
                "rating": review.rating,
                "review": review.review,
                "date": review.date.isoformat(),
                "status": review.status
            }
            for review in reviews
        ]
        return make_response(jsonify(review_list), 200)

    @jwt_required()
    def post(self):
        data = request.get_json()
        if not data:
            response = {"message": "No input data provided"}
            return make_response(jsonify(response), 400)

        user_id = get_jwt_identity()  # Retrieving user ID from JWT token

        new_review = Review(
            user_id=user_id,
            product_id=data.get('product_id'),
            rating=data.get('rating'),
            review=data.get('review'),
            status=data.get('status', 'pending')
        )

        db.session.add(new_review)
        db.session.commit()

        response = {"message": "Review created successfully"}
        return make_response(jsonify(response), 201)

api.add_resource(Reviews, "/reviews")



class Addresses(Resource):
    # @jwt_required()
    def get(self):
        addresses = Address.query.all()
        address_list = [
            {
                "id": address.id,
                "user_id": address.user_id,
                "address": address.address,
                "city": address.city,
                "state": address.state,
                "zip_code": address.zip_code,
                "country": address.country,
                "phone": address.phone,
                "date": address.date.isoformat(),
                "status": address.status
            }
            for address in addresses
        ]
        return make_response(jsonify(address_list), 200)

    # @jwt_required()
    def post(self):
        data = request.get_json()
        if not data:
            response = {"message": "No input data provided"}
            return make_response(jsonify(response), 400)

        user_id = get_jwt_identity()

        new_address = Address(
            user_id=user_id,
            address=data.get('address'),
            city=data.get('city'),
            state=data.get('state'),
            zip_code=data.get('zip_code'),
            country=data.get('country'),
            phone=data.get('phone'),
            status=data.get('status', 'pending')
        )

        db.session.add(new_address)
        db.session.commit()

        response = {"message": "Address created successfully"}
        return make_response(jsonify(response), 201)

api.add_resource(Addresses, "/address")



class Notifications(Resource):
    @jwt_required()
    def get(self):
        notifications = Notification.query.all()
        notification_list = [
            {
                "id": notification.id,
                "user_id": notification.user_id,
                "title": notification.title,
                "content": notification.content,
                "created_at": notification.created_at.isoformat(),
                "status": notification.status,
                "type": notification.type,
                "read": notification.read
            }
            for notification in notifications
        ]
        return make_response(jsonify(notification_list), 200)

    @jwt_required()
    def post(self):
        data = request.get_json()
        if not data:
            response = {"message": "No input data provided"}
            return make_response(jsonify(response), 400)

        user_id = get_jwt_identity()  # Retrieving user ID from JWT token

        new_notification = Notification(
            user_id=user_id,
            title=data.get('title'),
            content=data.get('content'),
            status=data.get('status', 'pending'),
            type=data.get('type'),
            read=data.get('read', False)
        )

        db.session.add(new_notification)
        db.session.commit()

        response = {"message": "Notification created successfully"}
        return make_response(jsonify(response), 201)

api.add_resource(Notifications, "/notification")


if __name__ == '__main__':
    app.run(port=5555, debug=True)