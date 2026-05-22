import asyncio
import json
import websockets

async def run():
    uri = "ws://localhost:8000/ws"
    async with websockets.connect(uri) as ws:
        print("Connected to", uri)
        # receive initial snapshot
        msg = await ws.recv()
        print("RECV:", msg[:200])

        # send new patient
        patient = {
            "edad": 45,
            "genero": "M",
            "nivel_urgencia": 2,
            "sintomas": "Dolor toracico agudo",
        }

        payload = {"action": "NEW_PATIENT", "patient": patient}
        await ws.send(json.dumps(payload))
        print("Sent NEW_PATIENT")

        # read a few messages
        for _ in range(6):
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=5)
                print("EVENT:", msg)
            except asyncio.TimeoutError:
                break

if __name__ == '__main__':
    asyncio.run(run())
