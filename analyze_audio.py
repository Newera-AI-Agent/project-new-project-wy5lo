import librosa
import numpy as np
import json
import os

# Load the audio file
audio_path = "ptasinski - life force (ft. RJ Pasin)_128k.mp3"
y, sr = librosa.load(audio_path, sr=None)

duration = len(y) / sr
print(f"Duration: {duration:.2f} seconds ({duration/60:.2f} minutes)")
print(f"Sample rate: {sr} Hz")

# 1. Beat tracking
tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
tempo = float(tempo) if isinstance(tempo, np.ndarray) else tempo
beat_times = librosa.frames_to_time(beat_frames, sr=sr)
print(f"Estimated tempo: {tempo:.2f} BPM")
print(f"Number of beats: {len(beat_times)}")

# 2. Onset detection
onset_frames = librosa.onset.onset_detect(y=y, sr=sr, units='frames')
onset_times = librosa.frames_to_time(onset_frames, sr=sr)
print(f"Number of onsets: {len(onset_times)}")

# 3. Spectral centroid (brightness)
spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
spectral_centroid_times = librosa.frames_to_time(range(len(spectral_centroids)), sr=sr)

# 4. Spectral rolloff
spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]

# 5. RMS energy (loudness)
rms = librosa.feature.rms(y=y)[0]
rms_times = librosa.frames_to_time(range(len(rms)), sr=sr)

# 6. Spectral bandwidth
spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]

# 7. Zero crossing rate
zcr = librosa.feature.zero_crossing_rate(y)[0]

# 8. Chroma features (harmonic content)
chroma = librosa.feature.chroma_stft(y=y, sr=sr)

# 9. MFCCs
mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)

# 10. Harmonic/Percussive separation
y_harmonic, y_percussive = librosa.effects.hpss(y)

# Find high-energy sections (for major cuts)
# Smooth RMS for section detection
window_size = int(sr * 2 / 512)  # ~2 second window
if window_size > 1:
    rms_smooth = np.convolve(rms, np.ones(window_size)/window_size, mode='same')
else:
    rms_smooth = rms

# Detect peaks in energy
from scipy.signal import find_peaks
peaks, properties = find_peaks(rms_smooth, distance=int(sr*1/512), prominence=np.std(rms_smooth)*0.5)
peak_times = librosa.frames_to_time(peaks, sr=sr)
print(f"High-energy peaks: {len(peak_times)}")

# 11. Tempogram (rhythm analysis)
tempogram = librosa.feature.tempogram(y=y, sr=sr)

# Save all analysis data
analysis_data = {
    "duration": float(duration),
    "sample_rate": int(sr),
    "tempo": float(tempo),
    "beat_times": beat_times.tolist(),
    "onset_times": onset_times.tolist(),
    "spectral_centroid": spectral_centroids.tolist(),
    "spectral_centroid_times": spectral_centroid_times.tolist(),
    "spectral_rolloff": spectral_rolloff.tolist(),
    "rms": rms.tolist(),
    "rms_times": rms_times.tolist(),
    "spectral_bandwidth": spectral_bandwidth.tolist(),
    "zcr": zcr.tolist(),
    "chroma": chroma.tolist(),
    "mfccs": mfccs.tolist(),
    "high_energy_peaks": peak_times.tolist(),
    "harmonic_percussive": {
        "harmonic_energy": float(np.sum(y_harmonic**2)),
        "percussive_energy": float(np.sum(y_percussive**2))
    }
}

with open('audio_analysis.json', 'w') as f:
    json.dump(analysis_data, f, indent=2)

print("Analysis saved to audio_analysis.json")

# Print key timing info for video editing
print("\n=== KEY TIMING FOR VIDEO EDITING ===")
print(f"Total duration: {duration:.2f}s")
print(f"Beat times (first 20): {beat_times[:20]}")
print(f"Onset times (first 20): {onset_times[:20]}")
print(f"High energy peaks: {peak_times}")

# Calculate beat intervals for cut timing
beat_intervals = np.diff(beat_times)
print(f"\nAverage beat interval: {np.mean(beat_intervals):.3f}s")
print(f"Min beat interval: {np.min(beat_intervals):.3f}s")
print(f"Max beat interval: {np.max(beat_intervals):.3f}s")