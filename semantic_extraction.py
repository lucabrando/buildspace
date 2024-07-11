import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import os
import time
from pathlib import Path

# Load the API key from the environment variable
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

# Directory containing the content
content_directory = Path("/Users/lucabrandosanfilippo/GitHub Folder/buildspace/content_from_user")

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

# Initialize the model
model = genai.GenerativeModel(model_name="models/gemini-1.5-pro")

def process_file(file_path, prompt):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Upload the file
            print(f"Uploading file {file_path}...")
            sample_file = genai.upload_file(path=str(file_path), display_name=file_path.name)
            print(f"Completed upload: {sample_file.uri}")

            # Wait for the file to be processed if it's a video
            if file_path.suffix.lower() in ['.mp4', '.mov', '.avi']:
                while sample_file.state.name == "PROCESSING":
                    print('.', end='')
                    time.sleep(10)
                    sample_file = genai.get_file(sample_file.name)

                if sample_file.state.name == "FAILED":
                    raise ValueError(sample_file.state.name)

            # Generate content using the uploaded file and the prompt
            print("Making LLM inference request...")
            response = model.generate_content(
                [sample_file, prompt],
                generation_config={
                    "temperature": 0.3,
                    "top_p": 1,
                    "top_k": 32,
                    "max_output_tokens": 4096,
                },
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                },
                request_options={"timeout": 600}
            )
            return response.text
        except Exception as e:
            if "500" in str(e) and attempt < max_retries - 1:
                print(f"Error processing file {file_path.name}: {str(e)}. Retrying ({attempt + 1}/{max_retries})...")
                time.sleep(5)  # Wait before retrying
            else:
                return f"Error processing file {file_path.name}: {str(e)}"

def main():
    if not content_directory.exists():
        print(f"The folder {content_directory} does not exist.")
        return

    all_texts = []

    for file in content_directory.iterdir():
        if file.suffix.lower() in ['.mp4', '.mov', '.avi']:
            print(f"Processing video: {file.name}")
            text = process_file(file, universal_prompt)
            all_texts.append(text)
        elif file.suffix.lower() in ['.jpg', '.jpeg', '.png']:
            print(f"Processing image: {file.name}")
            text = process_file(file, universal_prompt)
            all_texts.append(text)

    combined_text = "\n".join(all_texts)
    return combined_text

if __name__ == "__main__":
    print(main())