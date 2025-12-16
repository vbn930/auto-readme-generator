from .gemini import GeminiProvider
from .openai import OpenAIProvider

def get_ai_provider(provider_name: str, api_key: str, model_name: str = None):
    """
    팩토리 함수: 이름에 따라 적절한 AI 인스턴스를 반환
    """
    provider_name = provider_name.lower()
    
    if provider_name == "gemini":
        target_model = model_name if model_name else "gemini-1.5-flash"
        return GeminiProvider(api_key, model_name=target_model)
    
    elif provider_name == "openai":
        target_model = model_name if model_name else "gpt-4o-mini"
        return OpenAIProvider(api_key, model_name=target_model)
    
    else:
        print( f"Unsupported provider: {provider_name}" )
        raise ValueError(f"지원하지 않는 AI Provider입니다: {provider_name}")