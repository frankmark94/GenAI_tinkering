from flask import Flask, render_template, request, jsonify
from main import call_openai_api
from email_sender import EmailSender
import os
from dotenv import load_dotenv
from openai import OpenAI
from database import Database
import json


# Load environment variables
load_dotenv()

app = Flask(__name__)

# Email configuration
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
SENDER_PASSWORD = os.getenv('SENDER_PASSWORD')

# At the top of app.py, after loading environment variables
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY must be set in environment variables")

# Initialize database
db = Database()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit-query', methods=['POST'])
def submit_query():
    try:
        data = request.get_json()
        send_email = data.get('sendEmail', False)
        recipient_email = data.get('email')
        prompt = data.get('prompt')
        model = data.get('model', 'gpt-4-0125-preview')  # Default to GPT-4 Turbo if not specified
        
        if not prompt:
            return jsonify({
                'message': 'Prompt is required'
            }), 400
            
        if send_email and not recipient_email:
            return jsonify({
                'message': 'Email is required when email sending is enabled'
            }), 400
        
        # Call OpenAI API with specified model
        result, filepath = call_openai_api(prompt, model=model)
        
        # Send email if enabled
        if send_email:
            email_sender = EmailSender(SMTP_SERVER, SMTP_PORT)
            email_sent = email_sender.send_results(
                result,
                SENDER_EMAIL,
                SENDER_PASSWORD,
                recipient_email
            )
            
            if not email_sent:
                return jsonify({
                    'message': 'Query processed but failed to send email. Please try again.',
                    'result': result
                }), 500
        
        # Save to database
        db.save_query(model, prompt, result, send_email)
        
        # Get token usage from the response
        token_usage = result.get('usage', {})
        if token_usage:
            estimated_cost = calculate_cost(
                model,
                token_usage.get('prompt_tokens', 0),
                token_usage.get('completion_tokens', 0)
            )
            db.save_token_usage(
                'General Query',
                model,
                token_usage.get('prompt_tokens', 0),
                token_usage.get('completion_tokens', 0),
                token_usage.get('total_tokens', 0),
                estimated_cost
            )
        
        return jsonify({
            'message': 'Query processed successfully!' + 
                      (' Check your email for results.' if send_email else ''),
            'result': result,
            'filepath': filepath
        })
            
    except Exception as e:
        return jsonify({
            'message': f'An error occurred: {str(e)}'
        }), 500

