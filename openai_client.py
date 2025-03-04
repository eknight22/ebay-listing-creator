"""
Custom OpenAI client module designed to avoid proxy-related initialization issues
"""
import os
import json
import requests
from typing import Dict, List, Any, Optional

class CustomOpenAIClient:
    """
    A simplified client for OpenAI API that doesn't use the OpenAI library,
    to avoid issues with proxy configurations on Render
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the client with API key"""
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.base_url = "https://api.openai.com/v1"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })
    
    def chat_completion(self, 
                       model: str, 
                       messages: List[Dict[str, Any]], 
                       max_tokens: int = 1000,
                       temperature: float = 0.7) -> Dict[str, Any]:
        """
        Create a chat completion similar to openai.chat.completions.create
        
        Args:
            model: The model to use (e.g., "gpt-4o")
            messages: List of message objects with role and content
            max_tokens: Maximum tokens to generate
            temperature: Controls randomness of output
            
        Returns:
            API response as a dictionary
        """
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()  # Raise exception for non-200 responses
            return response.json()
        except requests.RequestException as e:
            print(f"Error calling OpenAI API: {str(e)}")
            raise

# Create client instance
custom_client = CustomOpenAIClient()

def create_chat_completion(model, messages, max_tokens=4000):
    """
    Wrapper function to make OpenAI API calls in a way similar to the official client
    
    Returns:
        A response object with a similar structure to the official client's response
    """
    try:
        response = custom_client.chat_completion(
            model=model,
            messages=messages,
            max_tokens=max_tokens
        )
        
        # Extract message content similar to how the official client does
        message_content = response.get('choices', [{}])[0].get('message', {}).get('content', '')
        
        # Create a response object that mimics the structure used in the existing code
        class ChatCompletionResponse:
            class Choice:
                class Message:
                    def __init__(self, content):
                        self.content = content
                
                def __init__(self, message_content):
                    self.message = self.Message(message_content)
            
            def __init__(self, choices):
                self.choices = choices
        
        # Return a response object that matches the structure expected in app.py
        return ChatCompletionResponse(
            choices=[ChatCompletionResponse.Choice(message_content)]
        )
    except Exception as e:
        print(f"Error in create_chat_completion: {str(e)}")
        raise 