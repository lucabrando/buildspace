import os
import requests
from google.cloud import storage
from google.oauth2 import service_account
from dotenv import load_dotenv
import psycopg2
import logging

# Load environment variables
load_dotenv('.env.development.local')

# Database connection setup
DATABASE_URL = os.getenv("POSTGRES_URL")

# Google Cloud Storage setup
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
GCS_CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

def fetch_instagram_data():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, video_url, display_url FROM instagram_data")
            return cur.fetchall()

def download_and_store_content(url, id, is_video):
    file_extension = '.mp4' if is_video else '.jpg'
    blob_name = f"instagram_content/{id}{file_extension}"

    # Initialize GCS client
    credentials = service_account.Credentials.from_service_account_file(
        GCS_CREDENTIALS_PATH, scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    storage_client = storage.Client(credentials=credentials)
    bucket = storage_client.bucket(GCS_BUCKET_NAME)
    blob = bucket.blob(blob_name)

    logger.info(f"Attempting to fetch content for ID {id} with URL: {url}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://www.instagram.com/',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=60)
        response.raise_for_status()

        blob.upload_from_string(response.content)

        gcs_url = f"gs://{GCS_BUCKET_NAME}/{blob_name}"
        logger.info(f"Stored {'video' if is_video else 'image'} for ID {id} in GCS: {gcs_url}")
        return True
    except requests.RequestException as e:
        logger.error(f"Network error occurred while processing ID {id}: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error occurred while processing ID {id}: {str(e)}")
    return False

def process_instagram_data():
    rows = fetch_instagram_data()
    for id, video_url, display_url in rows:
        if video_url:
            logger.info(f"Processing video URL for ID {id}: {video_url}")
            success = download_and_store_content(video_url, id, is_video=True)
        elif display_url:
            logger.info(f"Processing image URL for ID {id}: {display_url}")
            success = download_and_store_content(display_url, id, is_video=False)
        else:
            logger.warning(f"No URL found for ID {id}")
            continue

        if not success:
            logger.warning(f"Failed to process content for ID {id}")

if __name__ == "__main__":
    process_instagram_data()