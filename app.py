from flask import Flask, render_template, request
from scrape_ig import run_instagram_scraper, save_scraped_data
from download_content import create_directory, clear_directory, download_content
from semantic_extraction import process_file, universal_prompt
from pathlib import Path
import json
import os

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    summary = None
    if request.method == 'POST':
        instagram_url = request.form['instagram_url']
        username = instagram_url.rstrip('/').split('/')[-1]  # Extract username from URL
        
        # Run the Instagram scraper with the new username
        run = run_instagram_scraper(username)
        
        # Save scraped data
        save_scraped_data(run)
        
        # Download content
        content_directory = 'content_from_user'
        create_directory(content_directory)
        clear_directory(content_directory)  # Clear the directory before downloading new content
        with open('instagram_data.json', 'r') as file:
            data = json.load(file)
        for item in data:
            if item.get("videoUrl"):
                download_content(item["videoUrl"], content_directory, is_video=True)
            elif item.get("displayUrl"):
                download_content(item["displayUrl"], content_directory, is_video=False)
        
        # Process content and generate summary
        all_texts = []
        content_path = Path(content_directory)
        for file in content_path.iterdir():
            if file.suffix.lower() in ['.mp4', '.mov', '.avi', '.jpg', '.jpeg', '.png']:
                text = process_file(file, universal_prompt)
                all_texts.append(text)
        
        summary = "\n\n".join(all_texts)
    
    return render_template('index.html', summary=summary)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)