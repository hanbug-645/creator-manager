# AI Email Assistant

An AI-powered email assistant that automatically responds to emails, with special handling for car sponsorship requests.

## Features

- Monitors Gmail for new emails from specific senders
- Generates AI-powered responses using GPT-4
- Special handling for car sponsorship emails:
  - Intelligent car-related content detection
  - Automatic image generation with DALL-E
  - Car-specific response formatting
- Professional email handling with customizable instructions
- Secure credential management

## Setup

1. Clone the repository
2. Create a `config` directory and copy files from `config.example`:
   ```bash
   mkdir config
   cp config.example/instructions.example.txt config/instructions.txt
   cp config.example/instruction_image.example.txt config/instruction_image.txt
   cp config.example/.env.example config/.env
   ```
3. Update the configuration files in the `config` directory:
   - Edit `instructions.txt` with your specific requirements
   - Edit `instruction_image.txt` with your image generation preferences
   - Add your API keys and settings to `.env`
   - Place your Gmail credentials JSON file in `config/credentials.json`

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Run the application:
   ```bash
   python src/main.py
   ```

## Configuration Files

- `instructions.txt`: Main instructions for email responses
- `instruction_image.txt`: Template for DALL-E image generation
- `.env`: Environment variables and API keys
- `credentials.json`: Gmail API credentials (obtain from Google Cloud Console)

## Security Notes

- Never commit the `config` directory to version control
- Keep your API keys and credentials secure
- Use environment variables for sensitive information
