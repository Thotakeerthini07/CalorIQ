import mysql.connector


db_config = {
    'host': 'localhost',
    'user': 'root',          # ✅ your MySQL username
    'password': 'keer7',  # ✅ replace this with your actual MySQL password
    'database': 'calorIQ'    # ✅ make sure this database exists
}



def get_connection():
    return mysql.connector.connect(**db_config)

def add_user(email):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT IGNORE INTO users (email) VALUES (%s)", (email,))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def get_user_id(email):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] if result else None

def save_profile(email, age, gender, weight, height, goal):
    user_id = get_user_id(email)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO profiles (user_id, age, gender, weight, height, goal)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            age = VALUES(age),
            gender = VALUES(gender),
            weight = VALUES(weight),
            height = VALUES(height),
            goal = VALUES(goal)
    ''', (user_id, age, gender, weight, height, goal))
    conn.commit()
    cursor.close()
    conn.close()

def load_profile(email):
    user_id = get_user_id(email)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT age, gender, weight, height, goal FROM profiles WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    if result:
        return {
            'age': result[0],
            'gender': result[1],
            'weight': result[2],
            'height': result[3],
            'goal': result[4]
        }
    return {}
