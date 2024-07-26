from flask import Flask, render_template, request, flash
from scrape_ig import run_instagram_scraper, save_scraped_data
from download_content import process_instagram_data as download_process
from semantic_extraction import process_instagram_data as semantic_process, universal_prompt
import os
from dotenv import load_dotenv

load_dotenv('.env.development.local')

app = Flask(__name__)
app.secret_key = os.urandom(24)

@app.route('/', methods=['GET', 'POST'])
def index():
    summary = None
    if request.method == 'POST':
        username = request.form['instagram_username']
        try:
            # Run the Instagram scraper with the username
            run = run_instagram_scraper(username)
            
            # Save scraped data
            save_scraped_data(run)
            
            # Download and store content
            download_process(username)  # Assuming you update this function to accept username
            
            # Process content and generate summary
            summary = semantic_process(universal_prompt)  # Removed username parameter
        except Exception as e:
            flash(f"An error occurred: {str(e)}")
    
    return render_template('index.html', summary=summary)

if __name__ == "__main__":
    app.run(debug=True)