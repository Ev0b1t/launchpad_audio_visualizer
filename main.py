import cProfile
import pstats
import asyncio
import argparse
import numpy as np
import launchpad_py as launchpad
from asyncstdlib import enumerate as aenumerate
from core.config import CONFIG
from core.laucnhpad_visualization import visualize_audio_bands
from utils.general import find_opened_port
from utils.logger import logger
from core.capture_audio import capture_audio, handle_chunk
from core.state import reset_state, STATE_RESETTED

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

    fast_ema_smoothing = CONFIG.ema.FAST_SMOOTHING
    slow_ema_smoothing = CONFIG.ema.SLOW_SMOOTHING

    # Updating the global and the individual EMA
    for i, rms_val in enumerate(bands_rms):
        # add fast and slow EMA
        CONFIG.bands.FAST[i] = (fast_ema_smoothing * rms_val) + ((1 - fast_ema_smoothing) * CONFIG.bands.FAST[i])
        CONFIG.bands.SLOW[i] = (slow_ema_smoothing * rms_val) + ((1 - slow_ema_smoothing) * CONFIG.bands.SLOW[i])

    normalized_bands = []

    for i in range(len(bands_rms)):
        fast = CONFIG.bands.FAST[i]
        slow = CONFIG.bands.SLOW[i]

        # Protection from division by zero
        if slow < 1e-6:
            ratio = 0.0
        else:
            ratio = fast / slow

        # Limit the range to 0..1
        brightness = np.tanh(ratio)

        normalized_bands.append(brightness)

    # wave effect
    for i in range(len(normalized_bands)):
        left = normalized_bands[i-1] if i > 0 else normalized_bands[i]
        right = normalized_bands[i+1] if i < len(normalized_bands)-1 else normalized_bands[i]
        center = normalized_bands[i]
        diff_left = abs(center - left)
        diff_right = abs(center - right)

        weight_left = 0.25 * (1 - diff_left)
        weight_right = 0.25 * (1 - diff_right)
        weight_center = 1.0 - weight_left - weight_right

        normalized_bands[i] = weight_left * left + weight_center * center + weight_right * right

    return normalized_bands

async def play_and_visualize(lp, chunk_size: int = 1024, hanning_window: np.ndarray = np.hanning(1024)):
    global CONFIG, STATE_RESETTED

    async for i, audio_b in aenumerate(capture_audio(chunk_size)):
        chunk = handle_chunk(audio_b)
        if not(len(chunk) < chunk_size * CONFIG.audio.CHANNELS):
            if i % 2 == 0:
                bands_rms = process_audio_chunk(
                    chunk, CONFIG.audio.SAMPLERATE, CONFIG.audio.CHANNELS, chunk_size, hanning_window,
                    CONFIG.bands.RANGE
                )
                if np.any(bands_rms):
                    normalized_bands = normalize_bands(bands_rms)
                    await visualize_audio_bands(lp, normalized_bands)
                    # if the state was resetted, set it to False one time
                    if STATE_RESETTED is not False:
                        STATE_RESETTED = False
                else:
                    # if the bands rms is empty, reset the state
                    if not STATE_RESETTED:
                        logger.info("Resetting state...")
                        reset_state()
                        await visualize_audio_bands(lp, [0.0] * len(CONFIG.bands.RANGE))
                        lp.Reset()
                        logger.info("State resetted.")
                        STATE_RESETTED = True
                    else:
                        # wait for the new input signal
                        await asyncio.sleep(0.01)

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
