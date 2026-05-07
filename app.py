import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Admin, Educator, Parent, Learner, Game, TestAssignment, TestResult
from utils.games_data import get_all_games
from utils.validators import validate_rsa_id, calculate_age, validate_learner_age, determine_grade_from_age
from datetime import datetime
import json

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__)

# Database configuration for PostgreSQL on Render
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    # Fix for PostgreSQL URL (Render uses postgres:// not postgresql://)
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('RENDER', 'false').lower() == 'true'
app.config['REMEMBER_COOKIE_SECURE'] = os.environ.get('RENDER', 'false').lower() == 'true'

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Custom Jinja2 filter
@app.template_filter('fromjson')
def from_json_filter(value):
    if value:
        try:
            return json.loads(value)
        except:
            return []
    return []

# Initialize database with app context
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
                time_limit_minutes=60
            )
            db.session.add(game)
    
    db.session.commit()
    print(f"Database initialized with {len(games_data)} games")

# ==================== AUTHENTICATION ROUTES ====================

@app.route('/')
def index():
    games_count = Game.query.count()
    return render_template('index.html', games_count=games_count)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email_or_id = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        
        user = User.query.filter_by(email=email_or_id).first()
        
        if not user and role == 'learner':
            learner = Learner.query.filter_by(id_number=email_or_id).first()
            if learner:
                user = learner.user
        
        if user and user.check_password(password) and user.role == role:
            login_user(user)
            
            if role == 'educator':
                return redirect(url_for('educator_dashboard'))
            elif role == 'parent':
                return redirect(url_for('parent_dashboard'))
            elif role == 'learner':
                return redirect(url_for('learner_dashboard'))
            elif role == 'admin':
                return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials or role mismatch', 'error')
    
    return render_template('login.html')

