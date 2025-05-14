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


@app.route("/slack/prompt", methods=["POST"])
def slack_prompt():
    data = request.form
    user_id = data.get("user_id")
    query = data.get("text")  # This is the user's prompt message

    # Change this to your RAG model's response function
    # This is where you would call your RAG model
    # For example, if you have a function `get_rag_response`:
    response = get_rag_response(query)

    # Respond back publicly in the slack channel or privately to the user
    return jsonify({
        "response_type": "in_channel",  # or "ephemeral" for private replies
        "text": f"<@{user_id}> {response}"
    })


if __name__ == "__main__":
    app.run(debug=True,port=3000)
