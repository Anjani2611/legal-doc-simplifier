import httpx

class WebhookManager:
    def __init__(self):
        self.webhooks = {}  # {event: [url, ...]}

    async def trigger_webhook(self, event: str, document_id: int, data: dict):
        urls = self.webhooks.get(event, [])
        for url in urls:
            try:
                async with httpx.AsyncClient() as client:
                    await client.post(
                        url,
                        json={"event": event, "document_id": document_id, "data": data},
                        timeout=10,
                    )
            except Exception as e:
                print(f"Webhook failed: {e}")


webhook_manager = WebhookManager()