@app.route('/register/educator', methods=['GET', 'POST'])
def register_educator():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        grade = int(request.form.get('grade'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('register_educator'))
        
        user = User(email=email, name=name, role='educator')
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        
        educator = Educator(user_id=user.id, phone_number=phone, grade_teaching=grade)
        db.session.add(educator)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register_educator.html')

@app.route('/register/parent', methods=['GET', 'POST'])
def register_parent():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        id_number = request.form.get('id_number')
        password = request.form.get('password')
        
        is_valid, result = validate_rsa_id(id_number)
        if not is_valid:
            flash(result, 'error')
            return redirect(url_for('register_parent'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('register_parent'))
        
        if Parent.query.filter_by(id_number=id_number).first():
            flash('ID number already registered', 'error')
            return redirect(url_for('register_parent'))
        
        user = User(email=email, name=name, role='parent')
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        
        parent = Parent(user_id=user.id, id_number=id_number)
        db.session.add(parent)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register_parent.html')

@app.route('/register/learner', methods=['GET', 'POST'])
def register_learner():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        id_number = request.form.get('id_number')
        grade = int(request.form.get('grade'))
        parent_id_number = request.form.get('parent_id')
        password = request.form.get('password')
        
        if not email or '@' not in email:
            flash('Please enter a valid email address', 'error')
            return redirect(url_for('register_learner'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('register_learner'))
        
        if grade not in [1, 2, 3]:
            flash('Please select a valid grade (1-3)', 'error')
            return redirect(url_for('register_learner'))
        
        is_valid, result = validate_rsa_id(id_number)
        if not is_valid:
            flash(result, 'error')
            return redirect(url_for('register_learner'))
        
        date_of_birth = result
        age = calculate_age(date_of_birth)
        
        is_valid_age, age_message = validate_learner_age(age)
        if not is_valid_age:
            flash(age_message, 'error')
            return redirect(url_for('register_learner'))
        
        parent = Parent.query.filter_by(id_number=parent_id_number).first()
        if not parent:
            flash('Parent ID number not found', 'error')
            return redirect(url_for('register_learner'))
        
        if Learner.query.filter_by(id_number=id_number).first():
            flash('ID number already registered', 'error')
            return redirect(url_for('register_learner'))
        
        user = User(email=email, name=name, role='learner')
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        
        learner = Learner(
            user_id=user.id,
            email=email,
            id_number=id_number,
            date_of_birth=date_of_birth,
            age=age,
            grade=grade,
            parent_id=parent.id
        )
        db.session.add(learner)
        db.session.commit()
        
        flash(f'Registration successful! Age: {age}, Grade: {grade}', 'success')
        return redirect(url_for('login'))
    
    return render_template('register_learner.html')

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
            user.address = request.form.get('address')
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
            user.address = request.form.get('address')
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
            user.address = request.form.get('address')
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
            user.address = request.form.get('address')
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
                assignments = TestAssignment.query.filter_by(learner_id=learner.id).all()
                for assignment in assignments:
                    TestResult.query.filter_by(assignment_id=assignment.id).delete()
                    db.session.delete(assignment)
                db.session.delete(learner)
        elif user.role == 'parent':
            parent = Parent.query.filter_by(user_id=user.id).first()
            if parent:
                learners = Learner.query.filter_by(parent_id=parent.id).all()
                for learner in learners:
                    assignments = TestAssignment.query.filter_by(learner_id=learner.id).all()
                    for assignment in assignments:
                        TestResult.query.filter_by(assignment_id=assignment.id).delete()
                        db.session.delete(assignment)
                    db.session.delete(learner)
                db.session.delete(parent)
        elif user.role == 'educator':
            educator = Educator.query.filter_by(user_id=user.id).first()
            if educator:
                assignments = TestAssignment.query.filter_by(educator_id=educator.id).all()
                for assignment in assignments:
                    db.session.delete(assignment)
                db.session.delete(educator)
        
        db.session.delete(user)
        db.session.commit()
        flash(f'User {user.name} deleted', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('admin_users'))

# ==================== EDUCATOR ROUTES ====================

@app.route('/educator/dashboard')
@login_required
def educator_dashboard():
    if current_user.role != 'educator':
        return redirect(url_for('login'))
    
    educator = Educator.query.filter_by(user_id=current_user.id).first()
    learners = Learner.query.filter_by(grade=educator.grade_teaching).all()
    assignments = TestAssignment.query.filter_by(educator_id=educator.id).all()
    games = Game.query.all()
    
    assignments_with_results = []
    for assignment in assignments:
        result = TestResult.query.filter_by(assignment_id=assignment.id).first()
        assignments_with_results.append({
            'assignment': assignment,
            'result': result
        })
    
    return render_template('educator_dashboard.html', 
                         educator=educator,
                         learners=learners, 
                         assignments=assignments_with_results,
                         games=games)

@app.route('/educator/assign_test', methods=['POST'])
@login_required
def assign_test():
    if current_user.role != 'educator':
        flash('Unauthorized', 'error')
        return redirect(url_for('login'))
    
    educator = Educator.query.filter_by(user_id=current_user.id).first()
    learner_id = request.form.get('learner_id')
    game_id = request.form.get('game_id')
    
    existing = TestAssignment.query.filter_by(
        game_id=game_id,
        learner_id=learner_id,
        educator_id=educator.id,
        status='pending'
    ).first()
    
    if existing:
        flash('Test already assigned', 'warning')
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
    
    return redirect(url_for('educator_dashboard'))

# ==================== LEARNER ROUTES ====================

@app.route('/learner/dashboard')
@login_required
def learner_dashboard():
    if current_user.role != 'learner':
        return redirect(url_for('login'))
    
    learner = Learner.query.filter_by(user_id=current_user.id).first()
    assignments = TestAssignment.query.filter_by(learner_id=learner.id).all()
    
    available_tests = []
    completed_tests = []
    
    for assignment in assignments:
        game = Game.query.get(assignment.game_id)
        result = TestResult.query.filter_by(assignment_id=assignment.id).first()
        
        if result:
            completed_tests.append({
                'assignment': assignment,
                'game': game,
                'result': result
            })
        else:
            if assignment.status == 'in_progress' and assignment.started_at:
                time_elapsed = (datetime.utcnow() - assignment.started_at).total_seconds()
                if time_elapsed > 3600:
                    assignment.status = 'expired'
                    db.session.commit()
                    continue
            
            available_tests.append({
                'assignment': assignment,
                'game': game
            })
    
    return render_template('learner_dashboard.html', 
                         learner=learner,
                         available_tests=available_tests,
                         completed_tests=completed_tests)

@app.route('/test/start/<int:assignment_id>')
@login_required
def start_test(assignment_id):
    if current_user.role != 'learner':
        return redirect(url_for('login'))
    
    assignment = TestAssignment.query.get_or_404(assignment_id)
    learner = Learner.query.filter_by(user_id=current_user.id).first()
    
    if assignment.learner_id != learner.id:
        flash('This test is not assigned to you', 'error')
        return redirect(url_for('learner_dashboard'))
    
    if assignment.status == 'completed':
        flash('You have already completed this test', 'warning')
        return redirect(url_for('learner_dashboard'))
    
    if assignment.status == 'expired':
        flash('This test has expired', 'error')
        return redirect(url_for('learner_dashboard'))
    
    if assignment.status == 'pending':
        assignment.status = 'in_progress'
        assignment.started_at = datetime.utcnow()
        db.session.commit()
    
    game = Game.query.get(assignment.game_id)
    questions = json.loads(game.questions)
    
    return render_template('take_test.html', 
                         assignment=assignment, 
                         game=game, 
                         questions=questions)

@app.route('/test/submit/<int:assignment_id>', methods=['POST'])
@login_required
def submit_test(assignment_id):
    if current_user.role != 'learner':
        return redirect(url_for('login'))
    
    assignment = TestAssignment.query.get_or_404(assignment_id)
    learner = Learner.query.filter_by(user_id=current_user.id).first()
    
    if assignment.learner_id != learner.id:
        flash('Unauthorized', 'error')
        return redirect(url_for('learner_dashboard'))
    
    if assignment.status == 'completed':
        flash('Test already submitted', 'warning')
        return redirect(url_for('learner_dashboard'))
    
    game = Game.query.get(assignment.game_id)
    questions = json.loads(game.questions)
    
    total_points = 0
    earned_points = 0
    user_answers = []
    
    for i, question in enumerate(questions):
        points = question.get('points', 2)
        total_points += points
        
        user_answer = request.form.get(f'question_{i}')
        user_answers.append(user_answer or 'Not answered')
        
        if user_answer == question['correct']:
            earned_points += points
    
    percentage = (earned_points / total_points) * 100
    passed = percentage >= 50
    
    result = TestResult(
        assignment_id=assignment.id,
        score=earned_points,
        percentage=percentage,
        passed=passed,
        answers=json.dumps(user_answers)
    )
    
    assignment.status = 'completed'
    assignment.completed_at = datetime.utcnow()
    
    db.session.add(result)
    db.session.commit()
    
    flash(f'Test submitted! Score: {earned_points}/{total_points} ({percentage:.1f}%)', 'success')
    return redirect(url_for('test_results', result_id=result.id))

@app.route('/test/results/<int:result_id>')
@login_required
def test_results(result_id):
    result = TestResult.query.get_or_404(result_id)
    assignment = result.assignment
    game = Game.query.get(assignment.game_id)
    questions = json.loads(game.questions)
    user_answers = json.loads(result.answers) if result.answers else []
    
    learner = assignment.learner
    educator = assignment.educator
    
    if current_user.role == 'learner':
        learner_user = Learner.query.filter_by(user_id=current_user.id).first()
        if assignment.learner_id != learner_user.id:
            return redirect(url_for('login'))
    elif current_user.role == 'parent':
        parent = Parent.query.filter_by(user_id=current_user.id).first()
        if learner.parent_id != parent.id:
            return redirect(url_for('login'))
    elif current_user.role == 'educator':
        if assignment.educator_id != educator.id:
            return redirect(url_for('login'))
    
    question_review = []
    for i, question in enumerate(questions):
        user_answer = user_answers[i] if i < len(user_answers) else 'Not answered'
        is_correct = user_answer == question['correct']
        question_review.append({
            'number': i + 1,
            'question': question['question'],
            'user_answer': user_answer,
            'correct_answer': question['correct'],
            'is_correct': is_correct,
            'points': question['points']
        })
    
    return render_template('test_results.html', 
                         result=result, 
                         assignment=assignment, 
                         game=game,
                         learner=learner,
                         educator=educator,
                         question_review=question_review,
                         total_points=len(questions) * 2)

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
        results = []
        for assignment in assignments:
            result = TestResult.query.filter_by(assignment_id=assignment.id).first()
            if result:
                results.append({
                    'assignment': assignment,
                    'result': result,
                    'game': assignment.game,
                    'educator': assignment.educator
                })
        
        total_tests = len(results)
        passed_tests = len([r for r in results if r['result'].passed])
        avg_score = sum([r['result'].percentage for r in results]) / total_tests if total_tests > 0 else 0
        
        pending_assignments = []
        for assignment in assignments:
            if assignment.status != 'completed':
                pending_assignments.append({
                    'assignment': assignment,
                    'game': assignment.game,
                    'educator': assignment.educator
                })
        
        learners_data.append({
            'learner': learner,
            'results': results,
            'pending_assignments': pending_assignments,
            'pending_count': len(pending_assignments),
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'avg_score': avg_score
        })
    
    return render_template('parent_dashboard.html', learners_data=learners_data)

# ==================== GAMES ROUTES ====================

@app.route('/games')
@login_required
def view_all_games():
    if current_user.role == 'learner':
        flash('Access denied. Learners cannot view the games library.', 'error')
        return redirect(url_for('learner_dashboard'))
    
    games = Game.query.all()
    return render_template('games_list.html', games=games)

@app.route('/games/<int:game_id>')
@login_required
def view_game_details(game_id):
    if current_user.role == 'learner':
        flash('Access denied. Learners cannot view game details.', 'error')
        return redirect(url_for('learner_dashboard'))
    
    game = Game.query.get_or_404(game_id)
    questions = json.loads(game.questions)
    return render_template('game_details.html', game=game, questions=questions)

@app.route('/games/public')
@login_required
def view_public_games():
    if current_user.role != 'learner':
        return redirect(url_for('view_all_games'))
    
    games = Game.query.all()
    return render_template('public_games.html', games=games)

# ==================== AI ANALYSIS ROUTE ====================

def generate_ai_analysis(test_results, learner):
    if not test_results:
        return {
            'summary': {'total_tests': 0, 'average_score': 0, 'best_score': 0, 'lowest_score': 0, 'improving': None},
            'category_analysis': {},
            'strengths': [{'message': 'Complete your first test to see your strengths!'}],
            'weaknesses': [],
            'overall_assessment': "Welcome to EduBridge! Take your first test to get personalized AI analysis.",
            'recommendations': [{'priority': 'High', 'area': 'Getting Started', 'recommendation': 'Complete your first assigned test', 'action': 'Go to your dashboard', 'expected_improvement': 'Unlock insights'}],
            'motivation': "Ready to start learning? Complete your first test!",
            'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M')
        }
    
    scores = [r['percentage'] for r in test_results]
    avg_score = sum(scores) / len(scores)
    
    category_scores = {}
    for result in test_results:
        if result.get('game'):
            category = result['game'].category
            if category not in category_scores:
                category_scores[category] = []
            category_scores[category].append(result['percentage'])
    
    category_analysis = {}
    for category, scores_list in category_scores.items():
        avg = sum(scores_list) / len(scores_list)
        if avg >= 70:
            level = 'Strong'
            explanation = f"You're doing very well in {category}!"
        elif avg >= 50:
            level = 'Developing'
            explanation = f"You're making good progress in {category}."
        else:
            level = 'Needs Attention'
            explanation = f"{category} is an area to focus on."
        
        category_analysis[category] = {
            'name': category,
            'average': round(avg, 1),
            'level': level,
            'explanation': explanation,
            'tips': ['Practice regularly', 'Review mistakes'],
            'tests_taken': len(scores_list)
        }
    
    strengths = []
    weaknesses = []
    for category, data in category_analysis.items():
        if data['average'] >= 65:
            strengths.append({'name': category, 'score': data['average'], 'message': f"You excel at {category}!"})
        elif data['average'] < 55:
            weaknesses.append({'name': category, 'score': data['average'], 'message': f"Let's work on {category}."})
    
    if avg_score >= 70:
        overall = "Excellent work! You're mastering the material very well."
        motivation = "Amazing work! Keep challenging yourself!"
    elif avg_score >= 50:
        overall = "Good progress! You're on the right track."
        motivation = "Great progress! Keep going!"
    else:
        overall = "Learning takes time. Don't be discouraged!"
        motivation = "Every test teaches you something new. Keep trying!"
    
    return {
        'summary': {
            'total_tests': len(test_results),
            'average_score': round(avg_score, 1),
            'best_score': max(scores),
            'lowest_score': min(scores),
            'improving': None
        },
        'category_analysis': category_analysis,
        'strengths': strengths[:3] if strengths else [{'message': 'Complete more tests to identify strengths!'}],
        'weaknesses': weaknesses[:3],
        'overall_assessment': overall,
        'recommendations': [],
        'motivation': motivation,
        'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M')
    }

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
    test_results = []
    
    for assignment in assignments:
        result = TestResult.query.filter_by(assignment_id=assignment.id).first()
        if result:
            game = Game.query.get(assignment.game_id)
            test_results.append({
                'result': result,
                'game': game,
                'percentage': result.percentage,
                'score': result.score,
                'passed': result.passed,
                'date': result.completed_at
            })
    
    analysis = generate_ai_analysis(test_results, learner)
    
    return render_template('ai_analysis.html', 
                         learner=learner,
                         analysis=analysis,
                         test_results=test_results)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'success')
    return redirect(url_for('index'))

# ==================== RUN THE APP ====================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('RENDER', 'false').lower() != 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=port)