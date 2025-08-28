import sys
import asyncio
import numpy as np
import launchpad_py as launchpad
from pydub import AudioSegment
import sounddevice as sd
from core.config import CONFIG
from core.state import EMA_GLOBAL_PEAK
from core.laucnhpad_visualization import visualize_audio_bands
from utils.general import find_opened_port
from utils.logger import logger




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

def normalize_bands(bands_rms):
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



async def play_and_visualize(lp, audio, chunk_size: int = 1024):
    """
    Main function to play an audio file and visualize it in real-time.
    """

    # SoundDevice callback for audio playback
    def audio_callback(outdata, frames, time, status):
        nonlocal pos
        if status:
            logger.debug(f"Audio callback status: {status}")

        end = pos + frames * channels
        if end > len(samples):
            # End of audio stream
            out_chunk = np.zeros((frames, channels), dtype=np.float32)
            available = (len(samples) - pos) // channels
            if available > 0:
                out_chunk[:available] = samples[pos:pos+available*channels].reshape(-1, channels)
            outdata[:] = out_chunk
            raise sd.CallbackStop()
        else:
            # Normal audio chunk playback
            out_chunk = samples[pos:end].reshape(-1, channels)
            outdata[:] = out_chunk
        pos = end


    samplerate = audio.frame_rate
    channels = audio.channels
    pos = 0

    # Convert audio to a float32 numpy array and normalize to [-1, 1]
    samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
    samples /= np.iinfo(audio.array_type).max

    # Windowing function to reduce spectral leakage
    window = np.hanning(chunk_size)

    stream = sd.OutputStream(
        samplerate=samplerate,
        channels=channels,
        callback=audio_callback,
        blocksize=chunk_size
    )

    with stream:
        while pos < len(samples):
            # Extract and process audio chunk
            chunk = samples[pos:pos + chunk_size * channels]
            if 0 < len(chunk) < chunk_size * channels:
                break

            bands_rms = process_audio_chunk(
                chunk, samplerate, channels, chunk_size, window,
                CONFIG.bands.RANGE
            )

            # Normalize and send to Launchpad
            normalized_bands = normalize_bands(bands_rms)
            await visualize_audio_bands(lp, normalized_bands)

            # Wait for the chunk to finish playing
            await asyncio.sleep(chunk_size / samplerate)

def main():
    """
    Main function to run the audio visualizer.
    """
    if len(sys.argv) < 2:
        logger.debug(r"Usage: python your_script_name.py \<path_to_audio_file.mp3>")
        sys.exit(1)

    AUDIO_FPATH = sys.argv[1]
    lp = launchpad.LaunchpadPro()
    launchpad_port_index = find_opened_port(lp)

    if launchpad_port_index == -1:
        logger.debug("The launchpad port was not found.")
        return

    # Reset lights
    lp.Reset()

    # Load audio
    try:
        audio = AudioSegment.from_mp3(AUDIO_FPATH)
    except FileNotFoundError:
        logger.error(f"Error: The file at {AUDIO_FPATH} was not found.")
        return
    except Exception as e:
        logger.exception(f"Error loading audio file: {e}")
        return

    try:
        asyncio.run(play_and_visualize(lp, audio))
    except KeyboardInterrupt:
        logger.debug("Visualization stopped by user.")
    finally:
        lp.Reset()


if __name__ == "__main__":
    main()
