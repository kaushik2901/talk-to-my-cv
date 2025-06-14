from typing import Self
from openai import OpenAI, APIError, RateLimitError, APITimeoutError
from agents.evaluator_agent import EvaluatorAgent
from tools.base_tool import BaseTool
from tools.record_user_details_tool import RecordUserDetailsTool
import logging
import json

logger = logging.getLogger(__name__)

class ChatAgentError(Exception):
    """Base exception class for ChatAgent errors"""
    pass

class ToolExecutionError(ChatAgentError):
    """Exception raised when a tool execution fails"""
    pass

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
        logger.info("ChatAgent initialized", extra = {'agent_name': name, 'model': self._model})

    def chat(self: Self, message: str, history: any) -> str:
        logger.info("Processing chat message", extra = {'message_length': len(message)})
        messages = self._create_messages(message, history)
        done = False

        while not done:
            try:
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
                    logger.debug("Initial evaluation", extra = {'is_acceptable': evaluation.is_acceptable})

                    while evaluation.is_acceptable == False and retry_attempt < self._MAX_REEVALUATION_ATTEMPTS:
                        logger.info("Reevaluating response", extra = {'attempt': retry_attempt + 1})
                        reply = self._rerun(reply, message, history, evaluation.feedback)
                        evaluation = self._evaluator.run(reply, message, history)
                        retry_attempt += 1

                    if retry_attempt > 0:
                        logger.info("Response reevaluated", extra = {'final_attempt': retry_attempt})

                    done = True
                else:
                    tool_call_message = response.choices[0].message
                    logger.info("Tool call detected", extra = {'tool_calls': len(tool_call_message.tool_calls)})
                    results = self._handle_tool_call(tool_call_message.tool_calls, message, history)
                    messages.append(tool_call_message)
                    messages.extend(results)

            except RateLimitError:
                logger.error("Rate limit exceeded")
                raise ChatAgentError("Rate limit exceeded. Please try again later.")
            except APITimeoutError:
                logger.error("Request timed out")
                raise ChatAgentError("Request timed out. Please try again.")
            except APIError as e:
                logger.error("OpenAI API error", extra = {'error': str(e)})
                raise ChatAgentError(f"OpenAI API error: {str(e)}")
            except Exception as e:
                logger.error("Unexpected error in chat", extra = {'error': str(e)})
                raise ChatAgentError(f"Unexpected error in chat: {str(e)}")

        logger.info("Chat message processed successfully", extra = {'reply_length': len(reply)})
        return reply
    
    def _rerun(self: Self, reply: str, message: str, history: any, feedback: str) -> str:
        try:
            logger.debug("Rerunning chat with feedback", extra = {'feedback': feedback})
            messages = self._create_rerun_messages(reply, message, history, feedback)
            response = self._client.chat.completions.create(model=self._model, messages=messages)
            return response.choices[0].message.content
        except Exception as e:
            logger.error("Error during rerun", extra = {'error': str(e)})
            raise ChatAgentError(f"Error during rerun: {str(e)}")
    
    def _handle_tool_call(self: Self, tool_calls: any, message: str, history: any):
        results = []

        for tool_call in tool_calls:
            try:
                tool_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                tool = self._tools.get(tool_name)
                
                logger.info("Executing tool", extra = {'tool_name': tool_name})
                
                if not tool or not tool.function:
                    logger.error("Tool not found or has no function", extra = {'tool_name': tool_name})
                    raise ToolExecutionError(f"Tool {tool_name} not found or has no function")
                
                result = tool.function(message, history, **arguments)
                results.append({
                    "role": "tool",
                    "content": json.dumps(result),
                    "tool_call_id": tool_call.id
                })
                logger.info("Tool execution successful", extra = {'tool_name': tool_name})
            except json.JSONDecodeError:
                logger.error("Invalid JSON arguments for tool", extra = {'tool_name': tool_name})
                raise ToolExecutionError(f"Invalid JSON arguments for tool {tool_name}")
            except Exception as e:
                logger.error("Error executing tool", extra = {'tool_name': tool_name, 'error': str(e)})
                raise ToolExecutionError(f"Error executing tool {tool_name}: {str(e)}")

        return results
    
    def _get_tool_definitions(self: Self, tools: dict[str, BaseTool]):
        try:
            definitions = []
            for tool_name in tools:
                definitions.append({
                    "type": "function",
                    "function": tools.get(tool_name).definition
                })
            logger.debug("Tool definitions retrieved", extra = {'tool_count': len(definitions)})
            return definitions
        except Exception as e:
            logger.error("Error getting tool definitions", extra = {'error': str(e)})
            raise ChatAgentError(f"Error getting tool definitions: {str(e)}")
    
    def _get_tools(self: Self) -> dict[str, BaseTool]:
        tools = {
            "record_user_details": RecordUserDetailsTool()
        }
        logger.debug("Tools initialized", extra = {'tool_count': len(tools)})
        return tools
    
    def _create_messages(self: Self, message: str, history: any) -> any:
        try:
            messages = [{"role": "system", "content": self._system_prompt}]
            messages.extend(history)
            messages.append({"role": "user", "content": message})
            logger.debug("Messages created", extra = {'message_count': len(messages)})
            return messages
        except Exception as e:
            logger.error("Error creating messages", extra = {'error': str(e)})
            raise ChatAgentError(f"Error creating messages: {str(e)}")
    
    def _get_system_prompt(self: Self, name: str, profile: str) -> str:
        return f"""
            You are {name}, responding to visitors on your professional website. You represent {name} authentically based on the provided professional background information.

            ## Your Role & Scope:
            - Answer questions about {name}'s professional experience, skills, education, projects, and career journey
            - Maintain a professional yet approachable tone, as if speaking to potential employers, clients, or collaborators
            - Stay strictly within the bounds of the provided profile information
            - Redirect off-topic questions back to professional matters
            - **Actively build connections by encouraging visitors to get in touch for deeper conversations**

            ## Response Guidelines:
            - Be conversational but professional - avoid overly formal language
            - Provide specific examples from the profile when possible
            - Keep responses concise but informative (2-4 sentences typically)
            - Express enthusiasm about relevant opportunities or projects
            - **Proactively suggest connecting when conversations show potential value**

            ## Building Connections - Be Proactive:
            Look for opportunities to suggest connecting, such as when visitors:
            - Ask about specific skills or experience
            - Mention they're hiring or have projects
            - Show interest in particular technologies or approaches
            - Ask detailed questions about your background
            - Seem like potential collaborators or clients

            **Encourage connection with phrases like:**
            - "This sounds like something we should discuss in more detail - what's your email so I can send you some additional information?"
            - "I'd love to hear more about your project/role - shall we connect over email to explore this further?"
            - "Based on what you're describing, I think I could be a great fit. Would you like to continue this conversation via email?"
            - "I have some relevant examples I could share with you directly - what's the best email to reach you?"
            - "It sounds like we're aligned on [topic] - I'd be happy to discuss this opportunity further if you'd like to share your contact details"

            ## When You Don't Know Something:
            Turn unknowns into connection opportunities:
            "I don't have those specific details readily available, but I'd be happy to provide more comprehensive information if you'd like to connect directly. What's your email address?"

            ## Topics to Politely Decline:
            - Personal/private information not in the professional profile
            - Controversial topics unrelated to professional work

            **For salary/compensation questions:** "Those are great questions that I'd prefer to discuss directly. Would you like to share your email so we can set up a proper conversation about the details?"

            ## Profile Information:
            {profile}

            Remember: You ARE {name}. Your goal is not just to answer questions, but to build meaningful professional relationships. Be genuinely interested in connecting with visitors who could be potential employers, clients, or collaborators. When someone engages thoughtfully with your background, that's an opportunity to deepen the relationship through direct contact.
        """
    
    def _create_rerun_messages(self: Self, reply: str, message: str, history: any, feedback: str) -> any:
        try:
            messages = [{"role": "system", "content": self._get_rerun_system_prompt(reply, feedback)}]
            messages.extend(history)
            messages.append({"role": "user", "content": message})
            return messages
        except Exception as e:
            raise ChatAgentError(f"Error creating rerun messages: {str(e)}")
    
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