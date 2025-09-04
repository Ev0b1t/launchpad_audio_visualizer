import cProfile
import pstats
import asyncio
import argparse
from datetime import datetime
import numpy as np
import launchpad_py as launchpad
from asyncstdlib import enumerate as aenumerate
from core.config import CONFIG
from core.laucnhpad_visualization import visualize_audio_bands
from utils.general import find_opened_port
from utils.logger import logger
from core.capture_audio import capture_audio, handle_chunk
from core.state import reset_state, STATE_RESETTED, GLOBAL_PAUSE_START_TIME
from core.constants import PSYCHOACOUSTIC_WEIGHTS

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
    global CONFIG, PSYCHOACOUSTIC_WEIGHTS

    fast_ema = CONFIG.ema.FAST_SMOOTHING
    slow_ema = CONFIG.ema.SLOW_SMOOTHING

    # Apply psychoacoustic weights to the input data
    weighted_rms = bands_rms * np.array(PSYCHOACOUSTIC_WEIGHTS)

    # Update EMA with weighted values
    for i, rms_val in enumerate(weighted_rms):
        CONFIG.bands.FAST[i] = fast_ema * rms_val + (1 - fast_ema) * CONFIG.bands.FAST[i]
        CONFIG.bands.SLOW[i] = slow_ema * rms_val + (1 - slow_ema) * CONFIG.bands.SLOW[i]

    # Vectorized normalization
    fast_arr = np.array(CONFIG.bands.FAST)
    slow_arr = np.array(CONFIG.bands.SLOW)

    # Protection from division by zero + normalization
    ratio = np.where(slow_arr < 1e-6, 0.0, fast_arr / slow_arr)
    brightness = np.tanh(ratio)

    # Hard threshold for noise
    brightness[brightness < 0.08] = 0.0

    # Simple smoothing of adjacent bands
    if len(brightness) > 2:
        smoothed = brightness
        smoothed[1:-1] = 0.5 * brightness[1:-1] + 0.25 * (brightness[:-2] + brightness[2:])

    return brightness

async def play_and_visualize(lp, chunk_size: int = 1024, hanning_window: np.ndarray = np.hanning(1024)):
    global CONFIG, STATE_RESETTED, GLOBAL_PAUSE_START_TIME

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

                    # Reset the pause timer, since the signal is back
                    if GLOBAL_PAUSE_START_TIME is not None:
                        GLOBAL_PAUSE_START_TIME = None
                else:
                    # No signal, start or continue the pause countdown
                    if GLOBAL_PAUSE_START_TIME is None:
                        # First moment of silence, start the timer
                        GLOBAL_PAUSE_START_TIME = datetime.now()
                        logger.info(f"Signal lost. Starting {CONFIG.threshold.PAUSE_THRESHOLD_TO_RESET_STATE.total_seconds()} second countdown to reset.")

                    # Check if the pause threshold has been exceeded
                    if (datetime.now() - GLOBAL_PAUSE_START_TIME) >= CONFIG.threshold.PAUSE_THRESHOLD_TO_RESET_STATE:
                        # If the state is not already resetted, reset it now
                        if not STATE_RESETTED:
                            logger.info(f"{CONFIG.threshold.PAUSE_THRESHOLD_TO_RESET_STATE.total_seconds()} second pause detected. Resetting state...")
                            reset_state()
                            await visualize_audio_bands(lp, [0.0] * len(CONFIG.bands.RANGE))
                            lp.Reset()
                            logger.info("State resetted.")
                            STATE_RESETTED = True
                        else:
                            # State is already resetted, wait for the new input signal
                            await asyncio.sleep(0.01)
                    else:
                        # Still in the second pause, just wait
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
