import mysql.connector
from mysql.connector import Error
from flask import current_app
#::::::::::::::::::::::::::::::::::::::::::::::::::sqlalchemy new part::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
#::::::::::::::::::::::::::::::::::::::::::::::::::::::::::mysql connector::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=current_app.config['DB_HOST'],
            database=current_app.config['DB_NAME'],
            user=current_app.config['DB_USER'],
            password=current_app.config['DB_PASSWORD']
        )
        return connection
    except Error as e:
        print(f"Error: {e}")
        return None
