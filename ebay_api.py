import os
import json
import time
from datetime import datetime, timedelta
from flask import session, redirect, url_for, request, flash
from requests_oauthlib import OAuth2Session
from ebaysdk.trading import Connection as Trading
from ebaysdk.exception import ConnectionError
import requests
from urllib.parse import urlencode

# Load eBay API credentials from environment variables
EBAY_APP_ID = os.environ.get('EBAY_APP_ID')
EBAY_CERT_ID = os.environ.get('EBAY_CERT_ID')
EBAY_DEV_ID = os.environ.get('EBAY_DEV_ID')
EBAY_CLIENT_ID = os.environ.get('EBAY_CLIENT_ID')
EBAY_CLIENT_SECRET = os.environ.get('EBAY_CLIENT_SECRET')
EBAY_RU_NAME = os.environ.get('EBAY_RU_NAME')

# eBay OAuth URLs
EBAY_SANDBOX = os.environ.get('EBAY_SANDBOX', 'True').lower() in ('true', 'yes', '1')
EBAY_SITE_ID = os.environ.get('EBAY_SITE_ID', '0')  # 0 = US

# Set correct eBay OAuth URLs based on environment
if EBAY_SANDBOX:
    EBAY_OAUTH_URL = 'https://auth.sandbox.ebay.com/oauth2/authorize'
    EBAY_TOKEN_URL = 'https://api.sandbox.ebay.com/identity/v1/oauth2/token'
else:
    EBAY_OAUTH_URL = 'https://auth.ebay.com/oauth2/authorize'
    EBAY_TOKEN_URL = 'https://api.ebay.com/identity/v1/oauth2/token'

# Scopes needed for listing creation
EBAY_SCOPES = [
    'https://api.ebay.com/oauth/api_scope',
    'https://api.ebay.com/oauth/api_scope/sell.inventory',
    'https://api.ebay.com/oauth/api_scope/sell.marketing',
    'https://api.ebay.com/oauth/api_scope/sell.account',
    'https://api.ebay.com/oauth/api_scope/sell.fulfillment'
]

