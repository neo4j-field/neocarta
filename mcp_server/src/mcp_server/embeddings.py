from openai import AsyncOpenAI

from .settings import mcp_server_settings


async def create_embedding(embedding_client: AsyncOpenAI, query: str) -> list[float]:
    """Create an embedding for a query."""
    response = await embedding_client.embeddings.create(
        model=mcp_server_settings.embedding_model,
        input=query,
        encoding_format="float",
        dimensions=mcp_server_settings.embedding_dimensions,
    )
    return response.data[0].embedding
