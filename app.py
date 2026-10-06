from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from config import Config
# Initializing Flask App
app = Flask(__name__)

# Load configuration settings
app.config.from_object(Config)

# Initialize SQLAlchemy DB instance
db = SQLAlchemy(app)

@app.route('/')
def home():
    """Temporary home page route to verify setup."""
    return render_template('base.html')

if __name__ == '__main__':
    # Explicitly set host to localhost (127.0.0.1) and port to 5000
    app.run(host='127.0.0.1', port=5000, debug=True)