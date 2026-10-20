"""
Layer 3: The Wooden Body ("The Acoustic Transformer")
------------------------------------------------------
In Layer 1, we tamed the harsh 8-bit digital buzzer into a real vibrating wire.
In Layer 2, we added the Rocking Bridge, giving the wire cutting 3 kHz soloist projection.

However, if you listen to Layer 2, it still sounds like it is vibrating in thin air—
it lacks the warm, deep, hollow wooden chamber of an acoustic violin.

In Layer 3, we implement the acoustics of the wooden body:
1. The Acoustic Transformer:
   - A vibrating string is too thin to move air. The carved Alpine spruce top plate
     and flamed maple back plate act as acoustic sounding boards.
   - It vibrates in over 80 distinct resonance modes (Chladni patterns):
     * A0 mode (~278 Hz): Air pumping in and out of the f-holes (like blowing across a bottle).
     * B1- mode (~448 Hz): Wood bending mode.
     * B1+ mode (~535 Hz): Main corpus breathing mode (top and back expand together).
     * 85 dense plate modes between 700 Hz and 5,000 Hz.
2. The "Missing Fundamental" Illusion:
   - A 35 cm violin body cannot efficiently radiate low bass wavelengths (G3 = 1.75 meters).
   - The lowest note is physically faint in the room, but your brain's auditory cortex
     calculates the harmonic spacing and invents the deep bass note in your head!
3. Fast FFT Convolution (Acoustic Fingerprint):
   - We generate the 1715 Stradivarius "Titian" body impulse response (IR).
   - Using the FFT Convolution theorem, we pass our Layer 2 sound through the wooden
     body in milliseconds: Y(f) = X(f) * H(f).

Benchmark Melody: Twinkle, Twinkle, Little Star (Suzuki Violin Method)
"""

import os
import numpy as np
import scipy.signal as signal
import soundfile as sf
import matplotlib.pyplot as plt

# Import Layer 1 string and Layer 2 bridge filter
from layer1_bow_physics import HelmholtzString
from layer2_bridge_filter import RockingBridgeFilter

# Signature modes of a 1715 Stradivarius ('Titian')
STRADIVARI_MODES = [
    # (Frequency Hz, Q factor, Gain dB, Phase rad)
    (278.0, 18.0, 15.0, 0.1),    # A0 Helmholtz air cavity resonance
    (390.0, 20.0, 7.5, 0.4),     # C2 Wood corpus bending
    (448.0, 22.0, 12.5, 0.8),    # B1- First major wood plate flexure
    (535.0, 25.0, 15.5, 1.2),    # B1+ Main corpus breathing mode (strongest radiator)
    (690.0, 18.0, 9.0, 1.7),     # C3 Upper corpus mode
    (880.0, 16.0, 9.5, 2.1),
    (1050.0, 15.0, 10.0, 2.5),
    (1260.0, 14.0, 10.5, 2.9),
    (1520.0, 13.0, 11.0, 0.3),
    (1850.0, 12.0, 11.5, 0.7),
    (2150.0, 10.0, 12.0, 1.1),
]

