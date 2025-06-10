from typing import Self
from tools.base_tool import BaseTool
import logging

logger = logging.getLogger(__name__)

class RecordUserDetailsError(Exception):
    """Base exception class for RecordUserDetailsTool errors"""
    pass

class RecordUserDetailsTool(BaseTool):
    
    def __init__(self: Self):
        super().__init__({
            "name": "record_user_details",
            "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {
                        "type": "string",
                        "description": "The email address of this user"
                    },
                    "name": {
                        "type": "string",
                        "description": "The user's name, if they provided it"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Any additional information about the conversation that's worth recording to give context"
                    }
                },
                "required": ["email"],
                "additionalProperties": False
            }
        })
        logger.info("RecordUserDetailsTool initialized")

    def function(self: Self, message: str, history: any, email: str, **kwargs) -> dict:
        try:
            logger.info("Recording user details", extra = {'email': email, 'has_name': 'user_name' in kwargs})
            
            # Validate email format
            if not self._is_valid_email(email):
                logger.error("Invalid email format", extra = {'email': email})
                raise RecordUserDetailsError("Invalid email format")

            # Call parent class function
            super().function(message, history)

            response = {
                "status": "success",
                "args": [email, kwargs]
            }
            
            logger.info("User details recorded successfully", extra = {'email': email})
            return response
        except RecordUserDetailsError as e:
            logger.error("RecordUserDetailsError", extra = {'error': str(e)})
            raise e
        except Exception as e:
            logger.error("Error recording user details", extra = {'error': str(e)})
            raise RecordUserDetailsError(f"Error recording user details: {str(e)}")

    def _is_valid_email(self, email: str) -> bool:
        """Basic email validation"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        is_valid = bool(re.match(pattern, email))
        logger.debug("Email validation result", extra = {'email': email, 'is_valid': is_valid})
        return is_valid