@app.route('/get-weather', methods=['POST'])
def get_weather():
    try:
        data = request.get_json()
        city = data.get('city')
        state = data.get('state')
        
        if not city or not state:
            return jsonify({
                'message': 'City and state are required'
            }), 400
            
        # Create weather query prompt
        weather_prompt = f"""Return a detailed current weather description for {city}, {state} in JSON format.
        Include temperature, conditions, humidity, wind speed, and a brief forecast.
        Format as: {{"temperature": "X°F", "conditions": "...", "humidity": "X%", "wind_speed": "X mph", "forecast": "..."}}"""
        
        # Get weather data from OpenAI
        weather_data, _ = call_openai_api(weather_prompt)
        
        # Track token usage for weather query
        if 'usage' in weather_data:
            estimated_cost = calculate_cost(
                'gpt-4-0125-preview',  # or get from request
                weather_data['usage'].get('prompt_tokens', 0),
                weather_data['usage'].get('completion_tokens', 0)
            )
            db.save_token_usage(
                'Weather Query',
                'gpt-4-0125-preview',  # or get from request
                weather_data['usage'].get('prompt_tokens', 0),
                weather_data['usage'].get('completion_tokens', 0),
                weather_data['usage'].get('total_tokens', 0),
                estimated_cost
            )

        # Create DALL-E prompt based on weather
        conditions = weather_data.get('conditions', '')
        time_of_day = "daytime"  # You could make this dynamic based on current time
        dalle_prompt = f"A beautiful, realistic photograph showing the weather in {city} with {conditions} during {time_of_day}. Wide angle city view."
        
        # Track DALL-E usage (approximate as it's per image)
        dalle_cost = 0.040  # $0.040 per image for DALL-E 3 standard quality
        db.save_token_usage(
            'DALL-E Image',
            'dall-e-3',
            0,  # DALL-E doesn't use tokens
            0,
            0,
            dalle_cost
        )
        
        # Generate image with DALL-E using the environment variable
        client = OpenAI(api_key=OPENAI_API_KEY)
        image_response = client.images.generate(
            model="dall-e-3",
            prompt=dalle_prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        
        # Format weather description
        weather_description = f"""
            <p><strong>Temperature:</strong> {weather_data.get('temperature')}</p>
            <p><strong>Conditions:</strong> {weather_data.get('conditions')}</p>
            <p><strong>Humidity:</strong> {weather_data.get('humidity')}</p>
            <p><strong>Wind Speed:</strong> {weather_data.get('wind_speed')}</p>
            <p><strong>Forecast:</strong> {weather_data.get('forecast')}</p>
        """
        
        # Save to database
        db.save_weather_query(city, state, weather_data, image_response.data[0].url)
        
        return jsonify({
            'weather_description': weather_description,
            'image_url': image_response.data[0].url
        })
            
    except Exception as e:
        return jsonify({
            'message': f'An error occurred: {str(e)}'
        }), 500

@app.route('/generate-schema', methods=['POST'])
def generate_schema():
    try:
        data = request.get_json()
        description = data.get('description')
        
        if not description:
            return jsonify({
                'message': 'Table description is required'
            }), 400
            
        # Create schema generation prompt
        schema_prompt = f"""Create a SQL database schema and sample data for: {description}
        Return as JSON with the following structure:
        {{
            "schema": {{
                "table_name": "name_of_table",
                "columns": [
                    {{"name": "column_name", "type": "data_type", "constraints": "any_constraints"}}
                ],
                "sql": "complete CREATE TABLE statement"
            }},
            "sample_data": [
                // 5 rows of realistic sample data as objects
            ]
        }}
        Ensure the schema is properly normalized and includes appropriate primary keys, foreign keys, and constraints."""
        
        # Get schema from OpenAI
        schema_data, _ = call_openai_api(schema_prompt)
        
        # Track token usage for schema generation
        if 'usage' in schema_data:
            estimated_cost = calculate_cost(
                'gpt-4-0125-preview',  # or get from request
                schema_data['usage'].get('prompt_tokens', 0),
                schema_data['usage'].get('completion_tokens', 0)
            )
            db.save_token_usage(
                'Schema Generation',
                'gpt-4-0125-preview',  # or get from request
                schema_data['usage'].get('prompt_tokens', 0),
                schema_data['usage'].get('completion_tokens', 0),
                schema_data['usage'].get('total_tokens', 0),
                estimated_cost
            )
        
        # Format the schema for display
        formatted_schema = f"""Table: {schema_data['schema']['table_name']}

Columns:
{chr(10).join(f"- {col['name']} ({col['type']}) {col['constraints']}" for col in schema_data['schema']['columns'])}

SQL:
{schema_data['schema']['sql']}"""
        
        # Save to database
        db.save_schema_query(description, schema_data['schema'], schema_data['sample_data'])
        
        return jsonify({
            'schema': formatted_schema,
            'sample_data': schema_data['sample_data']
        })
            
    except Exception as e:
        return jsonify({
            'message': f'An error occurred: {str(e)}'
        }), 500

@app.route('/history/queries')
def query_history():
    history = db.get_query_history()
    return jsonify([{
        'id': h[0],
        'timestamp': h[1],
        'model': h[2],
        'prompt': h[3],
        'response': json.loads(h[4]),
        'email_sent': h[5]
    } for h in history])

@app.route('/history/weather')
def weather_history():
    history = db.get_weather_history()
    return jsonify([{
        'id': h[0],
        'timestamp': h[1],
        'city': h[2],
        'state': h[3],
        'weather_data': json.loads(h[4]),
        'image_url': h[5]
    } for h in history])

@app.route('/history/schemas')
def schema_history():
    history = db.get_schema_history()
    return jsonify([{
        'id': h[0],
        'timestamp': h[1],
        'description': h[2],
        'schema_data': json.loads(h[3]),
        'sample_data': json.loads(h[4])
    } for h in history])

@app.route('/token-usage')
def token_usage():
    usage = db.get_token_usage()
    return jsonify([{
        'id': u[0],
        'timestamp': u[1],
        'request_type': u[2],
        'model': u[3],
        'prompt_tokens': u[4],
        'completion_tokens': u[5],
        'total_tokens': u[6],
        'estimated_cost': u[7]
    } for u in usage])

@app.route('/token-usage', methods=['POST'])
def track_token_usage():
    try:
        data = request.get_json()
        
        # Calculate cost based on the model
        estimated_cost = calculate_cost(
            data.get('model', 'gpt-4-0125-preview'),
            data.get('prompt_tokens', 0),
            data.get('completion_tokens', 0)
        )
        
        # Save to database
        db.save_token_usage(
            data.get('request_type', 'AI Generation'),
            data.get('model', 'gpt-4-0125-preview'),
            data.get('prompt_tokens', 0),
            data.get('completion_tokens', 0),
            data.get('total_tokens', 0),
            estimated_cost
        )
        
        return jsonify({'message': 'Token usage tracked successfully'})
            
    except Exception as e:
        return jsonify({
            'message': f'An error occurred: {str(e)}'
        }), 500

@app.route('/generate-flashcards', methods=['POST'])
def generate_flashcards():
    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        # System message to ensure proper AWS SA exam style questions
        system_message = """You are an AWS Solutions Architect exam question generator.
        Generate 5 unique exam-style questions with detailed answers.
        Focus on different AWS services and concepts in each question.
        Return the response in JSON format with an array of objects containing 'question' and 'answer' fields.
        Format the response as:
        {
            "flashcards": [
                {
                    "question": "Question text here",
                    "answer": "Detailed answer here"
                },
                ...
            ]
        }"""
        
        response = client.chat.completions.create(
            model="gpt-4-0125-preview",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": "Generate 5 AWS Solutions Architect exam questions with answers"}
            ],
            response_format={"type": "json_object"}
        )
        
        # Parse the response
        content = json.loads(response.choices[0].message.content)
        
        # Track token usage
        db.save_token_usage(
            request_type="Flashcard Generation",
            model="gpt-4-0125-preview",
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens,
            estimated_cost=calculate_cost(
                "gpt-4-0125-preview",
                response.usage.prompt_tokens,
                response.usage.completion_tokens
            )
        )
        
        return jsonify(content)
    except json.JSONDecodeError as e:
        print("JSON parsing error:", str(e))
        print("Raw response:", response.choices[0].message.content)
        return jsonify({"error": "Invalid JSON response from OpenAI"}), 500
    except Exception as e:
        print("Error generating flashcards:", str(e))
        return jsonify({"error": str(e)}), 500

