import sys
import asyncio
import numpy as np
import launchpad_py as launchpad
from pydub import AudioSegment
import sounddevice as sd
from core.constants import *
from core.laucnhpad_visualization import visualize_audio_bands
from utils.general import find_opened_port
from utils.logger import logger



async def play_and_visualize(lp, audio, chunk_size: int = 1024):
    """
    Plays an audio file and visualizes it in real-time on the Launchpad Pro.
    """
    global PEAK_EMA, BANDS_RANGE, EMA_SMOOTHING

    samplerate = audio.frame_rate
    channels = audio.channels
    pos = 0

    # Convert audio to a float32 numpy array and normalize to [-1, 1]
    samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
    samples /= np.iinfo(audio.array_type).max

    # Windowing function to reduce spectral leakage
    window = np.hanning(chunk_size)

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

    # Setup the output stream
    stream = sd.OutputStream(
        samplerate=samplerate,
        channels=channels,
        callback=audio_callback,
        blocksize=chunk_size
    )

    with stream:
        while pos < len(samples):
            # Extract a chunk of audio for FFT
            chunk = samples[pos:pos + chunk_size * channels]

            # Break if the chunk is too small
            if 0 < len(chunk) < chunk_size * channels:
                logger.debug(f"Got a final chunk - {len(chunk)}")
                break

            # Convert to mono if stereo
            if channels == 2:
                chunk = chunk.reshape(-1, 2)
                chunk_mono = chunk.mean(axis=1)
            else:
                chunk_mono = chunk

            # Apply the Hann window to the chunk
            chunk_windowed = chunk_mono * window

            # Perform a Real FFT (rfft) to get the frequency spectrum
            spectrum = np.abs(np.fft.rfft(chunk_windowed))
            freqs = np.fft.rfftfreq(len(chunk_windowed), 1.0 / samplerate)

            # Calculate RMS for each frequency band
            bands_arr = []
            for low, high in BANDS_RANGE:
                mask = (freqs >= low) & (freqs < high)
                band_vals = spectrum[mask]
                if band_vals.size > 0:
                    band_rms = np.sqrt(np.mean(band_vals ** 2))
                    bands_arr.append(band_rms)
                else:
                    bands_arr.append(0.0)

            # --- KEY IMPROVEMENT: Normalization with EMA ---
            # This logic prevents all bars from jumping to max simultaneously.
            # It creates a smoother, more dynamic visualization that adapts to the song's energy.

            # Find the max value in the current chunk
            max_val = max(bands_arr) if bands_arr else 0.0

            # Update the smoothed peak EMA
            PEAK_EMA = (EMA_SMOOTHING * max_val) + ((1 - EMA_SMOOTHING) * PEAK_EMA)

            # Normalize the bands using the smoothed EMA peak
            if PEAK_EMA > 0.01:  # Prevent division by a very small number
                bands_arr = [x / PEAK_EMA for x in bands_arr]
            else:
                bands_arr = [0.0] * len(bands_arr)

            # Cap the values at 1.0
            bands_arr = [min(1.0, x) for x in bands_arr]

            # Send the normalized data to the Launchpad
            await visualize_audio_bands(lp, bands_arr)

            # Wait for the chunk to finish playing
            await asyncio.sleep(chunk_size / samplerate)

def main():
    """
    Main function to run the audio visualizer.
    """
    if len(sys.argv) < 2:
        logger.debug("Usage: python your_script_name.py <path_to_audio_file.mp3>")
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
        logger.debug(f"Error: The file at {AUDIO_FPATH} was not found.")
        return
    except Exception as e:
        logger.debug(f"Error loading audio file: {e}")
        return

    try:
        asyncio.run(play_and_visualize(lp, audio))
    except KeyboardInterrupt:
        logger.debug("Visualization stopped by user.")
    finally:
        lp.Reset()


if __name__ == "__main__":
    main()
