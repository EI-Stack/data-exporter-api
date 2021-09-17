from .spc import spc_bp
from .dataset import dataset_bp


def init_app(app):
    app.register_blueprint(spc_bp)
    app.register_blueprint(dataset_bp)
