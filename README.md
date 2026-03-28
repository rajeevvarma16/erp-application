# Flask ERP System

A secure login/register/logout app with:
- Password hashing (Werkzeug)
- Session management (Flask-Login)
- Rate limiting (Flask-Limiter)
- MySQL support via SQLAlchemy

## Setup
```bash
github download:
git clone <your-repo-link>
cd construction-erp

virtual environment:
python3 -m venv venv
source venv/bin/activate

download requirements and run app:
pip install -r requirements.txt
python run.py

open in browser:
http://127.0.0.1:5000
