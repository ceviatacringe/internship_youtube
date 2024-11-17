import moviepy.editor as mp
import numpy as np
from scipy.io import wavfile
import os
from log import logger

def extract_audio_from_video(mp4_file, output_audio_file="audio.wav"):
    video = mp.VideoFileClip(mp4_file)
    # Extract the audio
    audio = video.audio
    # Write the audio to a wav file
    audio.write_audiofile(output_audio_file, codec='pcm_s16le')
    return output_audio_file

def calculate_dB_levels(audio_file):
    # Load the audio file
    sample_rate, audio_data = wavfile.read(audio_file)
    # Ensure the audio is mono (one channel)
    if len(audio_data.shape) > 1:
        audio_data = audio_data.mean(axis=1)
    
    # Calculate the dB levels
    def rms_to_db(rms):
        return 20 * np.log10(rms) if rms > 0 else -np.inf

    # Calculate the RMS value for audio data
    rms_values = np.sqrt(np.mean(audio_data.astype(np.float32) ** 2))
    peak_db = rms_to_db(np.max(np.abs(audio_data.astype(np.float32))))  # Highest peak
    average_db = rms_to_db(rms_values)  # Average level
    
    # Filter out silent periods by setting a threshold
    threshold = 1e-6
    non_silent_audio = audio_data[np.abs(audio_data) > threshold]

    if non_silent_audio.size == 0:
        min_db = -np.inf  # If no non-silent audio, return -inf
    else:
        min_db = rms_to_db(np.min(np.abs(non_silent_audio.astype(np.float32))))  # Quietest non-silent part

    return min_db, peak_db, average_db

def write_to_file(min_db, peak_db, average_db, output_file="audiovalues.txt"):
    with open(output_file, "w") as file:
        file.write(f"Lowest Volume (dB): {min_db:.2f} dB\n")
        file.write(f"Highest Peak (dB): {peak_db:.2f} dB\n")
        file.write(f"Average Volume (dB): {average_db:.2f} dB\n")

def measure_audio(mp4_file):
    audio_file = extract_audio_from_video(mp4_file)
    min_db, peak_db, average_db = calculate_dB_levels(audio_file)
    
    # Write the values to the file
    write_to_file(min_db, peak_db, average_db)
    
    # logger the values
    logger.info(f"Lowest Volume (dB): {min_db:.2f} dB")
    logger.info(f"Highest Peak (dB): {peak_db:.2f} dB")
    logger.info(f"Average Volume (dB): {average_db:.2f} dB")
    
    # Clean up the temporary audio file
    if os.path.exists(audio_file):
        os.remove(audio_file)
