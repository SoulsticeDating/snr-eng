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
            ("Regularly", "Regularly"): 2,
            ("Never", "Never"): 2,
            ("Socially", "Socially"): 2,
            ("Regularly", "Socially"): 1,
            ("Regularly", "Never"): 0,
            ("Socially", "Regularly"): 1,
            ("Socially", "Never"): 1,
            ("Never", "Regularly"): 0,
            ("Never", "Socially"): 1
            
        },
        "relationship_type": {
            ("Casual", "Casual"): 2,
            ("Long-Term", "Long-Term"): 2,
            ("Marriage-minded", "Marriage-minded"): 2,
            ("Casual", "Long-Term"): 1,
            ("Casual", "Marriage-minded"): 0,
            ("Long-Term", "Casual"): 1,
            ("Long-Term", "Marriage-minded"): 1,
            ("Marriage-minded", "Casual"): 0,
            ("Marriage-minded", "Long-Term"): 1
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
    match_criteria = {
        'Male Straight': ['Female Straight', 'Female Bisexual'],
        'Female Straight': ['Male Straight', 'Male Bisexual'],
        'Male Gay': ['Male Gay', 'Male Bisexual'],
        'Female Lesbian': ['Female Lesbian', 'Female Bisexual'],
        'Non-Binary': ['Non-Binary']
    }

    for user in data['users']:
        user_id = user['id']
        gender_orientation = f"{user['gender']} {user['orientation']}"
        
        # Get the allowed matches based on gender and orientation
        valid_matches = match_criteria.get(gender_orientation, [])

        matched_users = []
        scores = []

        for other_user in data['users']:
            if user_id != other_user['id']:  # Avoid self-matching
                other_gender_orientation = f"{other_user['gender']} {other_user['orientation']}"

                if other_gender_orientation in valid_matches:
                    score = calculate_score(user, other_user)
                    if score > 0:  # Only store meaningful matches
                        matched_users.append(other_user['id'])
                        scores.append(str(score))

                        # Insert into `matches` table (storing individual match records)
                        cursor.execute('''
                        INSERT OR REPLACE INTO matches (user_id, matched_user_id, score)
                        VALUES (?, ?, ?)
                        ''', (user_id, other_user['id'], score))

        if matched_users:
            matched_users_csv = ",".join(matched_users)
            scores_csv = ",".join(scores)

            # Store matches in `match_results` (CSV storage)
            cursor.execute('''
            INSERT OR REPLACE INTO match_results (user_id, matched_users_csv, scores_csv)
            VALUES (?, ?, ?)
            ''', (user_id, matched_users_csv, scores_csv))



def PopulateMatches():
    # Step 1: Connect to the existing database
    conn = sqlite3.connect('dating_profiles.db')
    cursor = conn.cursor()

    # Step 2: Ensure the matches and match_results tables exist
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

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS match_results (
        user_id TEXT PRIMARY KEY,
        matched_users_csv TEXT,
        scores_csv TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')

    # Step 3: Retrieve all users from the database
    cursor.execute("SELECT * FROM users")
    users_data = cursor.fetchall()

    # Step 4: Convert fetched users into a structured list of dictionaries
    users = []
    for user in users_data:
        user_id, name, age, bio, gender, orientation = user

        # Fetch dealbreakers for the user
        cursor.execute("SELECT * FROM dealbreakers WHERE user_id = ?", (user_id,))
        dealbreaker_data = cursor.fetchone()

        if dealbreaker_data:
            _, drinking, relationship_type, religion, smoking, wants_kids = dealbreaker_data
            dealbreakers = {
                "drinking": drinking,
                "relationship_type": relationship_type,
                "religion": religion,
                "smoking": smoking,
                "wants_kids": wants_kids
            }
        else:
            dealbreakers = {}

        users.append({
            "id": user_id,
            "name": name,
            "age": age,
            "bio": bio,
            "gender": gender,
            "orientation": orientation,
            "dealbreakers": dealbreakers
        })

    # Step 5: Run the matching algorithm and store results
    store_match_results(cursor, {"users": users})

    # Step 6: Commit changes and close the connection
    conn.commit()
    conn.close()

    print("Matches have been calculated and stored successfully.")

def clean_matches():
    """Deletes all records from the matches and match_results tables."""
    conn = sqlite3.connect('dating_profiles.db')
    cursor = conn.cursor()

    # Step 1: Delete existing match data
    cursor.execute("DELETE FROM matches")
    cursor.execute("DELETE FROM match_results")

    # Step 2: Commit and close
    conn.commit()
    conn.close()
    print("All match data cleared. Ready to recalculate scores.")


def validate_matches(min_score):
    """Fetch matches from the database and validate only those with a score >= min_score."""
    conn = sqlite3.connect('dating_profiles.db')
    cursor = conn.cursor()

    # Step 1: Retrieve matches that meet the score requirement
    cursor.execute("SELECT user_id, matched_user_id FROM matches WHERE score >= ?", (min_score,))
    matches_data = cursor.fetchall()

    if not matches_data:
        print(f"No matches found with a minimum score of {min_score}.")
        conn.close()
        return

    validation_url = "https://snr-eng-7c5af300401d.herokuapp.com/api/validate-matches"
    valid_matches = []

    for user1, user2 in matches_data:
        request_body = {"matches": [{"user1_id": user1, "user2_id": user2}]}

        try:
            response = requests.post(validation_url, json=request_body)
            response_data = response.json()

            if response_data.get("success"):
                valid_matches.append((user1, user2))
            else:
                print(f"Match ({user1}, {user2}) is NOT 100% compatible.")

        except requests.exceptions.RequestException as e:
            print(f"Error validating match ({user1}, {user2}): {e}")

    conn.close()

    print(f"Validation complete. {len(valid_matches)} valid matches found with a minimum score of {min_score}.")

def main():
    """Clean matches, recalculate scores, and validate."""
    clean_matches()  # Step 1: Clear existing matches
    PopulateMatches()  # Step 2: Recalculate and store new matches
    validate_matches(10)  # Step 3: Validate new matches


if __name__ == "__main__":
    main()