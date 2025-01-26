import os
import json
from datetime import datetime
from openai import OpenAI
from email_sender import EmailSender

def save_response(json_response, output_dir="responses"):
    """
    Save JSON response to a file with timestamp
    
    Args:
        json_response (dict): JSON response to save
        output_dir (str): Directory to save responses, defaults to 'responses'
    
    Returns:
        str: Path to saved file
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"response_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)
    
    # Save response to file
    with open(filepath, 'w') as f:
        json.dump(json_response, f, indent=2)
    
    return filepath

def call_openai_api(prompt, model="gpt-3.5-turbo"):
    """
    Call OpenAI API with a prompt and return JSON response
    
    Args:
        prompt (str): The prompt to send to OpenAI
        model (str): The model to use, defaults to gpt-3.5-turbo
        
    Returns:
        tuple: (dict: JSON response from OpenAI with usage info, str: path to saved file)
    """
    try:
        # Initialize OpenAI client with environment variable
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        print(f"Sending prompt to OpenAI: {prompt}")
        
        # Add system message to enforce JSON response
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": """You are a JSON-only response API. 
                Always respond with valid JSON only. 
                No natural language or explanations outside the JSON structure.
                If providing a list, always wrap it in a JSON object with a descriptive key.
                Example format: {"results": [...]} or {"data": {...}}"""},
                {"role": "user", "content": f"Return the following as properly formatted JSON: {prompt}"}
            ],
            temperature=0.7,
            response_format={ "type": "json_object" }  # Enforce JSON response format
        )
        
        # Extract the response text and usage information
        response_text = response.choices[0].message.content
        usage_data = {
            'prompt_tokens': response.usage.prompt_tokens,
            'completion_tokens': response.usage.completion_tokens,
            'total_tokens': response.usage.total_tokens
        }
        print(f"\nRaw response from OpenAI: {response_text}\n")
        print(f"Token usage: {usage_data}\n")
        
        # Parse JSON from response
        try:
            json_response = json.loads(response_text)
            # Add usage information to the response
            json_response['usage'] = usage_data
            saved_filepath = save_response(json_response)
            print(f"Successfully parsed JSON and saved to: {saved_filepath}")
            return json_response, saved_filepath
        except json.JSONDecodeError:
            print("Failed to parse JSON from response")
            error_response = {
                "error": "Response was not in valid JSON format", 
                "raw_response": response_text,
                "usage": usage_data
            }
            saved_filepath = save_response(error_response)
            return error_response, saved_filepath
            
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        error_response = {"error": str(e)}
        saved_filepath = save_response(error_response)
        return error_response, saved_filepath

# Example usage - uncommented for testing
if __name__ == "__main__":
    # Email configuration
    SENDER_EMAIL = "your_email@gmail.com"  # Replace with your email
    SENDER_PASSWORD = "your_app_password"   # Replace with your app password
    RECIPIENT_EMAIL = "recipient@email.com" # Replace with recipient email
    
    # Get API response
    prompt = 'Provide me with a list of the most common issues found in new homes, or homes which need ongoing maintenance, as well as the expected cost of repair. Response should only contain valid JSON.'
    result, filepath = call_openai_api(prompt)
    
    print("\nFinal Result:")
    print(f"Response: {json.dumps(result, indent=2)}")
    print(f"Saved to: {filepath}")
    
    # Send email with results
    email_sender = EmailSender()
    email_sender.send_results(
        result,
        SENDER_EMAIL,
        SENDER_PASSWORD,
        RECIPIENT_EMAIL
    )
