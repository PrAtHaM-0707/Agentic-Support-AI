# Agentic Support AI

An advanced AI-powered customer support system that leverages multi-agent orchestration, Retrieval-Augmented Generation (RAG), and tool execution to provide intelligent, automated support ticket resolution.

## 🚀 Features

- **Multi-Agent Orchestration**: Uses LangGraph for coordinating multiple AI agents (analyzer, planner, retriever, decision, responder, supervisor, evaluator)
- **RAG Integration**: Qdrant vector database for context-aware responses
- **Tool Execution**: Supports payment checks, refunds, escalations, and custom tools
- **Planning & Self-Correction**: Agents can plan complex resolutions and self-correct based on evaluation
- **Quality Evaluation**: Built-in quality assessment and guardrails for response validation
- **Async Processing**: Background task processing for better performance
- **RESTful API**: FastAPI-based API with authentication
- **Database Integration**: PostgreSQL with SQLAlchemy ORM

## 🏗️ Architecture

The system consists of several key components:

### Core Components
- **Agents**: Specialized AI agents for different aspects of ticket processing
  - `analyzer.py`: Analyzes ticket content and categorizes issues
  - `planner.py`: Creates resolution plans for complex tickets
  - `retriever.py`: Retrieves relevant context from knowledge base
  - `decision.py`: Makes decisions on actions to take
  - `responder.py`: Generates responses with tool integration
  - `supervisor.py`: Oversees the entire workflow and handles escalations

### API Layer
- **Authentication**: JWT-based auth with signup/login endpoints
- **Tickets API**: CRUD operations for support tickets with AI processing

### Data Layer
- **Models**: User and Ticket models with relationships
- **Database**: PostgreSQL with SQLAlchemy
- **Vector Store**: Qdrant for RAG implementation

### AI/ML Components
- **LLM Integration**: Groq API for language model interactions
- **Embeddings**: Sentence Transformers for document embeddings
- **LangChain**: Memory and chain management
- **Evaluation**: Quality assessment and guardrail checking

## 📋 Prerequisites

- Python 3.8+
- PostgreSQL database
- Qdrant vector database
- Groq API key

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/PrAtHaM-0707/Agentic-Support-AI.git
   cd agentic-support-ai
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```env
   DATABASE_URL=postgresql://user:password@localhost:5432/support_db
   QDRANT_URL=http://localhost:6333
   GROQ_API_KEY=your_groq_api_key_here
   SECRET_KEY=your_secret_key_here
   ```

5. **Initialize database**
   ```bash
   python create_tables.py
   ```

6. **Initialize knowledge base** (optional)
   The knowledge base is initialized automatically on startup, but you can run it manually:
   ```python
   from app.core.init_kb import initialize_knowledge_base
   initialize_knowledge_base()
   ```

## 🚀 Usage

1. **Start the server**
   ```bash
   uvicorn app.main:app --reload
   ```

2. **Access the API**
   - API documentation: http://localhost:8000/docs
   - Health check: http://localhost:8000/
   - System info: http://localhost:8000/system/info

### API Endpoints

#### Authentication
- `POST /auth/signup` - User registration
- `POST /auth/login` - User login

#### Tickets
- `POST /tickets/` - Create and process a support ticket
- `GET /tickets/me` - Get current user profile
- `GET /tickets/{ticket_id}` - Get ticket details

### Example Usage

```python
import requests

# Login
response = requests.post("http://localhost:8000/auth/login", json={
    "email": "user@example.com",
    "password": "password"
})
token = response.json()["access_token"]

# Create ticket
headers = {"Authorization": f"Bearer {token}"}
response = requests.post("http://localhost:8000/tickets/", 
    json={"content": "I can't access my account"},
    headers=headers
)
print(response.json())
```

## ⚙️ Configuration

### Environment Variables
- `DATABASE_URL`: PostgreSQL connection string
- `QDRANT_URL`: Qdrant server URL
- `GROQ_API_KEY`: API key for Groq LLM service
- `SECRET_KEY`: JWT secret key

### Database Setup
The system uses PostgreSQL. Run `create_tables.py` to initialize the schema.

### Vector Database
Qdrant is used for vector storage. Ensure Qdrant is running and accessible.

## 🤖 Agent Workflow

When a ticket is created, the system follows this workflow:

1. **Analysis**: Analyzer agent categorizes and analyzes the ticket
2. **Planning**: Planner creates a resolution plan if needed
3. **Supervision**: Supervisor decides the workflow path
4. **Retrieval**: Context is retrieved from knowledge base if required
5. **Decision**: Decision agent determines the appropriate action
6. **Response**: Responder generates the final response, potentially using tools
7. **Evaluation**: Quality evaluation and guardrail checking

## 🧪 Testing

Run tests (if available):
```bash
pytest
```

## 📊 Monitoring

- Health endpoint: `GET /`
- System info: `GET /system/info`
- Check logs for detailed processing information

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 🙏 Acknowledgments

- FastAPI for the web framework
- LangChain and LangGraph for agent orchestration
- Qdrant for vector database
- Groq for LLM services
- Sentence Transformers for embeddings
