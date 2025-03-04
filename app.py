import os
import json
import secrets
import csv
import io
import datetime
from PIL import Image
from io import BytesIO
from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash, send_file, Response
from werkzeug.utils import secure_filename
import openai
from dotenv import load_dotenv
import re
import requests
from ebay_api import ebay_client

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', secrets.token_hex(16))

# Initialize eBay client with app
ebay_client.init_app(app)

# OpenAI API configuration
openai.api_key = os.getenv('OPENAI_API_KEY')

# Configure upload settings
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_UPLOADS = 12
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    # Reset session data if starting a new upload
    if 'reset' in request.form and request.form['reset'] == 'true':
        if 'uploaded_files' in session:
            # Remove previously uploaded files
            for file_path in session['uploaded_files']:
                try:
                    os.remove(os.path.join(app.root_path, file_path))
                except (FileNotFoundError, PermissionError):
                    pass
        session.pop('uploaded_files', None)
        session.pop('item_data', None)
        
    # Initialize session storage for uploaded files
    if 'uploaded_files' not in session:
        session['uploaded_files'] = []
    
    uploaded_files = session['uploaded_files']
    
    # Check if there are files in the request
    if 'files[]' not in request.files:
        return jsonify({'success': False, 'error': 'No files uploaded'})
    
    files = request.files.getlist('files[]')
    
    # Check if the user is trying to upload too many files
    if len(files) + len(uploaded_files) > MAX_UPLOADS:
        return jsonify({'success': False, 'error': f'Maximum {MAX_UPLOADS} photos allowed'})
    
    # Process and save each file
    for file in files:
        if file and allowed_file(file.filename):
            # Create a secure filename with timestamp to avoid duplicates
            filename = secure_filename(file.filename)
            file_ext = filename.rsplit('.', 1)[1].lower()
            random_filename = f"{secrets.token_hex(8)}.{file_ext}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], random_filename)
            
            # Save the file
            file.save(file_path)
            
            # Add to session
            relative_path = os.path.join('static', 'uploads', random_filename)
            uploaded_files.append(relative_path)
    
    session['uploaded_files'] = uploaded_files
    session.modified = True
    
    return jsonify({
        'success': True, 
        'files': uploaded_files,
        'count': len(uploaded_files)
    })

