from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from backend.routes.auth_routes import auth_bp
from backend.routes.verify_routes import verify_bp

def create_app():
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = "supersecretkey123"  # Change in production
    JWTManager(app)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(verify_bp)

    @app.route("/", methods=["GET"])
    def index():
        return jsonify({"message": "✅ VeriSight backend is running"})

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
