import asyncio
from whatsapp_ai import WhatsAppClient, WhatsAppConfig

async def main() -> None:
    # Load configuration from environment variables or .env file
    config = WhatsAppConfig()
    client = WhatsAppClient(config)

    recipient = "33612345678"  # Example number
    message = "Hello from WhatsApp AI SDK!"

    try:
        response = await client.send_text_message(to=recipient, text=message)
        print("Message sent:", response)
    except Exception as e:
        print("Failed to send message:", e)

if __name__ == "__main__":
    asyncio.run(main())
