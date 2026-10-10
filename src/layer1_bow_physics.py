"""
Layer 1: Bow & Rosin Physics ("Taming the Buzzer")
--------------------------------------------------
In Layer 0, we saw that a pure mathematical sawtooth wave sounds like an angry
electric buzzer. Why? Because a computer wave is "too perfect":
1. It assumes the bow is a zero-width needle.
2. It assumes the string has zero stiffness and can bend at infinite sharpness.
3. It has zero friction noise and starts instantaneously without physical resistance.

In Layer 1, we implement the real physical mechanics of the bow and string:
- Finite Bow-Ribbon Width (horsehair is a 10 mm ribbon, modeled via sinc smoothing).
- Corner Rounding & Dispersion (real string stiffness rounds off the harsh kink).
- Rosin Attack Crunch ("Chiff") & Cycle-Synchronous Friction Noise.

Benchmark Melody: Twinkle, Twinkle, Little Star (Suzuki Violin Method)
"""

import os
import numpy as np
import scipy.signal as signal
import soundfile as sf
import matplotlib.pyplot as plt

class HelmholtzString:
    def __init__(
        self,
        sample_rate: int = 44100,
        beta: float = 0.10,                   # Bow contact position from bridge (~10%)
        corner_rounding: float = 0.0018,      # String stiffness damping factor
        attack_crunch_level: float = 0.15,    # Initial rosin bite ("chiff")
        attack_crunch_sec: float = 0.040,     # 40ms attack transient
        rosin_noise_level: float = 0.035      # Steady friction hiss
    ):
        self.sample_rate = sample_rate
        self.beta = beta
        self.corner_rounding = corner_rounding
        self.attack_crunch_level = attack_crunch_level
        self.attack_crunch_sec = attack_crunch_sec
        self.rosin_noise_level = rosin_noise_level
        
        # Rosin noise filter: pine rosin friction concentrates between 2 kHz and 7.5 kHz
        nyq = sample_rate / 2.0
        low = min(2200.0 / nyq, 0.95)
        high = min(7500.0 / nyq, 0.99)
        self.noise_b, self.noise_a = signal.butter(2, [low, high], btype="bandpass")

    def synthesize_note(self, freq: float, duration: float, bow_dir: int = 1) -> np.ndarray:
        n_samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, n_samples, endpoint=False)
        phase = 2.0 * np.pi * freq * t
        
        # 1. Band-limited Helmholtz string synthesis
        # Real strings cannot vibrate past the Nyquist frequency
        max_harmonics = min(int(self.sample_rate / (2.2 * freq)), 45)
        max_harmonics = max(max_harmonics, 1)
        
        string_wave = np.zeros(n_samples, dtype=np.float64)
        
        for n in range(1, max_harmonics + 1):
            # Physical Phenomenon 1: Finite Bow Ribbon Width (~10 mm wide horsehair)
            # A wide bow band smooths out ultra-high harsh harmonics via sinc integration
            ribbon_filter = 0.30 + 0.70 * np.abs(np.sinc(n * self.beta))
            
            # Physical Phenomenon 2: Corner Rounding (String stiffness EI)
            # High harmonics travel faster and dampen faster, rounding the sharp kink
            stiffness_damping = np.exp(-self.corner_rounding * (n ** 1.65))
            
            # Physical Phenomenon 3: Dispersion Phase Shift
            # Harmonics are not locked in zero phase; phase curvature removes digital buzz
            dispersion_phase = 0.08 * (n ** 1.35)
            
            # 1/n fundamental sawtooth harmonic amplitude
            amp = (1.0 / n) * ribbon_filter * stiffness_damping
            string_wave += amp * np.sin(n * phase + dispersion_phase)
            
        # Direction polarity: down-bow (+1) vs up-bow (-1)
        string_wave *= float(np.sign(bow_dir))
        
        # 2. Physical Phenomenon 4: Rosin Friction Mechanics
        # White noise filtered to the acoustic frequency of crystalline pine rosin
        raw_noise = np.random.randn(n_samples)
        filtered_rosin = signal.lfilter(self.noise_b, self.noise_a, raw_noise)
        
        # Attack crunch ("chiff"): bow hair biting the string for the first 30-50 ms
        attack_env = np.exp(-t / max(self.attack_crunch_sec, 0.005)) * self.attack_crunch_level
        
        # Cycle-synchronous friction: horsehair scrapes during the slip phase of every period
        slip_pulse = (0.5 + 0.5 * np.sin(phase - np.pi / 2.0)) ** 2
        steady_noise = self.rosin_noise_level * (0.35 + 0.65 * slip_pulse)
        
        rosin_texture = filtered_rosin * (attack_env + steady_noise)
        
        # Combine string vibration with rosin friction
        full_note = string_wave + rosin_texture
        
        # Musical amplitude envelope (smooth bow entry and exit)
        rise_len = int(0.025 * self.sample_rate)  # 25ms bow acceleration rise
        fall_len = int(0.035 * self.sample_rate)  # 35ms bow release
        env = np.ones(n_samples)
        if rise_len > 0:
            env[:rise_len] = np.sin(np.linspace(0, np.pi / 2, rise_len)) ** 2
        if fall_len > 0:
            env[-fall_len:] = np.cos(np.linspace(0, np.pi / 2, fall_len)) ** 2
            
        return full_note * env