@app.route('/analyze', methods=['POST'])
def analyze_images():
    if 'uploaded_files' not in session or not session['uploaded_files']:
        return jsonify({'success': False, 'error': 'No images uploaded'})
    
    try:
        # Prepare images for vision API using base64 encoding
        image_contents = []
        for file_path in session['uploaded_files']:
            # Get the full path to the image file
            full_path = os.path.join(app.root_path, file_path)
            
            # Read the image file and encode it as base64
            with open(full_path, "rb") as image_file:
                import base64
                encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
                
                # Add properly formatted image content with base64 data
                image_contents.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{encoded_image}"
                    }
                })
        
        # Call OpenAI Vision API
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert eBay seller with years of experience creating high-converting auction listings. 
                    Your specialty is crafting compelling, detailed descriptions that highlight value and generate maximum bids.
                    You have a deep understanding of what makes buyers click "Bid Now" and how to create listings that stand out in search results.
                    Analyze the images provided to identify the item, focusing exclusively on details relevant for an eBay auction listing.
                    Be extremely thorough and detailed in your analysis, noting every relevant feature, flaw, and selling point."""
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """Please analyze these images of an item I want to sell on eBay. 
                            Create a professional eBay auction listing with the following eBay-specific fields:
                            
                            1. Title (use all 80 characters if possible, include key specs and high-value search terms)
                            2. Subtitle (optional, 55 characters max)
                            3. Category (use a real eBay category with the category ID number in parentheses - for example: "Video Games & Consoles > PlayStation 4 > Consoles (139971)")
                            4. Item Specifics:
                               - Brand
                               - Model/MPN (Manufacturer Part Number)
                               - Type/Style
                               - Size/Dimensions
                               - Color
                               - Material
                               - Condition (New, New other, Used, For parts/not working)
                               - Condition Description (detailed assessment of flaws/wear)
                            5. Price (starting bid and Buy It Now if applicable)
                            6. Item Description:
                               - Create a captivating, detailed description that builds desire
                               - Highlight unique features and benefits
                               - Address condition honestly but positively
                               - Include measurements and specifications
                               - Mention any included accessories or original packaging
                               - Add persuasive selling points that create urgency
                               - Use HTML formatting to make the description visually appealing
                               - Include bullet points for key features
                               - Use headings and subheadings to organize information
                            7. Shipping Details (weight estimate, recommended shipping methods)
                            8. Return Policy Recommendation
                            9. Keywords (for SEO)
                            
                            Structure your response as a JSON object with these exact field names:
                            {
                              "title": "Item title",
                              "subtitle": "Optional subtitle",
                              "category": "eBay category path with ID number",
                              "brand": "Brand name",
                              "model": "Model or MPN",
                              "type_style": "Type or style",
                              "color": "Color",
                              "size_dimensions": "Size or dimensions",
                              "material": "Material",
                              "condition": "New/New other/Used/For parts/not working",
                              "condition_description": "Detailed condition assessment",
                              "starting_price": "Starting bid amount (number only, no $ sign)",
                              "buy_it_now_price": "Buy It Now price (number only, no $ sign)",
                              "description": "Detailed item description with HTML formatting",
                              "included_items": "What's included with the item",
                              "shipping_details": "Shipping information",
                              "return_policy": "Return policy details",
                              "keywords": ["keyword1", "keyword2", "etc"]
                            }
                            
                            For the description, create compelling, benefit-focused content that will make buyers eager to bid. 
                            Use persuasive language that highlights value and creates emotional connection with the item.
                            Make the description visually appealing with HTML formatting - use <h2>, <h3>, <ul>, <li>, <strong>, <em> tags.
                            Include a section on condition, features, specifications, and why this item is worth bidding on.
                            The description should be at least 200 words and extremely detailed to maximize buyer interest."""
                        }
                    ] + image_contents
                }
            ],
            max_tokens=4000
        )
        
        # Extract JSON from response
        result_text = response.choices[0].message.content
        
        # Print the raw response for debugging
        print("Raw API response:")
        print(result_text)
        
        # Try to extract JSON from the response
        try:
            # Look for JSON in the response
            json_start = result_text.find('{')
            json_end = result_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = result_text[json_start:json_end]
                
                # Print the extracted JSON string for debugging
                print("Extracted JSON string:")
                print(json_str)
                
                item_data = json.loads(json_str)
                
                # Print the parsed JSON for debugging
                print("Parsed JSON data:")
                print(json.dumps(item_data, indent=2))
                
                # Map fields to ensure compatibility with our templates
                # Create a standardized structure with all our expected fields
                standardized_data = {
                    "title": item_data.get("title", ""),
                    "subtitle": item_data.get("subtitle", ""),
                    "category": item_data.get("category", ""),
                    "brand": item_data.get("brand", ""),
                    "model": item_data.get("model", "") or item_data.get("mpn", "") or item_data.get("model_mpn", ""),
                    "type_style": item_data.get("type_style", "") or item_data.get("type", "") or item_data.get("style", ""),
                    "color": item_data.get("color", ""),
                    "size_dimensions": item_data.get("size_dimensions", "") or item_data.get("size", "") or item_data.get("dimensions", ""),
                    "material": item_data.get("material", ""),
                    "condition": item_data.get("condition", "Used"),
                    "condition_description": item_data.get("condition_description", ""),
                    "starting_price": item_data.get("starting_price", "") or item_data.get("starting_bid", "") or 
                                     (item_data.get("price", {}).get("starting_bid") if isinstance(item_data.get("price"), dict) else ""),
                    "buy_it_now_price": item_data.get("buy_it_now_price", "") or item_data.get("buy_it_now", "") or 
                                       (item_data.get("price", {}).get("buy_it_now") if isinstance(item_data.get("price"), dict) else ""),
                    "description": item_data.get("description", "") or item_data.get("item_description", ""),
                    "included_items": item_data.get("included_items", "") or item_data.get("whats_included", "") or item_data.get("accessories", ""),
                    "shipping_details": item_data.get("shipping_details", "") or item_data.get("shipping", ""),
                    "return_policy": item_data.get("return_policy", ""),
                    "keywords": item_data.get("keywords", [])
                }
                
                # Handle price fields that might be in different formats
                if "price" in item_data and isinstance(item_data["price"], str):
                    price_str = item_data["price"]
                    if "-" in price_str:  # Handle price range
                        parts = price_str.replace("$", "").split("-")
                        if len(parts) == 2:
                            standardized_data["starting_price"] = parts[0].strip()
                            standardized_data["buy_it_now_price"] = parts[1].strip()
                    else:  # Single price
                        standardized_data["starting_price"] = price_str.replace("$", "").strip()
                
                # Use the standardized data
                item_data = standardized_data
            else:
                # If no JSON format found, parse the text into structured data
                item_data = {
                    "title": "Untitled Item",
                    "subtitle": "",
                    "category": "",
                    "brand": "",
                    "model": "",
                    "type_style": "",
                    "color": "",
                    "size_dimensions": "",
                    "material": "",
                    "condition": "Used",
                    "condition_description": "",
                    "starting_price": "",
                    "buy_it_now_price": "",
                    "description": result_text,
                    "included_items": "",
                    "shipping_details": "",
                    "return_policy": "",
                    "keywords": []
                }
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            item_data = {
                "title": "Untitled Item",
                "subtitle": "",
                "category": "",
                "brand": "",
                "model": "",
                "type_style": "",
                "color": "",
                "size_dimensions": "",
                "material": "",
                "condition": "Used",
                "condition_description": "",
                "starting_price": "",
                "buy_it_now_price": "",
                "description": result_text,
                "included_items": "",
                "shipping_details": "",
                "return_policy": "",
                "keywords": []
            }
            
        # Store the results in session
        session['item_data'] = item_data
        session.modified = True
        
        return jsonify({
            'success': True,
            'data': item_data
        })
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)})

@app.route('/generate-listing', methods=['POST'])
def generate_listing():
    if 'item_data' not in session:
        return redirect(url_for('index'))
    
    # Merge the original AI-generated data with any user edits
    item_data = session['item_data'].copy()
    form_data = request.form.to_dict()
    
    # Update item data with form inputs
    for key in form_data:
        if key in item_data or key in ['subtitle', 'condition_description', 'type_style', 'color', 
                                      'size_dimensions', 'material', 'starting_price', 'buy_it_now_price',
                                      'included_items', 'shipping_details', 'return_policy']:
            item_data[key] = form_data[key]
    
    # Store updated data
    session['item_data'] = item_data
    
    return render_template('listing.html', 
                          item=item_data, 
                          images=session.get('uploaded_files', []))

@app.route('/preview')
def preview():
    if 'item_data' not in session or 'uploaded_files' not in session:
        return redirect(url_for('index'))
        
    return render_template('preview.html', 
                          item=session['item_data'], 
                          images=session['uploaded_files'])

@app.route('/export')
def export():
    if 'item_data' not in session:
        return redirect(url_for('index'))
    
    # Generate HTML code for eBay listing
    listing_html = render_template('ebay_template.html', 
                                  item=session['item_data'],
                                  images=session['uploaded_files'])
    
    return render_template('export.html', 
                          listing_html=listing_html,
                          item=session['item_data'])

@app.route('/export-csv')
def export_csv():
    if 'item_data' not in session:
        return redirect(url_for('index'))
    
    item_data = session['item_data']
    images = session.get('uploaded_files', [])
    
    # Create a CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header rows (info rows)
    writer.writerow(['#INFO', 'Version=0.0.2', 'Template= eBay-draft-listings-template_US', '', '', '', '', '', '', ''])
    writer.writerow(['#INFO Action and Category ID are required fields. 1) Set Action to Draft 2) Please find the category ID for your listings here: https://pages.ebay.com/sellerinformation/news/categorychanges.html', '', '', '', '', '', '', '', '', '', ''])
    writer.writerow(['#INFO After you\'ve successfully uploaded your draft from the Seller Hub Reports tab, complete your drafts to active listings here: https://www.ebay.com/sh/lst/drafts', '', '', '', '', '', '', '', '', '', ''])
    writer.writerow(['#INFO', '', '', '', '', '', '', '', '', '', ''])
    
    # Write column headers
    writer.writerow([
        'Action(SiteID=US|Country=US|Currency=USD|Version=1193|CC=UTF-8)', 
        'Custom label (SKU)', 
        'Category ID', 
        'Title', 
        'UPC', 
        'Price', 
        'Quantity', 
        'Item photo URL', 
        'Condition ID', 
        'Description', 
        'Format'
    ])
    
    # Map condition to eBay condition ID
    condition_map = {
        'New': 'NEW',           # New with tags/New with box
        'New other': 'NEW_OTHER',     # New without tags/New without box
        'Used': 'USED',          # Used
        'For parts/not working': 'FOR_PARTS'  # For parts or not working
    }
    
    # Get condition ID - use text-based eBay condition IDs
    item_condition = item_data.get('condition', 'Used')
    condition_id = condition_map.get(item_condition, 'USED')
    
    # Print debug info about condition mapping
    print(f"Original condition: {item_condition}")
    print(f"Mapped condition ID: {condition_id}")
    
    # Get category ID (use a default if not available)
    # Try to extract just the numeric ID from the category string
    category_string = item_data.get('category', '')
    category_id = ''
    
    # Print debug info
    print(f"Original category string: {category_string}")
    
    # First try to find a numeric ID in parentheses (common eBay format)
    category_match = re.search(r'\((\d+)\)', category_string)
    if category_match:
        category_id = category_match.group(1)
        print(f"Found category ID in parentheses: {category_id}")
    # If not found, try to find a numeric ID at the end of the string
    elif re.search(r'(\d+)$', category_string):
        category_match = re.search(r'(\d+)$', category_string)
        category_id = category_match.group(1)
        print(f"Found category ID at end: {category_id}")
    # If not found, try to extract any numeric part
    elif re.search(r'(\d+)', category_string):
        category_match = re.search(r'(\d+)', category_string)
        category_id = category_match.group(1)
        print(f"Found category ID in string: {category_id}")
    # If still not found, try to extract the first part before any delimiter
    else:
        parts = re.split(r'[ \-:]', category_string)
        for part in parts:
            if part.isdigit():
                category_id = part
                print(f"Found category ID in parts: {category_id}")
                break
    
    # If still no valid category ID, use a default
    if not category_id or not category_id.isdigit():
        category_id = '139971'  # Default category ID - using PlayStation 4 category
        print(f"Using default category ID: {category_id}")
    else:
        # Validate that the category ID is reasonable (not too short, not too long)
        if len(category_id) < 3 or len(category_id) > 10:
            print(f"Category ID seems invalid (unusual length): {category_id}")
            # Common eBay category IDs for reference
            common_categories = {
                'electronics': '293',
                'computers': '58058',
                'phones': '9355',
                'clothing': '11450',
                'shoes': '3034',
                'toys': '220',
                'collectibles': '1',
                'home': '11700',
                'sporting_goods': '888',
                'jewelry': '281',
                'music': '11233',
                'video_games': '1249',
                'playstation': '139971',
                'xbox': '139973',
                'nintendo': '139972',
                'books': '267',
                'dvd': '617',
                'automotive': '6000',
                'business': '12576',
                'cameras': '625',
                'crafts': '14339'
            }
            
            # Try to guess the category from the title or description
            title_lower = item_data.get('title', '').lower()
            description_lower = item_data.get('description', '').lower()
            
            # Look for keywords in title and description
            for category_name, category_id_value in common_categories.items():
                if category_name in title_lower or category_name in description_lower:
                    category_id = category_id_value
                    print(f"Found better category ID from keywords: {category_id}")
                    break
            else:
                category_id = '220'  # Default to a common category (Toys & Hobbies)
                print(f"Using common category ID: {category_id}")
    
    # Get price
    price = item_data.get('buy_it_now_price', '') or item_data.get('starting_price', '')
    
    # Get image URL (use the first image if available)
    image_url = ''
    if images and len(images) > 0:
        # For a real production app, you would need to provide a publicly accessible URL
        # Here we're just using a placeholder or the local path
        image_url = request.url_root + images[0]
    
    # Create HTML description
    description = f"<p>{item_data.get('description', '')}</p>"
    
    if item_data.get('condition_description'):
        description += f"<p><strong>Condition:</strong> {item_data.get('condition_description')}</p>"
    
    if item_data.get('included_items'):
        description += f"<p><strong>What's Included:</strong> {item_data.get('included_items')}</p>"
    
    if item_data.get('shipping_details'):
        description += f"<p><strong>Shipping:</strong> {item_data.get('shipping_details')}</p>"
    
    if item_data.get('return_policy'):
        description += f"<p><strong>Returns:</strong> {item_data.get('return_policy')}</p>"
    
    # Write data row
    writer.writerow([
        'Draft',                          # Action
        '',                               # Custom label (SKU)
        category_id,                      # Category ID
        item_data.get('title', ''),       # Title
        '',                               # UPC
        price,                            # Price
        '1',                              # Quantity
        image_url,                        # Item photo URL
        condition_id,                     # Condition ID
        description,                      # Description
        'Auction'                         # Format (changed from 'FixedPrice' to 'Auction')
    ])
    
    # Prepare the CSV for download
    output.seek(0)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename=eBay-draft-listing-{timestamp}.csv"}
    )

@app.errorhandler(413)
def request_entity_too_large(error):
    flash('File too large! Maximum file size is 16MB.')
    return redirect(url_for('index')), 413

# eBay Integration Routes
@app.route('/auth/ebay')
def ebay_auth():
    """Start eBay OAuth flow"""
    authorization_url = ebay_client.get_authorization_url()
    return redirect(authorization_url)

@app.route('/auth/ebay/callback')
def ebay_callback():
    """Handle eBay OAuth callback"""
    code = request.args.get('code')
    if not code:
        flash('Authorization failed.')
        return redirect(url_for('index'))
    
    try:
        token = ebay_client.get_token_from_code(code)
        flash('Successfully connected to eBay!')
        return redirect(url_for('ebay_settings'))
    except Exception as e:
        flash(f'Error connecting to eBay: {str(e)}')
        return redirect(url_for('index'))

@app.route('/ebay/settings')
def ebay_settings():
    """eBay account settings page"""
    # Check if user is authenticated with eBay
    if 'ebay_token' not in session:
        return render_template('ebay_settings.html', authenticated=False)
    
    return render_template('ebay_settings.html', 
                          authenticated=True, 
                          email=session.get('ebay_paypal_email', ''),
                          postal_code=session.get('ebay_postal_code', ''))

@app.route('/ebay/settings/update', methods=['POST'])
def update_ebay_settings():
    """Update eBay settings"""
    session['ebay_paypal_email'] = request.form.get('paypal_email', '')
    session['ebay_postal_code'] = request.form.get('postal_code', '')
    flash('eBay settings updated successfully!')
    return redirect(url_for('ebay_settings'))

@app.route('/api/ebay/create_draft', methods=['POST'])
def create_ebay_draft():
    """Create a draft listing on eBay"""
    if 'ebay_token' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated with eBay'})
    
    if 'item_data' not in session:
        return jsonify({'success': False, 'error': 'No item data found'})
    
    # Get item data
    item_data = session['item_data']
    
    # Check if we're using mock authentication
    is_mock = isinstance(session.get('ebay_token'), dict) and session['ebay_token'].get('access_token', '').startswith('mock_')
    
    if is_mock:
        # Return a mock success response
        mock_id = 'MOCK-' + secrets.token_hex(4)
        return jsonify({
            'success': True,
            'listing_id': mock_id,
            'message': 'Mock draft listing created successfully!',
            'details': {
                'title': item_data.get('title', 'Unknown Title'),
                'price': item_data.get('starting_price', '0.00'),
                'category_id': item_data.get('category_id', 'Unknown Category'),
                'image_count': len(session.get('uploaded_files', [])),
                'mock_mode': True,
                'url': f"https://ebay.com/itm/{mock_id}" 
            }
        })
    
    # For real eBay integration:
    try:
        # Upload images to eBay
        images = session.get('uploaded_files', [])
        image_urls = []
        for image_path in images:
            full_path = os.path.join(app.config['UPLOAD_FOLDER'], image_path)
            result = ebay_client.upload_image(full_path)
            if result['success']:
                image_urls.append(result['image_url'])
        
        # Add image URLs to item data
        item_data['image_urls'] = image_urls
        
        # Create draft listing
        result = ebay_client.create_draft_listing(item_data)
        
        if result['success']:
            flash('Successfully created draft listing on eBay!')
            return jsonify(result)
        else:
            flash(f'Error creating draft listing: {result.get("error", "Unknown error")}')
            return jsonify(result)
    except Exception as e:
        error_msg = str(e)
        flash(f'Error creating draft listing: {error_msg}')
        return jsonify({
            'success': False, 
            'error': error_msg,
            'details': 'Check console logs for more information'
        })

# Add a mock eBay auth route for testing
@app.route('/mock_ebay_auth')
def mock_ebay_auth():
    """Mock eBay authentication for testing purposes"""
    session['ebay_token'] = {
        'access_token': 'mock_access_token',
        'refresh_token': 'mock_refresh_token',
        'expires_in': 7200,
        'token_type': 'User'
    }
    session['ebay_paypal_email'] = 'test@example.com'
    session['ebay_postal_code'] = '12345'
    flash('Successfully connected to eBay (MOCK)!')
    return redirect(url_for('preview'))

# Add a special local eBay auth callback that doesn't require HTTPS
@app.route('/auth/ebay/local_callback')
def ebay_local_callback():
    """Special handler for local testing with simulated OAuth flow"""
    flash('This is a simulated OAuth callback for local testing. In production, eBay requires HTTPS.')
    
    # The code would normally come from eBay's OAuth redirect
    mock_code = 'mock_authorization_code'
    
    try:
        # Simulate a token response
        session['ebay_token'] = {
            'access_token': 'mock_access_token_from_code',
            'refresh_token': 'mock_refresh_token',
            'expires_in': 7200,
            'token_type': 'User'
        }
        flash('Successfully connected to eBay (simulated)!')
        return redirect(url_for('ebay_settings'))
    except Exception as e:
        flash(f'Error in mock eBay authentication: {str(e)}')
        return redirect(url_for('index'))

if __name__ == '__main__':
    # Get port from environment variable (for Render compatibility)
    port = int(os.environ.get('PORT', 5000))
    
    # Use 0.0.0.0 to bind to all interfaces
    app.run(host='0.0.0.0', port=port, debug=False if os.environ.get('RENDER') else True) 