@app.route('/history/flashcards')
def flashcard_history():
    history = db.get_flashcard_history()  # You'll need to implement this in your Database class
    return jsonify([{
        'id': h[0],
        'timestamp': h[1],
        'flashcards': json.loads(h[2])
    } for h in history])

# Add this function to calculate costs
def calculate_cost(model, prompt_tokens, completion_tokens):
    # GPT-4 pricing (as of 2024)
    pricing = {
        'gpt-4-0125-preview': {'prompt': 0.01, 'completion': 0.03},  # per 1K tokens
        'gpt-4': {'prompt': 0.03, 'completion': 0.06},
        'gpt-4-1106-preview': {'prompt': 0.01, 'completion': 0.03},
        'gpt-3.5-turbo': {'prompt': 0.0005, 'completion': 0.0015},
        'gpt-3.5-turbo-16k': {'prompt': 0.001, 'completion': 0.002},
    }
    
    if model not in pricing:
        return 0.0
    
    prompt_cost = (prompt_tokens / 1000) * pricing[model]['prompt']
    completion_cost = (completion_tokens / 1000) * pricing[model]['completion']
    return prompt_cost + completion_cost

# Add this near the bottom of app.py, just before the if __name__ == '__main__': line
port = int(os.environ.get('PORT', 5000))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port) 