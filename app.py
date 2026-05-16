from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, MultiLabelBinarizer
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from flask_migrate import Migrate
from db import db, User, Favorite
import json

app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SECRET_KEY'] = 'your_secret_key'
db.init_app(app)
migrate = Migrate(app, db)

# Load and preprocess the dataset
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, MultiLabelBinarizer
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from flask_migrate import Migrate
from db import db, User, Favorite
import json

app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SECRET_KEY'] = 'your_secret_key'
db.init_app(app)
migrate = Migrate(app, db)

# Load and preprocess the dataset
file_path = r"C:\Users\DHANA\Desktop\minpro.py\pro\minpro.xlsx"


df = pd.read_excel(file_path)

# Preprocess the dataset
df['Role'] = df['Role'].str.lower()
le = LabelEncoder()
df['Role_encoded'] = le.fit_transform(df['Role'])

mlb_courses = MultiLabelBinarizer()
df_courses = pd.DataFrame(mlb_courses.fit_transform(df['Courses'].str.split(', ')), columns=mlb_courses.classes_)

mlb_skills = MultiLabelBinarizer()
df_skills = pd.DataFrame(mlb_skills.fit_transform(df['Skills'].str.split(', ')), columns=mlb_skills.classes_)

df_encoded = pd.concat([df, df_courses, df_skills], axis=1)

# Prepare data for role prediction
X = df_encoded.drop(['Role', 'Courses', 'Skills', 'Role_encoded'], axis=1)
y = df_encoded['Role_encoded']

# Train role prediction model
role_model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
role_model.fit(X, y)

# Prepare Salary Prediction Models
salary_columns = [
    '2022 Entry Level (0-2 years)', '2022 Mid Level (2-5 years)', '2022 Senior Level (5+ years)',
    '2023 Entry Level (0-2 years)', '2023 Mid Level (2-5 years)', '2023 Senior Level (5+ years)',
    '2024 Entry Level (0-2 years)', '2024 Mid Level (2-5 years)', '2024 Senior Level (5+ years)'
]

def prepare_salary_data(level):
    salary_X = df_encoded[salary_columns]
    salary_y = df_encoded[f'2024 {level}']
    X_train_salary, X_test_salary, y_train_salary, y_test_salary = train_test_split(salary_X, salary_y, test_size=0.2, random_state=42)
    return X_train_salary, y_train_salary

entry_X_train, entry_y_train = prepare_salary_data('Entry Level (0-2 years)')
mid_X_train, mid_y_train = prepare_salary_data('Mid Level (2-5 years)')
senior_X_train, senior_y_train = prepare_salary_data('Senior Level (5+ years)')

entry_model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
entry_model.fit(entry_X_train, entry_y_train)

mid_model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
mid_model.fit(mid_X_train, mid_y_train)

senior_model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
senior_model.fit(senior_X_train, senior_y_train)

def generate_links(items):
    base_urls = {
        'Coursera': 'https://www.coursera.org/search?query=',
        'Udemy': 'https://www.udemy.com/courses/search/?q=',
        'edX': 'https://www.edx.org/search?q=',
        'Google': 'https://www.google.com/search?q='
    }

    links = {}
    for item in items:
        item_links = {platform: f'{base_url}{item.replace(" ", "+")}' for platform, base_url in base_urls.items()}
        links[item] = item_links

    return links

# Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/users')
def users():
    if not session.get('admin_logged_in'):
        return redirect('/')
    
    users = User.query.all()
    return render_template('users.html', users=users)

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == 'vasanthi' and password == 'vassu45@':
            session['admin_logged_in'] = True
            session['username'] = username
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials, please try again.')
            return redirect(url_for('admin_login'))

    return render_template('admin_login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        
        if User.query.filter_by(username=username).first():
            flash("Username already exists. Please choose a different one.")
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash("Email already registered. Please use a different email.")
            return redirect(url_for('register'))
        
        new_user = User(username=username, email=email)
        new_user.password_hash = generate_password_hash(password)
        
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful! You can now log in.")
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/add_to_favorite', methods=['POST'])
def add_to_favorite():
    role = request.form.get('role')
    courses = request.form.get('courses')  # This will be a JSON string if you're sending it as above
    skills = request.form.get('skills')  # Same as above
    salary = request.form.get('salary')

    # Check if the user is logged in
    if 'user_id' in session:
        user_id = session['user_id']

        # Check if this favorite already exists
        existing_favorite = Favorite.query.filter_by(user_id=user_id, role=role).first()

        if existing_favorite:
            # If it exists, remove it
            db.session.delete(existing_favorite)
            db.session.commit()
            return jsonify({
                'action': 'removed',
                'message': 'Successfully removed from favorites!'
            })
        else:
            # If it doesn't exist, create a new favorite entry
            new_favorite = Favorite(user_id=user_id, role=role, courses=courses, skills=skills, salary=salary)

            # Add to database
            db.session.add(new_favorite)
            db.session.commit()
            return jsonify({
                'action': 'added',
                'message': 'Successfully added to favorites!'
            })
    else:
        return jsonify({
            'action': 'failed',
            'message': 'User not logged in.'
        }), 403

@app.route('/show_favorites')
def show_favorites():
    if 'user_id' not in session:
        flash('Please log in to view favorites.')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user = User.query.get(user_id)  # Assuming you have a User model
    favorites = Favorite.query.filter_by(user_id=user_id).all()
    
    # Convert JSON strings to dictionaries
    for favorite in favorites:
        favorite.courses = json.loads(favorite.courses) if favorite.courses else {}
        favorite.skills = json.loads(favorite.skills) if favorite.skills else {}
    
    return render_template('show_favorites.html', favorites=favorites, username=user.username)

@app.route('/remove_favorite/<int:favorite_id>', methods=['DELETE'])
def remove_favorite(favorite_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 403

    favorite = Favorite.query.get(favorite_id)
    if favorite:
        db.session.delete(favorite)
        db.session.commit()
        return jsonify({'success': True})
    
    return jsonify({'error': 'Favorite not found'}), 404



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        session['admin_logged_in'] = False
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            flash("Login successful!")
            session['user_logged_in'] = True
            session['user_id'] = user.id  # Store user ID in session
            return redirect(url_for('index'))
        elif not user:
            flash("Username does not exist. Please register first.")
        else:
            flash("Incorrect password. Please try again.")
        
        return redirect(url_for('login'))
    
    return render_template('login.html')
@app.route('/logout')
def logout():
    # Clear the user session
    session.pop('user_id', None)
    flash('You have been logged out successfully.', 'success')  # Optional: flash a success message
    return redirect(url_for('home'))  # Redirect to the login page or home page
@app.route('/index', methods=['GET', 'POST'])
def index():
    roles = sorted(df['Role'].unique())
    experience_levels = ['Entry Level (0-2 years)', 'Mid Level (2-5 years)', 'Senior Level (5+ years)']
    
    users = None
    if session.get('admin_logged_in'):
        users = User.query.all()

    return render_template('index.html', roles=roles, experience_levels=experience_levels, users=users)

@app.route('/recommend', methods=['POST'])
def recommend():
    role = request.form.get('role')
    experience = request.form.get('experience')

    role_data = df[df['Role'].str.lower() == role.lower()].iloc[0]

    courses = role_data['Courses'].split(', ')
    skills = role_data['Skills'].split(', ')

    course_links = generate_links(courses)
    skill_links = generate_links(skills)

    if experience == 'Entry Level (0-2 years)':
        predicted_salary_2025 = entry_model.predict([role_data[salary_columns]])[0]
    elif experience == 'Mid Level (2-5 years)':
        predicted_salary_2025 = mid_model.predict([role_data[salary_columns]])[0]
    else:
        predicted_salary_2025 = senior_model.predict([role_data[salary_columns]])[0]

    return render_template('result.html', role=role, courses=courses, skills=skills, predicted_salary=predicted_salary_2025, course_links=course_links, skill_links=skill_links)

if __name__ == '__main__':
    app.run(debug=True)


df = pd.read_excel(file_path)

# Preprocess the dataset
df['Role'] = df['Role'].str.lower()
le = LabelEncoder()
df['Role_encoded'] = le.fit_transform(df['Role'])

mlb_courses = MultiLabelBinarizer()
df_courses = pd.DataFrame(mlb_courses.fit_transform(df['Courses'].str.split(', ')), columns=mlb_courses.classes_)

mlb_skills = MultiLabelBinarizer()
df_skills = pd.DataFrame(mlb_skills.fit_transform(df['Skills'].str.split(', ')), columns=mlb_skills.classes_)

df_encoded = pd.concat([df, df_courses, df_skills], axis=1)

# Prepare data for role prediction
X = df_encoded.drop(['Role', 'Courses', 'Skills', 'Role_encoded'], axis=1)
y = df_encoded['Role_encoded']

# Train role prediction model
role_model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
role_model.fit(X, y)

# Prepare Salary Prediction Models
salary_columns = [
    '2022 Entry Level (0-2 years)', '2022 Mid Level (2-5 years)', '2022 Senior Level (5+ years)',
    '2023 Entry Level (0-2 years)', '2023 Mid Level (2-5 years)', '2023 Senior Level (5+ years)',
    '2024 Entry Level (0-2 years)', '2024 Mid Level (2-5 years)', '2024 Senior Level (5+ years)'
]

def prepare_salary_data(level):
    salary_X = df_encoded[salary_columns]
    salary_y = df_encoded[f'2024 {level}']
    X_train_salary, X_test_salary, y_train_salary, y_test_salary = train_test_split(salary_X, salary_y, test_size=0.2, random_state=42)
    return X_train_salary, y_train_salary

entry_X_train, entry_y_train = prepare_salary_data('Entry Level (0-2 years)')
mid_X_train, mid_y_train = prepare_salary_data('Mid Level (2-5 years)')
senior_X_train, senior_y_train = prepare_salary_data('Senior Level (5+ years)')

entry_model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
entry_model.fit(entry_X_train, entry_y_train)

mid_model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
mid_model.fit(mid_X_train, mid_y_train)

senior_model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
senior_model.fit(senior_X_train, senior_y_train)

def generate_links(items):
    base_urls = {
        'Coursera': 'https://www.coursera.org/search?query=',
        'Udemy': 'https://www.udemy.com/courses/search/?q=',
        'edX': 'https://www.edx.org/search?q=',
        'Google': 'https://www.google.com/search?q='
    }

    links = {}
    for item in items:
        item_links = {platform: f'{base_url}{item.replace(" ", "+")}' for platform, base_url in base_urls.items()}
        links[item] = item_links

    return links

# Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/users')
def users():
    if not session.get('admin_logged_in'):
        return redirect('/')
    
    users = User.query.all()
    return render_template('users.html', users=users)

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == 'vasanthi' and password == 'vassu45@':
            session['admin_logged_in'] = True
            session['username'] = username
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials, please try again.')
            return redirect(url_for('admin_login'))

    return render_template('admin_login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        
        if User.query.filter_by(username=username).first():
            flash("Username already exists. Please choose a different one.")
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash("Email already registered. Please use a different email.")
            return redirect(url_for('register'))
        
        new_user = User(username=username, email=email)
        new_user.password_hash = generate_password_hash(password)
        
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful! You can now log in.")
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/add_to_favorite', methods=['POST'])
def add_to_favorite():
    role = request.form.get('role')
    courses = request.form.get('courses')  # This will be a JSON string if you're sending it as above
    skills = request.form.get('skills')  # Same as above
    salary = request.form.get('salary')

    # Check if the user is logged in
    if 'user_id' in session:
        user_id = session['user_id']

        # Check if this favorite already exists
        existing_favorite = Favorite.query.filter_by(user_id=user_id, role=role).first()

        if existing_favorite:
            # If it exists, remove it
            db.session.delete(existing_favorite)
            db.session.commit()
            return jsonify({
                'action': 'removed',
                'message': 'Successfully removed from favorites!'
            })
        else:
            # If it doesn't exist, create a new favorite entry
            new_favorite = Favorite(user_id=user_id, role=role, courses=courses, skills=skills, salary=salary)

            # Add to database
            db.session.add(new_favorite)
            db.session.commit()
            return jsonify({
                'action': 'added',
                'message': 'Successfully added to favorites!'
            })
    else:
        return jsonify({
            'action': 'failed',
            'message': 'User not logged in.'
        }), 403

@app.route('/show_favorites')
def show_favorites():
    if 'user_id' not in session:
        flash('Please log in to view favorites.')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user = User.query.get(user_id)  # Assuming you have a User model
    favorites = Favorite.query.filter_by(user_id=user_id).all()
    
    # Convert JSON strings to dictionaries
    for favorite in favorites:
        favorite.courses = json.loads(favorite.courses) if favorite.courses else {}
        favorite.skills = json.loads(favorite.skills) if favorite.skills else {}
    
    return render_template('show_favorites.html', favorites=favorites, username=user.username)

@app.route('/remove_favorite/<int:favorite_id>', methods=['DELETE'])
def remove_favorite(favorite_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 403

    favorite = Favorite.query.get(favorite_id)
    if favorite:
        db.session.delete(favorite)
        db.session.commit()
        return jsonify({'success': True})
    
    return jsonify({'error': 'Favorite not found'}), 404



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        session['admin_logged_in'] = False
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            flash("Login successful!")
            session['user_logged_in'] = True
            session['user_id'] = user.id  # Store user ID in session
            return redirect(url_for('index'))
        elif not user:
            flash("Username does not exist. Please register first.")
        else:
            flash("Incorrect password. Please try again.")
        
        return redirect(url_for('login'))
    
    return render_template('login.html')
@app.route('/logout')
def logout():
    # Clear the user session
    session.pop('user_id', None)
    flash('You have been logged out successfully.', 'success')  # Optional: flash a success message
    return redirect(url_for('home'))  # Redirect to the login page or home page
@app.route('/index', methods=['GET', 'POST'])
def index():
    roles = sorted(df['Role'].unique())
    experience_levels = ['Entry Level (0-2 years)', 'Mid Level (2-5 years)', 'Senior Level (5+ years)']
    
    users = None
    if session.get('admin_logged_in'):
        users = User.query.all()

    return render_template('index.html', roles=roles, experience_levels=experience_levels, users=users)

@app.route('/recommend', methods=['POST'])
def recommend():
    role = request.form.get('role')
    experience = request.form.get('experience')

    role_data = df[df['Role'].str.lower() == role.lower()].iloc[0]

    courses = role_data['Courses'].split(', ')
    skills = role_data['Skills'].split(', ')

    course_links = generate_links(courses)
    skill_links = generate_links(skills)

    if experience == 'Entry Level (0-2 years)':
        predicted_salary_2025 = entry_model.predict([role_data[salary_columns]])[0]
    elif experience == 'Mid Level (2-5 years)':
        predicted_salary_2025 = mid_model.predict([role_data[salary_columns]])[0]
    else:
        predicted_salary_2025 = senior_model.predict([role_data[salary_columns]])[0]

    return render_template('result.html', role=role, courses=courses, skills=skills, predicted_salary=predicted_salary_2025, course_links=course_links, skill_links=skill_links)

if __name__ == '__main__':
    app.run(debug=True)
