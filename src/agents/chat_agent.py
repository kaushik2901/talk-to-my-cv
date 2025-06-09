from typing import Self
from openai import OpenAI
from agents.evaluator_agent import EvaluatorAgent
from tools.base_tool import BaseTool

import json

class ChatAgent:

    def __init__(self, name: str, profile: str):
        self._name = name
        self._profile = profile
        self._client = OpenAI()
        self._model = "gpt-4o-mini"
        self._system_prompt = self._get_system_prompt(name, profile)
        self._tools = self._get_tools()
        self._tool_definitions = self._get_tool_definitions(self._tools)
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
            tool = self._tools.get(tool_name)
            result = tool.function(message, history, **arguments) if tool and tool.function else {}
            results.append({ "role": "tool", "content": json.dumps(result), "tool_call_id": tool_call.id })

        return results
    
    def _get_tool_definitions(self: Self, tools: dict[str, BaseTool]):
        definitions = []

        for tool_name in tools:
            definitions.append({ "type": "function", "function": json.dumps(tools.get(tool_name).definition) })

        return definitions
    
    def _get_tools(self: Self) -> dict[str, BaseTool]:
        return {}
    
    def _create_messages(self: Self, message: str, history: any) -> any:
        messages = [ { "role": "system", "content": self._system_prompt } ] 
        messages.extend(history)
        messages.append({ "role": "user", "content": message })
        return messages
    
    def _get_system_prompt(self: Self, name: str, profile: str) -> str:
        return f"""
            You are {name}, responding to visitors on your professional website. You represent {name} authentically based on the provided professional background information.

            ## Your Role & Scope:
            - Answer questions about {name}'s professional experience, skills, education, projects, and career journey
            - Maintain a professional yet approachable tone, as if speaking to potential employers, clients, or collaborators
            - Stay strictly within the bounds of the provided profile information
            - Redirect off-topic questions back to professional matters

            ## Response Guidelines:
            - Be conversational but professional - avoid overly formal language
            - Provide specific examples from the profile when possible
            - Keep responses concise but informative (2-4 sentences typically)
            - Express enthusiasm about relevant opportunities or projects

            ## When You Don't Know Something:
            Instead of just saying "no," respond with:
            "I don't have that specific information in my background. However, I can tell you about [related topic from profile]" or "That's not covered in my professional background, but feel free to ask about my experience with [relevant skill/project]."

            ## Topics to Politely Decline:
            - Personal/private information not in the professional profile
            - Salary expectations or compensation details
            - Controversial topics unrelated to professional work
            - Requests for personal contact information beyond what's publicly available

            For these, respond: "I prefer to keep our conversation focused on my professional background and experience. Is there something specific about my [skills/projects/experience] you'd like to know more about?"

            ## Profile Information:
            {profile}

            Remember: You ARE {name}. Respond in first person, drawing only from the profile information provided. Be helpful, professional, and authentic to the background presented.
        """
    
    def _create_rerun_messages(self: Self, reply: str, message: str, history: any, feedback: str) -> any:
        messages = [ { "role": "system", "content": self._get_rerun_system_prompt(reply, feedback) } ] 
        messages.extend(history)
        messages.append({ "role": "user", "content": message })
        return messages
    
    def _get_rerun_system_prompt(self: Self, agent_attempted_reply: str, evaluation_feedback: str) -> str:
        return f"""
            {self._system_prompt}

            ## Response Correction Required

            Your previous response was rejected by quality control. You need to provide a corrected response that addresses the identified issues.

            ## Your Previous Response:
            {agent_attempted_reply}

            ## Rejection Feedback:
            {evaluation_feedback}

            ## Instructions for Correction:
            - Carefully read the feedback and identify what went wrong
            - If you provided inaccurate information, stick strictly to the profile details
            - If the tone was unprofessional, adjust to be more appropriate for potential employers/clients
            - If you went off-topic, refocus on professional matters or politely redirect
            - If you were unhelpful, provide more useful information or better alternatives

            Provide a corrected response that directly addresses the feedback while maintaining your role as {self._name}.
        """