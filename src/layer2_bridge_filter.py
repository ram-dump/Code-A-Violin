"""
Layer 2: The Rocking Bridge ("Finding the Soloist's Voice")
-----------------------------------------------------------
In Layer 1, we tamed the harsh 8-bit digital buzzer into a real vibrating wire
using bow ribbon width, string stiffness, and rosin friction.

However, if you listen to Layer 1, it sounds like an unplugged electric wire:
it is muffled, dry, and lacks acoustic projection.

In Layer 2, we implement the mechanical bridge filter:
1. The Bridge is an Asymmetric Rocking Lever:
   - The right foot is firmly anchored over the vertical soundpost ("the soul").
   - The left foot rocks up and down, pumping the bass bar.
2. The "Bridge Hill" (2.5 kHz - 3.5 kHz Resonance Boost):
   - The carved waist and heart of the maple bridge act as a mechanical spring-mass
     filter that boosts frequencies between 2.5 kHz and 3.5 kHz by +12 to +15 dB.
   - This matches human ear canal resonance (3 kHz), allowing an unamplified 400g violin
     to cut through a 90-piece symphony orchestra!
3. High-Frequency Lowpass Roll-off (>5.5 kHz):
   - Above 5.5 kHz, the bridge's physical mass rolls off screeching frequencies.

Benchmark Melody: Twinkle, Twinkle, Little Star (Suzuki Violin Method)
"""

import os
import numpy as np
import scipy.signal as signal
import soundfile as sf
import matplotlib.pyplot as plt

# Import the Layer 1 Helmholtz string generator
from layer1_bow_physics import HelmholtzString

class RockingBridgeFilter:
    """
    Simulates the acoustic transfer function of a carved maple violin bridge
    rocking on the soundpost pivot.
    """
    def __init__(
        self,
        sample_rate: int = 44100,
        bridge_hill_center_hz: float = 2850.0,   # Peak resonance of bridge rocking mode
        bridge_hill_gain_db: float = 14.5,       # +14.5 dB soloist projection boost
        bridge_hill_q: float = 2.2,              # Bandwidth quality factor
        cutoff_high_hz: float = 5800.0           # High-frequency inertia roll-off
    ):
        self.sample_rate = sample_rate
        self.bridge_hill_center_hz = bridge_hill_center_hz
        self.bridge_hill_gain_db = bridge_hill_gain_db
        self.bridge_hill_q = bridge_hill_q
        self.cutoff_high_hz = cutoff_high_hz
        
        # 1. Biquad Peaking Filter for the Bridge Hill (2.5 kHz - 3.5 kHz)
        # Standard Audio EQ CookBook formula
        A = 10.0 ** (bridge_hill_gain_db / 40.0)
        w0 = 2.0 * np.pi * bridge_hill_center_hz / sample_rate
        alpha = np.sin(w0) / (2.0 * bridge_hill_q)
        
        b0 = 1.0 + alpha * A
        b1 = -2.0 * np.cos(w0)
        b2 = 1.0 - alpha * A
        a0 = 1.0 + alpha / A
        a1 = -2.0 * np.cos(w0)
        a2 = 1.0 - alpha / A
        
        self.b_hill = np.array([b0, b1, b2]) / a0
        self.a_hill = np.array([a0, a1, a2]) / a0
        
        # 2. Secondary waist flexure peak around 3.3 kHz (+6 dB, Q=3.0)
        A2 = 10.0 ** (6.0 / 40.0)
        w02 = 2.0 * np.pi * 3350.0 / sample_rate
        alpha2 = np.sin(w02) / (2.0 * 3.0)
        self.b_hill2 = np.array([1.0 + alpha2 * A2, -2.0 * np.cos(w02), 1.0 - alpha2 * A2]) / (1.0 + alpha2 / A2)
        self.a_hill2 = np.array([1.0 + alpha2 / A2, -2.0 * np.cos(w02), 1.0 - alpha2 / A2]) / (1.0 + alpha2 / A2)
        
        # 3. 2nd-order lowpass filter at 5.8 kHz (rolling off harsh rasp)
        nyq = sample_rate / 2.0
        self.b_lp, self.a_lp = signal.butter(2, min(cutoff_high_hz / nyq, 0.95), btype='low')

    def filter_signal(self, string_audio: np.ndarray) -> np.ndarray:
        """
        Passes raw string shear force through the rocking bridge filter.
        """
        # Apply Bridge Hill resonance
        y1 = signal.lfilter(self.b_hill, self.a_hill, string_audio)
        y2 = signal.lfilter(self.b_hill2, self.a_hill2, y1)
        # Apply high-frequency bridge damping
        y_out = signal.lfilter(self.b_lp, self.a_lp, y2)
        return y_out

def generate_twinkle_layer2():
    sample_rate = 44100
    string_model = HelmholtzString(sample_rate=sample_rate)
    bridge = RockingBridgeFilter(sample_rate=sample_rate)
    
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
    gap = np.zeros(int(0.035 * sample_rate))
    bow_dir = 1
    
    for name, freq, dur in notes:
        # 1. Synthesize string excitation (Layer 1)
        raw_string = string_model.synthesize_note(freq, dur, bow_dir=bow_dir)
        # 2. Filter through the Rocking Bridge (Layer 2)
        bridge_audio = bridge.filter_signal(raw_string)
        
        audio_segments.append(bridge_audio)
        audio_segments.append(gap)
        bow_dir *= -1
        
    full_audio = np.concatenate(audio_segments)
    
    # Normalize peak to -1 dB
    peak = np.max(np.abs(full_audio))
    if peak > 0:
        full_audio = (full_audio / peak) * 0.85
        
    return full_audio, sample_rate

