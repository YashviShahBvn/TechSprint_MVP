# app.py - Main Flask Application
import os
import json
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from werkzeug.utils import secure_filename
from google import genai
from google.genai import types
from dotenv import load_dotenv
from PIL import Image

# Load environment variables
load_dotenv()

# Configure Gemini API
client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'pdf'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_invoice_schema():
    """Return the JSON schema for invoice parsing."""
    return {
        "invoice_details": {
            "invoice_no": None,
            "date": None,
            "invoice_type": None
        },
        "vendor_details": {
            "name": None,
            "address": None,
            "phone": None,
            "email": None,
            "gstin": None,
            "pan": None
        },
        "bill_to": {
            "name": None,
            "address": None
        },
        "ship_to": None,
        "line_items": [],
        "tax_breakup": [],
        "totals": {
            "total_qty": None,
            "sub_total": None,
            "total_tax_amount": None,
            "grand_total": None,
            "grand_total_in_words": None,
            "currency": None
        },
        "terms_and_remarks": {
            "payment_terms": None,
            "validity": None,
            "shipping_terms": None,
            "notes": None
        }
    }


def parse_invoice_with_gemini(file_path):
    """Parse invoice using Gemini API."""
    try:
        # Create the prompt with schema
        schema = get_invoice_schema()
        prompt = f"""
You are an expert invoice data extraction system. Analyze the provided invoice image/PDF and extract all information into the following JSON structure. 

CRITICAL INSTRUCTIONS:
1. Extract ALL available information accurately
2. For missing fields, use null (not empty strings)
3. Maintain exact data types (numbers as numbers, not strings)
4. Return ONLY valid JSON, no markdown formatting
5. Ensure all required fields are present

JSON Schema to follow:
{json.dumps(schema, indent=2)}

Extract and return the complete invoice data in this exact JSON format.
"""
        
        # Read file
        file_ext = file_path.rsplit('.', 1)[1].lower()
        
        if file_ext == 'pdf':
            # Upload PDF file
            uploaded_file = client.files.upload(path=file_path)
            response = client.models.generate_content(
                model='models/gemini-2.5-flash',
                contents=[
                    types.Content(
                        role='user',
                        parts=[
                            types.Part.from_text(prompt),
                            types.Part.from_uri(file_uri=uploaded_file.uri, mime_type=uploaded_file.mime_type)
                        ]
                    )
                ]
            )
        else:
            # Process image
            img = Image.open(file_path)
            response = client.models.generate_content(
                model='models/gemini-2.5-flash',
                contents=[prompt, img]
            )
        
        # Extract JSON from response
        response_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        
        response_text = response_text.strip()
        
        # Parse JSON
        invoice_data = json.loads(response_text)
        
        return invoice_data
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON response: {str(e)}")
    except Exception as e:
        raise Exception(f"Error parsing invoice: {str(e)}")


@app.route('/')
def index():
    """Serve the main page."""
    return render_template('index.html')


@app.route('/api/parse-invoice', methods=['POST'])
def parse_invoice():
    """API endpoint to parse uploaded invoice."""
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            # Parse invoice
            invoice_data = parse_invoice_with_gemini(filepath)
            
            # Clean up uploaded file
            os.remove(filepath)
            
            return jsonify(invoice_data), 200
            
        except Exception as e:
            # Clean up on error
            if os.path.exists(filepath):
                os.remove(filepath)
            raise e
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'}), 200


if __name__ == '__main__':
    # Check if API key is set
    if not os.getenv('GEMINI_API_KEY'):
        print("ERROR: GEMINI_API_KEY not found in environment variables")
        print("Please create a .env file with GEMINI_API_KEY=your_api_key")
        exit(1)
    
    app.run(debug=True, host='0.0.0.0', port=8080)