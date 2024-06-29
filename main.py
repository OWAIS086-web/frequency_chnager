import tkinter as tk
from tkinter import ttk, filedialog
import sounddevice as sd
import numpy as np
import wave
import os
from pydub import AudioSegment
from pydub.playback import play
from scipy.fft import fft, fftfreq

class ProAudioApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pro Audio Recorder and Player")

        self.recording = False
        self.frames = []
        self.sample_rate = 44100
        self.channels = 1
        self.volume = 1.0

        self.create_widgets()

    def create_widgets(self):
        # Frequency testing frame
        self.freq_frame = ttk.LabelFrame(self.root, text="Frequency Test")
        self.freq_frame.pack(pady=10, padx=10, fill="x")

        self.freq_label = ttk.Label(self.freq_frame, text="Frequency (Hz):")
        self.freq_label.grid(row=0, column=0, padx=5, pady=5)
        self.freq_entry = ttk.Entry(self.freq_frame)
        self.freq_entry.grid(row=0, column=1, padx=5, pady=5)
        self.freq_entry.insert(0, "140.85")

        self.freq_test_button = ttk.Button(self.freq_frame, text="Play Test Tone", command=self.play_test_tone)
        self.freq_test_button.grid(row=0, column=2, padx=5, pady=5)

        # Volume control frame
        self.volume_frame = ttk.LabelFrame(self.root, text="Volume Control")
        self.volume_frame.pack(pady=10, padx=10, fill="x")

        self.volume_label = ttk.Label(self.volume_frame, text="Volume (%):")
        self.volume_label.grid(row=0, column=0, padx=5, pady=5)
        self.volume_slider = ttk.Scale(self.volume_frame, from_=0, to=100, orient='horizontal', command=self.update_volume)
        self.volume_slider.set(100)
        self.volume_slider.grid(row=0, column=1, padx=5, pady=5)

        # File operations frame
        self.file_frame = ttk.LabelFrame(self.root, text="File Operations")
        self.file_frame.pack(pady=10, padx=10, fill="x")

        self.load_button = ttk.Button(self.file_frame, text="Load Audio File", command=self.load_audio_file)
        self.load_button.grid(row=0, column=0, padx=5, pady=5)

        self.play_file_button = ttk.Button(self.file_frame, text="Play Loaded File", command=self.play_loaded_audio)
        self.play_file_button.grid(row=0, column=1, padx=5, pady=5)

        self.analyze_button = ttk.Button(self.file_frame, text="Analyze Frequency", command=self.analyze_frequency)
        self.analyze_button.grid(row=0, column=2, padx=5, pady=5)

        # Record, play, and save buttons
        self.record_button = ttk.Button(self.root, text="Record", command=self.toggle_recording)
        self.record_button.pack(pady=5)

        self.play_button = ttk.Button(self.root, text="Play Recorded", command=self.play_audio)
        self.play_button.pack(pady=5)

        self.save_button = ttk.Button(self.root, text="Save Recorded", command=self.save_audio)
        self.save_button.pack(pady=5)

    def play_test_tone(self):
        frequency = float(self.freq_entry.get())
        duration = 2.0  # seconds
        t = np.linspace(0, duration, int(self.sample_rate * duration), endpoint=False)
        wave = 0.5 * np.sin(2 * np.pi * frequency * t)  # Generate sine wave
        wave = wave * self.volume  # Adjust volume
        sd.play(wave, self.sample_rate)

    def update_volume(self, event):
        self.volume = float(self.volume_slider.get()) / 100

    def toggle_recording(self):
        if self.recording:
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self):
        self.recording = True
        self.record_button.config(text="Stop")
        self.frames = []
        self.stream = sd.InputStream(callback=self.audio_callback, channels=self.channels, samplerate=self.sample_rate)
        self.stream.start()

    def stop_recording(self):
        self.recording = False
        self.record_button.config(text="Record")
        self.stream.stop()
        self.stream.close()

        # Auto-save the recorded audio
        self.save_audio(auto_save=True)

    def audio_callback(self, indata, frames, time, status):
        if self.recording:
            self.frames.append(indata.copy())

    def play_audio(self):
        if not self.frames:
            return
        audio_data = np.concatenate(self.frames, axis=0)
        audio_data = audio_data * self.volume  # Adjust volume
        sd.play(audio_data, self.sample_rate)

    def save_audio(self, auto_save=False):
        if not self.frames:
            return
        if auto_save:
            file_path = "recording_fixed.wav"
        else:
            file_path = filedialog.asksaveasfilename(defaultextension=".wav",
                                                     filetypes=[("WAV files", "*.wav"), ("All files", "*.*")])
            if not file_path:
                return

        fixed_frequency = 140.85  # Fixed frequency
        t = np.linspace(0, len(self.frames) / self.sample_rate, num=len(self.frames), endpoint=False)
        wave_data = 0.5 * np.sin(2 * np.pi * fixed_frequency * t)
        wave_data = wave_data * self.volume  # Adjust volume
        fixed_audio = (np.array(wave_data) + np.array(np.concatenate(self.frames, axis=0))) / 2

        with wave.open(file_path, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(fixed_audio.astype(np.int16).tobytes())

    def load_audio_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Audio files", "*.wav *.mp3"), ("All files", "*.*")])
        if file_path:
            self.loaded_audio = AudioSegment.from_file(file_path)
            self.loaded_audio_path = file_path

    def play_loaded_audio(self):
        if hasattr(self, 'loaded_audio'):
            play(self.loaded_audio)

    def analyze_frequency(self):
        if hasattr(self, 'loaded_audio'):
            samples = np.array(self.loaded_audio.get_array_of_samples())
            N = len(samples)
            yf = fft(samples)
            xf = fftfreq(N, 1 / self.sample_rate)
            idx = np.argmax(np.abs(yf))
            dominant_freq = xf[idx]
            tk.messagebox.showinfo("Frequency Analysis", f"Dominant Frequency: {dominant_freq:.2f} Hz")

if __name__ == "__main__":
    root = tk.Tk()
    app = ProAudioApp(root)
    root.mainloop()
