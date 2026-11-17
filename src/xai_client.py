from openai import OpenAI

from src.config import Settings, get_settings


def get_openai_client(settings: Settings | None = None) -> OpenAI:
    s = settings or get_settings()
    return OpenAI(api_key=s.xai_api_key, base_url=s.xai_base_url)


def embed_texts(texts: list[str], settings: Settings | None = None) -> list[list[float]]:
    s = settings or get_settings()
    client = get_openai_client(s)
    response = client.embeddings.create(model=s.embed_model, input=texts)
    return [item.embedding for item in response.data]