def generate_twinkle():
    sample_rate = 44100
    model = HelmholtzString(sample_rate=sample_rate)
    
    # Universal benchmark melody: Twinkle, Twinkle, Little Star (Suzuki Violin Method)
    notes = [
        # "Twinkle, twinkle, little star"
        ("C4", 261.63, 0.5),
        ("C4", 261.63, 0.5),
        ("G4", 392.00, 0.5),
        ("G4", 392.00, 0.5),
        ("A4", 440.00, 0.5),
        ("A4", 440.00, 0.5),
        ("G4", 392.00, 1.0),
        # "How I wonder what you are"
        ("F4", 349.23, 0.5),
        ("F4", 349.23, 0.5),
        ("E4", 329.63, 0.5),
        ("E4", 329.63, 0.5),
        ("D4", 293.66, 0.5),
        ("D4", 293.66, 0.5),
        ("C4", 261.63, 1.0),
    ]
    
    audio_segments = []
    gap = np.zeros(int(0.035 * sample_rate))  # 35ms bow articulation gap
    bow_dir = 1
    
    for name, freq, dur in notes:
        note_audio = model.synthesize_note(freq, dur, bow_dir=bow_dir)
        audio_segments.append(note_audio)
        audio_segments.append(gap)
        bow_dir *= -1  # Alternate down-bow and up-bow
        
    full_audio = np.concatenate(audio_segments)
    
    # Normalize peak to -1 dB
    peak = np.max(np.abs(full_audio))
    if peak > 0:
        full_audio = (full_audio / peak) * 0.85
        
    return full_audio, sample_rate

