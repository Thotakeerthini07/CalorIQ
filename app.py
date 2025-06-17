import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, session, flash
from werkzeug.utils import secure_filename
from utils import predict_food_label, load_calorie_data, save_calorie_data, get_user_limit
from database import add_user, save_profile, load_profile

app = Flask(__name__)
app.secret_key = 'your-secret-key'
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def home():
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        if not email:
            flash("Email is required.")
            return redirect('/login')

        add_user(email)  # Ensures user exists or creates one
        session['user_email'] = email
        return redirect('/dashboard')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        if not email:
            flash("Email is required.")
            return redirect('/register')

        add_user(email)
        session['user_email'] = email
        flash("Registration successful!")
        return redirect('/profile')

    return render_template('register.html')

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    user_email = session.get('user_email')
    if not user_email:
        return redirect('/login')

    if request.method == 'POST':
        age = int(request.form['age'])
        gender = request.form['gender']
        weight = float(request.form['weight'])
        height = float(request.form['height'])
        goal = request.form['goal']

        save_profile(user_email, age, gender, weight, height, goal)
        flash("Profile updated!")
        return redirect('/dashboard')

    profile = load_profile(user_email)
    return render_template("profile.html", profile=profile)

@app.route('/dashboard')
def dashboard():
    user_email = session.get('user_email')
    if not user_email:
        return redirect('/login')

    calorie_data = load_calorie_data()
    user_data = calorie_data.get(user_email, {})
    today = datetime.now().strftime('%Y-%m-%d')
    meals_today = user_data.get(today, [])

    total_calories = sum(entry['calories'] for entry in meals_today)
    user_limit = get_user_limit(user_email)

    if total_calories < user_limit:
        note = "You're within your limit. Great job!"
    elif total_calories == user_limit:
        note = "You've hit your goal exactly."
    else:
        note = "You've exceeded your goal! Consider a lighter next meal."

    return render_template("dashboard.html",
                           user_email=user_email,
                           user_limit=user_limit,
                           total_so_far=total_calories,
                           log_data=meals_today,
                           note=note)

@app.route('/upload_meal', methods=['POST'])
def upload_meal():
    if 'food_image' not in request.files:
        flash('No file part')
        return redirect('/dashboard')

    file = request.files['food_image']
    if file.filename == '':
        flash('No selected file')
        return redirect('/dashboard')

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    try:
        food_name, calories, confidence = predict_food_label(filepath)
    except Exception as e:
        flash(f'Error processing image: {str(e)}')
        if os.path.exists(filepath):
            os.remove(filepath)
        return redirect('/dashboard')

    if os.path.exists(filepath):
        os.remove(filepath)

    user_email = session.get('user_email')
    if not user_email:
        flash('Please login first')
        return redirect('/login')

    today = datetime.now().strftime('%Y-%m-%d')
    calorie_data = load_calorie_data()
    user_data = calorie_data.get(user_email, {})
    meals_today = user_data.get(today, [])

    meal_entry = {
        'food': food_name,
        'calories': calories,
        'confidence': confidence,
        'time': datetime.now().strftime('%H:%M:%S')
    }
    meals_today.append(meal_entry)
    user_data[today] = meals_today
    calorie_data[user_email] = user_data
    save_calorie_data(calorie_data)

    flash(f'Meal logged: {food_name} ({calories} kcal) with confidence {confidence:.2f}')
    return redirect('/dashboard')

@app.route('/history')
def history():
    user_email = session.get('user_email')
    if not user_email:
        return redirect('/login')

    calorie_data = load_calorie_data()
    user_data = calorie_data.get(user_email, {})
    sorted_dates = sorted(user_data.keys(), reverse=True)

    history_data = []
    for date in sorted_dates:
        meals = user_data[date]
        total = sum(entry['calories'] for entry in meals)
        history_data.append({'date': date, 'total': total, 'meals': meals})

    return render_template('history.html', history=history_data)

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)