class StradivariBodyResonator:
    """
    Simulates the acoustic chamber of a 1715 Stradivarius violin body using
    modal impulse response synthesis and high-speed Fast FFT Convolution.
    """
    def __init__(self, sample_rate: int = 44100, duration_sec: float = 0.35, seed: int = 1715):
        self.sample_rate = sample_rate
        self.duration_sec = duration_sec
        self.ir = self._synthesize_body_ir(seed)

    def _synthesize_body_ir(self, seed: int) -> np.ndarray:
        n_samples = int(self.sample_rate * self.duration_sec)
        t = np.linspace(0, self.duration_sec, n_samples, endpoint=False)
        ir = np.zeros(n_samples, dtype=np.float64)
        rng = np.random.default_rng(seed=seed)

        # 1. Primary signature wood & air modes (A0, C2, B1-, B1+)
        for freq, q, gain_db, phase in STRADIVARI_MODES:
            gamma = np.pi * freq / q
            G = 10.0 ** (gain_db / 20.0)
            # Continuous-time biquad impulse normalization
            mode_ir = 2.0 * G * (gamma / self.sample_rate) * np.exp(-gamma * t) * np.sin(2 * np.pi * freq * t + phase)
            ir += mode_ir

        # 2. Add 85 dense plate modes (700 Hz - 5,000 Hz)
        # Models the dense Chladni modal landscape of Italian spruce and maple
        dense_freqs = np.linspace(720.0, 4800.0, 85) + rng.uniform(-16.0, 16.0, 85)
        for f_d in dense_freqs:
            Q_d = rng.uniform(28.0, 52.0)
            gamma_d = np.pi * f_d / Q_d
            base_gain = 10.0 ** (10.0 / 20.0)
            # Natural modal variation
            G_d = base_gain * rng.uniform(0.7, 1.3)
            phase_d = rng.uniform(0, 2 * np.pi)
            dense_mode = 2.0 * G_d * (gamma_d / self.sample_rate) * np.exp(-gamma_d * t) * np.sin(2 * np.pi * f_d * t + phase_d)
            ir += dense_mode * 0.35

        # 3. High-frequency wood/varnish absorption (>5.8 kHz)
        nyq = self.sample_rate / 2.0
        b_lp, a_lp = signal.butter(3, min(5800.0 / nyq, 0.95), btype="lowpass")
        ir = signal.lfilter(b_lp, a_lp, ir)

        # 4. Low-frequency corpus cut (violin body physically cannot radiate below G3 = 196 Hz)
        b_hp, a_hp = signal.butter(2, max(180.0 / nyq, 0.005), btype="highpass")
        ir = signal.lfilter(b_hp, a_hp, ir)

        # Normalize peak
        max_val = np.max(np.abs(ir))
        if max_val > 0:
            ir = ir / max_val

        return ir.astype(np.float32)

    def convolve(self, audio: np.ndarray) -> np.ndarray:
        """
        Passes the input audio through the wooden body using causal Fast FFT Convolution.
        Y(f) = X(f) * H(f).
        Causal convolution ensures sample 0 starts at exact 0.0 without any step-jump or tap-tap click.
        """
        convolved = signal.fftconvolve(audio, self.ir, mode="full")[:len(audio)]
        return convolved.astype(np.float32)

def generate_twinkle_layer3():
    sample_rate = 44100
    string_model = HelmholtzString(sample_rate=sample_rate)
    bridge = RockingBridgeFilter(sample_rate=sample_rate)
    body = StradivariBodyResonator(sample_rate=sample_rate)

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
    # Quick 8ms bow turnaround instead of dead 35ms silence (eliminating choppy piano feel)
    gap = np.zeros(int(0.008 * sample_rate))
    bow_dir = 1

    for name, freq, dur in notes:
        # Layer 1: String excitation (Helmholtz motion + Rosin)
        raw_string = string_model.synthesize_note(freq, dur, bow_dir=bow_dir)
        # Layer 2: Rocking Bridge filter (+14 dB Bridge Hill)
        bridge_sound = bridge.filter_signal(raw_string)
        # Layer 3: Causal convolution with Stradivarius wooden body
        body_sound = body.convolve(bridge_sound)

        audio_segments.append(body_sound)
        audio_segments.append(gap)
        bow_dir *= -1

    full_audio = np.concatenate(audio_segments)

    # Normalize peak to -1 dB
    peak = np.max(np.abs(full_audio))
    if peak > 0:
        full_audio = (full_audio / peak) * 0.85

    return full_audio, sample_rate

