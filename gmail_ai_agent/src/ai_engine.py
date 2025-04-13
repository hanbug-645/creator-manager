import openai
from typing import Dict, Tuple, Optional, Union
import os
import base64
from datetime import datetime
import requests
import re
import logging
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EmailAction(Enum):
    NEGOTIATION = "Negotiation"
    REJECTED = "Rejected"
    ASSET_PROVIDED = "Asset Provided"

class AIEngine:
    def __init__(self, api_key: str, instructions_path: str):
        """Initialize the AI Engine with OpenAI API key and instructions"""
        self.client = openai.OpenAI(api_key=api_key)
        self.instructions_path = instructions_path
        self.image_instructions_path = os.path.join(
            os.path.dirname(instructions_path),
            'instruction_image.txt'
        )
        with open(instructions_path, 'r') as f:
            self.instructions = f.read()

    def extract_car_details(self, email_content: Dict) -> Optional[str]:
        """Extract car brand, model, and color from email content"""
        try:
            # First, try to extract using GPT-4 for accurate parsing
            prompt = f"""
            Extract the car details (brand, model, and color if available) from this email content.
            If multiple cars are mentioned, focus on the main one being sponsored.
            Format the response as a single line with just the car details, e.g., "Red Tesla Model 3" or "BMW M4 Competition".
            If no specific car details are found, respond with "None".

            Email subject: {email_content['subject']}
            Email content: {email_content['body']}
            """

            response = self.client.chat.completions.create(
                model="gpt-4-0125-preview",
                messages=[
                    {"role": "system", "content": "You are a car detail extractor. Only output the car details in the format specified, nothing else."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=50
            )

            car_details = response.choices[0].message.content.strip()
            if car_details.lower() != "none":
                logger.info(f"Extracted car details: {car_details}")
            return None if car_details.lower() == "none" else car_details

        except Exception as e:
            logger.error(f"Error extracting car details: {str(e)}")
            return None

    def is_car_related(self, email_content: Dict) -> bool:
        """Check if the email is related to car sponsorship"""
        try:
            # First do a quick keyword check
            subject = email_content['subject'].lower()
            body = email_content['body'].lower()
            car_keywords = {'car', 'automotive', 'vehicle', 'auto', 'motors', 'toyota', 'honda', 'ford', 'bmw', 'mercedes', 'tesla', 'porsche', 'audi', 'lexus', 'mustang','sponsorship car'}
            
            # If no car-related keywords found at all, return False quickly
            if not any(keyword in subject or keyword in body for keyword in car_keywords):
                return False
            
            # If keywords found, use GPT for more accurate analysis
            prompt = f"""
            Analyze if this email is specifically about car sponsorship or automotive promotion.
            Consider both the subject and content carefully.
            
            Email Subject: {email_content['subject']}
            Email Content: {email_content['body']}
            
            Response format: Only respond with 'true' if it's definitely about car sponsorship/promotion, or 'false' otherwise.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4-0125-preview",
                messages=[
                    {"role": "system", "content": "You are a car sponsorship email analyzer. Only respond with 'true' or 'false'."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=10
            )
            
            is_car = response.choices[0].message.content.strip().lower() == 'true'
            
            if is_car:
                logger.info("\n=== Car Sponsorship Email Detected ===")
                logger.info(f"Subject: {email_content['subject']}")
                logger.info(f"From: {email_content['from']}")
                logger.info("Analysis: This email is specifically about car sponsorship")
                logger.info("=====================================")
            
            return is_car
            
        except Exception as e:
            logger.error(f"Error checking car relation: {str(e)}")
            return False

    def generate_response(self, email_content: Dict) -> Tuple[str, Optional[str], EmailAction]:
        """Generate an AI response and optionally an image for car-related content"""
        try:
            is_car = self.is_car_related(email_content)
            prompt = self._create_prompt(email_content)
            
            logger.info("\n=== Email Action Decision ===")
            logger.info(f"Subject: {email_content['subject']}")
            logger.info(f"From: {email_content['from']}")
            
            # Check if email has attachments
            if 'attachments' in email_content and email_content['attachments']:
                logger.info("Decision: Email contains attachments - categorizing as ASSET_PROVIDED")
                logger.info(f"Attachments found: {len(email_content['attachments'])} files")
                action = EmailAction.ASSET_PROVIDED
            else:
                # First, determine the action to take
                action_prompt = f"""
                Analyze this email and determine the appropriate action to take:
                
                Email Subject: {email_content['subject']}
                Email Content: {email_content['body']}
                
                Choose ONE action from these options:
                1. NEGOTIATION - If the email requires price negotiation
                2. REJECTED - If we should decline the opportunity because it is about gun or knife
                3. ASSET_PROVIDED - If we are providing assets or it is about car sponsorship
                
                Respond with ONLY the action name, nothing else.
                """
                
                action_response = self.client.chat.completions.create(
                    model="gpt-4-0125-preview",
                    messages=[
                        {"role": "system", "content": "You are an email action classifier. Only respond with one of: NEGOTIATION, REJECTED, or ASSET_PROVIDED"},
                        {"role": "user", "content": action_prompt}
                    ],
                    temperature=0,
                    max_tokens=20
                )
                
                action_str = action_response.choices[0].message.content.strip()
                action = EmailAction[action_str]
                logger.info(f"Decision: AI classified email as {action_str}")
                logger.info(f"Email content analyzed for decision: {email_content['body'][:200]}...")
            
            logger.info("===========================\n")
            
            # Generate the actual response
            response = self.client.chat.completions.create(
                model="gpt-4-0125-preview",
                messages=[
                    {"role": "system", "content": "You are a professional email assistant. Your responses should be clear, concise, and appropriate for business communication."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            # If car-related, generate an image
            image_path = None
            if is_car:
                # Extract car details
                car_details = self.extract_car_details(email_content)
                image_path = self.generate_image(car_details)
                if image_path:
                    logger.info(f"Generated car image: {image_path}")
            
            return response.choices[0].message.content, image_path, action
        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}")
            return "", None, EmailAction.NEGOTIATION

    def generate_image(self, car_details: Optional[str] = None) -> str:
        """Generate an image using DALL-E based on instructions"""
        try:
            # Read image instructions
            with open(self.image_instructions_path, 'r') as f:
                image_prompt = f.read().strip()

            # Replace [car] placeholder with actual car details if available
            if car_details:
                image_prompt = image_prompt.replace("[car]", car_details)
            else:
                image_prompt = image_prompt.replace("[car]", "luxury car")

            logger.info(f"Generating image with prompt: {image_prompt}")

            # Generate image using DALL-E
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=image_prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )

            # Download and save the image
            image_url = response.data[0].url
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_path = f"generated_images/car_image_{timestamp}.png"
            
            # Create directory if it doesn't exist
            os.makedirs("generated_images", exist_ok=True)
            
            # Download and save the image
            response = requests.get(image_url)
            if response.status_code == 200:
                with open(image_path, 'wb') as f:
                    f.write(response.content)
                return image_path
            
            return None
        except Exception as e:
            logger.error(f"Error generating image: {str(e)}")
            return None

    def _create_prompt(self, email_content: Dict) -> str:
        """Create a prompt for the AI model"""
        return f"""
        Based on these instructions:
        {self.instructions}

        Please analyze this email and generate an appropriate response:
        From: {email_content['from']}
        Subject: {email_content['subject']}
        Content: {email_content['body']}

        Generate a professional and appropriate response following the instructions.
        The response should be in a format ready to be sent as an email.
        """

    def validate_response(self, response: str) -> bool:
        """Validate the AI-generated response"""
        if not response:
            return False
        if len(response) < 10:  # Arbitrary minimum length
            return False
        return True
