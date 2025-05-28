import os
import dotenv
from flask import Flask

dotenv.load_dotenv()

from routes.api_routes import router as api_router
from routes.ui_routes import router as ui_router
from routes.auth_routes import router as auth_router
from flask import request
# from flask import Blueprint

app = Flask(__name__, static_folder="assets", static_url_path="/assets")
app.register_blueprint(api_router)
app.register_blueprint(ui_router)
app.register_blueprint(auth_router)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
