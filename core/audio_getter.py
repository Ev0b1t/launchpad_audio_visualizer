import numpy as np


async def get_bands_parts(audio, chunk_size: int):
    for i in range(0, len(audio), chunk_size):
        c = audio[i:i+chunk_size]
        amplitude_arr = np.array(c.get_array_of_samples(), dtype=np.float32)
        normalized_arr = amplitude_arr / 32768.0  # PCM16 normalization

        yield normalized_arr, c, c.frame_rate


def main():
    # 1. Got chunk
    # 2. async send this chunk to the function
    #    to get the volume and spread of hz
    # np.set_printoptions(threshold=sys.maxsize)

    audio_fpath = r"/home/ev0b1t/Downloads/Basshunter DotA (Offical Video).mp3"

    res = get_bands_parts(audio_fpath)

    for pi, part in enumerate(res, start=1):
        logger.debug(f"Part Num - {pi} | Part data - {part}")



if __name__ == "__main__":
    main()