import os
import requests
import hashlib
import shutil

# Function to create directory if it doesn't exist
def create_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

# Function to clear the directory
def clear_directory(directory):
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')

# Function to download content from a URL
def download_content(url, directory, is_video):
    response = requests.get(url)
    
    # Generate a hash of the URL to use as the filename
    file_name = hashlib.md5(url.encode()).hexdigest()
    
    # Determine the file extension based on the content type
    file_extension = ".mp4" if is_video else ".jpg"
    
    # Combine the directory, filename, and extension to get the full file path
    file_path = os.path.join(directory, file_name + file_extension)

    # Write the content to the file
    with open(file_path, 'wb') as file:
        file.write(response.content)
    
    return file_path