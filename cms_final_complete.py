
import os
from flask import Flask, send_from_directory, request, jsonify, session, redirect
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__, static_folder="dist", static_url_path="")
CORS(app)

# Configuration
app.secret_key = os.environ.get("SECRET_KEY", "default_secret_key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///site.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Example API Route (you'll replace or expand these)
@app.route("/api/data", methods=["GET"])
def get_data():
    return jsonify({"message": "Data returned from API"}), 200

# Example Auth Route (replace with your real ones)
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        # Authenticate user (example only)
        return redirect("/admin/dashboard")
    return "<form method='post'><input name='user'><input name='pass'><button>Login</button></form>"

# Serve static admin files
@app.route("/admin/<path:path>")
def admin_static(path):
    return send_from_directory("admin", path)

# Catch-all for frontend routes (SPA handling)
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    # Allow static assets through
    if (
        path.startswith("api")
        or path.startswith("admin")
        or path.startswith("static")
        or path.endswith(".js")
        or path.endswith(".css")
        or path.endswith(".map")
        or path.endswith(".json")
        or path.endswith(".ico")
    ):
        return send_from_directory(app.static_folder, path)

    index_path = os.path.join(app.static_folder, "index.html")
    if os.path.exists(index_path):
        return send_from_directory(app.static_folder, "index.html")
    return "Index file not found", 404

if __name__ == "__main__":
    app.run(debug=True)

@app.route('/routes')
def show_routes():
    return jsonify([
        str(rule) for rule in app.url_map.iter_rules()
    ])

