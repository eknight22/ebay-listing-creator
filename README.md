# AI-Powered eBay Listing Creator

An intelligent web application that uses OpenAI's Vision API to analyze photos of items and automatically generate professional eBay listings.

## Features

- **Photo Analysis**: Upload up to 12 photos of an item to be analyzed by AI
- **Automatic Item Identification**: The system identifies the item, brand, model, condition, and key features
- **Professional Listing Generation**: Creates appealing, SEO-optimized eBay listing content
- **Editor Interface**: Review and edit AI-generated content before finalizing
- **Ready-to-Use HTML**: Generate eBay-compatible HTML code for direct use in listings
- **Responsive Design**: Works on desktop and mobile devices

## How It Works

1. **Upload Photos**: Take clear photos of your item from different angles
2. **AI Analysis**: The system uses OpenAI's Vision API to identify and analyze the item
3. **Edit Content**: Review and refine the AI-generated listing information
4. **Generate Listing**: Create a professional HTML listing ready for eBay
5. **Copy to eBay**: Use the generated HTML code in your eBay listing

## Technical Details

This application is built with:

- **Flask**: Python web framework for the backend
- **OpenAI API**: For Vision-based image analysis
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