import os
from typing import Self
from openai import OpenAI
from models.evaluation import Evaluation

class EvaluatorAgent:
    
    def __init__(self, name: str, profile: str):
        self._name = name
        self._profile = profile
        self._client = OpenAI(
            api_key = os.getenv('GEMINI_API_KEY'),
            base_url = 'https://generativelanguage.googleapis.com/v1beta/openai/'
        )
        self._model = "gemini-2.0-flash"
        self._system_prompt = self._get_system_prompt(name, profile)

    def run(self: Self, reply: str, message: str, history: any) -> Evaluation:
        messages = self._create_messages(reply, message, history)
        response = self._client.beta.chat.completions.parse(
            model = self._model, 
            messages = messages, 
            response_format = Evaluation
        )
        return response.choices[0].message.parsed

    def _create_messages(self: Self, reply: str, message: str, history: any) -> any:
        messages = [ {"role": "system", "content": self._system_prompt} ]
        messages.append({ "role": "user", "content": self._get_user_prompt(reply, message, history) })
        return messages
    
    def _get_user_prompt(self: Self, reply: str, message: str, history: str) -> str:
        return f"""
            Here's the conversation between the User and the Agent: 
            
            {history}

            Here's the latest message from the User: 
            
            {message}

            Here's the latest response from the Agent: 
            
            {reply}

            Please evaluate the response, replying with whether it is acceptable and your feedback.
        """

    def _get_system_prompt(self: Self, name: str, profile: str) -> str: 
        return f"""
            You are an evaluator that decides whether a response to a question is acceptable.
            You are provided with a conversation between a User and an Agent. Your task is to decide whether the Agent's latest response is acceptable quality.
            The Agent is playing the role of {name} and is representing {name} on their website.
            The Agent has been instructed to be professional and engaging, as if talking to a potential client or future employer who came across the website.
            The Agent must sound professional only it is really important as they will be speaking with potential client or future employer.
            The Agent has been provided with context on {name} in the form of their profession background details. Here's the information:

            ## Profile:

            {profile}

            With this context, please evaluate the latest response, replying with whether the response is acceptable and your feedback.
        """