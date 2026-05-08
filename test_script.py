import asyncio
import edge_tts

async def test():
    communicate = edge_tts.Communicate("Hello world", "en-GB-RyanNeural")
    await communicate.save("/tmp/test.mp3")

asyncio.run(test())
print("Success")
