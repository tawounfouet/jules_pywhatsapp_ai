# Email Webhooks (Mailgun, Resend)

The `whatsapp-ai` SDK includes a built-in module to trigger WhatsApp messages directly by sending an email via providers like Mailgun or Resend.

This is extremely useful to connect old CRMs, AWS SES lambda functions, or basic email flows directly to your WhatsApp users!

## 1. Setup

Enable the **Mail Bridge** when you create your `WebhookReceiver`.

```python
import logging
import uvicorn

from whatsapp_ai import WhatsAppConfig, WhatsAppClient, MessageRouter, WebhookReceiver, MailBridge

logging.basicConfig(level=logging.INFO)

config = WhatsAppConfig()
client = WhatsAppClient(config)

# The standard WhatsApp router
router = MessageRouter(client=client)

# The Mail Bridge
mail_bridge = MailBridge(config=config, messaging_client=client)

# Create the receiver and attach BOTH WhatsApp & Mail hooks
webhook = WebhookReceiver(config=config, router=router, mail_bridge=mail_bridge)
app = webhook.get_app()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## 2. Environment Configuration

To secure your webhooks via HMAC signatures, define the corresponding environment variables:

```env
# Mailgun Security
MAILGUN_SIGNING_KEY="your_mailgun_api_key_or_webhook_key"

# Resend Security
RESEND_WEBHOOK_SECRET="whsec_xxxxx"
```

If these variables are omitted, the SDK accepts webhooks *without* signature verification (useful for local development, dangerous in production).

## 3. Formatting your Emails

The `MailBridge` relies on clever parsing of either the **Destination Address (Alias)** or the **Email Subject**.

### Option A: The "To" Alias (Recommended)

When you forward emails to your webhook, send them to an address formatted as:
`{channel}+{target}@{yourdomain}`

*Example:* `whatsapp+23761234567@inbound.mybot.com`

The SDK will automatically detect that you want to send a `whatsapp` message to the number `23761234567`. The body of the email (plain text) becomes the content of the message.

### Option B: The Subject Fallback

If you cannot use aliases (or prefer a static email address like `bot@inbound.mybot.com`), put the channel and target in the subject:

*Subject:* `whatsapp +23761234567`
*Body:* `Hello this is an alert!`

## 4. Setting up the Providers

### Mailgun

1. Go to Mailgun > Receiving > Routes.
2. Create a route matching your alias logic (e.g. `match_recipient(".*@inbound.mybot.com")`).
3. Set the action to `forward("https://<your-server-url>/mailgun")`.
4. The SDK expects the standard `multipart/form-data` Mailgun sends.

### Resend

1. Go to Resend > Webhooks.
2. Add a new endpoint pointing to `https://<your-server-url>/resend`.
3. Select the events `email.received`.
4. Copy the Webhook Secret and put it in your `.env` under `RESEND_WEBHOOK_SECRET`.
