from flask import jsonify

from .spc import spc_bp
from .dataset import dataset_bp


def init_app(app):
    app.register_blueprint(spc_bp)
    app.register_blueprint(dataset_bp)

    @app.route("/", methods=["GET"])
    def init_route():
        return jsonify({"message": "Data Exporter API is already working."}, 200)
