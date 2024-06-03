# Import necessary modules
from flask import Flask, request, jsonify, stream_with_context, Response, send_from_directory
import requests
from flask_cors import CORS
import yaml
import json

# Initialize Flask application
app = Flask(__name__)
CORS(app)  # Enable CORS

# Load configuration from YAML file
with open("settings-vllm.yaml", 'r') as file:
    config = yaml.safe_load(file)

# Retrieve configuration parameters
OPENROUTER_API_KEY = config['openai']['api_key']
MODEL_NAME = config['openai']['model']
API_BASE = config['openai']['api_base']
REQUEST_TIMEOUT = config['openai']['request_timeout']

# In-memory chat history to store user interactions
chat_history = []

# Route to serve the main HTML page
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# Endpoint for handling user messages and providing responses
@app.route('/chat', methods=['POST'])
def chat():
    # Extract user message from request
    data = request.json
    user_message = data.get('message', '')
    
    # Append user message to chat history
    chat_history.append({"role": "user", "content": user_message})
    
    try:
        # Stream response from LLM
        response = stream_with_context(get_response_from_llm(user_message))
        return Response(response, content_type='text/event-stream')
    except Exception as e:
        # Return error message if there is an exception
        return jsonify({'error': str(e)}), 500

# Function to retrieve response from the Language Model (LLM)
def get_response_from_llm(message: str):
    # Construct API request URL and headers
    url = f"{API_BASE}/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Prepare payload with user message and chat history
    payload = {
        "model": MODEL_NAME,
        "messages": chat_history
    }
    
    # Make a POST request to the LLM API
    response = requests.post(url, headers=headers, json=payload, timeout=REQUEST_TIMEOUT, stream=True)
    response.raise_for_status()  # Raise an HTTPError for bad responses
    
    # Stream response from LLM API line by line
    for line in response.iter_lines():
        if line:
            decoded_line = line.decode('utf-8')
            try:
                # Parse JSON response and yield message content
                response_json = json.loads(decoded_line)
                chat_history.append(response_json['choices'][0]['message'])
                yield f"data: {json.dumps(response_json['choices'][0]['message'])}\n\n"
            except json.JSONDecodeError as e:
                # Continue iteration if there is an error parsing JSON
                continue

# Entry point for running the Flask application
if __name__ == '__main__':
    app.run(debug=True)
