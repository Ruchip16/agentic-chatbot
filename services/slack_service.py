from flask import Flask, request, jsonify
import os
# import slack_sdk
from slack_sdk.web import WebClient
from slack_sdk.signature import SignatureVerifier
import requests
import json
import threading
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

slack_token = os.getenv("SLACK_BOT_TOKEN")
signing_secret = os.getenv("SLACK_APP_SECRET")

client = WebClient(token=slack_token)
verifier = SignatureVerifier(signing_secret)

def get_rag_response(query: str) -> str:
    agent_service_url = f"{os.getenv('AGENT_SERVICE_URL')}/query"
    try:
        response = requests.post(
            agent_service_url,
            json={"query": query},
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        result = response.json()
        return result.get("response", "No response received from agent")
    except requests.exceptions.RequestException as e:
        print(f"Error querying agent service: {e}")
        return f"Sorry, I couldn't reach the knowledge base. Error: {str(e)}"
    except json.JSONDecodeError:
        print(f"Invalid response from agent service: {response.text}")
        return "Sorry, I received an invalid response from the knowledge base."

def send_delayed_response(response_url: str, user_id: str, query: str):
    """Process the query and send the response back to Slack."""
    response_text = get_rag_response(query)
    payload = {
        "response_type": "in_channel",  # or "ephemeral" for private replies
        "text": f"<@{user_id}> {response_text}"
    }
    try:
        requests.post(response_url, json=payload)
    except requests.exceptions.RequestException as e:
        print(f"Error sending response to Slack: {e}")

@app.route("/slack/prompt", methods=["POST"])
def slack_prompt():
    # Verify the request (optional, but recommended)
    if not verifier.is_valid_request(request.get_data(), request.headers):
        return jsonify({"text": "Invalid request signature"}), 403

    data = request.form
    user_id = data.get("user_id")
    query = data.get("text")
    response_url = data.get("response_url")  # Slack provides this for delayed responses

    # Start a background thread to process the query
    thread = threading.Thread(target=send_delayed_response, args=(response_url, user_id, query))
    thread.start()

    # Immediately acknowledge the command
    return jsonify({
        "response_type": "in_channel",
        "text": "Processing your request, please wait..."
    })

@app.route("/slack/commands", methods=["POST"])
def slack_commands():
    data = request.form
    command = data.get("command")
    if command == "/ping":
        return jsonify({
            "response_type": "in_channel",
            "text": "Pong! 🚀"
        })
    return jsonify({"text": "Unknown command"}), 200

if __name__ == "__main__":
    app.run(debug=True, port=3000)
