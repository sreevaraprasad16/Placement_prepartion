from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, StudentProfile, SkillAssessment
from ml_model import train_model, predict_placement, get_recommendations
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_change_me'
db_path = os.path.join(os.getcwd(), 'app.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        if User.query.filter_by(username=username).first():
            flash('Username exists')
            return render_template('register.html')
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        flash('Registered! Login now.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    if request.method == 'POST':
        if not profile:
            profile = StudentProfile(user_id=current_user.id, name=request.form['name'],
                                     cgpa=float(request.form['cgpa']), branch=request.form['branch'],
                                     skills=request.form['skills'])
            db.session.add(profile)
        else:
            profile.name = request.form['name']
            profile.cgpa = float(request.form['cgpa'])
            profile.branch = request.form['branch']
            profile.skills = request.form['skills']
        db.session.commit()
        flash('Profile updated')
    return render_template('profile.html', profile=profile)

@app.route('/assessment', methods=['GET', 'POST'])
@login_required
def assessment():
    if request.method == 'POST':
        assessment = SkillAssessment(
            user_id=current_user.id,
            aptitude_score=int(request.form['aptitude']),
            coding_score=int(request.form['coding']),
            technical_score=int(request.form['technical'])
        )
        db.session.add(assessment)
        db.session.commit()
        flash('Assessment submitted')
        return redirect(url_for('dashboard'))
    return render_template('assessment.html')

@app.route('/predict')
@login_required
def predict():
    profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        return jsonify({'error': 'Complete profile first'})
    last_assess = SkillAssessment.query.filter_by(user_id=current_user.id).order_by(SkillAssessment.date_taken.desc()).first()
    if not last_assess:
        return jsonify({'error': 'Take assessment first'})
    prob = predict_placement(profile.cgpa, last_assess.aptitude_score, last_assess.coding_score, last_assess.technical_score)
    recs = get_recommendations(last_assess.__dict__)
    return jsonify({'placement_chance': prob, 'recommendations': recs})

@app.route('/dashboard')
@login_required
def dashboard():
    profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    
    assessments_query = SkillAssessment.query.filter_by(user_id=current_user.id).order_by(SkillAssessment.date_taken.desc()).limit(10).all()
    assessments_json = []
    for a in assessments_query:
        assessments_json.append({
            'date_taken': a.date_taken.isoformat(),
            'aptitude_score': a.aptitude_score,
            'coding_score': a.coding_score,
            'technical_score': a.technical_score
        })
    
    return render_template('dashboard.html', profile=profile, assessments_json=assessments_json)

@app.route('/admin')
@login_required
def admin():
    if current_user.role != 'admin':
        flash('Admin only')
        return redirect(url_for('dashboard'))
    users = User.query.all()
    return render_template('admin.html', users=users)

@app.route('/chat', methods=['POST'])
@login_required
def chat():
    message = request.json.get('message', '').lower()
    responses = {
        'hello': 'Welcome to AI Placement Coach! 👋',
        'test': 'Take timed assessment tests.',
        'placement': 'Complete profile + test → ML prediction.',
        'help': 'Commands: test, placement, profile, admin',
        'admin': 'admin/admin',
        'binary': 'Binary search: O(log n)',
        'default': 'Ask about placement preparation!'
    }
    reply = responses.get(message, responses['default'])
    return jsonify({'reply': reply})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        train_model()
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', password=generate_password_hash('admin'), role='admin')
            db.session.add(admin)
            db.session.commit()
    app.run(debug=False, host='0.0.0.0', port=5000)
