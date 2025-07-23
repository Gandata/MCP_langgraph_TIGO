import os
from google import genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key from environment variable
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Create the client instance
client = genai.Client(api_key=GOOGLE_API_KEY)

# Send a simple message to the model
response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents="Hola"
)

# Print the model's response
print(response.text)
