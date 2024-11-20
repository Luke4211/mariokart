from flask import Flask



def create_app():
    app = Flask(__name__)

    app.config['PRIOR_TALLY'] = 91 

    from .routes import main
    app.register_blueprint(main)

    return app
