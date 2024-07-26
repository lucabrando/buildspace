import os
import psycopg2
from apify_client import ApifyClient
from dotenv import load_dotenv

# Load environment variables from .env.development.local
load_dotenv('.env.development.local')

# Database connection setup
DATABASE_URL = os.getenv("POSTGRES_URL")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

def ensure_table_exists_and_empty():
    create_table_query = """
    CREATE TABLE IF NOT EXISTS instagram_data (
        id SERIAL PRIMARY KEY,
        username TEXT,
        caption TEXT,
        url TEXT,
        timestamp TIMESTAMP,
        video_url TEXT,
        display_url TEXT
    )
    """
    truncate_table_query = "TRUNCATE TABLE instagram_data"
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Create table if it doesn't exist
            cur.execute(create_table_query)
            # Truncate (empty) the table
            cur.execute(truncate_table_query)
            conn.commit()
    print("Table 'instagram_data' has been created (if not exists) and emptied.")

# Get the API token from the environment variable
api_token = os.getenv("MY-APIFY-TOKEN")

# Initialize the ApifyClient with your API token
client = ApifyClient(api_token)

# Prepare the Actor input
run_input = {
    "username": ["placeholder"],  # Placeholder for the actual username
    "resultsLimit": 7,
}

# Function to run the Instagram scraper
def run_instagram_scraper(username):
    run_input['username'] = [username]
    print(f"Running Instagram scraper for username: {username}")
    run = client.actor("apify/instagram-post-scraper").call(run_input=run_input)
    print("Instagram scraper run completed.")
    return run

# Function to save scraped data to JSON file
def save_scraped_data(run, skip_table_check=False):
    if not skip_table_check:
        ensure_table_exists_and_empty()
    insert_query = """
    INSERT INTO instagram_data (username, caption, url, timestamp, video_url, display_url)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            for item in client.dataset(run["defaultDatasetId"]).iterate_items():
                cur.execute(insert_query, (
                    item.get("ownerUsername"),
                    item.get("caption"),
                    item.get("url"),
                    item.get("timestamp"),
                    item.get("videoUrl"),
                    item.get("displayUrl")
                ))
            conn.commit()
    print("Data has been saved to the database")

if __name__ == "__main__":
    # Test database connection
    def test_db_connection():
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute('SELECT 1')
            print("Database connection successful!")
        except Exception as e:
            print(f"Database connection failed: {e}")

    # Test table creation
    def test_table_creation():
        try:
            ensure_table_exists_and_empty()
            print("Table creation/check and emptying successful!")
        except Exception as e:
            print(f"Table creation/check failed: {e}")

    # Test Instagram scraping and data saving
    def test_scrape_and_save():
        try:
            # Use a test Instagram username
            test_username = "essereserena"  # You can change this to any public Instagram account
            run = run_instagram_scraper(test_username)
            save_scraped_data(run, skip_table_check=True)  # Add this parameter
            print(f"Successfully scraped and saved data for {test_username}")
        except Exception as e:
            print(f"Scraping and saving failed: {e}")

    # Run tests
    print("Starting tests...")
    test_db_connection()
    test_table_creation()
    test_scrape_and_save()
    print("Tests completed.")