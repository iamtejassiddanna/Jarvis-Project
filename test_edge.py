import asyncio
import edge_tts

async def main():
    communicate = edge_tts.Communicate("Hello world, this is a test.", "en-GB-RyanNeural")
    count = 0
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            count += 1
    print(f"Got {count} audio chunks")

asyncio.run(main())
