import os
from google.cloud import storage
from google.oauth2 import service_account
from dotenv import load_dotenv
import vertexai
from vertexai.generative_models import GenerativeModel, Part
import time
from google.api_core import retry
from google.api_core import exceptions as google_exceptions

# Load environment variables
load_dotenv('.env.development.local')

# Project and bucket setup
project_id = "profound-vista-384310"
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")  # This should be "ig2newsletter"
GCS_CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Initialize Vertex AI
vertexai.init(project=project_id, location="us-central1")

# Initialize the model
model = GenerativeModel("gemini-1.5-pro-001")

def get_gcs_client():
    credentials = service_account.Credentials.from_service_account_file(
        GCS_CREDENTIALS_PATH, scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    return storage.Client(credentials=credentials)

@retry.Retry(predicate=retry.if_exception_type(google_exceptions.ServiceUnavailable))
def process_content_with_retry(blob_name: str, prompt: str):
    file_uri = f"gs://{GCS_BUCKET_NAME}/{blob_name}"
    mime_type = "video/mp4" if blob_name.endswith('.mp4') else "image/jpeg"
    
    file_part = Part.from_uri(file_uri, mime_type=mime_type)
    contents = [file_part, prompt]

    response = model.generate_content(contents)
    return response.text

def process_instagram_data(prompt: str):
    storage_client = get_gcs_client()
    bucket = storage_client.bucket(GCS_BUCKET_NAME)
    
    all_texts = []
    for blob in bucket.list_blobs(prefix="instagram_content/"):
        try:
            text = process_content_with_retry(blob.name, prompt)
            all_texts.append(text)
        except Exception as e:
            print(f"Error processing {blob.name}: {str(e)}")
        time.sleep(1)  # Add a small delay between requests
    
    return "\n\n".join(all_texts)

# Prompts for video and image processing
universal_prompt = """
**Instructions:**

1. **Context:** You will be provided with a series of images and videos sourced from an Instagram content creator's profile. Each piece of content is a snapshot of the creator's weekly activity on the platform.
2. **Objective:**  Your task is to create a weekly digest that captures the essence of this content, transforming it into a cohesive and engaging newsletter format.
3. **Tone and Style:** The digest should be written in the creator's voice, using a warm, personal, and informative tone. Imagine you are the content creator speaking directly to their most loyal followers.
4. **Summary Approach:**
   - **Videos:** Summarize each video's core message or topic. Mention any key highlights, takeaways, or calls to action. Avoid simply describing the visuals. Instead, focus on the meaning or value the creator intended to convey.
   - **Images:** Briefly describe the image's subject, context, and any accompanying text or captions. If the image is part of a series (e.g., carousel), connect the images to create a narrative flow.
5. **Structure:** 
   - Begin with a friendly greeting (e.g., "Hey there!").
   - Organize the content into logical sections or themes.
   - Use subheadings to guide the reader.
   - Conclude with a personal note, call to action, or teaser for upcoming content. 
6. **Newsletter Format:**  
   - Keep paragraphs concise and easy to read.
   - Use bullet points or numbered lists for clarity.
   - Incorporate relevant emojis or informal language if it aligns with the creator's style.
   - Use line breaks and paragraphs to separate different sections and ideas.
7. **Additional Considerations:**
   - Assume the audience is already familiar with the creator and their content.
   - Prioritize highlighting valuable insights, discussions, or announcements.
   - Feel free to inject personality and humor where appropriate.

**Example Output Format:**

Hey!

Another week gone by, here's a quick recap of what I've been up to:

**[Section/Theme 1]**
* [Video/Image summary 1]
* [Video/Image summary 2] 

**[Section/Theme 2]**
* [Video/Image summary 3]
* [Video/Image summary 4]

[Concluding remarks, call to action, or teaser]
"""

if __name__ == "__main__":
    result = process_instagram_data(universal_prompt)
    print(result)
    
    # Optionally, save the result to a file
    with open("weekly_digest.txt", "w") as f:
        f.write(result)