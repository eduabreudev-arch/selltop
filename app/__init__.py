from flask import Flask

def create_app():
    app = Flask(__name__)

    # carregar config atual
    app.config.from_object("config")

    return app