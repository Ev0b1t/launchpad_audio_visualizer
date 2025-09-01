import cProfile
import pstats
import asyncio
import argparse
import numpy as np
import launchpad_py as launchpad
from asyncstdlib import enumerate as aenumerate
from core.config import CONFIG
from core.state import EMA_GLOBAL_PEAK
from core.laucnhpad_visualization import visualize_audio_bands
from utils.general import find_opened_port
from utils.logger import logger
from core.capture_audio import capture_audio, handle_chunk

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
            if rms_val < CONFIG.threshold.GENERAL:
                final_brightness = 0.0
            else:
                base_brightness = rms_val / EMA_GLOBAL_PEAK
                accent_boost = (rms_val / (CONFIG.bands.EMAS[i] + CONFIG.ema.MIN_PEAK))
                final_brightness = max(base_brightness, accent_boost * CONFIG.threshold.ACCENT_BOOST)

            normalized_bands.append(min(1.0, final_brightness))
    else:
        normalized_bands = [0.0] * len(bands_rms)

    return normalized_bands

async def play_and_visualize(lp, chunk_size: int = 1024, hanning_window: np.ndarray = np.hanning(1024)):
    global CONFIG

    async for i, audio_b in aenumerate(capture_audio(chunk_size)):
        chunk = handle_chunk(audio_b)
        if not(len(chunk) < chunk_size * CONFIG.audio.CHANNELS):
            if i % 2 == 0:
                bands_rms = process_audio_chunk(
                    chunk, CONFIG.audio.SAMPLERATE, CONFIG.audio.CHANNELS, chunk_size, hanning_window,
                    CONFIG.bands.RANGE
                )
                normalized_bands = normalize_bands(bands_rms)
                await visualize_audio_bands(lp, normalized_bands)

def main():
    """
    Main function to run the audio visualizer.
    """
    global CONFIG

    parser = argparse.ArgumentParser(description="Audio visualizer launchpad")
    parser.add_argument("-p", "--profiling", action="store_true", help="Enable profiling")
    args = parser.parse_args()

    lp = launchpad.LaunchpadPro()
    logger.info("Launchpad Pro opened.")
    logger.debug("Finding opened port...")
    launchpad_port_index = find_opened_port(lp)
    logger.debug(f"Result port index: {launchpad_port_index}")

    if launchpad_port_index == -1:
        logger.warning("The launchpad port was not found.")
        return

    # Reset lights
    logger.info("Resetting lights...")
    lp.Reset()

    if args.profiling:
        pr = cProfile.Profile()
    try:
        if args.profiling:
            logger.info("Profiling enabled.")
            pr.enable()
        logger.info("Starting visualization...")
        asyncio.run(play_and_visualize(lp, CONFIG.audio.CHUNK_SIZE))
    except KeyboardInterrupt:
        logger.warning("Visualization stopped by user.")
    except Exception as e:
        logger.exception("Visualization stopped by exception.")
    finally:
        if args.profiling:
            logger.info("Profiling disabled.")
            pr.disable()
            stats = pstats.Stats(pr)
            stats.sort_stats("tottime").print_stats(20)
        try:
            logger.info("Resetting lights...")
            lp.Reset()
        except Exception as e:
            logger.exception("Launchpad reset failed.")
    logger.info("Visualization stopped.")


if __name__ == "__main__":
    main()
