from flask import Flask, request, jsonify
import os
import slack_sdk
from slack_sdk.web import WebClient
from slack_sdk.signature import SignatureVerifier
from rag_model import get_rag_response


app = Flask(__name__)

slack_token = "xoxb-8848313668450-8848330175890-NxONtME4RybfiHlAZfIDsJVf"
signing_secret = "165bb0d941425645b37d1ff7a6d77f30"

client = WebClient(token=slack_token)
verifier = SignatureVerifier(signing_secret)


@app.route("/slack/events", methods=["POST"])
def slack_events():
    if not verifier.is_valid_request(request.get_data(), request.headers):
        return "Request verification failed", 403

    event_data = request.json

    if "challenge" in event_data:
        return jsonify({"challenge": event_data["challenge"]})

    if "event" in event_data:
        event = event_data["event"]

        if event.get("type") == "app_mention":
            user = event["user"]
            text = event["text"]
            channel = event["channel"]

            # Change this to your RAG model's response function
            # This is where you would call your RAG model
            # For example, if you have a function `get_rag_response`:
            response_text = get_rag_response(text)

            # Respond to Slack
            client.chat_postMessage(
                channel=channel,
                text=f"<@{user}> {response_text}"
            )

    return "OK", 200

@app.route("/slack/commands", methods=["POST"])
def slack_commands():
    data = request.form
    command = data.get("command")
    if command == "/ping":
        return jsonify({
            "response_type": "in_channel",
            "text": "Pong! 🚀"
        })
    return "Unknown command", 200

if __name__ == "__main__":
    app.run(debug=True,port=3000)
