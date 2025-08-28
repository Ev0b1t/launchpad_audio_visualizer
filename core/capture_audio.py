import asyncio
import numpy as np


MONITOR_SRC = 'alsa_output.pci-0000_00_1f.3.analog-stereo.monitor'
FORMAT_AUDIO_CARD = "pulse"
CODEC = "pcm_f32le"
RAW_FORMAT = "f32le"
CHANNELS = 2
SAMPLERATE = 44100
OUTPUT = "pipe:1"
CHUNK_SIZE = 1024 * 1
FLUSH_PACKETS = 0
BLOCK_SIZE = 65536

SAMPLE_WIDTH = 4 # pcm 32 -> 4 bytes

def handle_chunk(raw: bytes):
    data = np.frombuffer(raw, dtype=np.float32)
    return data


async def capture_audio(chunk_size: int = 1024):
    process = await asyncio.create_subprocess_exec(
        "ffmpeg",
        "-f", FORMAT_AUDIO_CARD,
        "-i", MONITOR_SRC,
        "-f", RAW_FORMAT,
        "-acodec", CODEC,
        "-ac", str(CHANNELS),
        "-ar", str(SAMPLERATE),
        # "-flush_packets", str(FLUSH_PACKETS),
        # "-blocksize", str(BLOCK_SIZE),
        OUTPUT,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL
    )

    bytes_per_frame = SAMPLE_WIDTH * CHANNELS
    target_bytes = chunk_size * bytes_per_frame
    buffer = b""

    while True:
        chunk = await process.stdout.read(target_bytes - len(buffer))
        if not chunk:
            break

        buffer += chunk

        while len(buffer) >= target_bytes:
            frame, buffer = buffer[:target_bytes], buffer[target_bytes:]
            yield frame
            # yield np.frombuffer(frame, dtype=np.int16).astype(np.float32) / 32768.0

def main():
    for i, chunk in enumerate(capture_audio()):
        print(f"Got chunk {i}, size={len(chunk)} bytes")
        if i > 5:
            break

if __name__ == "__main__":
    main()