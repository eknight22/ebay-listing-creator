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