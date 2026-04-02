# WhatsApp Cloud API Reference

This document summarizes the full capabilities of the Meta WhatsApp Cloud API based on the official Postman collection. It serves as a reference for future features to be implemented in the `whatsapp-ai` SDK.

## Core Messaging Endpoints

The primary endpoint for sending messages is `POST /{{Version}}/{{Phone-Number-ID}}/messages`.

### Supported Message Types (`type`)
- `text`: Standard text messages.
- `template`: Pre-approved message templates (can include text, media headers, buttons).
- `image`: Send an image by Media ID or public URL.
- `document`: Send a PDF or document by Media ID or public URL.
- `audio`: Send an audio file or voice note by Media ID or public URL.
- `video`: Send a video by Media ID or public URL.
- `sticker`: Send static (.webp) or animated stickers by Media ID or public URL.
- `location`: Send a static location (latitude, longitude, name, address).
- `contacts`: Send a contact card (vCard).
- `interactive`: Send rich interactive messages (Reply Buttons, Lists, Product messages).
- `reaction`: Send an emoji reaction to a previous message.

### Advanced Features

#### 1. Context (Replies)
Any message can include a `context` object containing a `message_id` to act as a direct reply to a previous message.

#### 2. Interactive Messages
Interactive messages use the `interactive` type and require an `interactive` object containing:
- `type`: `button` (up to 3 quick reply buttons), `list` (up to 10 rows grouped by sections), or `product` (catalog integrations).
- `header`: Optional text or media.
- `body`: The main text content.
- `footer`: Optional small gray text at the bottom.
- `action`: Contains the buttons (`buttons`) or list sections (`sections`).

#### 3. Mark as Read & Typing Indicators
- **Mark as Read**: Send a `POST` to `/messages` with `status: "read"` and the `message_id` of the incoming message.
- **Typing Indicator**: Send a `POST` to `/messages` with `typing_indicator: {"type": "text"}` (Not available on all Cloud API versions, heavily restricted).

## Media Management (`/media`)

- **Upload Media**: `POST /{{Phone-Number-ID}}/media` using `multipart/form-data`. Returns a `Media-ID`.
- **Download Media**: `GET /{{Media-URL}}` using a Bearer token.
- **Delete Media**: `DELETE /{{Media-ID}}`.

## Webhook Subscriptions (`/subscribed_apps`)

- Subscribe your WABA to your Meta App automatically via the API.
- Override Callback URLs per WABA if managing multiple clients.

## Business Profiles (`/whatsapp_business_profile`)

- Get profile data (about, address, description, email, websites).
- Update profile data.
- Resumable Uploads for setting a new `profile_picture_handle`.

## Templates (`/message_templates`)

- Create templates (Text, Media, Authentication with OTP, Marketing with Buttons).
- Delete templates.
- Query approved/rejected statuses.

## Other Capabilities
- **QR Codes**: Generate deep links and QR codes (`/message_qrdls`) to start conversations.
- **Analytics**: Retrieve message counts, delivery metrics, and conversation pricing stats (`/analytics`).
- **Account Migration**: Migrate from On-Premises API to Cloud API (`/register` with backup data).
- **Block Users**: Programmatically block and unblock users (`/block_users`).
