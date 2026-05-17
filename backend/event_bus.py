import asyncio
from collections import defaultdict
from typing import Callable, Dict, List, Any


class EventBus:
    """
    Sistema Pub/Sub asíncrono en memoria.
    Permite desacoplar completamente los agentes.
    """

    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)

    def subscribe(self, event_type: str, callback: Callable):
        """
        Registra un agente/callback para escuchar un evento.
        """

        self.subscribers[event_type].append(callback)

        print(f"[EVENT BUS] Subscriber added -> {event_type}")

    async def publish(self, event_type: str, data: Dict[str, Any]):
        """
        Publica un evento a todos los agentes suscritos.
        """

        print(f"\n[EVENT PUBLISHED] {event_type}")

        if event_type not in self.subscribers:
            print(f"[EVENT BUS] No subscribers for {event_type}")
            return

        tasks = []

        for callback in self.subscribers[event_type]:
            tasks.append(asyncio.create_task(callback(data)))

        await asyncio.gather(*tasks)
        