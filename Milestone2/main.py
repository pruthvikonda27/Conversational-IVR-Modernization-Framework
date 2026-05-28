from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend import app

from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Backend Running"

if __name__ == "__main__":
    app.run()

