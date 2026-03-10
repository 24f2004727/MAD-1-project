from flask_sqlalchemy import SQLAlchemy # Lets Python classes to create database tables
from flask_login import UserMixin # User model like is_authentication properties are added 

db = SQLAlchemy() # Creates database objects that are used in app.py

class User(db.Model, UserMixin): # Class representing a table, which inherit from userMixin allowing users to log in and out
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False) # distinguish  between 'Admin', 'Company', 'Student'
    qualification = db.Column(db.String(100))
    is_approved = db.Column(db.Boolean, default=False) # Approval for Companies/Drives
    is_active = db.Column(db.Boolean, default=True) # For blacklisting

class PlacementDrive(db.Model): # table for drives by companies
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    job_title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    eligibility = db.Column(db.String(200))
    deadline = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='Pending') # Pending, Approved, Closed
    date_posted = db.Column(db.DateTime, default=db.func.current_timestamp())

class Application(db.Model): # table for applications for students
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    drive_id = db.Column(db.Integer, db.ForeignKey('placement_drive.id'))
    application_date = db.Column(db.DateTime, default=db.func.current_timestamp()) 
    status = db.Column(db.String(20), default='Applied') # Applied, Shortlisted, Selected, Rejected
    student = db.relationship('User', backref='applications_list')
    drive = db.relationship('PlacementDrive', backref='applications_list')

class JobDrive(db.Model): # Job posting by comapnies
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(100), nullable=False)
    job_role = db.Column(db.String(100), nullable=False)
    salary = db.Column(db.String(50))
    description = db.Column(db.Text)
    # automatically records the exact data and time when the row is created
    date_posted = db.Column(db.DateTime, default=db.func.current_timestamp()) 



class CompanyProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    hr_contact = db.Column(db.String(100))
    website = db.Column(db.String(100))
    approval_status = db.Column(db.Boolean, default=False)