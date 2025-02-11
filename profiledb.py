import sqlite3
import json
import requests

def fetch_data(api_url):
    """Fetch data from the API"""
    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from API: {e}")
        return None

def create_database():
    # Connect to SQLite database (creates it if it doesn't exist)
    conn = sqlite3.connect('dating_profiles.db')
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        age INTEGER NOT NULL,
        bio TEXT,
        gender TEXT NOT NULL,
        orientation TEXT NOT NULL
    )
    ''')

    # Create dealbreakers table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS dealbreakers (
        user_id TEXT PRIMARY KEY,
        drinking TEXT,
        relationship_type TEXT,
        religion TEXT,
        smoking TEXT,
        wants_kids TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')

    # Create liked_users table for future matching functionality
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS liked_users (
        user_id TEXT,
        liked_user_id TEXT,
        PRIMARY KEY (user_id, liked_user_id),
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (liked_user_id) REFERENCES users(id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS matches (
        user_id TEXT,
        matched_user_id TEXT,
        score INTEGER,
        PRIMARY KEY (user_id, matched_user_id),
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (matched_user_id) REFERENCES users(id)
    )
    ''')

    # NEW TABLE: match_results
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS match_results (
        user_id TEXT PRIMARY KEY,
        matched_users_csv TEXT,
        scores_csv TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')

    return conn, cursor

def populate_database(data, cursor):
    # Insert users
    for user in data['users']:
        # Insert into users table
        cursor.execute('''
        INSERT OR REPLACE INTO users (id, name, age, bio, gender, orientation)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            user['id'],
            user['name'],
            user['age'],
            user['bio'],
            user['gender'],
            user['orientation']
        ))

        # Insert into dealbreakers table
        cursor.execute('''
        INSERT OR REPLACE INTO dealbreakers (user_id, drinking, relationship_type, religion, smoking, wants_kids)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            user['id'],
            user['dealbreakers']['drinking'],
            user['dealbreakers']['relationship_type'],
            user['dealbreakers']['religion'],
            user['dealbreakers']['smoking'],
            user['dealbreakers']['wants_kids']
        ))

        # Insert liked users if any
        for liked_user in user['liked_users']:
            cursor.execute('''
            INSERT OR REPLACE INTO liked_users (user_id, liked_user_id)
            VALUES (?, ?)
            ''', (user['id'], liked_user))


def calculate_score(user1, user2):
    score = 0

    dealbreakers = ['drinking', 'relationship_type', 'religion', 'smoking', 'wants_kids']

    dealbreaker_scores = {
        "drinking": {
            ("Regularly", "Never"): 0,
            ("Never", "Regularly"): 0,
            ("Socially", "Socially"): 2,
            ("Regularly", "Socially"): 1,
            ("Socially", "Regularly"): 1,
            ("Never", "Socially"): 1,
            ("Socially", "Never"): 1
        },
        "relationship_type": {
            ("Casual", "Casual"): 2,
            ("Long-Term", "Long-Term"): 2,
            ("Marriage-minded", "Marriage-minded"): 2,
            ("Casual", "Long-Term"): 0,
            ("Casual", "Marriage-minded"): 0,
            ("Long-Term", "Casual"): 0,
            ("Marriage-minded", "Casual"): 0
        },
        "religion": {
            ("Non-religious", "Non-religious"): 2,
            ("Spiritual", "Spiritual"): 2,
            ("Religious", "Religious"): 2,
            ("Non-religious", "Religious"): 0,
            ("Religious", "Non-religious"): 0,
            ("Spiritual", "Religious"): 1,
            ("Religious", "Spiritual"): 1,
            ("Spiritual", "Non-religious"): 1,
            ("Non-religious", "Spiritual"): 1
        },
        "smoking": {
            ("Regularly", "Regularly"): 2,
            ("Socially", "Socially"): 2,
            ("Never", "Never"): 2,
            ("Regularly", "Never"): 0,
            ("Never", "Regularly"): 0,
            ("Socially", "Regularly"): 1,
            ("Regularly", "Socially"): 1,
            ("Socially", "Never"): 1,
            ("Never", "Socially"): 1
        },
        "wants_kids": {
            ("Yes", "Yes"): 2,
            ("No", "No"): 2,
            ("Maybe", "Maybe"): 2,
            ("Yes", "Maybe"): 1,
            ("Maybe", "Yes"): 1,
            ("No", "Maybe"): 1,
            ("Maybe", "No"): 1,
            ("Yes", "No"): 0,
            ("No", "Yes"): 0
        }
    }

    for key in dealbreakers:
        user1_pref = user1['dealbreakers'][key]
        user2_pref = user2['dealbreakers'][key]
        score += dealbreaker_scores[key].get((user1_pref, user2_pref), 0)  # Default 0 if no match found

    return score

def store_match_results(cursor, data):
    for user in data['users']:
        user_id = user['id']
        matched_users = []
        scores = []

        for other_user in data['users']:
            if user_id != other_user['id']:  # Avoid self-matching
                score = calculate_score(user, other_user)
                if score > 0:  # Only store meaningful matches
                    matched_users.append(other_user['id'])
                    scores.append(str(score))

        if matched_users:
            matched_users_csv = ",".join(matched_users)
            scores_csv = ",".join(scores)

            cursor.execute('''
            INSERT OR REPLACE INTO match_results (user_id, matched_users_csv, scores_csv)
            VALUES (?, ?, ?)
            ''', (user_id, matched_users_csv, scores_csv))


def main():
    #first pull the first user in the db and start with sexuality. (Male Straight) = Female only, (Male Bisexual) = Male and Female
    match_criteria = {
        'Male Straight': {
            'matches': ['Female Straight'],
            'points': [5.0]  # 1 point for straight female
        },
        'Male Straight': {
            'matches': ['Female Bisexual'],
            'points': [2.5]
        },
        'Female Straight': {
            'matches': ['Male Straight'],
            'points': [5]
        },
        'Female Straight': {
            'matches': ['Male Bisexual'],
            'points': [2.5]
        },
        'Male Gay': {
            'matches': ['Male Gay'],
            'points': [5]
        },
        'Male Gay': {
            'matches': ['Male Bisexual'],
            'points': [2.5]
        },
        'Female Lesbian': {
            'matches': ['Female Straight'],
            'points': [5]
        },
        'Female Lesbian': {
            'matches': ['Female Bisexual'],
            'points': [2.5]
        },
        'Non-Binary': {
            'matches': ['Non-Binary'],
            'points': [5]
        }
    }

if __name__ == "__main__":
    main()