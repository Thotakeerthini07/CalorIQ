import tensorflow as tf
import numpy as np
from PIL import Image
import json
import os
from database import load_profile

# Load pre-trained MobileNetV2 model
model = tf.keras.applications.MobileNetV2(weights='imagenet')

# JSON calorie mapping
CALORIE_DATA_FILE = 'calorie_data.json'

# === Food Recognition ===

def preprocess_image(image_path):
    img = Image.open(image_path).convert('RGB')
    img = img.resize((224, 224))
    img_array = np.array(img)
    img_array = tf.keras.applications.mobilenet_v2.preprocess_input(img_array)
    return np.expand_dims(img_array, axis=0)

def predict_food_label(image_path):
    img_array = preprocess_image(image_path)
    preds = model.predict(img_array)
    decoded = tf.keras.applications.mobilenet_v2.decode_predictions(preds, top=1)[0][0]

    class_name = decoded[1].lower()  # e.g., "pizza"
    confidence = float(decoded[2])

    calorie_data = load_calorie_data()
    calories = calorie_data.get(class_name, 250)  # fallback if not found

    return class_name, calories, confidence

def load_calorie_data():
    if not os.path.exists(CALORIE_DATA_FILE):
        return {}
    with open(CALORIE_DATA_FILE, 'r') as f:
        return json.load(f)

def save_calorie_data(data):
    with open(CALORIE_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# === Calorie Logic (using DB profile) ===

def calculate_bmr(age, gender, weight, height):
    if gender == 'male':
        return 88.362 + 13.397 * weight + 4.799 * height - 5.677 * age
    else:
        return 447.593 + 9.247 * weight + 3.098 * height - 4.330 * age

def calculate_calorie_goal(age, gender, weight, height, goal):
    bmr = calculate_bmr(age, gender, weight, height)
    if goal == 'lose':
        return bmr - 500
    elif goal == 'gain':
        return bmr + 500
    return bmr

def get_user_limit(user_email):
    profile = load_profile(user_email)
    if not profile:
        return 1800  # fallback if no profile found

    return int(calculate_calorie_goal(
        profile['age'],
        profile['gender'],
        profile['weight'],
        profile['height'],
        profile['goal']
    ))
