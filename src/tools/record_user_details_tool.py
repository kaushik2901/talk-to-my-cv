from typing import Self
from tools.base_tool import BaseTool


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
                    }
                    ,
                    "notes": {
                        "type": "string",
                        "description": "Any additional information about the conversation that's worth recording to give context"
                    }
                },
                "required": ["email"],
                "additionalProperties": False
            }
        })

    def function(self: Self, message: str, history: any, email: str, **kwargs) -> dict:
        super().function(message, history)

        response = { "status": "success", "args": [ email, kwargs] }
        
        print(response)
        
        return response
