from flask import Flask, render_template, redirect, url_for, request, flash # HTML codes and to direct b/w pages
from models import db, User, PlacementDrive, Application, JobDrive, CompanyProfile
from flask_login import LoginManager, login_user, logout_user, login_required, current_user # Manage user sessions 
from werkzeug.security import generate_password_hash, check_password_hash # Hashed password

app = Flask(__name__) # web application software
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///portal.db' # where database file is located
app.config['SECRET_KEY'] = 'secret-key-123' # secure sessions

db.init_app(app)
login_manager = LoginManager(app) # links login system to app
login_manager.login_view = 'login' # how to find database based on stored ID 

@login_manager.user_loader
def load_user(user_id):
    # Fetches specific user from portal.db by their ID 
    return User.query.get(int(user_id))

# PROGRAMMATIC DB CREATION (creats database if not present and sets it as default admin account)
with app.app_context():
    db.create_all()
    if not User.query.filter_by(role='Admin').first():
        hashed_pw = generate_password_hash('admin123')
        admin = User(username='admin', password=hashed_pw, role='Admin', is_approved=True)
        db.session.add(admin)
        db.session.commit()
        print("Database initialized and Admin 'admin' created with password 'admin123'")



@app.route('/')
def index():
    return redirect(url_for('login'))

# defines veiwing and submitting (GET and POST) , checks for existance of data (verify password),  
# keeps the user logged in , based on the user name (Admin, company, student) directs to dashboard

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and check_password_hash(user.password, request.form.get('password')):
            login_user(user)
            if user.role == 'Company' and not user.is_approved:
                flash('Your company is pending admin approval.')
                return redirect(url_for('dashboard'))
            if user.role == 'Admin':
               return redirect(url_for('admin_dashboard'))
            else:
               return redirect(url_for('dashboard'))
        flash('Invalid credentials')
    return render_template('login.html')



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_name = request.form.get('username')
        user_pass = request.form.get('password')
        user_role = request.form.get('role')
        
        # Security: Hash the password
        hashed_pw = generate_password_hash(user_pass)
        
        # 1. Save the User
        qualification = request.form.get('qualification')
        new_user = User(username=user_name, password=hashed_pw, role=user_role, qualification=qualification, is_approved=True)
        db.session.add(new_user)
        db.session.flush() # CRITICAL: This assigns an ID to new_user without committing yet
        
        # 2. If the user is a Company, create their linked profile
        if user_role == 'Company':
            new_profile = CompanyProfile(company_id=new_user.id) # Link using the new user's ID
            db.session.add(new_profile)
        
        # 3. Commit all changes (User + optional Profile)
        db.session.commit()
        
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    user_applications = Application.query.filter_by(student_id=current_user.id).all()
    return render_template('dashboard.html', applications=user_applications)
    

# Access firewall directing back to dashboard
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    # Only allow users with the 'Admin' role to enter
    if current_user.role != 'Admin':
        flash("Access denied: Admins only!")
        return redirect(url_for('dashboard'))
    
    # Query the database
    s_count = User.query.filter_by(role='Student').count()
    c_count = User.query.filter_by(role='Company').count()
    
    # NEW: Fetch pending drives and get count of approved ones
    pending_drives = PlacementDrive.query.filter_by(status='Pending').all()
    d_count = PlacementDrive.query.filter_by(status='Approved').count()
    
    return render_template('admin_dashboard.html', 
                           student_count=s_count, 
                           company_count=c_count, 
                           drive_count=d_count,
                           pending_drives=pending_drives) # Pass the list here

# Posing of jobs from companies
@app.route('/post_job', methods=['GET', 'POST'])
@login_required
def post_job():
    if current_user.role != 'Company':
        flash("Only companies can post jobs!")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        new_job = JobDrive(
            company_name=current_user.username,
            job_role=request.form.get('job_role'),
            salary=request.form.get('salary'),
            description=request.form.get('description')
        )
        db.session.add(new_job)
        db.session.commit()
        flash("Job Drive Posted Successfully!")
        return redirect(url_for('dashboard'))
    
    return render_template('post_job.html')

# Viewing jobs by students 
@app.route('/view_jobs')
@login_required
def view_jobs():
    # Fetch ONLY approved jobs so students don't see pending ones
    all_jobs = PlacementDrive.query.filter_by(status='Approved').all()
    
    return render_template('view_jobs.html', jobs=all_jobs)

# Redirects to login page 
@app.route('/logout')
@login_required
def logout():
    logout_user() # Clears the session
    flash('You have been logged out.')
    return redirect(url_for('login'))

@app.route('/apply/<int:drive_id>', methods=['POST'])
@login_required
def apply_to_job(drive_id):
    # Check if the student already applied to prevent duplicates
    existing = Application.query.filter_by(student_id=current_user.id, drive_id=drive_id).first()
    if existing:
        flash('You have already applied to this job!')
    else:
        # Create a new application record
        new_app = Application(student_id=current_user.id, drive_id=drive_id, status='Applied')
        db.session.add(new_app)
        db.session.commit()
        flash('Application submitted successfully!')
    
    return redirect(url_for('view_jobs'))

@app.route('/create_drive', methods=['POST'])
@login_required
def create_drive():
    # Ensure only companies can do this
    if current_user.role != 'Company':
        return "Unauthorized"

    new_drive = PlacementDrive(
        company_id=current_user.id,
        job_title=request.form.get('title'),
        description=request.form.get('desc'),
        status='Pending' # Admins must approve this later
    )
    db.session.add(new_drive)
    db.session.commit()
    return redirect(url_for('company_dashboard'))

@app.route('/admin/approve/<int:drive_id>', methods=['POST'])
@login_required
def approve_drive(drive_id):
    if current_user.role != 'Admin':
        return "Unauthorized", 403
    
    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.status = 'Approved'
    db.session.commit()
    flash('Drive approved successfully!')
    return redirect(url_for('admin_dashboard'))

@app.route('/company_dashboard')
@login_required
def company_dashboard():
    if current_user.role != 'Company':
        return redirect(url_for('dashboard'))
    
    # 1. Get all drives posted by this company
    my_drives = PlacementDrive.query.filter_by(company_id=current_user.id).all()
    drive_ids = [d.id for d in my_drives]
    
    # 2. Get all applications for these specific drives
    # This joins the Application table with the User (Student) table
    applications = Application.query.filter(Application.drive_id.in_(drive_ids)).all()
    
    return render_template('company_dashboard.html', drives=my_drives, applications=applications)


if __name__ == "__main__": # commands for execution of the code
    app.run(debug=True) # Restarts server