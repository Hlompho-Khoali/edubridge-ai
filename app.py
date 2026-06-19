# app.py
import re
import os
import random
import string
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Admin, Educator, Parent, Learner, Game, TestAssignment, TestResult, CognitiveAssessment, LearnerBadge
from utils.games_data import get_all_games
from utils.cognitive_assessment import CognitiveAssessmentService
from utils.validators import validate_rsa_id, calculate_age, validate_learner_age, determine_grade_from_age
from datetime import datetime
import json
from werkzeug.security import generate_password_hash
from ai_service import AIService
from ai_config import AIConfig
from utils.email import EmailService
from utils.badges import BadgeService

# Load environment variables
load_dotenv()

# ==================== CREATE FLASK APP ====================
app = Flask(__name__)

# ==================== DATABASE CONFIGURATION ====================
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql+psycopg://', 1)
    elif '+psycopg' not in DATABASE_URL and not DATABASE_URL.startswith('sqlite'):
        DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+psycopg://', 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    print(f"Using PostgreSQL with psycopg: {DATABASE_URL[:50]}...")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
    print("Using SQLite (local development)")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('RENDER', 'false').lower() == 'true'
app.config['REMEMBER_COOKIE_SECURE'] = os.environ.get('RENDER', 'false').lower() == 'true'

# ==================== INITIALIZE EXTENSIONS ====================
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ==================== AUTO-MIGRATION FUNCTION ====================
def run_migrations():
    """Check and add missing columns to games table on startup"""
    try:
        from sqlalchemy import inspect, text
        
        with app.app_context():
            inspector = inspect(db.engine)
            
            # Games table columns
            games_columns = [col['name'] for col in inspector.get_columns('games')]
            games_new_columns = {
                'grade_level': 'INTEGER DEFAULT 1',
                'subcategory': 'VARCHAR(50) DEFAULT \'default\'',
                'accessibility_features': 'TEXT DEFAULT \'{}\'',
                'visual_style': 'VARCHAR(50) DEFAULT \'default\'',
                'audio_support': 'BOOLEAN DEFAULT FALSE',
                'movement_breaks': 'BOOLEAN DEFAULT FALSE',
                'progress_tracking': 'BOOLEAN DEFAULT TRUE',
                'max_questions': 'INTEGER DEFAULT 10',
                'disability_type': 'VARCHAR(50) DEFAULT \'none\'',
                'recommended_for': 'VARCHAR(50) DEFAULT \'all\''
            }
            
            for col_name, col_type in games_new_columns.items():
                if col_name not in games_columns:
                    try:
                        db.session.execute(text(f'ALTER TABLE games ADD COLUMN {col_name} {col_type}'))
                        print(f"Added column to games: {col_name}")
                    except Exception as e:
                        print(f"Error adding {col_name} to games: {e}")
            
            # Learners table columns
            learners_columns = [col['name'] for col in inspector.get_columns('learners')]
            learners_new_columns = {
                'accessibility_preferences': 'TEXT DEFAULT \'{}\'',
                'disability_type': 'VARCHAR(50) DEFAULT \'none\'',
                'disability_notes': 'TEXT',
                'assessment_completed': 'BOOLEAN DEFAULT FALSE',
                'assessment_date': 'DATETIME',
                'cognitive_scores': 'TEXT DEFAULT \'{}\'',
                'condition_probabilities': 'TEXT DEFAULT \'{}\'',
                'recommendations': 'TEXT DEFAULT \'[]\'',
                'last_assessment': 'DATETIME'
            }
            
            for col_name, col_type in learners_new_columns.items():
                if col_name not in learners_columns:
                    try:
                        db.session.execute(text(f'ALTER TABLE learners ADD COLUMN {col_name} {col_type}'))
                        print(f"Added column to learners: {col_name}")
                    except Exception as e:
                        print(f"Error adding {col_name} to learners: {e}")
            
            db.session.commit()
            print("Migration completed successfully!")
                
    except Exception as e:
        print(f"Migration warning: {e}")

# ==================== RUN MIGRATION ON STARTUP ====================
with app.app_context():
    run_migrations()

# ==================== USER LOADER ====================
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# ==================== CUSTOM JINJA2 FILTERS ====================
@app.template_filter('fromjson')
def from_json_filter(value):
    if value:
        try:
            return json.loads(value)
        except:
            return []
    return []

@app.template_filter('contains')
def contains_filter(value, substring):
    """Check if a string contains a substring"""
    if value and substring:
        return substring.lower() in value.lower()
    return False

# ==================== INITIALIZE DATABASE ====================
with app.app_context():
    db.create_all()
    print("Database tables created/verified")
    
    # Create super admin if not exists
    admin_user = User.query.filter_by(email='admin@edubridge.com').first()
    if not admin_user:
        admin_user = User(
            email='admin@edubridge.com',
            name='Super Admin',
            role='admin'
        )
        admin_user.set_password('admin123')
        db.session.add(admin_user)
        db.session.flush()
        
        admin_profile = Admin(
            user_id=admin_user.id,
            employee_id='ADMIN001',
            department='System Administration'
        )
        db.session.add(admin_profile)
        db.session.commit()
        print("Super Admin created: admin@edubridge.com / admin123")
    
    # Add default games if not exists
    games_data = get_all_games()
    for game_data in games_data:
        game = Game.query.filter_by(name=game_data['name']).first()
        if not game:
            game = Game(
                name=game_data['name'],
                description=game_data['description'],
                category=game_data.get('category', 'General'),
                questions=json.dumps(game_data['questions']),
                passing_score=15,
                time_limit_minutes=60,
                difficulty=game_data.get('difficulty', 'Intermediate')
            )
            db.session.add(game)
    
    # Initialize badges
    BadgeService.initialize_badges()
    
    db.session.commit()
    print(f"Database initialized with {len(games_data)} games")

# ==================== AUTHENTICATION ROUTES ====================

@app.route('/')
def index():
    games_count = Game.query.count()
    return render_template('index.html', games_count=games_count)

@app.route('/login', methods=['GET', 'POST'])
def login():
    role = request.args.get('role', '')
    
    if request.method == 'POST':
        email_or_id = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email_or_id).first()
        
        if not user and email_or_id.isdigit() and len(email_or_id) == 13:
            learner = Learner.query.filter_by(id_number=email_or_id).first()
            if learner:
                user = learner.user
        
        if user and user.check_password(password):
            login_user(user)
            
            if user.role == 'educator':
                return redirect(url_for('educator_dashboard'))
            elif user.role == 'parent':
                return redirect(url_for('parent_dashboard'))
            elif user.role == 'learner':
                return redirect(url_for('learner_dashboard'))
            elif user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html', role=role)

@app.route('/register/educator', methods=['GET', 'POST'])
def register_educator():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        grade = int(request.form.get('grade'))
        
        form_data = {
            'name': name,
            'email': email,
            'phone': phone,
            'grade': grade
        }
        
        if not name or not re.match(r"^[A-Za-z\s\-']+$", name):
            flash('Name must contain only letters, spaces, hyphens, and apostrophes.', 'error')
            return render_template('register_educator.html', form_data=form_data)
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('register_educator.html', form_data=form_data)
        
        user = User(email=email, name=name, role='educator')
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        
        educator = Educator(user_id=user.id, phone_number=phone, grade_teaching=grade)
        db.session.add(educator)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register_educator.html', form_data={})

