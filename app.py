from flask import jsonify, request, Flask, make_response
from flask.views import MethodView
import jwt
from datetime import datetime, timedelta
from model import db, UserProduct, app, migrate, token_required, UserData
from  werkzeug.security import generate_password_hash, check_password_hash
import uuid # for public id


def create_app():
    app = Flask(__name__)
    db.init_app(app)
    migrate.init_app(app, db)
    return app


class SignUp(MethodView):
    def post(self):
        # creates a dictionary of the form data
        data = request.json

        # gets name, email and password
        name, email = data.get('name'), data.get('email')
        password = data.get('password')
        # checking for existing user
        user = UserData.query \
            .filter_by(email=email) \
            .first()
        if not user:
            # database ORM object
            user = UserData(
                public_id=str(uuid.uuid4()),
                name=name,
                email=email,
                password=generate_password_hash(password)
            )
            # insert user
            db.session.add(user)
            db.session.commit()

            return make_response('Successfully registered.', 201)
        else:
            # returns 202 if user already exists
            return make_response('User already exists. Please Log in.', 202)


class LogIn(MethodView):
    def post(self):
        # creates dictionary of form data
        auth = request.json

        if not auth or not auth.get('email') or not auth.get('password'):
            # returns 401 if any email or / and password is missing
            return make_response(
                'Could not verify',
                401,
                {'WWW-Authenticate': 'Basic realm ="Login required !!"'}
            )

        user = UserData.query \
            .filter_by(email=auth.get('email')) \
            .first()

        if not user:
            # returns 401 if user does not exist
            return make_response(
                'Could not verify',
                401,
                {'WWW-Authenticate': 'Basic realm ="User does not exist !!"'}
            )

        if check_password_hash(user.password, auth.get('password')):
            # generates the JWT Token
            token = jwt.encode({
                'public_id': user.public_id,
                'exp': datetime.utcnow() + timedelta(minutes=30)
            }, app.config['SECRET_KEY'])

            return make_response(jsonify({'token': token.decode('UTF-8')}), 201)
        # returns 403 if password is wrong
        return make_response(
            'Could not verify',
            403,
            {'WWW-Authenticate': 'Basic realm ="Wrong Password !!"'}
        )


class AddProduct(MethodView):
    @token_required
    def post(self):
        auth_header = request.environ.get('HTTP_AUTHORIZATION')
        token = None
        if auth_header:
            key, token = auth_header.split(' ')
        data = jwt.decode(token, app.config['SECRET_KEY'])
        user_data = UserData.query.filter_by(public_id=data['public_id']).first()

        product_data = request.json
        product_name = product_data['product_name']
        type = product_data['type']
        price = product_data['price']
        description = product_data['description']
        is_product = UserProduct.query \
            .filter_by(product_name=product_name) \
            .first()
        if not is_product:
            product = UserProduct(product_name=product_name, type=type, price=price, description=description,
                                  user=user_data.id)
            db.session.add(product)
            db.session.commit()
            return jsonify({"success": True, "response": "Product added Successfully"})
        else:
            return make_response('Product name already exists. Please try another name.', 202)


class UpdateProduct(MethodView):
    @token_required
    def patch(self):
        product_id = request.json["product_id"]
        product = UserProduct.query.get(product_id)
        product_name = request.json['product_name']
        description = request.json['description']
        price = request.json['price']
        type = request.json['type']

        product.product_name = product_name
        product.description = description
        product.price = price
        product.type = type
        db.session.add(product)
        db.session.commit()
        return jsonify({"success": True, "response": "Product Details updated Successfully"})


class GetProducts(MethodView):
    @token_required
    def get(self):
        all_products = []
        products = UserProduct.query.all()
        for product in products:
            results = {
              "product_id": product.id,
              "product_name": product.product_name,
              "product_description": product.description,
              "product_type": product.type,
              "product_price": product.price, }
            all_products.append(results)

        return jsonify(
          {
            "success": True,
            "products": all_products,
            "product_counts": len(products),
          }
        )


class DeleteProduct(MethodView):
    @token_required
    def delete(self):
        product_id = request.json['product_id']
        product = UserProduct.query.get(product_id)
        db.session.delete(product)
        db.session.commit()

        return jsonify({"success": True, "response": "Product deleted Successfully"})


app.add_url_rule('/signup', view_func=SignUp.as_view('signup'))
app.add_url_rule('/login', view_func=LogIn.as_view('login'))
app.add_url_rule('/get-products', view_func=GetProducts.as_view('get'))
app.add_url_rule('/add-product', view_func=AddProduct.as_view('add'))
app.add_url_rule('/update-product', view_func=UpdateProduct.as_view('update'))
app.add_url_rule('/delete-product', view_func=DeleteProduct.as_view('delete'))

if __name__ == '__main__':
  app.run(debug=True)
