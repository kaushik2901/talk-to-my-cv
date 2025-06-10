from dotenv import load_dotenv
from agents.chat_agent import ChatAgent
from utils.logger import setup_logging
from utils.reader import read_file_text

import gradio
import os
import sys
import logging

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)

def main():
    try:
        # Load environment variables
        load_dotenv()
        logger.info("Environment variables loaded")
        
        # Validate required environment variables
        required_env_vars = ['OPENAI_API_KEY', 'GEMINI_API_KEY']
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        if missing_vars:
            raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.info("Environment variables validated")

        # Read profile data
        try:
            name = read_file_text("../data/name.txt")
            summary = read_file_text("../data/profile.md")
            logger.info("Profile data loaded successfully", extra = {'profile_name': name})
        except Exception as e:
            logger.error("Failed to read profile data", extra = {'error': str(e)})
            raise FileNotFoundError(f"Failed to read profile data: {str(e)}")

        # Initialize chat agent
        try:
            agent = ChatAgent(name, summary)
            logger.info("Chat agent initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize chat agent", extra = {'error': str(e)})
            raise RuntimeError(f"Failed to initialize chat agent: {str(e)}")

        # Create and launch chat interface
        try:
            chat_interface = gradio.ChatInterface(agent.chat, type="messages")
            logger.info("Chat interface created successfully")
            chat_interface.launch()
            logger.info("Chat interface launched successfully")
        except Exception as e:
            logger.error("Failed to launch chat interface", extra = {'error': str(e)})
            raise RuntimeError(f"Failed to launch chat interface: {str(e)}")

    except EnvironmentError as e:
        logger.error("Environment error", extra = {'error': str(e)})
        sys.exit(1)
    except FileNotFoundError as e:
        logger.error("File error", extra = {'error': str(e)})
        sys.exit(1)
    except RuntimeError as e:
        logger.error("Runtime error", extra = {'error': str(e)})
        sys.exit(1)
    except Exception as e:
        logger.error("Unexpected error", extra = {'error': str(e)})
        sys.exit(1)

if __name__ == "__main__":
    main()