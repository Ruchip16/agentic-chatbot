# 🤖 Agentic Chatbot: Navigating Red Hat Internal resources from THE SOURCE

## Overview

The Agentic Chatbot is an intelligent assistant designed to help Red Hat associates navigate internal resources efficiently.

## Project Goals

- Simplify access to internal documentation
- Reduce onboarding friction
- Provide intelligent, context-aware resource discovery

## Use Case

Instead of navigating the Source portal manually, associates can ask:

- "What is the process for updating a Red Hat product?"
- "Where can I find the latest documentation for a specific product?"
- "How do I resolve a common issue with a Red Hat product?"

And receive:

- Direct answers
- Links to the exact documents/pages
- Context-aware follow-up suggestions

## Technical Architecture

### Core Components

| Layer         | Technology                          |
|---------------|--------------------------------------|
| **Backend**   | Python + FastAPI / Flask             |
| **LLMs**      | OpenAI GPT, Ollama, Hugging Face     |
| **Vector DB** | ChromaDB / FAISS                     |
| **Embeddings**| Hugging Face Transformers            |
| **Frontend**  | Slack Bot (via Slack Bolt SDK)|

### Agentic Workflow

The chatbot operates on a **multi-agent architecture**, where each agent specializes in a sub-task:

- **Query Understanding Agent**
  Interprets user inputs into actionable formats.

- **Content Indexing Agent**
  Parses documents and pushes them to a vector database after generating embeddings.

- **Response Generation Agent**
  Retrieves relevant data and composes human-like, informative replies.

## Slack Integration

The chatbot is tightly integrated with Slack for enterprise accessibility:

- Users interact via DM or threads
- Replies include embedded links to Source documents
- Backend uses Slack Bolt SDK with FastAPI
- Events are securely handled with workspace-level tokens

## Key Features

- **Semantic Search**
  Leverages vector embeddings to match intent with content, even for vague queries

- **Model Flexibility**
  Easily swap between OpenAI, Hugging Face, or locally hosted models via Ollama

- **Microservice Architecture**
  Modular design allows for scaling and independent agent upgrades

- **Multilingual Support**
  Via Hugging Face embeddings and tokenizers

- **Secure Document Handling**
  Respects access controls and data privacy protocols

## Impact

- **Significantly reduces time** spent navigating documentation manually
- **Improves onboarding** experience for new Red Hatters
- **Promotes self-service** culture and reduces dependency on internal channels
- **Lays foundation** for enterprise-grade knowledge retrieval systems

## Future Scope

- **EagleView API Integration**
  Post-authentication, the chatbot can dynamically fetch the complete Source portal data and continuously update its knowledge base

- **Scalable to Entire Source Ecosystem**
  Once EagleView API access is enabled, the chatbot will be able to answer **all** questions across teams and departments

- **Credential-Aware Access Control**
  Role-based response customization based on user credentials

- **Intelligent Logging & Feedback Loop**
  Enable query analytics to improve answers through fine-tuning

- **Horizontally Scalable Architecture**
  Multi-agent system allows parallel processing, independent agent upgrades, and multi-tenant support

## Installation

```bash
# Clone the repository
git clone https://github.com/your-org/agentic-chatbot.git

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp sample.env .env
# Edit .env with your configurations
```

## Quick Start

### Running the Slack Bot
```bash
python services/slack_service.py
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

Distributed under the MIT License. See `LICENSE` for more information.
