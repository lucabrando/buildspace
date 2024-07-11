import json
from apify_client import ApifyClient
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Get the API token from the environment variable
api_token = os.getenv("MY-APIFY-TOKEN")

# Initialize the ApifyClient with your API token
client = ApifyClient(api_token)

# Prepare the Actor input
run_input = {
    "username": ["PLACEHOLDER"],  # Placeholder for the actual username
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
def save_scraped_data(run):
    json_file_path = 'instagram_data.json'
    
    # Initialize an empty list for data
    data = []

    print("Fetching dataset items...")
    # Fetch and append Actor results to the data list
    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        specific_data = {
            "caption": item.get("caption"),
            "ownerFullName": item.get("ownerFullName"),
            "ownerUsername": item.get("ownerUsername"),
            "url": item.get("url"),
            "commentsCount": item.get("commentsCount"),
            "likesCount": item.get("likesCount"),
            "timestamp": item.get("timestamp"),
            "videoUrl": item.get("videoUrl"),
            "displayUrl": item.get("displayUrl")
        }
        data.append(specific_data)

    # Save the updated data back to the JSON file
    with open(json_file_path, 'w') as file:
        json.dump(data, file, indent=4)

    print(f"Data has been saved to {json_file_path}")

# Example usage
if __name__ == "__main__":
    username = "byjeffreysun"  # Replace with actual username
    run = run_instagram_scraper(username)
    save_scraped_data(run)