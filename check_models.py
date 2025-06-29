# check_models.py
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables from .env file
print("Loading .env file...")
load_dotenv()
print("...done.")

# Configure the API client
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("\nERROR: GOOGLE_API_KEY not found in .env file.")
else:
    genai.configure(api_key=api_key)
    print("\nSuccessfully configured API key. Listing models that support 'generateContent':\n")
    
    try:
        for m in genai.list_models():
            # We only care about models that can generate text content
            if 'generateContent' in m.supported_generation_methods:
                print(f"-> {m.name}")
    except Exception as e:
        print(f"An error occurred while listing models: {e}")