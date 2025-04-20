from flask import Flask
from flasgger import Swagger
from mongo_db_connection_manager import MongoConnectionManager
from controller.ad_entrypoints import ad_routes_blueprint
from routes import init_routes
import os


app = Flask(__name__)
Swagger(app)

# Initalize Database Connection
MongoConnectionManager.init_db()

#Importe the routes
init_routes(app)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 1993))
    app.run(debug=True, port=port)