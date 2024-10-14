#!/usr/bin/env python3
from models import db, Restaurant, RestaurantPizza, Pizza
from flask_migrate import Migrate
from flask import Flask, request, jsonify, make_response
from flask_restful import Api, Resource
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

migrate = Migrate(app, db)
db.init_app(app)
api = Api(app)


@app.route("/")
def index():
    return "<h1>Code challenge</h1>"


class RestaurantList(Resource):
    def get(self):
        restaurants = Restaurant.query.all()
        return jsonify([restaurant.to_dict('id', 'name', 'address') for restaurant in restaurants])


class RestaurantDetail(Resource):
    def get(self, id):
        restaurant = Restaurant.query.get(id)
        if restaurant:
            restaurant_data = restaurant.to_dict('id', 'name', 'address')
            restaurant_data['restaurant_pizzas'] = [
                {
                    'id': rp.id,
                    'pizza': rp.pizza.to_dict('id', 'name', 'ingredients'),
                    'pizza_id': rp.pizza_id,
                    'price': rp.price,
                    'restaurant_id': rp.restaurant_id
                }
                for rp in restaurant.restaurant_pizzas
            ]
            return jsonify(restaurant_data)
        else:
            return make_response(jsonify({"error": "Restaurant not found"}), 404)

    def delete(self, id):
        restaurant = Restaurant.query.get(id)
        if restaurant:
            RestaurantPizza.query.filter_by(restaurant_id=id).delete()
            db.session.delete(restaurant)
            db.session.commit()
            return make_response('', 204)
        else:
            return make_response(jsonify({"error": "Restaurant not found"}), 404)


class PizzaList(Resource):
    def get(self):
        pizzas = Pizza.query.all()
        return jsonify([pizza.to_dict('id', 'name', 'ingredients') for pizza in pizzas])


class RestaurantPizzaCreate(Resource):
    def post(self):
        data = request.get_json()
        try:
            new_restaurant_pizza = RestaurantPizza(
                price=data['price'],
                pizza_id=data['pizza_id'],
                restaurant_id=data['restaurant_id']
            )
            db.session.add(new_restaurant_pizza)
            db.session.commit()
            
            pizza = new_restaurant_pizza.pizza.to_dict('id', 'name', 'ingredients')
            restaurant = new_restaurant_pizza.restaurant.to_dict('id', 'name', 'address')
            response_data = {
                'id': new_restaurant_pizza.id,
                'pizza': pizza,
                'pizza_id': new_restaurant_pizza.pizza_id,
                'price': new_restaurant_pizza.price,
                'restaurant': restaurant,
                'restaurant_id': new_restaurant_pizza.restaurant_id
            }
            return jsonify(response_data), 201

        except Exception as e:
            return make_response(jsonify({"errors": ["validation errors"]}), 400)


# Adding routes to the API
api.add_resource(RestaurantList, '/restaurants')
api.add_resource(RestaurantDetail, '/restaurants/<int:id>')
api.add_resource(PizzaList, '/pizzas')
api.add_resource(RestaurantPizzaCreate, '/restaurant_pizzas')


if __name__ == "__main__":
    app.run(port=5555, debug=True)
