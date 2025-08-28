import cProfile
import pstats
import asyncio
import numpy as np
import launchpad_py as launchpad
import sounddevice as sd
from core.config import CONFIG
from core.state import EMA_GLOBAL_PEAK
from core.laucnhpad_visualization import visualize_audio_bands
from utils.general import find_opened_port
from utils.logger import logger
from core.capture_audio import capture_audio, handle_chunk, CHANNELS, SAMPLERATE, CHUNK_SIZE


Q = asyncio.Queue()

def process_audio_chunk(
    chunk, samplerate, channels, chunk_size, window,
    bands_range,
):
    """
    Processes a single audio chunk and returns the RMS values for each frequency band.
    """
    if channels == 2:
        chunk = chunk.reshape(-1, 2)
        chunk_mono = chunk.mean(axis=1)
    else:
        chunk_mono = chunk

    # Apply window function and perform FFT
    chunk_windowed = chunk_mono * window
    spectrum = np.abs(np.fft.rfft(chunk_windowed))
    freqs = np.fft.rfftfreq(len(chunk_windowed), 1.0 / samplerate)

    # Calculate RMS for each frequency band
    bands_rms = []
    for low, high in bands_range:
        mask = (freqs >= low) & (freqs < high)
        band_vals = spectrum[mask]
        if band_vals.size > 0:
            band_rms = np.sqrt(np.mean(band_vals ** 2))
            bands_rms.append(band_rms)
        else:
            bands_rms.append(0.0)

    return bands_rms

def normalize_bands(bands_rms: np.ndarray):
    """
    Bands normalazing
    """
    global EMA_GLOBAL_PEAK

    # Updating the global and the individual EMA
    for i, rms_val in enumerate(bands_rms):
        CONFIG.bands.EMAS[i] = (CONFIG.ema.SMOOTHING * rms_val) + ((1 - CONFIG.ema.SMOOTHING) * CONFIG.bands.EMAS[i])

    max_rms = max(bands_rms) if bands_rms else 0.0
    EMA_GLOBAL_PEAK = (CONFIG.ema.SMOOTHING * max_rms) + ((1 - CONFIG.ema.SMOOTHING) * EMA_GLOBAL_PEAK)

    normalized_bands = []
    if EMA_GLOBAL_PEAK > CONFIG.ema.MIN_PEAK:
        # Normalization with adaptive accent
        for i, rms_val in enumerate(bands_rms):
            # check by threshold
            # if the RMS value less than threshold change it to 0.0
            if rms_val < CONFIG.threshold.VAL:
                final_brightness = 0.0
            else:
                base_brightness = rms_val / EMA_GLOBAL_PEAK
                accent_boost = (rms_val / (CONFIG.bands.EMAS[i] + CONFIG.ema.MIN_PEAK))
                final_brightness = max(base_brightness, accent_boost * 0.7)

            normalized_bands.append(min(1.0, final_brightness))
    else:
        normalized_bands = [0.0] * len(bands_rms)

    return normalized_bands



async def play_and_visualize(lp, chunk_size: int = 1024):
    counter = 0

    async for audio_b in capture_audio(chunk_size):
        chunk = handle_chunk(audio_b)
        if len(chunk) < chunk_size * CHANNELS:
            continue

        if counter % 2 == 0:
            window = np.hanning(chunk_size)
            bands_rms = process_audio_chunk(
                chunk, SAMPLERATE, CHANNELS, chunk_size, window,
                CONFIG.bands.RANGE
            )
            normalized_bands = normalize_bands(bands_rms)
            await visualize_audio_bands(lp, normalized_bands)
            counter = 0
        counter += 1


def main():
    """
    Main function to run the audio visualizer.
    """
    global CHUNK_SIZE

    lp = launchpad.LaunchpadPro()
    launchpad_port_index = find_opened_port(lp)

    if launchpad_port_index == -1:
        logger.debug("The launchpad port was not found.")
        return

    # Reset lights
    lp.Reset()

    pr = cProfile.Profile()
    try:
        pr.enable()
        asyncio.run(play_and_visualize(lp, CHUNK_SIZE))
    except KeyboardInterrupt:
        logger.debug("Visualization stopped by user.")
    finally:
        pr.disable()
        stats = pstats.Stats(pr)
        stats.sort_stats("tottime").print_stats(20)
        lp.Reset()



if __name__ == "__main__":
    main()
