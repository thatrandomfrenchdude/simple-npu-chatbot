import asyncio
import httpx
import json
import sys
import yaml

class Chatbot:
    def __init__(self):
        # Load configuration from YAML
        with open("config.yaml", "r") as file:
            config = yaml.safe_load(file)

        self.api_key = config["api_key"]
        self.base_url = config["model_server_base_url"]
        self.stream_timeout = config["stream_timeout"]
        self.workspace_slug = config["workspace_slug"]

        self.chat_url = f"{self.base_url}/workspace/{self.workspace_slug}/stream-chat"
        self.headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.api_key
        }

    def run(self) -> None:
        """Run the chat application loop."""
        while True:
            user_message = input("You: ")
            if user_message.lower() in ["exit", "quit", "q", "stop", "bye"]:
                print("Exiting chat. Goodbye!")
                break
            print("")
            try:
                self._streaming_chat_async_handler(user_message)
            except Exception as e:
                sys.exit(f"Error details: {e}")
        
    def _streaming_chat_async_handler(self, message: str) -> None:
        """Wrapper to run the asynchronous streaming chat."""
        asyncio.run(self.streaming_chat(message))

    async def streaming_chat(self, message: str) -> None:
        """Stream chat responses asynchronously."""
        data = {
            "message": message,
            "mode": "chat",
            "sessionId": "example-session-id",
            "attachments": []
        }

        buffer = ""
        try:
            async with httpx.AsyncClient(timeout=self.stream_timeout) as client:
                async with client.stream("POST", self.chat_url, headers=self.headers, json=data) as response:
                    print("Agent: ", end="")
                    async for chunk in response.aiter_text():
                        if chunk:
                            buffer += chunk
                            while "\n" in buffer:
                                line, buffer = buffer.split("\n", 1)
                                if line.startswith("data: "):
                                    line = line[len("data: "):]
                                try:
                                    parsed_chunk = json.loads(line.strip())
                                    print(parsed_chunk.get("textResponse", ""), end="", flush=True)
                                    if parsed_chunk.get("close", False):
                                        print("")
                                        return
                                except json.JSONDecodeError:
                                    # The line is not a complete JSON; wait for more data.
                                    continue
                                except Exception as e:
                                    print(f"Error processing chunk: {e}")
                                    return
        except httpx.RequestError as e:
            print(f"Request error: {e}")

if __name__ == '__main__':
    stop_loading = False
    chatbot = Chatbot()
    chatbot.run()