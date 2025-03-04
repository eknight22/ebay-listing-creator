# AI-Powered eBay Listing Creator

An intelligent web application that uses OpenAI's Vision API to analyze photos of items and automatically generate professional eBay listings.

## Features

- **Photo Analysis**: Upload up to 12 photos of an item to be analyzed by AI
- **Automatic Item Identification**: The system identifies the item, brand, model, condition, and key features
- **Professional Listing Generation**: Creates appealing, SEO-optimized eBay listing content
- **Editor Interface**: Review and edit AI-generated content before finalizing
- **Ready-to-Use HTML**: Generate eBay-compatible HTML code for direct use in listings
- **CSV Export**: Export listing data in eBay's bulk upload CSV format
- **Direct eBay Integration**: Create draft listings directly on eBay with OAuth authentication
- **Responsive Design**: Works on desktop and mobile devices

## How It Works

1. **Upload Photos**: Take clear photos of your item from different angles
2. **AI Analysis**: The system uses OpenAI's Vision API to identify and analyze the item
3. **Edit Content**: Review and refine the AI-generated listing information
4. **Choose Export Method**:
   - **HTML Export**: Generate and copy HTML code to your eBay listing
   - **CSV Export**: Download a CSV file for bulk uploading to eBay
   - **Direct Creation**: Create a draft listing directly on eBay (requires eBay account connection)
5. **Finalize on eBay**: Complete the listing process on eBay's platform

## Technical Details

This application is built with:

- **Flask**: Python web framework for the backend
- **OpenAI API**: For Vision-based image analysis
- **eBay API**: For direct listing creation and OAuth authentication
- **Bootstrap 5**: For responsive UI components
- **JavaScript**: For dynamic frontend functionality

## Setup and Installation

### Prerequisites

- Python 3.8 or higher
- OpenAI API key

### Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/ebay-listing-creator.git
   cd ebay-listing-creator
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   SECRET_KEY=your_secret_key_here
   ```

5. Run the application:
   ```
   python app.py
   ```

6. Open your browser and navigate to `http://localhost:5000`

## Usage Tips

- **Photo Quality**: Use well-lit, clear photos with neutral backgrounds
- **Multiple Angles**: Include photos from different angles to help AI identify features
- **Close-ups**: Include close-ups of any special features, model numbers, or wear/damage
- **Review Carefully**: Always review the AI-generated content for accuracy
- **Customize**: Add your personal touch to descriptions and selling points

## License

MIT License

## Acknowledgements

- OpenAI for the Vision API
- Flask and Bootstrap teams for their excellent frameworks

### eBay API Integration Setup

To enable direct eBay listing creation, you need to:

1. Create an eBay developer account at [developer.ebay.com](https://developer.ebay.com)
2. Register a new application to obtain API credentials
3. Add these credentials to your `.env` file:
   ```
   # eBay API credentials
   EBAY_APP_ID=your_ebay_app_id_here
   EBAY_CERT_ID=your_ebay_cert_id_here
   EBAY_DEV_ID=your_ebay_dev_id_here
   EBAY_CLIENT_ID=your_ebay_client_id_here
   EBAY_CLIENT_SECRET=your_ebay_client_secret_here
   EBAY_RU_NAME=your_ebay_ru_name_here
   
   # eBay environment (True for sandbox, False for production)
   EBAY_SANDBOX=True
   
   # eBay site ID (0 = US, 3 = UK, 77 = Germany, etc.)
   EBAY_SITE_ID=0
   ```

4. Configure your eBay application's OAuth settings:
   - Set the OAuth Redirect URL to: `http://your-domain.com/auth/ebay/callback`
   - For local testing: `http://localhost:5000/auth/ebay/callback`

For more information on eBay API integration, see the [eBay Developer Documentation](https://developer.ebay.com/develop/guides)

### eBay API Integration for Local Development

eBay's API requires HTTPS redirect URLs for OAuth authentication, which creates challenges for local development. Here are several options to get the integration working:

#### Option 1: Use ngrok for Local Testing

1. Install [ngrok](https://ngrok.com/download)

2. Start your Flask application:
   ```
   python app.py
   ```

3. In a separate terminal, start ngrok pointing to your Flask port:
   ```
   ngrok http 5000
   ```

4. Ngrok will provide you with a temporary public HTTPS URL (e.g., `https://a1b2c3d4.ngrok.io`)

5. Update your eBay Developer Application:
   - Log in to [eBay Developer Program](https://developer.ebay.com/)
   - Navigate to your application
   - Update the OAuth Redirect URL to: `https://a1b2c3d4.ngrok.io/auth/ebay/callback`

6. Update your `.env` file with this URL:
   ```
   EBAY_RU_NAME=https://a1b2c3d4.ngrok.io/auth/ebay/callback
   ```

7. Restart your Flask application and try authenticating with eBay

#### Option 2: Use Mock eBay Authentication for Development

For rapid development without setting up ngrok, you can use the built-in mock authentication:

1. Navigate to the preview page for a listing
2. Click the "Test eBay Integration" button
3. This will set up a mock eBay token in your session, allowing you to test the "Create eBay Draft" functionality

#### Option 3: Configure a Development HTTPS Proxy

If you prefer to use HTTPS locally:

1. Install [mkcert](https://github.com/FiloSottile/mkcert) to create local trusted certificates
2. Configure your Flask app to use HTTPS
3. Register `https://localhost:5000/auth/ebay/callback` as your redirect URL

This requires additional configuration but provides a more stable development environment

### Deployment to Render

This application is configured for easy deployment to Render.com:

1. **Fork or Clone the Repository**
   - Ensure you have your own copy of the code on GitHub

2. **Sign Up for Render**
   - Create an account at [render.com](https://render.com)
   - Connect your GitHub account

3. **Create a New Web Service**
   - Click "New" and select "Web Service"
   - Select your repository
   - Render will automatically detect the configuration in `render.yaml`

4. **Set Environment Variables**
   - In the Render dashboard, add the following environment variables:
     - `OPENAI_API_KEY`: Your OpenAI API key
     - `EBAY_APP_ID`: Your eBay App ID
     - `EBAY_CERT_ID`: Your eBay Cert ID
     - `EBAY_DEV_ID`: Your eBay Dev ID
     - `EBAY_CLIENT_ID`: Your eBay Client ID
     - `EBAY_CLIENT_SECRET`: Your eBay Client Secret
     - `EBAY_RU_NAME`: Your eBay RU Name (or complete redirect URL)

5. **Update eBay Developer Settings**
   - Log in to [eBay Developer Program](https://developer.ebay.com/)
   - Update your OAuth Redirect URL to your Render URL:
     `https://your-app-name.onrender.com/auth/ebay/callback`

6. **Deploy**
   - Click "Deploy" and wait for the build to complete
   - Your application will be available at `https://your-app-name.onrender.com`

7. **Verify Deployment**
   - Visit your application URL
   - Test the eBay integration functionality 