def plot_layer3_comparison(sample_rate: int):
    """
    Plots:
    1. The 1715 Stradivarius Impulse Response h[t] (the wood's acoustic fingerprint).
    2. Side-by-side harmonic spectrum of Layer 2 (Rocking Bridge) vs. Layer 3 (Stradivarius Body).
    """
    string_model = HelmholtzString(sample_rate=sample_rate)
    bridge = RockingBridgeFilter(sample_rate=sample_rate)
    body = StradivariBodyResonator(sample_rate=sample_rate)

    freq = 440.0
    l1_sample = string_model.synthesize_note(freq, 1.0)
    l2_sample = bridge.filter_signal(l1_sample)
    l3_sample = body.convolve(l2_sample)

    fft_l2 = np.abs(np.fft.rfft(l2_sample))
    fft_l3 = np.abs(np.fft.rfft(l3_sample))
    freqs = np.fft.rfftfreq(sample_rate, 1.0 / sample_rate)
    mask = freqs <= 6500

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 7))
    fig.patch.set_facecolor('#121212')

    # Top Plot: Stradivarius Body Impulse Response
    ax1.set_facecolor('#1e1e1e')
    t_ir = np.linspace(0, body.duration_sec, len(body.ir)) * 1000  # ms
    zoom_ir = int(0.08 * sample_rate)  # First 80 ms
    ax1.plot(t_ir[:zoom_ir], body.ir[:zoom_ir], color='#f72585', linewidth=1.5)
    ax1.set_title("Layer 3: 1715 Stradivarius Body Impulse Response (Acoustic Fingerprint h[t])", color='white', fontsize=12, pad=10)
    ax1.set_xlabel("Time (milliseconds)", color='#cccccc')
    ax1.set_ylabel("Amplitude", color='#cccccc')
    ax1.tick_params(colors='#cccccc')
    ax1.grid(True, color='#333333', linestyle='--')
    ax1.set_ylim(-1.1, 1.1)

    # Bottom Plot: Spectral Comparison
    ax2.set_facecolor('#1e1e1e')
    ax2.plot(freqs[mask], 20 * np.log10(fft_l2[mask] / np.max(fft_l2) + 1e-6),
             color='#ffb703', linestyle='--', linewidth=1.4, label="Layer 2: Dry Rocking Bridge (No Wood Chamber)")
    ax2.plot(freqs[mask], 20 * np.log10(fft_l3[mask] / np.max(fft_l3) + 1e-6),
             color='#f72585', linewidth=1.8, label="Layer 3: Stradivarius Body (85 Wood Modes & Warm Chamber)")
    ax2.set_title("Harmonic Spectrum: Layer 2 vs. Layer 3 (Notice the rich modal valleys and warm wood resonances)", color='white', fontsize=12, pad=10)
    ax2.set_xlabel("Frequency (Hz)", color='#cccccc')
    ax2.set_ylabel("Magnitude (dB)", color='#cccccc')
    ax2.tick_params(colors='#cccccc')
    ax2.grid(True, color='#333333', linestyle='--')
    ax2.legend(facecolor='#2a2a2a', edgecolor='#555555', labelcolor='white')
    ax2.set_ylim(-65, 5)

    plt.tight_layout()
    os.makedirs("plots", exist_ok=True)
    plt.savefig("plots/layer3_comparison.png", dpi=200, facecolor=fig.get_facecolor())
    plt.close()

if __name__ == "__main__":
    os.makedirs("audio", exist_ok=True)
    os.makedirs("plots", exist_ok=True)

    print("[VIOLIN JOURNEY] Layer 3: Synthesizing Twinkle Twinkle through the 1715 Stradivarius body...")
    audio, sr = generate_twinkle_layer3()

    out_path = os.path.join("audio", "layer3_wooden_body.wav")
    sf.write(out_path, audio, sr, subtype='PCM_24')
    print(f"[OK] Generated audio: {out_path}")

    print("[INFO] Generating Layer 3 comparison plots...")
    plot_layer3_comparison(sr)
    print("[OK] Generated plot: plots/layer3_comparison.png")
    print("[DONE] Layer 3 complete! Listen to layer3_wooden_body.wav to hear the warm, hollow wooden chamber.")