class EbayAPIClient:
    """Client for interacting with eBay's API"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app
        
        # Ensure all required environment variables are set
        if not all([EBAY_APP_ID, EBAY_CERT_ID, EBAY_CLIENT_ID, EBAY_CLIENT_SECRET, EBAY_RU_NAME]):
            app.logger.warning('eBay API credentials not found in environment variables')
    
    def get_authorization_url(self):
        """Get eBay OAuth authorization URL"""
        # Debug output
        print("eBay OAuth Debug Info:")
        print(f"CLIENT_ID (length): {len(EBAY_CLIENT_ID) if EBAY_CLIENT_ID else 0}")
        print(f"CLIENT_SECRET (length): {len(EBAY_CLIENT_SECRET) if EBAY_CLIENT_SECRET else 0}")
        print(f"RU_NAME: {EBAY_RU_NAME}")
        print(f"OAUTH_URL: {EBAY_OAUTH_URL}")
        print(f"SANDBOX: {EBAY_SANDBOX}")
        
        # Check if RU_NAME is a URL or an eBay RU name
        if EBAY_RU_NAME and '://' in EBAY_RU_NAME:
            # It's a full URL, use it directly
            redirect_uri = EBAY_RU_NAME
            print(f"Using full URL as redirect_uri: {redirect_uri}")
        else:
            # It's an eBay RU name, handle accordingly
            # For local development with ngrok, follow the instructions in README.md
            print(f"Using eBay RU name: {EBAY_RU_NAME}")
            # When using an RU name, it's different from a redirect URI in OAuth terminology
            # eBay's authorization server will handle the translation internally
            redirect_uri = EBAY_RU_NAME
        
        # eBay requires special parameters for their OAuth implementation
        params = {
            'client_id': EBAY_CLIENT_ID,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': ' '.join(EBAY_SCOPES),
            'prompt': 'login',
            # Add RuName parameter if it's the eBay format
            **({"runame": EBAY_RU_NAME} if not '://' in EBAY_RU_NAME else {})
        }
        
        # Use urllib to properly encode the parameters
        authorization_url = f"{EBAY_OAUTH_URL}?{urlencode(params)}"
        
        print(f"Generated Authorization URL: {authorization_url}")
        session['oauth_state'] = 'ebay_oauth_state'  # eBay doesn't use standard state parameter
        return authorization_url
    
    def get_token_from_code(self, code):
        """Exchange authorization code for token"""
        print(f"Exchanging authorization code for token. Code length: {len(code)}")
        
        # Determine if we're using a URL or RU name
        if EBAY_RU_NAME and '://' in EBAY_RU_NAME:
            redirect_uri = EBAY_RU_NAME
            print(f"Using full URL as redirect_uri: {redirect_uri}")
        else:
            redirect_uri = EBAY_RU_NAME
            print(f"Using eBay RU name: {EBAY_RU_NAME}")
        
        # eBay requires a specific format for token requests
        token_data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri
        }
        
        # Add RuName parameter if using eBay RU name format
        if not '://' in EBAY_RU_NAME:
            token_data['runame'] = EBAY_RU_NAME
            
        # eBay requires client_id and client_secret in the Authorization header
        auth = (EBAY_CLIENT_ID, EBAY_CLIENT_SECRET)
        
        # Make the token request
        try:
            print(f"Token request data: {token_data}")
            response = requests.post(
                EBAY_TOKEN_URL,
                data=token_data,
                auth=auth,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            # Check if the request was successful
            if response.status_code == 200:
                token = response.json()
                print(f"Token retrieved successfully. Access token length: {len(token.get('access_token', ''))}")
                
                # Store only essential token info to reduce session size
                essential_token = {
                    'access_token': token.get('access_token'),
                    'refresh_token': token.get('refresh_token'),
                    'expires_at': int(time.time()) + token.get('expires_in', 7200),
                    'token_type': token.get('token_type', 'Bearer')
                }
                
                session['ebay_token'] = essential_token
                
                # Print session size debug info
                token_size = len(json.dumps(essential_token))
                print(f"Token storage size (bytes): {token_size}")
                
                return token
            else:
                print(f"Error retrieving token. Status code: {response.status_code}")
                print(f"Response: {response.text}")
                raise Exception(f"Failed to retrieve token: {response.text}")
                
        except Exception as e:
            print(f"Exception during token retrieval: {str(e)}")
            raise
    
    def _get_trading_api(self):
        """Get Trading API connection"""
        if EBAY_SANDBOX:
            config_dict = {
                'domain': 'api.sandbox.ebay.com',
                'appid': EBAY_APP_ID,
                'devid': EBAY_DEV_ID,
                'certid': EBAY_CERT_ID,
                'token': session.get('ebay_token', {}).get('access_token', ''),
                'siteid': EBAY_SITE_ID
            }
        else:
            config_dict = {
                'appid': EBAY_APP_ID,
                'devid': EBAY_DEV_ID,
                'certid': EBAY_CERT_ID,
                'token': session.get('ebay_token', {}).get('access_token', ''),
                'siteid': EBAY_SITE_ID
            }
        
        return Trading(config_dict=config_dict, config_file=None)
    
    def create_draft_listing(self, item_data):
        """Create a draft listing on eBay"""
        try:
            # Convert our item_data to eBay's format
            ebay_item = self._convert_to_ebay_format(item_data)
            
            # Use Trading API to create the draft
            api = self._get_trading_api()
            response = api.execute('AddItem', ebay_item)
            
            return {
                'success': True,
                'listing_id': response.dict()['ItemID'],
                'start_time': response.dict()['StartTime'],
                'end_time': response.dict()['EndTime'],
                'fees': response.dict()['Fees']
            }
        
        except ConnectionError as e:
            return {
                'success': False,
                'error': str(e),
                'error_details': e.response.dict()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _convert_to_ebay_format(self, item_data):
        """Convert our item data format to eBay's format"""
        # Basic listing details
        item = {
            'Item': {
                'Title': item_data.get('title', ''),
                'Description': self._create_html_description(item_data),
                'PrimaryCategory': {'CategoryID': self._extract_category_id(item_data.get('category', ''))},
                'StartPrice': item_data.get('starting_price', ''),
                'CategoryMappingAllowed': 'true',
                'Country': 'US',
                'Currency': 'USD',
                'DispatchTimeMax': '3',
                'ListingDuration': 'Days_7',
                'ListingType': 'Auction',
                'PaymentMethods': 'PayPal',
                'PayPalEmailAddress': session.get('ebay_paypal_email', ''),
                'PostalCode': session.get('ebay_postal_code', ''),
                'Quantity': '1',
                'ReturnPolicy': {
                    'ReturnsAcceptedOption': 'ReturnsAccepted',
                    'RefundOption': 'MoneyBack',
                    'ReturnsWithinOption': 'Days_30',
                    'ShippingCostPaidByOption': 'Buyer'
                },
                'ShippingDetails': {
                    'ShippingType': 'Flat',
                    'ShippingServiceOptions': {
                        'ShippingServicePriority': '1',
                        'ShippingService': 'USPSPriority',
                        'ShippingServiceCost': item_data.get('shipping_cost', '0.0')
                    }
                },
                'Site': 'US'
            }
        }
        
        # Add condition
        if item_data.get('condition'):
            condition_map = {
                'New': '1000',
                'New without tags': '1500',
                'New with defects': '1750',
                'New other': '1500',
                'Used': '3000',
                'Very Good': '4000',
                'Good': '5000',
                'Acceptable': '6000',
                'For parts/not working': '7000'
            }
            item['Item']['ConditionID'] = condition_map.get(item_data.get('condition'), '3000')
        
        # Add specific item details
        item_specifics = []
        
        # Add brand if available
        if item_data.get('brand'):
            item_specifics.append({
                'Name': 'Brand',
                'Value': item_data.get('brand')
            })
            
        # Add model if available
        if item_data.get('model'):
            item_specifics.append({
                'Name': 'Model',
                'Value': item_data.get('model')
            })
            
        # Add color if available
        if item_data.get('color'):
            item_specifics.append({
                'Name': 'Color',
                'Value': item_data.get('color')
            })
            
        # Add size/dimensions if available
        if item_data.get('size_dimensions'):
            item_specifics.append({
                'Name': 'Size',
                'Value': item_data.get('size_dimensions')
            })
            
        # Add material if available
        if item_data.get('material'):
            item_specifics.append({
                'Name': 'Material',
                'Value': item_data.get('material')
            })
            
        # Add type/style if available
        if item_data.get('type_style'):
            item_specifics.append({
                'Name': 'Style',
                'Value': item_data.get('type_style')
            })
            
        # Add MPN (Manufacturer Part Number) if available
        if item_data.get('mpn'):
            item_specifics.append({
                'Name': 'MPN',
                'Value': item_data.get('mpn')
            })
            
        # Add UPC if available
        if item_data.get('upc'):
            item['Item']['ProductListingDetails'] = {
                'UPC': item_data.get('upc')
            }
            
        # Add EAN if available
        if item_data.get('ean'):
            if 'ProductListingDetails' not in item['Item']:
                item['Item']['ProductListingDetails'] = {}
            item['Item']['ProductListingDetails']['EAN'] = item_data.get('ean')
            
        # Add ISBN if available
        if item_data.get('isbn'):
            if 'ProductListingDetails' not in item['Item']:
                item['Item']['ProductListingDetails'] = {}
            item['Item']['ProductListingDetails']['ISBN'] = item_data.get('isbn')
        
        # Add all item specifics if we have any
        if item_specifics:
            item['Item']['ItemSpecifics'] = {'NameValueList': item_specifics}
        
        # Add SubTitle if present
        if item_data.get('subtitle'):
            item['Item']['SubTitle'] = item_data.get('subtitle')
        
        # Add Buy It Now price if present
        if item_data.get('buy_it_now_price'):
            item['Item']['BuyItNowPrice'] = item_data.get('buy_it_now_price')
            
        # Add custom shipping details if provided
        if item_data.get('shipping_details'):
            # Basic shipping cost handling - more complex shipping options would need custom UI fields
            if item_data.get('shipping_cost'):
                item['Item']['ShippingDetails']['ShippingServiceOptions']['ShippingServiceCost'] = item_data.get('shipping_cost')
        
        # Set listing as draft
        item['Item']['InventoryTrackingMethod'] = 'NotTracked'
        
        return item
    
    def _extract_category_id(self, category_string):
        """Extract the eBay category ID from the category string"""
        import re
        # Try to find a numeric ID in parentheses
        category_match = re.search(r'\((\d+)\)', category_string)
        if category_match:
            return category_match.group(1)
        
        # If not found, try to extract any numeric part
        category_match = re.search(r'(\d+)', category_string)
        if category_match:
            return category_match.group(1)
        
        # Default category
        return '1'
    
    def _create_html_description(self, item_data):
        """Create an HTML description for the eBay listing"""
        description = f"<h2>{item_data.get('title', '')}</h2>"
        
        # Main description
        if item_data.get('description'):
            description += f"<div>{item_data.get('description')}</div>"
        
        # Condition description
        if item_data.get('condition_description'):
            description += f"<h3>Condition</h3><p>{item_data.get('condition_description')}</p>"
        
        # What's included
        if item_data.get('included_items'):
            description += f"<h3>What's Included</h3><p>{item_data.get('included_items')}</p>"
        
        # Shipping details
        if item_data.get('shipping_details'):
            description += f"<h3>Shipping Information</h3><p>{item_data.get('shipping_details')}</p>"
        
        # Return policy
        if item_data.get('return_policy'):
            description += f"<h3>Return Policy</h3><p>{item_data.get('return_policy')}</p>"
        
        # Add seller notes
        description += "<p><i>Thank you for viewing this listing. Please contact me with any questions.</i></p>"
        
        return description
    
    def get_ebay_categories(self, parent_id=None):
        """Get eBay categories"""
        try:
            api = self._get_trading_api()
            
            request = {'DetailLevel': 'ReturnAll'}
            if parent_id:
                request['CategoryParent'] = str(parent_id)
            
            response = api.execute('GetCategories', request)
            categories = response.dict()['CategoryArray']['Category']
            
            return {
                'success': True,
                'categories': categories
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def upload_image(self, image_path):
        """Upload an image to eBay's picture service"""
        try:
            api = self._get_trading_api()
            
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            request = {
                'PictureName': os.path.basename(image_path),
                'PictureData': image_data
            }
            
            response = api.execute('UploadSiteHostedPictures', request)
            
            return {
                'success': True,
                'image_url': response.dict()['SiteHostedPictureDetails']['FullURL']
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# Initialize the client
ebay_client = EbayAPIClient() 