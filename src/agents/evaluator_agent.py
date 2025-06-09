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
        messages.append({ "role": "user", "content": self._get_user_prompt(self._name, reply, message, history) })
        return messages
    
    def _get_user_prompt(self: Self, name: str, reply: str, message: str, history: str) -> str:
        return f"""
            ## Conversation History:
            {history}

            ## User's Latest Message:
            {message}

            ## Agent's Response to Evaluate:
            {reply}

            Evaluate whether this response meets the professional standards for {name}'s website. Consider: Does it accurately represent the profile? Is the tone appropriate for potential employers/clients? Is it helpful and professional?
        """
    
    def _get_system_prompt(self: Self, name: str, profile: str) -> str:
        return f"""
            You are an evaluator assessing whether an AI agent's response is acceptable for a professional website.

            The agent represents {name} and responds to visitors asking about their professional background. 

            ## Evaluation Criteria:
            A response is ACCEPTABLE only if it meets ALL of these requirements:
            1. **Accurate**: Information comes only from the provided profile - no made-up details
            2. **Professional**: Appropriate tone for potential employers/clients visiting the website
            3. **In-scope**: Answers professional questions or politely redirects off-topic ones
            4. **Helpful**: Provides useful information or clear explanation when information isn't available

            ## Profile Information:
            {profile}

            ## Auto-REJECT if response:
            - Contains information not in the profile
            - Uses unprofessional or inappropriate tone
            - Ignores off-topic questions instead of redirecting
            - Simply says "no" without being helpful

            Provide clear, specific feedback explaining your decision.
        """