@app.route('/register_parent', methods=['GET', 'POST'])
def register_parent():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        id_number = request.form.get('id_number', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        form_data = {
            'name': name,
            'email': email,
            'phone': phone,
            'id_number': id_number
        }
        
        if not name or not re.match(r"^[A-Za-z\s\-']+$", name):
            flash('Name must contain only letters, spaces, hyphens, and apostrophes.', 'error')
            return render_template('register_parent.html', form_data=form_data)
        
        if not email or '@' not in email:
            flash('Please enter a valid email address.', 'error')
            return render_template('register_parent.html', form_data=form_data)
        
        if not phone or not phone.replace('+', '').replace(' ', '').replace('-', '').isdigit():
            flash('Please enter a valid phone number.', 'error')
            return render_template('register_parent.html', form_data=form_data)
        
        if not id_number or len(id_number) != 13 or not id_number.isdigit():
            flash('ID number must be exactly 13 digits.', 'error')
            return render_template('register_parent.html', form_data=form_data)
        
        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return render_template('register_parent.html', form_data=form_data)
        
        if len(password) < 8:
            flash('Password must be at least 8 characters long!', 'error')
            return render_template('register_parent.html', form_data=form_data)
        
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered!', 'error')
            return render_template('register_parent.html', form_data=form_data)
        
        existing_parent = Parent.query.filter_by(id_number=id_number).first()
        if existing_parent:
            flash('ID number already registered!', 'error')
            return render_template('register_parent.html', form_data=form_data)
        
        user = User(
            name=name,
            email=email,
            phone=phone,
            role='parent'
        )
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        
        parent = Parent(user_id=user.id, id_number=id_number)
        db.session.add(parent)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register_parent.html', form_data={})

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            flash('Password reset link has been sent to your email!', 'success')
            return redirect(url_for('login'))
        else:
            flash('No account found with that email address.', 'error')
    
    return render_template('forgot_password.html')

@app.route('/learner-login', methods=['GET', 'POST'])
def learner_login():
    if request.method == 'POST':
        code = ''.join([request.form.get(f'digit{i}') for i in range(1, 7)])
        
        learner = Learner.query.filter_by(login_code=code).first()
        
        if learner:
            login_user(learner.user)
            flash(f'Welcome back, {learner.user.name}!', 'success')
            return redirect(url_for('learner_dashboard'))
        else:
            flash('Invalid code! Please check with your teacher or parent.', 'error')
    
    return render_template('learner_login.html')

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    session.clear()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('index'))

# ==================== PROFILE ROUTES ====================

@app.route('/profile')
@login_required
def view_profile():
    user = current_user
    
    if user.role == 'educator':
        profile = Educator.query.filter_by(user_id=user.id).first()
        return render_template('profile.html', user=user, profile=profile, role_data=profile)
    elif user.role == 'parent':
        profile = Parent.query.filter_by(user_id=user.id).first()
        return render_template('profile.html', user=user, profile=profile, role_data=profile)
    elif user.role == 'learner':
        profile = Learner.query.filter_by(user_id=user.id).first()
        return render_template('profile.html', user=user, profile=profile, role_data=profile)
    elif user.role == 'admin':
        profile = Admin.query.filter_by(user_id=user.id).first()
        return render_template('profile.html', user=user, profile=profile, role_data=profile)
    
    return render_template('profile.html', user=user, profile=None, role_data=None)

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    user = current_user
    
    if user.role == 'educator':
        profile = Educator.query.filter_by(user_id=user.id).first()
        if request.method == 'POST':
            user.name = request.form.get('name')
            user.phone = request.form.get('phone')
            profile.phone_number = request.form.get('phone_number')
            profile.qualification = request.form.get('qualification')
            profile.school = request.form.get('school')
            
            new_password = request.form.get('new_password')
            if new_password:
                user.set_password(new_password)
            
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('view_profile'))
        
        return render_template('edit_profile.html', user=user, profile=profile)
    
    elif user.role == 'parent':
        profile = Parent.query.filter_by(user_id=user.id).first()
        if request.method == 'POST':
            user.name = request.form.get('name')
            user.phone = request.form.get('phone')
            profile.occupation = request.form.get('occupation')
            
            new_password = request.form.get('new_password')
            if new_password:
                user.set_password(new_password)
            
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('view_profile'))
        
        return render_template('edit_profile.html', user=user, profile=profile)
    
    elif user.role == 'learner':
        profile = Learner.query.filter_by(user_id=user.id).first()
        if request.method == 'POST':
            user.name = request.form.get('name')
            user.phone = request.form.get('phone')
            profile.school = request.form.get('school')
            
            new_password = request.form.get('new_password')
            if new_password:
                user.set_password(new_password)
            
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('view_profile'))
        
        return render_template('edit_profile.html', user=user, profile=profile)
    
    elif user.role == 'admin':
        profile = Admin.query.filter_by(user_id=user.id).first()
        if request.method == 'POST':
            user.name = request.form.get('name')
            user.phone = request.form.get('phone')
            profile.department = request.form.get('department')
            
            new_password = request.form.get('new_password')
            if new_password:
                user.set_password(new_password)
            
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('view_profile'))
        
        return render_template('edit_profile.html', user=user, profile=profile)
    
    return redirect(url_for('index'))

@app.route('/profile/delete', methods=['POST'])
@login_required
def delete_profile():
    user = current_user
    role = user.role
    
    if role == 'admin':
        flash('Admin accounts cannot be deleted', 'error')
        return redirect(url_for('view_profile'))
    
    try:
        user_id = user.id
        
        if role == 'educator':
            profile = Educator.query.filter_by(user_id=user_id).first()
            if profile:
                db.session.delete(profile)
        elif role == 'parent':
            profile = Parent.query.filter_by(user_id=user_id).first()
            if profile:
                db.session.delete(profile)
        elif role == 'learner':
            profile = Learner.query.filter_by(user_id=user_id).first()
            if profile:
                db.session.delete(profile)
        
        db.session.commit()
        
        user_to_delete = User.query.get(user_id)
        if user_to_delete:
            db.session.delete(user_to_delete)
            db.session.commit()
        
        logout_user()
        flash('Your account has been deleted', 'success')
        return redirect(url_for('index'))
        
    except Exception as e:
        db.session.rollback()
        flash('An error occurred', 'error')
        return redirect(url_for('view_profile'))

# ==================== ADMIN ROUTES ====================

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('login'))
    
    admin_profile = Admin.query.filter_by(user_id=current_user.id).first()
    educators = Educator.query.all()
    parents = Parent.query.all()
    learners = Learner.query.all()
    games = Game.query.all()
    assignments = TestAssignment.query.all()
    results = TestResult.query.all()
    
    stats = {
        'total_educators': len(educators),
        'total_parents': len(parents),
        'total_learners': len(learners),
        'total_games': len(games),
        'total_assignments': len(assignments),
        'total_completed': len(results),
        'total_pending': len([a for a in assignments if a.status == 'pending']),
        'avg_score': sum([r.percentage for r in results]) / len(results) if results else 0,
        'pass_rate': len([r for r in results if r.passed]) / len(results) * 100 if results else 0
    }
    
    return render_template('admin_dashboard.html', stats=stats, admin_profile=admin_profile)

@app.route('/admin/users')
@login_required
def admin_users():
    if current_user.role != 'admin':
        return redirect(url_for('login'))
    
    educators = Educator.query.all()
    parents = Parent.query.all()
    learners = Learner.query.all()
    
    return render_template('admin_users.html', educators=educators, parents=parents, learners=learners)

@app.route('/admin/games')
@login_required
def admin_games():
    if current_user.role != 'admin':
        return redirect(url_for('login'))
    
    games = Game.query.all()
    return render_template('admin_games.html', games=games)

@app.route('/admin/results')
@login_required
def admin_results():
    if current_user.role != 'admin':
        return redirect(url_for('login'))
    
    results = TestResult.query.all()
    results_data = []
    for result in results:
        assignment = result.assignment
        results_data.append({
            'result': result,
            'assignment': assignment,
            'game': assignment.game,
            'learner': assignment.learner,
            'educator': assignment.educator
        })
    
    return render_template('admin_results.html', results_data=results_data)

