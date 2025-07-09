from flask import Flask, render_template_string, redirect, url_for, request, flash, jsonify, send_from_directory, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_cors import CORS
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from werkzeug.utils import secure_filename
import os
import re
import json
import uuid

app = Flask(__name__, static_folder="dist", static_url_path="")
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cms.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

CORS(app)
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'admin_login'

# ----------------------
# DATABASE MODELS (EXAMPLE)
# ----------------------
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

# Define other models like Councillor, Event, PageContent, etc.

# ----------------------
# AUTH SETUP
# ----------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ----------------------
# ADMIN ROUTES (PREFIXED WITH /admin)
# ----------------------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for("admin_dashboard"))
        flash("Invalid credentials")
    return render_template_string("""
    <form method='post'>
        <input name='username'><input name='password' type='password'><button>Login</button>
    </form>
    """)

@app.route("/admin/logout")
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for("admin_login"))

@app.route("/admin")
@login_required
def admin_dashboard():
    return "Admin Dashboard"

@app.route("/admin/councillors")
@login_required
def admin_councillors():
    return "Councillors Management Page"

# Add other /admin routes as needed

# ----------------------
# API ROUTES (OPTIONAL)
# ----------------------
@app.route("/api/councillors")
def api_councillors():
    # Example: Return dummy data
    return jsonify([{"name": "Paul Arnold", "ward": "East Ward"}])

# ----------------------
# FRONTEND FALLBACK ROUTING
# ----------------------
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    if path.startswith("admin") or path.startswith("api") or path.startswith("static"):
        return "Not Found", 404
    file_path = os.path.join(app.static_folder, path)
    if path != "" and os.path.exists(file_path):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, "index.html")

# ----------------------
# ENTRY POINT (for local testing only)
# ----------------------
if __name__ == '__main__':
    app.run(debug=True)
