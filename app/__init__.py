from flask import Flask



def create_app():
    app = Flask(__name__)

    app.config['PRIOR_TALLY'] = 91 
    app.config['P1_NAME'] = 'Luke'
    app.config['P2_NAME'] = 'Liam'

    from .routes import main
    app.register_blueprint(main)

    return app