@app.route('/admin/user/delete/<int:user_id>')
@login_required
def admin_delete_user(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('login'))
    
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot delete your own admin account', 'error')
        return redirect(url_for('admin_users'))
    
    if user.role == 'admin':
        flash('Cannot delete other admin users', 'error')
        return redirect(url_for('admin_users'))
    
    try:
        if user.role == 'learner':
            learner = Learner.query.filter_by(user_id=user.id).first()
            if learner:
                # Delete learner badges
                LearnerBadge.query.filter_by(learner_id=learner.id).delete()
                
                # Delete assignments and results
                assignments = TestAssignment.query.filter_by(learner_id=learner.id).all()
                for assignment in assignments:
                    TestResult.query.filter_by(assignment_id=assignment.id).delete()
                    db.session.delete(assignment)
                
                # Delete cognitive assessments
                CognitiveAssessment.query.filter_by(learner_id=learner.id).delete()
                
                db.session.delete(learner)
                
        elif user.role == 'parent':
            parent = Parent.query.filter_by(user_id=user.id).first()
            if parent:
                # Get all learners under this parent
                learners = Learner.query.filter_by(parent_id=parent.id).all()
                
                for learner in learners:
                    # 1. Delete learner badges FIRST
                    LearnerBadge.query.filter_by(learner_id=learner.id).delete()
                    
                    # 2. Delete test results and assignments
                    assignments = TestAssignment.query.filter_by(learner_id=learner.id).all()
                    for assignment in assignments:
                        TestResult.query.filter_by(assignment_id=assignment.id).delete()
                        db.session.delete(assignment)
                    
                    # 3. Delete cognitive assessments
                    CognitiveAssessment.query.filter_by(learner_id=learner.id).delete()
                    
                    # 4. Delete the learner
                    db.session.delete(learner)
                
                # 5. Delete the parent
                db.session.delete(parent)
                
        elif user.role == 'educator':
            educator = Educator.query.filter_by(user_id=user.id).first()
            if educator:
                assignments = TestAssignment.query.filter_by(educator_id=educator.id).all()
                for assignment in assignments:
                    TestResult.query.filter_by(assignment_id=assignment.id).delete()
                    db.session.delete(assignment)
                db.session.delete(educator)
        
        # Finally, delete the user
        db.session.delete(user)
        db.session.commit()
        flash(f'User {user.name} deleted successfully', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')
        print(f"Delete error: {e}")
    
    return redirect(url_for('admin_users'))
@app.route('/admin/wipe-games')
@login_required
def admin_wipe_games():
    """Wipe all games (Admin only)"""
    if current_user.role != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('index'))
    
    try:
        results_count = TestResult.query.count()
        TestResult.query.delete()
        
        assignments_count = TestAssignment.query.count()
        TestAssignment.query.delete()
        
        games_count = Game.query.count()
        Game.query.delete()
        
        db.session.commit()
        
        flash(f'All games wiped! ({games_count} games, {assignments_count} assignments, {results_count} results deleted)', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {e}', 'error')
    
    return redirect(url_for('admin_dashboard'))

    # ==================== ADMIN EDIT USER ROUTES ====================

@app.route('/admin/edit-user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_user(user_id):
    """Edit a user's details"""
    if current_user.role != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('login'))
    
    user = User.query.get_or_404(user_id)
    
    # Don't allow editing own admin account
    if user.id == current_user.id:
        flash('You cannot edit your own admin account.', 'error')
        return redirect(url_for('admin_users'))
    
    # Get profile based on role
    profile = None
    if user.role == 'educator':
        profile = Educator.query.filter_by(user_id=user.id).first()
    elif user.role == 'parent':
        profile = Parent.query.filter_by(user_id=user.id).first()
    elif user.role == 'learner':
        profile = Learner.query.filter_by(user_id=user.id).first()
    
    if request.method == 'POST':
        try:
            # Update common user fields
            user.name = request.form.get('name', user.name)
            user.email = request.form.get('email', user.email)
            user.phone = request.form.get('phone', user.phone)
            
            # Update role-specific fields
            if user.role == 'educator' and profile:
                profile.phone_number = request.form.get('phone_number', profile.phone_number)
                profile.grade_teaching = int(request.form.get('grade_teaching', profile.grade_teaching))
                profile.qualification = request.form.get('qualification', profile.qualification)
                profile.school = request.form.get('school', profile.school)
                
            elif user.role == 'parent' and profile:
                profile.id_number = request.form.get('id_number', profile.id_number)
                profile.occupation = request.form.get('occupation', profile.occupation)
                
            elif user.role == 'learner' and profile:
                profile.id_number = request.form.get('id_number', profile.id_number)
                profile.grade = int(request.form.get('grade', profile.grade))
                profile.school = request.form.get('school', profile.school)
                profile.disability_type = request.form.get('disability_type', profile.disability_type)
                profile.disability_notes = request.form.get('disability_notes', profile.disability_notes)
            
            # Update password if provided
            new_password = request.form.get('new_password')
            if new_password and len(new_password) >= 6:
                user.set_password(new_password)
                flash('Password updated successfully.', 'success')
            
            db.session.commit()
            flash(f'User {user.name} updated successfully!', 'success')
            return redirect(url_for('admin_users'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating user: {str(e)}', 'error')
    
    return render_template('admin_edit_user.html', user=user, profile=profile)


@app.route('/admin/delete-user/<int:user_id>')
@login_required
def admin_delete_user_redirect(user_id):
    """Redirect to delete user (keeps existing functionality)"""
    return redirect(url_for('admin_delete_user', user_id=user_id))

# ==================== EDUCATOR ROUTES ====================

@app.route('/educator/dashboard')
@login_required
def educator_dashboard():
    if current_user.role != 'educator':
        return redirect(url_for('login'))
    
    educator = Educator.query.filter_by(user_id=current_user.id).first()
    learners = Learner.query.filter_by(grade=educator.grade_teaching).all()
    games = Game.query.all()
    
    assignments = TestAssignment.query.filter_by(educator_id=educator.id).all()
    assignments_with_results = []
    for assignment in assignments:
        result = TestResult.query.filter_by(assignment_id=assignment.id).first()
        assignments_with_results.append({
            'assignment': assignment,
            'result': result
        })
    
    for learner in learners:
        learner_assignments = TestAssignment.query.filter_by(learner_id=learner.id).all()
        learner.assignment_count = len(learner_assignments)
        
        completed = [a for a in learner_assignments if a.status == 'completed']
        learner.completed_count = len(completed)
        
        scores = []
        passed_count = 0
        for assignment in completed:
            result = TestResult.query.filter_by(assignment_id=assignment.id).first()
            if result:
                scores.append(result.percentage)
                if result.passed:
                    passed_count += 1
        
        learner.avg_score = round(sum(scores) / len(scores), 1) if scores else 0
        learner.passed_count = passed_count
    
    search_query = request.args.get('search', '').strip()
    if search_query:
        filtered_learners = []
        for learner in learners:
            if (search_query.lower() in learner.user.name.lower() or 
                search_query in learner.id_number):
                filtered_learners.append(learner)
        learners = filtered_learners
    
    return render_template('educator_dashboard.html', 
                         educator=educator,
                         learners=learners, 
                         assignments=assignments_with_results,
                         games=games,
                         search_query=search_query)

@app.route('/educator/assign_test', methods=['POST'])
@login_required
def assign_test():
    """Assign a test to a learner - FIXED: Convert IDs to integers"""
    if current_user.role != 'educator':
        flash('Unauthorized', 'error')
        return redirect(url_for('login'))
    
    try:
        educator = Educator.query.filter_by(user_id=current_user.id).first()
        if not educator:
            flash('Educator profile not found.', 'error')
            return redirect(url_for('educator_dashboard'))
        
        learner_id = request.form.get('learner_id')
        game_id = request.form.get('game_id')
        
        if not learner_id or not game_id:
            flash('Please select both a student and a test.', 'error')
            return redirect(url_for('educator_dashboard'))
        
        learner_id = int(learner_id)
        game_id = int(game_id)
        
        learner = Learner.query.get(learner_id)
        if not learner:
            flash('Student not found.', 'error')
            return redirect(url_for('educator_dashboard'))
        
        if learner.grade != educator.grade_teaching:
            flash('This student is not in your grade.', 'error')
            return redirect(url_for('educator_dashboard'))
        
        game = Game.query.get(game_id)
        if not game:
            flash('Game not found.', 'error')
            return redirect(url_for('educator_dashboard'))
        
        existing = TestAssignment.query.filter_by(
            game_id=game_id,
            learner_id=learner_id,
            educator_id=educator.id,
            status='pending'
        ).first()
        
        if existing:
            flash('Test already assigned to this student', 'warning')
        else:
            assignment = TestAssignment(
                game_id=game_id,
                educator_id=educator.id,
                learner_id=learner_id,
                status='pending'
            )
            db.session.add(assignment)
            db.session.commit()
            flash('Test assigned successfully!', 'success')
        
    except ValueError as e:
        flash('Invalid student or game selection.', 'error')
        print(f"ValueError in assign_test: {e}")
    except Exception as e:
        db.session.rollback()
        flash(f'Error assigning test: {str(e)}', 'error')
        print(f"Error in assign_test: {e}")
    
    return redirect(url_for('educator_dashboard'))

# ==================== ASSESSMENT ROUTES ====================

# ==================== ASSESSMENT ROUTES ====================

@app.route('/educator/assess-learner/<int:learner_id>')
@login_required
def assess_learner(learner_id):
    """View assessment results for a learner"""
    if current_user.role != 'educator':
        flash('Access denied.', 'error')
        return redirect(url_for('login'))
    
    educator = Educator.query.filter_by(user_id=current_user.id).first()
    learner = Learner.query.get_or_404(learner_id)
    
    if learner.grade != educator.grade_teaching:
        flash('You do not have access to this learner.', 'error')
        return redirect(url_for('educator_dashboard'))
    
    try:
        from utils.cognitive_assessment import CognitiveAssessmentService
        
        assessment = CognitiveAssessmentService.analyze_learner_performance(learner.id)
        
        if not assessment:
            flash('Need at least 3 completed games for assessment.', 'warning')
            return redirect(url_for('educator_dashboard'))
        
        if assessment.get('status') == 'insufficient_data':
            flash(f'Need at least 3 completed games for assessment. Currently: {assessment.get("games_played")} games.', 'warning')
            return redirect(url_for('educator_dashboard'))
        
        return render_template('assessment_results.html',
                             learner=learner,
                             assessment=assessment)
                             
    except Exception as e:
        print(f"Assessment error: {e}")
        flash(f'Error running assessment: {str(e)}', 'error')
        return redirect(url_for('educator_dashboard'))
@app.route('/educator/run-assessment/<int:learner_id>')
@login_required
def run_assessment(learner_id):
    """Run a new assessment for a learner"""
    if current_user.role != 'educator':
        flash('Access denied.', 'error')
        return redirect(url_for('login'))
    
    educator = Educator.query.filter_by(user_id=current_user.id).first()
    learner = Learner.query.get_or_404(learner_id)
    
    if learner.grade != educator.grade_teaching:
        flash('You do not have access to this learner.', 'error')
        return redirect(url_for('educator_dashboard'))
    
    try:
        from utils.cognitive_assessment import CognitiveAssessmentService
        
        assessment = CognitiveAssessmentService.analyze_learner_performance(learner.id)
        
        if assessment and assessment.get('status') == 'insufficient_data':
            flash(f'Need at least 3 completed games for assessment. Currently: {assessment.get("games_played")} games.', 'warning')
            return redirect(url_for('educator_dashboard'))
        
        flash('Assessment completed successfully!', 'success')
        return redirect(url_for('assess_learner', learner_id=learner.id))
        
    except Exception as e:
        print(f"Run assessment error: {e}")
        flash(f'Error running assessment: {str(e)}', 'error')
        return redirect(url_for('educator_dashboard'))
@app.route('/educator/assign-disability-test/<int:learner_id>')
@login_required
def assign_test_for_learner(learner_id):
    """Show assignment page with disability-specific options"""
    if current_user.role != 'educator':
        flash('Access denied.', 'error')
        return redirect(url_for('login'))
    
    educator = Educator.query.filter_by(user_id=current_user.id).first()
    learner = Learner.query.get_or_404(learner_id)
    
    if learner.grade != educator.grade_teaching:
        flash('You do not have access to this learner.', 'error')
        return redirect(url_for('educator_dashboard'))
    
    disability_types = AIService.get_disability_types()
    disability_config = disability_types.get(learner.disability_type or 'none', {})
    features = disability_config.get('features', {})
    tips = disability_config.get('features', {}).get('tips', [])
    
    return render_template('assign_test_disability.html',
                         learner=learner,
                         features=features,
                         tips=tips)


@app.route('/educator/assign-disability-test', methods=['POST'])
@login_required
def assign_disability_test():
    """Generate and assign a disability-specific game"""
    if current_user.role != 'educator':
        flash('Access denied.', 'error')
        return redirect(url_for('login'))
    
    educator = Educator.query.filter_by(user_id=current_user.id).first()
    learner_id = request.form.get('learner_id')
    topic = request.form.get('topic', '').strip()
    game_type = request.form.get('game_type', 'memory')
    num_questions = int(request.form.get('num_questions', 10))
    
    learner = Learner.query.get_or_404(learner_id)
    
    if learner.grade != educator.grade_teaching:
        flash('You do not have access to this learner.', 'error')
        return redirect(url_for('educator_dashboard'))
    
    if not topic:
        flash('Please enter a topic.', 'error')
        return redirect(url_for('assign_test_for_learner', learner_id=learner.id))
    
    try:
        disability_type = learner.disability_type or 'none'
        game_data = AIService.generate_game_for_disability(
            topic, 
            learner.grade, 
            disability_type,
            game_type,
            num_questions
        )
        
        if not game_data or not game_data.get('questions'):
            flash('Failed to generate game. Please try again.', 'error')
            return redirect(url_for('assign_test_for_learner', learner_id=learner.id))
        
        questions = game_data.get('questions', [])
        for q in questions:
            if 'correct_answer' not in q or q['correct_answer'] == '':
                if 'options' in q and q['options']:
                    q['correct_answer'] = q['options'][0]
                else:
                    q['correct_answer'] = 'Not specified'
            if 'points' not in q:
                q['points'] = 2
        
        game = Game(
            name=game_data['name'],
            description=game_data['description'],
            category=game_data.get('category', game_type.capitalize()),
            difficulty=game_data.get('difficulty', 'Intermediate'),
            questions=json.dumps(game_data['questions']),
            passing_score=15,
            time_limit_minutes=game_data.get('time_limit', 10) or 10,
            is_latest=True,
            generated_at=datetime.utcnow(),
            grade_level=game_data.get('grade_level', learner.grade),
            subcategory=game_data.get('subcategory', disability_type),
            accessibility_features=json.dumps(game_data.get('accessibility_features', {})),
            visual_style=game_data.get('visual_style', 'default'),
            audio_support=game_data.get('audio_support', False),
            movement_breaks=game_data.get('movement_breaks', False),
            progress_tracking=game_data.get('progress_tracking', True),
            max_questions=len(game_data['questions']),
            disability_type=disability_type,
            recommended_for=disability_type
        )
        db.session.add(game)
        db.session.commit()
        
        assignment = TestAssignment(
            game_id=game.id,
            educator_id=educator.id,
            learner_id=learner.id,
            status='pending'
        )
        db.session.add(assignment)
        db.session.commit()
        
        flash(f'Disability-specific game "{game.name}" assigned to {learner.user.name}!', 'success')
        return redirect(url_for('educator_dashboard'))
        
    except Exception as e:
        print(f"Error: {e}")
        db.session.rollback()
        flash('An error occurred. Please try again.', 'error')
        return redirect(url_for('assign_test_for_learner', learner_id=learner.id))

# ==================== LEARNER ROUTES ====================

@app.route('/learner/dashboard')
@login_required
def learner_dashboard():
    if current_user.role != 'learner':
        return redirect(url_for('login'))
    
    learner = Learner.query.filter_by(user_id=current_user.id).first()
    if not learner:
        flash('Learner profile not found.', 'error')
        return redirect(url_for('index'))
    
    assignments = TestAssignment.query.filter_by(learner_id=learner.id).all()
    
    assignments_data = []
    completed_assignments = []
    passed_assignments = []
    
    for assignment in assignments:
        result = TestResult.query.filter_by(assignment_id=assignment.id).first()
        game = Game.query.get(assignment.game_id)
        
        assignment_data = {
            'assignment': assignment,
            'game': game,
            'result': result
        }
        assignments_data.append(assignment_data)
        
        if assignment.status == 'completed':
            completed_assignments.append(assignment_data)
            if result and result.passed:
                passed_assignments.append(assignment_data)
    
    return render_template('learner_dashboard.html',
                         learner=learner,
                         assignments=assignments_data,
                         completed_assignments=completed_assignments,
                         passed_assignments=passed_assignments)

@app.route('/test/start/<int:assignment_id>')
@login_required
def start_test(assignment_id):
    if current_user.role != 'learner':
        flash('Access denied.', 'error')
        return redirect(url_for('login'))
    
    assignment = TestAssignment.query.get_or_404(assignment_id)
    learner = Learner.query.filter_by(user_id=current_user.id).first()
    
    if assignment.learner_id != learner.id:
        flash('You do not have access to this test.', 'error')
        return redirect(url_for('learner_dashboard'))
    
    if assignment.status == 'pending':
        assignment.status = 'in_progress'
        assignment.started_at = datetime.utcnow()
        db.session.commit()
    
    game = Game.query.get(assignment.game_id)
    questions = json.loads(game.questions) if game.questions else []
    
    return render_template('take_test.html', 
                         assignment=assignment, 
                         game=game,
                         questions=questions)

@app.route('/test/submit/<int:assignment_id>', methods=['POST'])
@login_required
def submit_test(assignment_id):
    if current_user.role != 'learner':
        flash('Access denied.', 'error')
        return redirect(url_for('login'))
    
    assignment = TestAssignment.query.get_or_404(assignment_id)
    learner = Learner.query.filter_by(user_id=current_user.id).first()
    
    if assignment.learner_id != learner.id:
        flash('You do not have access to this test.', 'error')
        return redirect(url_for('learner_dashboard'))
    
    if assignment.status == 'completed':
        flash('Test already submitted.', 'warning')
        return redirect(url_for('learner_dashboard'))
    
    game = Game.query.get(assignment.game_id)
    questions = json.loads(game.questions) if game.questions else []
    
    score = 0
    total = len(questions)
    user_answers = []
    
    for i, question in enumerate(questions):
        user_answer = request.form.get(f'question_{i}')
        
        if user_answer is None:
            user_answer = request.form.get(f'q_{i}')
        if user_answer is None:
            user_answer = request.form.get(f'answer_{i}')
        if user_answer is None:
            user_answer = request.form.get(str(i))
        
        user_answers.append(user_answer or 'Not answered')
        
        correct_answer = question.get('correct_answer') or question.get('correct')
        if user_answer and correct_answer:
            user_answer = user_answer.strip()
            correct_answer = correct_answer.strip()
            
            if user_answer == correct_answer:
                score += 1
    
    percentage = (score / total * 100) if total > 0 else 0
    passed = percentage >= 50
    
    result = TestResult(
        assignment_id=assignment.id,
        score=score,
        percentage=percentage,
        passed=passed,
        answers=json.dumps(user_answers),
        completed_at=datetime.utcnow()
    )
    db.session.add(result)
    
    assignment.status = 'completed'
    assignment.completed_at = datetime.utcnow()
    
    db.session.commit()
    
    BadgeService.check_and_award_badges(learner)
    EmailService.send_game_completion_email(learner, game, percentage, passed)
    
    flash(f'Test submitted! Score: {score}/{total} ({percentage:.1f}%)', 'success')
    return redirect(url_for('test_results', result_id=result.id))

@app.route('/test/results/<int:result_id>')
@login_required
def test_results(result_id):
    result = TestResult.query.get_or_404(result_id)
    assignment = result.assignment
    game = assignment.game
    learner = assignment.learner
    educator = assignment.educator
    
    if current_user.role == 'learner' and learner.user_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('learner_dashboard'))
    elif current_user.role == 'educator':
        educator_user = Educator.query.filter_by(user_id=current_user.id).first()
        if assignment.educator_id != educator_user.id:
            flash('Access denied.', 'error')
            return redirect(url_for('educator_dashboard'))
    elif current_user.role == 'parent':
        parent = Parent.query.filter_by(user_id=current_user.id).first()
        if learner.parent_id != parent.id:
            flash('Access denied.', 'error')
            return redirect(url_for('parent_dashboard'))
    
    questions = json.loads(game.questions) if game.questions else []
    user_answers = json.loads(result.answers) if result.answers else []
    
    question_review = []
    for i, question in enumerate(questions):
        user_answer = user_answers[i] if i < len(user_answers) else 'Not answered'
        is_correct = user_answer == question.get('correct_answer')
        question_review.append({
            'number': i + 1,
            'question': question.get('question', ''),
            'user_answer': user_answer,
            'correct_answer': question.get('correct_answer', ''),
            'is_correct': is_correct
        })
    
    return render_template('test_results.html',
                         result=result,
                         assignment=assignment,
                         game=game,
                         learner=learner,
                         educator=educator,
                         question_review=question_review,
                         total_questions=len(questions))

@app.route('/learner/recommendations/<int:learner_id>')
@login_required
def view_learner_recommendations(learner_id):
    if current_user.role != 'educator':
        flash('Access denied. Educators only.', 'error')
        return redirect(url_for('login'))
    
    learner = Learner.query.get_or_404(learner_id)
    
    educator = Educator.query.filter_by(user_id=current_user.id).first()
    if not educator or learner.grade != educator.grade_teaching:
        flash('You do not have access to this learner\'s data.', 'error')
        return redirect(url_for('educator_dashboard'))
    
    assignments = TestAssignment.query.filter_by(learner_id=learner_id).all()
    completed_assignments = [a for a in assignments if a.status == 'completed']
    
    total_assigned = len(assignments)
    total_completed = len(completed_assignments)
    
    scores = []
    passed_count = 0
    game_performance = {}
    
    for assignment in completed_assignments:
        result = TestResult.query.filter_by(assignment_id=assignment.id).first()
        if result:
            scores.append(result.percentage)
            if result.passed:
                passed_count += 1
            
            game = assignment.game
            category = game.category if game else 'Unknown'
            if category not in game_performance:
                game_performance[category] = {'total': 0, 'passed': 0, 'scores': []}
            game_performance[category]['total'] += 1
            game_performance[category]['scores'].append(result.percentage)
            if result.passed:
                game_performance[category]['passed'] += 1
    
    avg_score = sum(scores) / len(scores) if scores else 0
    pass_rate = (passed_count / total_completed * 100) if total_completed > 0 else 0
    
    recommendations = generate_recommendations(
        learner=learner,
        total_completed=total_completed,
        avg_score=avg_score,
        pass_rate=pass_rate,
        game_performance=game_performance,
        total_assigned=total_assigned
    )
    
    return render_template('learner_recommendations.html',
                         learner=learner,
                         recommendations=recommendations,
                         total_assigned=total_assigned,
                         total_completed=total_completed,
                         avg_score=avg_score,
                         pass_rate=pass_rate,
                         game_performance=game_performance)

def generate_recommendations(learner, total_completed, avg_score, pass_rate, game_performance, total_assigned):
    """Generate AI-powered recommendations based on learner performance."""
    
    recommendations = {
        'overall': [],
        'strengths': [],
        'weaknesses': [],
        'suggested_games': [],
        'learning_tips': [],
        'priority': 'medium'
    }
    
    if total_completed == 0:
        recommendations['overall'].append({
            'level': 'info',
            'message': f'{learner.user.name} has not completed any games yet. Please encourage them to start with beginner-level games.'
        })
        recommendations['priority'] = 'high'
    elif pass_rate >= 80:
        recommendations['overall'].append({
            'level': 'success',
            'message': f'Excellent performance! {learner.user.name} is mastering the material with a {pass_rate:.0f}% pass rate.'
        })
        recommendations['priority'] = 'low'
    elif pass_rate >= 50:
        recommendations['overall'].append({
            'level': 'warning',
            'message': f'Good progress! {learner.user.name} has a {pass_rate:.0f}% pass rate. Consistent practice will help improve.'
        })
        recommendations['priority'] = 'medium'
    else:
        recommendations['overall'].append({
            'level': 'danger',
            'message': f'{learner.user.name} needs additional support with a {pass_rate:.0f}% pass rate. Consider reviewing concepts together.'
        })
        recommendations['priority'] = 'high'
    
    for category, data in game_performance.items():
        category_pass_rate = (data['passed'] / data['total'] * 100) if data['total'] > 0 else 0
        if category_pass_rate >= 70 and data['total'] >= 2:
            recommendations['strengths'].append({
                'category': category,
                'pass_rate': category_pass_rate,
                'games_played': data['total'],
                'message': f'Strong performance in {category} games ({category_pass_rate:.0f}% pass rate)'
            })
    
    for category, data in game_performance.items():
        category_pass_rate = (data['passed'] / data['total'] * 100) if data['total'] > 0 else 0
        if category_pass_rate < 50 and data['total'] >= 1:
            recommendations['weaknesses'].append({
                'category': category,
                'pass_rate': category_pass_rate,
                'games_played': data['total'],
                'message': f'Needs improvement in {category} games ({category_pass_rate:.0f}% pass rate)'
            })
    
    if total_completed > 0:
        all_games = Game.query.all()
        
        if pass_rate < 40:
            played_categories = list(game_performance.keys())
            for game in all_games:
                if game.category not in played_categories:
                    recommendations['suggested_games'].append({
                        'name': game.name,
                        'category': game.category,
                        'reason': 'Try this new category to build skills'
                    })
                    if len(recommendations['suggested_games']) >= 3:
                        break
            
            if not recommendations['suggested_games']:
                for game in all_games[:3]:
                    recommendations['suggested_games'].append({
                        'name': game.name,
                        'category': game.category,
                        'reason': 'Practice to build confidence'
                    })
                    
        elif pass_rate < 70:
            weak_categories = [w['category'] for w in recommendations['weaknesses']]
            for game in all_games:
                if game.category in weak_categories:
                    recommendations['suggested_games'].append({
                        'name': game.name,
                        'category': game.category,
                        'reason': f'Focus on {game.category} to improve weak areas'
                    })
                    if len(recommendations['suggested_games']) >= 3:
                        break
            
            if not recommendations['suggested_games']:
                for category, data in game_performance.items():
                    if data['total'] < 2:
                        for game in all_games:
                            if game.category == category:
                                recommendations['suggested_games'].append({
                                    'name': game.name,
                                    'category': game.category,
                                    'reason': f'Practice more in {category} to improve'
                                })
                                if len(recommendations['suggested_games']) >= 3:
                                    break
                                break
        else:
            strong_categories = [s['category'] for s in recommendations['strengths']]
            for game in all_games:
                if game.category in strong_categories:
                    recommendations['suggested_games'].append({
                        'name': game.name,
                        'category': game.category,
                        'reason': 'Challenge yourself with more in your strong areas'
                    })
                    if len(recommendations['suggested_games']) >= 3:
                        break
        
        if not recommendations['suggested_games']:
            for game in all_games[:3]:
                recommendations['suggested_games'].append({
                    'name': game.name,
                    'category': game.category,
                    'reason': 'Continue practicing to improve your skills'
                })
    
    if total_completed == 0:
        recommendations['learning_tips'] = [
            'Start with beginner-level games to build confidence',
            'Set aside 15-20 minutes daily for practice',
            'Review game instructions together before starting'
        ]
    elif pass_rate >= 80:
        recommendations['learning_tips'] = [
            'Introduce more challenging games to keep engaged',
            'Consider peer tutoring to reinforce learning',
            'Encourage teaching concepts to others'
        ]
    elif pass_rate >= 50:
        recommendations['learning_tips'] = [
            'Practice 20-30 minutes daily to improve scores',
            'Focus on games with lower scores',
            'Use the "Review" feature after each game'
        ]
    else:
        recommendations['learning_tips'] = [
            'Work together on game instructions',
            'Break games into smaller sessions',
            'Celebrate small wins to build confidence',
            'Try simpler versions of the games first'
        ]
    
    return recommendations

# ==================== PARENT ROUTES ====================

@app.route('/parent/dashboard')
@login_required
def parent_dashboard():
    if current_user.role != 'parent':
        return redirect(url_for('login'))
    
    parent = Parent.query.filter_by(user_id=current_user.id).first()
    learners = Learner.query.filter_by(parent_id=parent.id).all()
    
    learners_data = []
    for learner in learners:
        assignments = TestAssignment.query.filter_by(learner_id=learner.id).all()
        total_games = len(assignments)
        completed_games = len([a for a in assignments if a.status == 'completed'])
        
        scores = []
        for a in assignments:
            if a.status == 'completed':
                result = TestResult.query.filter_by(assignment_id=a.id).first()
                if result:
                    scores.append(result.percentage)
        
        avg_score = sum(scores) / len(scores) if scores else 0
        
        learners_data.append({
            'learner': learner,
            'total_games': total_games,
            'completed_games': completed_games,
            'average_score': avg_score,
            'games_played': completed_games
        })
    
    return render_template('parent_dashboard.html', learners_data=learners_data)

@app.route('/parent/add-learner', methods=['POST'])
@login_required
def parent_add_learner():
    if current_user.role != 'parent':
        flash('Access denied', 'error')
        return redirect(url_for('login'))
    
    name = request.form.get('name')
    email = request.form.get('email')
    id_number = request.form.get('id_number')
    grade = int(request.form.get('grade'))
    
    parent = Parent.query.filter_by(user_id=current_user.id).first()
    
    if User.query.filter_by(email=email).first():
        flash('Email already registered', 'error')
        return redirect(url_for('parent_dashboard'))
    
    is_valid, result = validate_rsa_id(id_number)
    if not is_valid:
        flash(result, 'error')
        return redirect(url_for('parent_dashboard'))
    
    date_of_birth = result
    age = calculate_age(date_of_birth)
    
    if Learner.query.filter_by(id_number=id_number).first():
        flash('ID number already registered', 'error')
        return redirect(url_for('parent_dashboard'))
    
    def generate_code():
        return ''.join(random.choices(string.digits, k=6))
    
    login_code = generate_code()
    while Learner.query.filter_by(login_code=login_code).first():
        login_code = generate_code()
    
    user = User(email=email, name=name, role='learner')
    user.set_password(login_code)
    db.session.add(user)
    db.session.flush()
    
    learner = Learner(
        user_id=user.id,
        email=email,
        id_number=id_number,
        date_of_birth=date_of_birth,
        age=age,
        grade=grade,
        parent_id=parent.id,
        login_code=login_code
    )
    db.session.add(learner)
    db.session.commit()
    
    return render_template('learner_code_display.html', 
                           login_code=login_code, 
                           learner_name=name, 
                           grade=grade)

@app.route('/parent/learner-progress/<int:learner_id>')
@login_required
def view_learner_progress(learner_id):
    if current_user.role not in ['parent', 'educator']:
        flash('Access denied', 'error')
        return redirect(url_for('login'))
    
    learner = Learner.query.get_or_404(learner_id)
    
    if current_user.role == 'parent':
        parent = Parent.query.filter_by(user_id=current_user.id).first()
        if learner.parent_id != parent.id:
            flash('Access denied', 'error')
            return redirect(url_for('parent_dashboard'))
    elif current_user.role == 'educator':
        educator = Educator.query.filter_by(user_id=current_user.id).first()
        if learner.grade != educator.grade_teaching:
            flash('Access denied', 'error')
            return redirect(url_for('educator_dashboard'))
    
    assignments = TestAssignment.query.filter_by(learner_id=learner.id).all()
    assignments_data = []
    
    for assignment in assignments:
        result = TestResult.query.filter_by(assignment_id=assignment.id).first()
        game = Game.query.get(assignment.game_id)
        assignments_data.append({
            'assignment': assignment,
            'game': game,
            'result': result
        })
    
    return render_template('view_learner_progress.html', 
                         learner=learner, 
                         assignments=assignments_data)

# ==================== ANALYTICS ROUTE ====================

@app.route('/analytics')
@login_required
def analytics_dashboard():
    if current_user.role != 'educator':
        flash('Access denied.', 'error')
        return redirect(url_for('index'))
    
    educator = Educator.query.filter_by(user_id=current_user.id).first()
    learners = Learner.query.filter_by(grade=educator.grade_teaching).all()
    
    learner_ids = [l.id for l in learners]
    assignments = TestAssignment.query.filter(
        TestAssignment.learner_id.in_(learner_ids),
        TestAssignment.status == 'completed'
    ).all()
    
    scores = []
    for a in assignments:
        result = TestResult.query.filter_by(assignment_id=a.id).first()
        if result:
            scores.append(result.percentage)
    
    avg_score = sum(scores) / len(scores) if scores else 0
    
    if len(scores) > 5:
        recent = scores[-3:]
        previous = scores[-6:-3]
        if recent and previous:
            avg_recent = sum(recent) / len(recent)
            avg_previous = sum(previous) / len(previous)
            if avg_recent > avg_previous + 5:
                trend = 'up'
            elif avg_recent < avg_previous - 5:
                trend = 'down'
            else:
                trend = 'steady'
        else:
            trend = 'steady'
    else:
        trend = 'steady'
    
    passed = [s for s in scores if s >= 50]
    pass_rate = len(passed) / len(scores) * 100 if scores else 0
    
    stats = {
        'total_learners': len(learners),
        'total_games': len(scores),
        'avg_score': avg_score,
        'trend': trend,
        'pass_rate': round(pass_rate, 1)
    }
    
    chart_data = {
        'dates': [f'Day {i+1}' for i in range(min(len(scores), 10))],
        'scores': scores[-10:] if scores else [0],
        'categories': ['Memory', 'Attention', 'Math', 'Problem Solving'],
        'category_scores': [75, 68, 82, 70],
        'top_performers_names': [],
        'top_performers_scores': [],
        'weekly_days': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        'weekly_activity': [5, 8, 6, 7, 9, 3, 4]
    }
    
    return render_template('analytics_dashboard.html', 
                         stats=stats, 
                         chart_data=chart_data)

# ==================== LEADERBOARD ROUTE ====================

@app.route('/leaderboard')
@login_required
def leaderboard():
    if current_user.role != 'educator':
        flash('Access denied.', 'error')
        return redirect(url_for('index'))
    
    grade = request.args.get('grade', '2')
    
    learners = Learner.query.filter_by(grade=int(grade)).all()
    
    leaderboard_data = []
    for learner in learners:
        assignments = TestAssignment.query.filter_by(
            learner_id=learner.id,
            status='completed'
        ).all()
        
        scores = []
        for a in assignments:
            result = TestResult.query.filter_by(assignment_id=a.id).first()
            if result:
                scores.append(result.percentage)
        
        if scores:
            avg_score = sum(scores) / len(scores)
            leaderboard_data.append({
                'name': learner.user.name,
                'avg_score': avg_score,
                'games_played': len(scores),
                'badges': learner.badge_count if hasattr(learner, 'badge_count') else 0
            })
    
    leaderboard_data.sort(key=lambda x: x['avg_score'], reverse=True)
    
    grades = [1, 2, 3]
    
    return render_template('leaderboard.html', 
                         leaderboard_data=leaderboard_data,
                         current_grade=int(grade),
                         grades=grades)

# ==================== AI GAME GENERATOR ROUTES ====================

@app.route('/ai/generate-game', methods=['GET', 'POST'])
@login_required
def ai_generate_game():
    """Generate a new game using AI with accessibility features"""
    if current_user.role != 'educator':
        flash('Access denied.', 'error')
        return redirect(url_for('index'))
    
    generated_game = None
    
    if request.method == 'POST':
        topic = request.form.get('topic', '').strip()
        grade = int(request.form.get('grade', 2))
        access_type = request.form.get('access_type', 'default')
        game_type = request.form.get('game_type', 'default')
        num_questions = int(request.form.get('num_questions', 10))
        
        if not topic:
            flash('Please enter a topic for the game.', 'error')
            return redirect(url_for('ai_generate_game'))
        
        try:
            game_data = AIService.generate_game(topic, grade, access_type, num_questions)
            
            if not game_data or not game_data.get('questions'):
                flash('Failed to generate game. Please try again.', 'error')
                return redirect(url_for('ai_generate_game'))
            
            questions = game_data.get('questions', [])
            for q in questions:
                if 'correct_answer' not in q or q['correct_answer'] == '':
                    if 'options' in q and q['options']:
                        q['correct_answer'] = q['options'][0]
                    else:
                        q['correct_answer'] = 'Not specified'
                if 'points' not in q:
                    q['points'] = 2
            
            Game.query.update({Game.is_latest: False})
            
            game = Game(
                name=game_data['name'],
                description=game_data['description'],
                category=game_data.get('category', game_type.capitalize()),
                difficulty=game_data.get('difficulty', 'Intermediate'),
                questions=json.dumps(game_data['questions']),
                passing_score=15,
                time_limit_minutes=game_data.get('time_limit', 10) or 10,
                is_latest=True,
                generated_at=datetime.utcnow(),
                grade_level=game_data.get('grade_level', grade),
                subcategory=game_data.get('subcategory', access_type),
                accessibility_features=json.dumps(game_data.get('accessibility_features', {})),
                visual_style=game_data.get('visual_style', 'default'),
                audio_support=game_data.get('audio_support', False),
                movement_breaks=game_data.get('movement_breaks', False),
                progress_tracking=game_data.get('progress_tracking', True),
                max_questions=len(game_data['questions'])
            )
            db.session.add(game)
            db.session.commit()
            
            game_data['id'] = game.id
            
            flash(f'Game "{game.name}" created successfully!', 'success')
            return render_template('ai_generate_game.html', generated_game=game_data)
            
        except Exception as e:
            print(f"Game generation error: {e}")
            db.session.rollback()
            flash('An error occurred while generating the game. Please try again.', 'error')
            return redirect(url_for('ai_generate_game'))
    
    return render_template('ai_generate_game.html', generated_game=None)


@app.route('/game/<int:game_id>')
@login_required
def view_game(game_id):
    """View a specific game"""
    game = Game.query.get_or_404(game_id)
    questions = json.loads(game.questions) if game.questions else []
    
    students = []
    if current_user.role == 'educator':
        educator = Educator.query.filter_by(user_id=current_user.id).first()
        if educator:
            students = Learner.query.filter_by(grade=educator.grade_teaching).all()
            for student in students:
                assignments = TestAssignment.query.filter_by(
                    learner_id=student.id,
                    status='completed'
                ).all()
                student.completed_count = len(assignments)
    
    return render_template('view_game.html', 
                         game=game, 
                         questions=questions,
                         students=students)


@app.route('/game/assign/<int:game_id>', methods=['POST'])
@login_required
def assign_ai_game(game_id):
    """Assign an AI-generated game to selected students"""
    if current_user.role != 'educator':
        flash('Access denied.', 'error')
        return redirect(url_for('index'))
    
    try:
        educator = Educator.query.filter_by(user_id=current_user.id).first()
        if not educator:
            flash('Educator profile not found.', 'error')
            return redirect(url_for('educator_dashboard'))
        
        game = Game.query.get_or_404(game_id)
        
        student_ids = request.form.getlist('student_ids')
        
        if not student_ids:
            flash('Please select at least one student.', 'warning')
            return redirect(url_for('view_game', game_id=game_id))
        
        student_ids = [int(id) for id in student_ids if id]
        
        assigned_count = 0
        already_assigned = 0
        
        for student_id in student_ids:
            learner = Learner.query.get(student_id)
            if not learner:
                continue
            
            if learner.grade != educator.grade_teaching:
                continue
            
            existing = TestAssignment.query.filter_by(
                game_id=game.id,
                learner_id=student_id,
                educator_id=educator.id,
                status='pending'
            ).first()
            
            if existing:
                already_assigned += 1
                continue
            
            assignment = TestAssignment(
                game_id=game.id,
                learner_id=student_id,
                educator_id=educator.id,
                status='pending'
            )
            db.session.add(assignment)
            assigned_count += 1
        
        db.session.commit()
        
        if assigned_count > 0:
            flash(f'Game "{game.name}" assigned to {assigned_count} student(s)!', 'success')
        if already_assigned > 0:
            flash(f'{already_assigned} student(s) already had this game assigned.', 'info')
        if assigned_count == 0 and already_assigned == 0:
            flash('No students were assigned. Please select valid students.', 'warning')
        
    except ValueError as e:
        flash('Invalid student selection.', 'error')
        print(f"ValueError in assign_ai_game: {e}")
    except Exception as e:
        db.session.rollback()
        flash(f'Error assigning game: {str(e)}', 'error')
        print(f"Error in assign_ai_game: {e}")
    
    return redirect(url_for('view_game', game_id=game_id))


@app.route('/game/enhance/<int:game_id>')
@login_required
def enhance_game(game_id):
    """Enhance an existing game using AI"""
    if current_user.role != 'educator':
        flash('Access denied.', 'error')
        return redirect(url_for('index'))
    
    game = Game.query.get_or_404(game_id)
    
    game_data = {
        'name': game.name,
        'description': game.description,
        'category': game.category,
        'questions': json.loads(game.questions) if game.questions else []
    }
    
    enhanced = AIService.enhance_game(game_data)
    
    if enhanced and enhanced.get('questions'):
        game.name = enhanced.get('name', game.name)
        game.description = enhanced.get('description', game.description)
        game.questions = json.dumps(enhanced['questions'])
        db.session.commit()
        flash(f'Game "{game.name}" enhanced successfully!', 'success')
    else:
        flash('Could not enhance game. Please try again.', 'warning')
    
    return redirect(url_for('view_game', game_id=game_id))


@app.route('/game/latest')
@login_required
def view_latest_game():
    """View the latest generated game"""
    if current_user.role != 'educator':
        flash('Access denied.', 'error')
        return redirect(url_for('index'))
    
    game = Game.query.filter_by(is_latest=True).first()
    
    if not game:
        flash('No games have been generated yet. Generate a game first!', 'warning')
        return redirect(url_for('ai_generate_game'))
    
    return redirect(url_for('view_game', game_id=game.id))


# ==================== AI ANALYSIS ROUTE ====================

@app.route('/ai/analysis')
@login_required
def ai_analysis():
    if current_user.role != 'learner':
        flash('AI analysis is only available for learners', 'warning')
        return redirect(url_for('learner_dashboard'))
    
    learner = Learner.query.filter_by(user_id=current_user.id).first()
    if not learner:
        flash('Learner profile not found', 'error')
        return redirect(url_for('learner_dashboard'))
    
    assignments = TestAssignment.query.filter_by(learner_id=learner.id).all()
    completed = [a for a in assignments if a.status == 'completed']
    
    analysis = {
        'total_games': len(assignments),
        'completed_games': len(completed),
        'pending_games': len([a for a in assignments if a.status == 'pending']),
        'in_progress': len([a for a in assignments if a.status == 'in_progress'])
    }
    
    scores = []
    for a in completed:
        result = TestResult.query.filter_by(assignment_id=a.id).first()
        if result:
            scores.append(result.percentage)
    
    analysis['average_score'] = sum(scores) / len(scores) if scores else 0
    analysis['best_score'] = max(scores) if scores else 0
    
    return render_template('ai_analysis.html', learner=learner, analysis=analysis)


# ==================== GAME ROUTES ====================

@app.route('/game/penguin-says')
@login_required
def penguin_says_game():
    if current_user.role != 'learner':
        return redirect(url_for('login'))
    return render_template('game_penguin_says.html')

@app.route('/game/red-light')
@login_required
def red_light_game():
    if current_user.role != 'learner':
        return redirect(url_for('login'))
    return render_template('game_red_light.html')

@app.route('/game/memory-match')
@login_required
def memory_match_game():
    if current_user.role != 'learner':
        return redirect(url_for('login'))
    return render_template('game_memory_match.html')

@app.route('/game/save-result', methods=['POST'])
@login_required
def save_game_result():
    if current_user.role != 'learner':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    learner = Learner.query.filter_by(user_id=current_user.id).first()
    
    game = Game.query.filter_by(name=data.get('game_name')).first()
    if not game:
        return jsonify({'error': 'Game not found'}), 404
    
    existing_assignment = TestAssignment.query.filter_by(
        learner_id=learner.id,
        game_id=game.id
    ).first()
    
    if existing_assignment and existing_assignment.status == 'completed':
        return jsonify({'success': True, 'message': 'Already completed'})
    
    if not existing_assignment:
        assignment = TestAssignment(
            game_id=game.id,
            learner_id=learner.id,
            status='completed',
            completed_at=datetime.utcnow()
        )
        db.session.add(assignment)
        db.session.flush()
        
        total_points = len(json.loads(game.questions)) * 2 if game.questions else 30
        earned_points = int((data.get('percentage', 0) / 100) * total_points)
        
        result = TestResult(
            assignment_id=assignment.id,
            score=earned_points,
            percentage=data.get('percentage', 0),
            passed=data.get('passed', False),
            answers=json.dumps(['game']),
            completed_at=datetime.utcnow()
        )
        db.session.add(result)
        db.session.commit()
    else:
        existing_assignment.status = 'completed'
        existing_assignment.completed_at = datetime.utcnow()
        db.session.commit()
    
    return jsonify({'success': True})

# ==================== AI ROUTES ====================

@app.route('/ai/recommendations/<int:learner_id>')
@login_required
def ai_recommendations(learner_id):
    """Get AI-powered recommendations for a learner"""
    
    if current_user.role not in ['educator', 'parent']:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    learner = Learner.query.get_or_404(learner_id)
    
    if current_user.role == 'educator':
        educator = Educator.query.filter_by(user_id=current_user.id).first()
        if learner.grade != educator.grade_teaching:
            flash('Access denied', 'error')
            return redirect(url_for('educator_dashboard'))
    
    elif current_user.role == 'parent':
        parent = Parent.query.filter_by(user_id=current_user.id).first()
        if learner.parent_id != parent.id:
            flash('Access denied', 'error')
            return redirect(url_for('parent_dashboard'))
    
    assignments = TestAssignment.query.filter_by(learner_id=learner.id).all()
    completed = [a for a in assignments if a.status == 'completed']
    
    scores = []
    past_scores = []
    game_history = []
    
    for a in completed:
        result = TestResult.query.filter_by(assignment_id=a.id).first()
        if result:
            scores.append(result.percentage)
            past_scores.append(result.percentage)
            game = Game.query.get(a.game_id)
            if game:
                game_history.append({
                    'name': game.name,
                    'score': result.percentage
                })
    
    avg_score = sum(scores) / len(scores) if scores else 0
    
    past_scores = past_scores[::-1]
    
    learner_data = {
        'name': learner.user.name,
        'grade': learner.grade,
        'avg_score': avg_score,
        'games_completed': len(completed),
        'strengths': 'Good at memory and attention' if avg_score > 70 else 'Developing skills',
        'weaknesses': 'Needs practice with problem solving' if avg_score < 60 else 'Keep building on strengths',
        'past_scores': past_scores,
        'game_history': game_history
    }
    
    recommendations = AIService.get_recommendations(learner_data)
    
    if not recommendations:
        flash('AI service temporarily unavailable. Please try again later.', 'warning')
        return redirect(url_for('view_learner_progress', learner_id=learner.id))
    
    return render_template('ai_recommendations.html',
                         learner=learner,
                         recommendations=recommendations,
                         avg_score=avg_score)


@app.route('/ai/chat', methods=['POST'])
@login_required
def ai_chat():
    """AI Chatbot for learners"""
    if current_user.role != 'learner':
        return jsonify({'error': 'Access denied'}), 403
    
    question = request.form.get('question')
    if not question:
        return jsonify({'error': 'Please ask a question'}), 400
    
    learner = Learner.query.filter_by(user_id=current_user.id).first()
    context = f"Learner in Grade {learner.grade}"
    
    response = AIService.get_chat_response(question, context)
    
    return jsonify({'response': response})


@app.route('/ai/learning-path/<int:learner_id>')
@login_required
def ai_learning_path(learner_id):
    """Generate a personalized learning path"""
    if current_user.role not in ['educator', 'parent']:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    learner = Learner.query.get_or_404(learner_id)
    
    assignments = TestAssignment.query.filter_by(learner_id=learner.id).all()
    completed = [a for a in assignments if a.status == 'completed']
    
    scores = []
    for a in completed:
        result = TestResult.query.filter_by(assignment_id=a.id).first()
        if result:
            scores.append(result.percentage)
    
    avg_score = sum(scores) / len(scores) if scores else 0
    
    learner_data = {
        'name': learner.user.name,
        'grade': learner.grade,
        'avg_score': avg_score,
        'games_completed': len(completed)
    }
    
    games = Game.query.all()
    curriculum = [{'name': g.name, 'category': g.category} for g in games]
    
    learning_path = AIService.generate_learning_path(learner_data, curriculum)
    
    if not learning_path:
        flash('AI service temporarily unavailable. Please try again later.', 'warning')
        return redirect(url_for('view_learner_progress', learner_id=learner.id))
    
    return render_template('ai_learning_path.html',
                         learner=learner,
                         learning_path=learning_path)


@app.route('/ai/chatbot')
@login_required
def ai_chatbot():
    """AI Chatbot page for learners"""
    if current_user.role != 'learner':
        flash('This page is for learners only.', 'warning')
        return redirect(url_for('index'))
    
    learner = Learner.query.filter_by(user_id=current_user.id).first()
    if not learner:
        flash('Learner profile not found.', 'error')
        return redirect(url_for('learner_dashboard'))
    
    return render_template('ai_chatbot.html', learner=learner)


@app.route('/educator/ai-chat', methods=['POST'])
@login_required
def educator_ai_chat():
    """AI Chat for Educators - Game Recommendations"""
    
    if current_user.role != 'educator':
        return jsonify({'error': 'Access denied'}), 403
    
    question = request.form.get('question')
    if not question:
        return jsonify({'error': 'Please ask a question'}), 400
    
    educator = Educator.query.filter_by(user_id=current_user.id).first()
    if not educator:
        return jsonify({'error': 'Educator profile not found'}), 404
    
    learners = Learner.query.filter_by(grade=educator.grade_teaching).all()
    
    learners_data = []
    for learner in learners:
        assignments = TestAssignment.query.filter_by(learner_id=learner.id).all()
        completed = [a for a in assignments if a.status == 'completed']
        
        scores = []
        weak_skills = []
        strong_skills = []
        completed_games = []
        
        for a in completed:
            result = TestResult.query.filter_by(assignment_id=a.id).first()
            if result:
                scores.append(result.percentage)
                game = Game.query.get(a.game_id)
                if game:
                    completed_games.append(game.name)
        
        avg_score = sum(scores) / len(scores) if scores else 0
        
        learners_data.append({
            'name': learner.user.name,
            'grade': learner.grade,
            'avg_score': avg_score,
            'weak_skills': weak_skills,
            'strong_skills': strong_skills,
            'completed_games': completed_games
        })
    
    response = AIService.get_educator_recommendations(question, educator, learners_data)
    
    return jsonify({'response': response})


@app.route('/educator/ai-chat-page')
@login_required
def educator_ai_chat_page():
    """Educator AI Chat Page"""
    if current_user.role != 'educator':
        flash('Access denied.', 'error')
        return redirect(url_for('login'))
    
    educator = Educator.query.filter_by(user_id=current_user.id).first()
    if not educator:
        flash('Educator profile not found.', 'error')
        return redirect(url_for('educator_dashboard'))
    
    learners = Learner.query.filter_by(grade=educator.grade_teaching).all()
    
    return render_template('educator_chatbot.html', learners=learners)


# ==================== RUN THE APP ====================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('RENDER', 'false').lower() != 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=port)