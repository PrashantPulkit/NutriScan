# routes.py
from flask import Blueprint

# Create a blueprint
my_routes = Blueprint('my_routes', __name__)

@my_routes.route('/dashboard')
def new_route():
    return "This is a new route!"


@my_routes.route('/new_route2')
def new_route2():
    return "This is a new route!"

@my_routes.route('/new_route3')
def new_route3():
    return "This is a new route!"