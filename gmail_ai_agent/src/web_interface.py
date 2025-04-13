from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from src.database import EmailDatabase, EmailAction
import os
import sqlite3

app = Flask(__name__)
Bootstrap(app)

# Initialize database
db = EmailDatabase()

@app.route('/')
def index():
    # Get the latest 3 entries
    latest_emails = db.get_latest_emails(3)  # Get latest 3 emails
    
    return render_template(
        'index.html',
        emails=latest_emails,
        actions=EmailAction,
        format_time=lambda dt: dt.strftime("%Y-%m-%d %H:%M:%S")
    )

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs(os.path.join(os.path.dirname(__file__), 'templates'), exist_ok=True)
    app.run(debug=True, port=5050)