def plot_layer2_comparison(sample_rate: int):
    """
    Plots:
    1. The frequency response curve of the Bridge Hill (showing the 3 kHz peak).
    2. Side-by-side harmonic spectrum of Layer 1 (Muffled Wire) vs. Layer 2 (Projected Bridge).
    """
    bridge = RockingBridgeFilter(sample_rate=sample_rate)
    string_model = HelmholtzString(sample_rate=sample_rate)
    
    # Compute bridge filter frequency response
    w, h_hill = signal.freqz(bridge.b_hill, bridge.a_hill, worN=2048, fs=sample_rate)
    _, h_hill2 = signal.freqz(bridge.b_hill2, bridge.a_hill2, worN=2048, fs=sample_rate)
    _, h_lp = signal.freqz(bridge.b_lp, bridge.a_lp, worN=2048, fs=sample_rate)
    total_resp_db = 20 * np.log10(np.abs(h_hill * h_hill2 * h_lp) + 1e-6)
    
    # Generate 1-second audio comparison for Concert A (440 Hz)
    freq = 440.0
    l1_sample = string_model.synthesize_note(freq, 1.0)
    l2_sample = bridge.filter_signal(l1_sample)
    
    fft_l1 = np.abs(np.fft.rfft(l1_sample))
    fft_l2 = np.abs(np.fft.rfft(l2_sample))
    freqs = np.fft.rfftfreq(sample_rate, 1.0 / sample_rate)
    mask = freqs <= 8000
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 7))
    fig.patch.set_facecolor('#121212')
    
    # Top Plot: The Bridge Hill Transfer Function
    ax1.set_facecolor('#1e1e1e')
    resp_mask = w <= 8000
    ax1.plot(w[resp_mask], total_resp_db[resp_mask], color='#ffb703', linewidth=2.5, 
             label="Bridge Rocking Filter Response (Bridge Hill + High Roll-off)")
    ax1.axvspan(2500, 3500, color='#ffb703', alpha=0.15, label="Bridge Hill Zone (2.5 kHz - 3.5 kHz)")
    ax1.set_title("Layer 2: The 'Bridge Hill' Mechanical Filter Response", color='white', fontsize=12, pad=10)
    ax1.set_xlabel("Frequency (Hz)", color='#cccccc')
    ax1.set_ylabel("Gain (dB)", color='#cccccc')
    ax1.tick_params(colors='#cccccc')
    ax1.grid(True, color='#333333', linestyle='--')
    ax1.legend(facecolor='#2a2a2a', edgecolor='#555555', labelcolor='white', loc='upper right')
    ax1.set_ylim(-20, 20)
    
    # Annotate peak
    peak_idx = np.argmax(total_resp_db[resp_mask])
    peak_freq = w[resp_mask][peak_idx]
    peak_val = total_resp_db[resp_mask][peak_idx]
    ax1.annotate(f"Peak Boost: +{peak_val:.1f} dB at {peak_freq:.0f} Hz\n(Matches Ear Sensitivity)",
                 xy=(peak_freq, peak_val), xytext=(peak_freq + 600, peak_val - 4),
                 arrowprops=dict(facecolor='#00ffcc', shrink=0.08, width=1.5, headwidth=6),
                 color='#00ffcc', fontsize=9, fontweight='bold')
    
    # Bottom Plot: Spectral Comparison
    ax2.set_facecolor('#1e1e1e')
    ax2.plot(freqs[mask], 20 * np.log10(fft_l1[mask] / np.max(fft_l1) + 1e-6), 
             color='#00ffcc', linestyle='--', linewidth=1.5, label="Layer 1: Muffled Dry String (Flat Overtones)")
    ax2.plot(freqs[mask], 20 * np.log10(fft_l2[mask] / np.max(fft_l2) + 1e-6), 
             color='#ffb703', linewidth=2.0, label="Layer 2: Rocking Bridge (+14 dB Soloist Boost in 2.5-3.5 kHz)")
    ax2.set_title("Harmonic Spectrum: Layer 1 vs. Layer 2 (Notice the Soloist Boost in 2.5-3.5 kHz)", color='white', fontsize=12, pad=10)
    ax2.set_xlabel("Frequency (Hz)", color='#cccccc')
    ax2.set_ylabel("Magnitude (dB)", color='#cccccc')
    ax2.tick_params(colors='#cccccc')
    ax2.grid(True, color='#333333', linestyle='--')
    ax2.legend(facecolor='#2a2a2a', edgecolor='#555555', labelcolor='white')
    ax2.set_ylim(-65, 5)
    
    plt.tight_layout()
    os.makedirs("plots", exist_ok=True)
    plt.savefig("plots/layer2_comparison.png", dpi=200, facecolor=fig.get_facecolor())
    plt.close()

if __name__ == "__main__":
    os.makedirs("audio", exist_ok=True)
    os.makedirs("plots", exist_ok=True)
    
    print("[VIOLIN JOURNEY] Layer 2: Synthesizing Twinkle Twinkle through the Rocking Bridge...")
    audio, sr = generate_twinkle_layer2()
    
    out_path = os.path.join("audio", "layer2_rocking_bridge.wav")
    sf.write(out_path, audio, sr, subtype='PCM_24')
    print(f"[OK] Generated audio: {out_path}")
    
    print("[INFO] Generating Layer 2 Bridge Hill comparison plots...")
    plot_layer2_comparison(sr)
    print("[OK] Generated plot: plots/layer2_comparison.png")
    print("[DONE] Layer 2 complete! Listen to layer2_rocking_bridge.wav to hear the cutting soloist projection.")
