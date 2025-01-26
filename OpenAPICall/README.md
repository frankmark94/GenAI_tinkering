# OpenAI API Integration Project

A personal project exploring various capabilities of OpenAI's APIs through a web interface. This application demonstrates integration with GPT-4, GPT-3.5, and DALL-E 3, showcasing different ways to interact with generative AI.

## Features

### 1. Query Console
- **Description**: Main interface for sending queries to GPT models
- **Endpoints**: 
  - `/submit-query` (POST) - Sends queries to OpenAI's Chat Completion API
- **Models**: 
  - GPT-4 Turbo (Latest)
  - GPT-4 (Base)
  - GPT-4 Turbo (Previous)
  - GPT-3.5 Turbo
  - GPT-3.5 Turbo 16K
- **Features**:
  - Model selection
  - Email results option
  - JSON response formatting
  - Download responses as JSON files
  - Query history tracking

### 2. Weather Widget
- **Description**: Generates weather descriptions and matching images
- **Endpoints**:
  - `/get-weather` (POST) - Calls both GPT-4 and DALL-E 3
- **Features**:
  - Natural language weather descriptions
  - AI-generated weather visualization
  - Support for all 50 US states
  - Weather history tracking

[Insert weather widget screenshot here - showing both the weather description and DALL-E generated image]

### 3. Database Schema Generator
- **Description**: Creates SQL database schemas from natural language descriptions
- **Endpoints**:
  - `/generate-schema` (POST) - Generates schema using GPT-4
- **Features**:
  - SQL schema generation
  - Sample data generation
  - Entity Relationship diagram visualization
  - Data analytics visualization
  - Schema history tracking

[Insert schema generator screenshot here - showing the schema, sample data, and ER diagram]

### 4. AWS Flashcards
- **Description**: Generates AWS Solutions Architect certification study materials
- **Endpoints**:
  - `/generate-flashcards` (POST) - Creates flashcards using GPT-4
- **Features**:
  - Interactive flashcards
  - Exam-style questions
  - Detailed explanations
  - Flashcard history tracking

[Insert flashcards screenshot here - showing both question and answer sides]

### 5. Token Usage Analytics
- **Description**: Tracks and visualizes API usage and costs
- **Endpoints**:
  - `/token-usage` (GET/POST) - Retrieves and records token usage
- **Features**:
  - Real-time token tracking
  - Cost calculation
  - Usage visualization
  - Historical data tracking

[Insert token usage screenshot here - showing the graph and usage table]

## Setup

1. Clone the repository
2. Create a `.env` file with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the application:
   ```bash
   python app.py
   ```

## Project Structure

- `app.py` - Flask application with all route handlers
- `main.py` - Core OpenAI API interaction functions
- `database.py` - SQLite database management
- `email_sender.py` - Email functionality
- `static/` - CSS, JavaScript, and other static files
- `templates/` - HTML templates
  - `base.html` - Base template with common elements
  - `content/` - Individual page templates
    - `query_console.html`
    - `ai_tools.html`
    - `database.html`
    - `token_usage.html`
    - `flashcards.html`

## Environment Variables

Required environment variables in `.env`:
- `OPENAI_API_KEY` - Your OpenAI API key

Optional email settings:
- `SMTP_SERVER` - Email server (default: smtp.gmail.com)
- `SMTP_PORT` - Server port (default: 587)
- `SENDER_EMAIL` - Sender's email address
- `SENDER_PASSWORD` - Email account password/app password

## Notes

- All API responses are formatted as JSON for consistency
- Token usage is tracked for all API calls
- The application uses SQLite for data persistence
- DALL-E 3 images are generated in standard quality (1024x1024)

## Future Improvements

- Add user authentication
- Implement rate limiting
- Add export functionality for history data
- Enhance visualization options
- Add more AI tools and widgets 