def plot_layer1_comparison(sample_rate: int):
    """
    Plots a direct side-by-side comparison between:
    - Layer 0: Naive Razor-Sharp Sawtooth
    - Layer 1: Physically Informed Helmholtz String (Corner Rounding + Attack Chiff)
    """
    freq = 440.0  # Concert A4
    duration = 0.08  # 80ms to see both the attack transient and the rounded cycles
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    
    # Layer 0 Wave
    layer0_wave = signal.sawtooth(2 * np.pi * freq * t)
    
    # Layer 1 Wave
    model = HelmholtzString(sample_rate=sample_rate)
    layer1_wave = model.synthesize_note(freq, duration)
    
    # Frequency Spectrum (1 second sample)
    t_long = np.linspace(0, 1.0, sample_rate, endpoint=False)
    l0_long = signal.sawtooth(2 * np.pi * freq * t_long)
    l1_long = model.synthesize_note(freq, 1.0)
    
    f0_fft = np.abs(np.fft.rfft(l0_long))
    f1_fft = np.abs(np.fft.rfft(l1_long))
    freqs = np.fft.rfftfreq(sample_rate, 1.0 / sample_rate)
    mask = freqs <= 8000
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 7))
    fig.patch.set_facecolor('#121212')
    
    # Subplot 1: Time Domain Comparison
    ax1.set_facecolor('#1e1e1e')
    # Plot first 20ms zoom
    zoom_samples = int(0.015 * sample_rate)
    ax1.plot(t[:zoom_samples] * 1000, layer0_wave[:zoom_samples], color='#ff4444', 
             linestyle='--', linewidth=1.8, label="Layer 0: Naive Sawtooth (Infinite Cliff)")
    ax1.plot(t[:zoom_samples] * 1000, layer1_wave[:zoom_samples] / np.max(np.abs(layer1_wave[:zoom_samples])), 
             color='#00ffcc', linewidth=2.2, label="Layer 1: Helmholtz String (Corner Rounded + Ribbon Sinc)")
    ax1.set_title("Waveform Comparison: Naive Cliff vs. Physical Corner Rounding", color='white', fontsize=12, pad=10)
    ax1.set_xlabel("Time (milliseconds)", color='#cccccc')
    ax1.set_ylabel("Amplitude", color='#cccccc')
    ax1.tick_params(colors='#cccccc')
    ax1.grid(True, color='#333333', linestyle='--')
    ax1.legend(facecolor='#2a2a2a', edgecolor='#555555', labelcolor='white')
    ax1.set_ylim(-1.3, 1.3)
    
    # Subplot 2: Frequency Spectrum Comparison
    ax2.set_facecolor('#1e1e1e')
    ax2.plot(freqs[mask], 20 * np.log10(f0_fft[mask] / np.max(f0_fft) + 1e-6), 
             color='#ff4444', linestyle='--', linewidth=1.5, label="Layer 0: Harsh Infinite Comb (1/n)")
    ax2.plot(freqs[mask], 20 * np.log10(f1_fft[mask] / np.max(f1_fft) + 1e-6), 
             color='#00ffcc', linewidth=1.8, label="Layer 1: Natural Stiffness Roll-off & Rosin Energy")
    ax2.set_title("Harmonic Spectrum: Eliminating Harsh Metallic Frequencies (>3 kHz)", color='white', fontsize=12, pad=10)
    ax2.set_xlabel("Frequency (Hz)", color='#cccccc')
    ax2.set_ylabel("Magnitude (dB)", color='#cccccc')
    ax2.tick_params(colors='#cccccc')
    ax2.grid(True, color='#333333', linestyle='--')
    ax2.legend(facecolor='#2a2a2a', edgecolor='#555555', labelcolor='white')
    ax2.set_ylim(-65, 5)
    
    plt.tight_layout()
    os.makedirs("plots", exist_ok=True)
    plt.savefig("plots/layer1_comparison.png", dpi=200, facecolor=fig.get_facecolor())
    plt.close()

if __name__ == "__main__":
    os.makedirs("audio", exist_ok=True)
    os.makedirs("plots", exist_ok=True)
    
    print("[VIOLIN JOURNEY] Layer 1: Synthesizing Helmholtz string with bow & rosin physics...")
    audio, sr = generate_twinkle()
    
    out_path = os.path.join("audio", "layer1_helmholtz_string.wav")
    sf.write(out_path, audio, sr, subtype='PCM_24')
    print(f"[OK] Generated audio: {out_path}")
    
    print("[INFO] Generating Layer 1 comparison plots...")
    plot_layer1_comparison(sr)
    print("[OK] Generated plot: plots/layer1_comparison.png")
    print("[DONE] Layer 1 complete! Listen to layer1_helmholtz_string.wav to hear the buzzer tamed into a string.")
