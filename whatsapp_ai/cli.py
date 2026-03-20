import asyncio
import logging

import typer
import uvicorn

from whatsapp_ai.ai.openai_provider import OpenAIProvider
from whatsapp_ai.client import WhatsAppClient
from whatsapp_ai.config import WhatsAppConfig
from whatsapp_ai.memory import InMemoryStore
from whatsapp_ai.router import MessageRouter
from whatsapp_ai.webhook import WebhookReceiver

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = typer.Typer(help="WhatsApp AI CLI Toolkit")


def get_components(use_ai: bool = False) -> tuple[WhatsAppConfig, WhatsAppClient, MessageRouter]:
    config = WhatsAppConfig()
    client = WhatsAppClient(config)

    memory = None
    ai_provider = None

    if use_ai:
        if not config.openai_api_key:
            typer.secho("OpenAI API key missing from config.", fg=typer.colors.RED)
            raise typer.Exit(1)

        memory = InMemoryStore()
        ai_provider = OpenAIProvider(config)

    router = MessageRouter(client=client, ai_provider=ai_provider, memory=memory)
    return config, client, router


@app.command()
def send(
    to: str = typer.Argument(..., help="Recipient phone number (with country code, no +)"),
    message: str = typer.Argument(..., help="Message to send"),
) -> None:
    """Send a plain text message to a WhatsApp number."""
    config, client, _ = get_components(use_ai=False)

    async def _send() -> None:
        try:
            res = await client.send_text_message(to=to, text=message)
            typer.secho(f"Message sent successfully: {res}", fg=typer.colors.GREEN)
        except Exception as e:
            typer.secho(f"Failed to send message: {e}", fg=typer.colors.RED)

    asyncio.run(_send())


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="Host to bind the webhook server"),
    port: int = typer.Option(8000, help="Port to bind the webhook server"),
    use_ai: bool = typer.Option(False, "--ai", help="Enable AI automatic replies via OpenAI"),
) -> None:
    """Start the Webhook server to receive incoming messages."""
    config, _, router = get_components(use_ai=use_ai)

    webhook_receiver = WebhookReceiver(config=config, router=router)
    fastapi_app = webhook_receiver.get_app()

    typer.secho(f"Starting server on {host}:{port}...", fg=typer.colors.BLUE)
    uvicorn.run(fastapi_app, host=host, port=port)


if __name__ == "__main__":
    app()
