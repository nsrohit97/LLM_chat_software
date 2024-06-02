from flask import Flask, request, jsonify, send_from_directory
import requests
from flask_cors import CORS
import yaml

# Initialize Flask application
app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing (CORS)

# Load configuration from YAML file
with open("settings-vllm-sample.yaml", 'r') as file:
    config = yaml.safe_load(file)

# Extract necessary configuration variables
OPENROUTER_API_KEY = config['openai']['api_key']
MODEL_NAME = config['openai']['model']
API_BASE = config['openai']['api_base']
REQUEST_TIMEOUT = config['openai']['request_timeout']

@app.route('/')
def index():
    """Serve the index.html file when accessing the root URL."""
    return send_from_directory('.', 'index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """Handle POST requests to the /chat endpoint."""
    app.logger.info("Entering chat function")
    data = request.json  # Get JSON data from the request
    user_message = data.get('message', '')  # Extract user message
    try:
        response = get_response_from_llm(user_message)  # Get response from LLM
        app.logger.info("Response received from LLM")
        return jsonify({'response': response})  # Return response as JSON
    except Exception as e:
        app.logger.error(f"Error occurred: {e}")  # Log any errors
        return jsonify({'error': str(e)}), 500  # Return error as JSON with status 500

def get_response_from_llm(message: str) -> str:
    """Send a message to the language model and return the response."""
    url = f"{API_BASE}/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": message}]
    }
    response = requests.post(url, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()  # Raise an error for bad responses
    response_json = response.json()
    return response_json['choices'][0]['message']['content']  # Extract and return the response content

if __name__ == '__main__':
    app.run(debug=True)  # Run the Flask application in debug mode
