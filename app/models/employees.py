from app import db
from datetime import date

class Employees(db.Model):
    __tablename__ = 'employees'

    id = db.Column(db.Integer, primary_key=True)
    employee_name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    joining_date = db.Column(db.Date, nullable=False, default=lambda: date.today())
    salary = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False)
