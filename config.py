class Config:
    
    DB_HOST = 'localhost'  

    DB_NAME = 'new_schema'  
    
    DB_USER = 'root'  
    DB_PASSWORD = 'Prashant'  
    SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://root:Prashant@localhost:3306/new_schema'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'your_secret_key'
    hello =  "hell"