from openai import AsyncOpenAI
from .base import BaseAIProvider

class OpenAIProvider(BaseAIProvider):
    def __init__(self, api_key: str, model_name: str = "gpt-4o-mini"):
        # 비동기 클라이언트 사용
        self.client = AsyncOpenAI(api_key=api_key)
        self.model_name = model_name

    async def generate_readme(self, repo_name: str, code_context: str) -> str:
        system_prompt = f"You are an expert developer. Generate a README.md for {repo_name}."
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Context:\n{code_context}"}
                ],
                temperature=0.2
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error (OpenAI): {str(e)}"