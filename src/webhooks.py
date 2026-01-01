import httpx


class WebhookManager:
    def __init__(self) -> None:
        # Mapping: event name -> list of webhook URLs
        self.webhooks: dict[str, list[str]] = {}

    async def trigger_webhook(self, event: str, document_id: int, data: dict) -> None:
        """Trigger all webhooks registered for a given event."""
        urls = self.webhooks.get(event, [])
        for url in urls:
            try:
                async with httpx.AsyncClient() as client:
                    await client.post(
                        url,
                        json={
                            "event": event,
                            "document_id": document_id,
                            "data": data,
                        },
                        timeout=10,
                    )
            except Exception as exc:
                # Optional: replace with logger.error(...)
                print(f"Webhook failed: {exc}")


# Singleton instance imported by other modules
webhook_manager = WebhookManager()
