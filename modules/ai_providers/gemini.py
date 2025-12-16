import asyncio
import google.generativeai as genai
from .base import BaseAIProvider

class GeminiProvider(BaseAIProvider):
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash"):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        # Gemini는 속도 제한이 빡빡할 수 있어 세마포어 사용
        self.semaphore = asyncio.Semaphore(3)

    async def generate_readme(self, repo_name: str, code_context: str, keywords: str = "", language: str = "Korean") -> str:
        
        # [핵심] 프롬프트 엔지니어링: 사용자의 요구사항 반영
        lang_instruction = "한국어로 작성해 주세요." if language == "Korean" else "Write in English."
        
        keyword_instruction = ""
        if keywords:
            keyword_instruction = f"""
            **Critical Instruction:**
            Please strongly emphasize the following keywords or technologies in the 'Key Features' or 'Introduction' section:
            👉 Keywords to highlight: [{keywords}]
            """

        system_prompt = f"""
        You are an expert developer and technical writer.
        Your task is to generate a professional `README.md` file for the GitHub repository named "{repo_name}".
        
        {keyword_instruction}
        
        **Structure:**
        1. Project Title & Description
        2. Key Features (Highlight user keywords if provided)
        3. Tech Stack
        4. Getting Started
        5. Usage
        
        **Rules:**
        - **Language:** {lang_instruction}
        - Use clean Markdown syntax.
        - Be concise but informative.
        """

        user_message = f"""
        # Repo Name: {repo_name}
        # Source Code Context:
        {code_context}
        """

        async with self.semaphore:
            try:
                response = await self.model.generate_content_async(
                    contents=[system_prompt, user_message],
                    generation_config=genai.types.GenerationConfig(temperature=0.2)
                )
                return response.text
            except Exception as e:
                return f"Error (Gemini): {str(e)}"