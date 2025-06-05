import logging
import subprocess
import uuid
from datetime import datetime
from typing import Any, Dict, List

from litellm import Choices, CustomLLM, Message, ModelResponse

logger = logging.getLogger(__name__)


class ClaudeCodeProvider(CustomLLM):
    """Custom LiteLLM provider for claude-code CLI"""

    def __init__(self):
        super().__init__()

    def completion(self, model: str, messages: List[Dict[str, Any]], **kwargs) -> ModelResponse:
        """Handle completion requests by calling claude-code CLI"""
        logger.info(f"ClaudeCodeProvider.completion called with model: {model}")

        # Extract the last user message
        user_messages = [m for m in messages if m.get("role") == "user"]
        if not user_messages:
            raise ValueError("No user messages found")

        prompt = user_messages[-1].get("content", "")

        # Execute claude command
        try:
            result = self._execute_claude_code(prompt)

            # Create response in LiteLLM format
            response_message = Message(content=result, role="assistant")
            response_choice = Choices(index=0, message=response_message, finish_reason="stop")

            model_response = ModelResponse(
                id=str(uuid.uuid4()),
                choices=[response_choice],
                model="claude-code-server/claude-code",  # Use actual provider model name
                object="chat.completion",
                created=int(datetime.now().timestamp()),
                usage={
                    "prompt_tokens": len(prompt.split()),
                    "completion_tokens": len(result.split()),
                    "total_tokens": len(prompt.split()) + len(result.split()),
                },
            )

            return model_response

        except Exception as e:
            logger.error(f"Error executing claude-code: {e}")
            raise

    async def acompletion(
        self, model: str, messages: List[Dict[str, Any]], **kwargs
    ) -> ModelResponse:
        """Handle async completion requests by calling claude-code CLI"""
        import asyncio

        logger.info(f"ClaudeCodeProvider.acompletion called with model: {model}")

        # Define a wrapper function that accepts the correct arguments
        def completion_wrapper():
            return self.completion(model, messages, **kwargs)

        # Use asyncio.run_in_executor to run the synchronous completion method
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, completion_wrapper)

    async def astreaming(
        self, model: str, messages: List[Dict[str, Any]], **kwargs
    ):
        """Handle async streaming requests"""
        # Get the response asynchronously
        response = await self.acompletion(model, messages, **kwargs)

        # Create streaming chunks - split content into words for demonstration
        content = response.choices[0].message.content
        
        # Since claude-code doesn't support streaming, return the full response as one chunk
        # Return raw dict format that LiteLLM expects
        chunk = {
            "text": content,
            "is_finished": True,
            "finish_reason": "stop",
            "usage": {
                "prompt_tokens": response.usage.get("prompt_tokens", 0),
                "completion_tokens": response.usage.get("completion_tokens", 0),
                "total_tokens": response.usage.get("total_tokens", 0),
            }
        }
        yield chunk

    def _execute_claude_code(self, prompt: str) -> str:
        """Execute claude-code CLI command"""
        # Try to find claude-code command
        import shutil
        
        claude_cmd = shutil.which("claude")
        
        if not claude_cmd:
            raise RuntimeError("claude command not found. Please install claude-code CLI.")
        
        cmd = [claude_cmd, "-p", prompt]
        logger.info(f"Executing command: {' '.join(cmd)}")

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"Command output: {result.stdout[:100]}...")
            return result.stdout.strip()

        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else e.stdout if e.stdout else "Unknown error"
            logger.error(f"claude-code failed: {error_msg}")
            
            # Check for common authentication issues
            if "Invalid API key" in error_msg or "Please run /login" in error_msg:
                raise RuntimeError(
                    "claude-code authentication failed. Please set ANTHROPIC_API_KEY environment variable "
                    "or run 'claude /login' to authenticate."
                )
            
            raise RuntimeError(f"claude-code failed: {error_msg}")


# Create an instance of the provider to be used in config.yaml
claude_code_provider_instance = ClaudeCodeProvider()
