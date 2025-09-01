import asyncio
import numpy as np
from core.config import CONFIG


def handle_chunk(raw: bytes):
    data = np.frombuffer(raw, dtype=np.float32)
    return data


async def capture_audio(chunk_size: int = 1024):
    process = await asyncio.create_subprocess_exec(
        "ffmpeg",
        "-f", CONFIG.audio.FORMAT_AUDIO_CARD,
        "-i", CONFIG.audio.MONITOR_SRC,
        "-f", CONFIG.audio.RAW_FORMAT,
        "-acodec", CONFIG.audio.CODEC,
        "-ac", str(CONFIG.audio.CHANNELS),
        "-ar", str(CONFIG.audio.SAMPLERATE),
        CONFIG.audio.OUTPUT,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL
    )

    bytes_per_frame = CONFIG.audio.SAMPLE_WIDTH * CONFIG.audio.CHANNELS
    target_bytes = chunk_size * bytes_per_frame
    buffer = b""

    while True:
        chunk = await process.stdout.read(target_bytes - len(buffer))
        if not chunk:
            break

        buffer += chunk

        while len(buffer) >= target_bytes:
            frame, buffer = buffer[:target_bytes], buffer[target_bytes:]
            yield handle_chunk(frame)

def main():
    for i, chunk in enumerate(capture_audio()):
        print(f"Got chunk {i}, size={len(chunk)} bytes")
        if i > 5:
            break

if __name__ == "__main__":
    main()