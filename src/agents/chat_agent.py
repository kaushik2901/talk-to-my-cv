from typing import Self
from openai import OpenAI
from agents.evaluator_agent import EvaluatorAgent

import json

class ChatAgent:

    def __init__(self, name: str, profile: str, tools: dict):
        self._name = name
        self._profile = profile
        self._client = OpenAI()
        self._model = "gpt-4o-mini"
        self._system_prompt = self._get_system_prompt(name, profile)
        self._tools = tools
        self._tool_definitions = self._get_tool_definitions(tools)
        self._evaluator = EvaluatorAgent(name, profile)
        self._MAX_REEVALUATION_ATTEMPTS = 3

    def chat(self: Self, message: str, history: any) -> str:
        messages = self._create_messages(message, history)
        done = False

        while not done:
            response = self._client.chat.completions.create(
                model = self._model,
                messages = messages,
                tools = self._tool_definitions
            )

            finish_reason = response.choices[0].finish_reason
            reply = response.choices[0].message.content

            if finish_reason != "tool_calls":
                retry_attempt = 0
                evaluation = self._evaluator.run(reply, message, history)

                while evaluation.is_acceptable == False and retry_attempt < 3:
                    reply = self._rerun(reply, message, history, evaluation.feedback)
                    evaluation = self._evaluator.run(reply, message, history)
                    retry_attempt += 1

                done = True
            else:
                tool_call_message = response.choices[0].message
                results = self._handle_tool_call(tool_call_message.tool_calls, message, history)
                messages.append(tool_call_message)
                messages.extend(results)

        return reply
    
    def _rerun(self: Self, reply: str, message: str, history: any, feedback: str) -> str:
        messages = self._create_rerun_messages(reply, message, history, feedback)
        response = self._client.chat.completions.create(model = self._model, messages = messages)
        return response.choices[0].message.content
    
    def _handle_tool_call(self: Self, tool_calls: any, message: str, history: any):
        results = []

        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            tool = self._tools.get(tool_name).function
            result = tool(message, history, **arguments) if tool else {}
            results.append(result)

        return results
    
    def _get_tool_definitions(self: Self, tools: dict):
        definitions = []

        for tool_name in tools:
            definitions.append({ "type": "function", "function": tools.get(tool_name).definition })

        return definitions
    
    def _create_messages(self: Self, message: str, history: any) -> any:
        messages = [ { "role": "system", "content": self._system_prompt } ] 
        messages.extend(history)
        messages.append({ "role": "user", "content": message })
        return messages
    
    def _get_system_prompt(self: Self, name: str, profile: str) -> str: 
        return f"""
            You are acting as {name}. You are answering questions on {name}'s website.
            Particularly questions related to {name}'s career, background, skills and experience.
            Your responsibility is to represent {name} for interactions on the website as faithfully as possible.
            You are given a complete information of {name}'s professional background which you can use to answer questions.
            Be professional and engaging, as if talking to a potential client or future employer who came across the website.
            If you don't know the answer, say no.

            ## Profile: 

            {profile}

            With this context, please chat with the user, always staying in character as {name}.
        """
    
    def _create_rerun_messages(self: Self, reply: str, message: str, history: any, feedback: str) -> any:
        messages = [ { "role": "system", "content": self._get_rerun_system_prompt(reply, feedback) } ] 
        messages.extend(history)
        messages.append({ "role": "user", "content": message })
        return messages
    
    def _get_rerun_system_prompt(self: Self, agent_attempted_reply: str, evaluation_feedback: str) -> str:
        return f"""
            {self._system_prompt}

            ## Previous answer rejected
            
            You just tried to reply, but the quality control rejected your reply

            ## Your attempted answer: 
        
            {agent_attempted_reply}

            ## Reason for rejection:
        
            {evaluation_feedback}
        """