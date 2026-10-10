# 🎻 Violin Journey: Building an Acoustic Violin in Python from First Principles

Welcome to the **Violin Journey** repository! 

This project documents an incremental, layer-by-layer exploration of acoustic physics and digital signal processing (DSP). The goal: recreate the rich, expressive sound of a master acoustic violin entirely from mathematical first principles—no pre-recorded samples, no heavy neural networks.

---

## 🎯 How This Repository Works

We build the violin **one acoustic layer at a time**:
1. Each layer starts with code that isolates a specific physical phenomenon.
2. Each layer outputs an **audio result** (`.wav`) demonstrating exactly what changed.
3. Every layer benchmarks against the universal standard melody: **"Twinkle, Twinkle, Little Star"** (Suzuki Violin School, Lesson 1).

For the full architectural plan, see [**`LAYERS_ROADMAP.md`**](LAYERS_ROADMAP.md).

---

## 🚀 Milestones

### 📍 Layer 0: The Naive Baseline
* **Code**: [`src/layer0_baseline.py`](src/layer0_baseline.py)
* **Audio Result**: [`audio/layer0_naive_sawtooth.wav`](audio/layer0_naive_sawtooth.wav)
* **Plot**: [`plots/layer0_waveform.png`](plots/layer0_waveform.png)
* **Command**: `python src/layer0_baseline.py`

### 📍 Layer 1: Bow & Rosin Physics (Current Milestone)
* **Code**: [`src/layer1_bow_physics.py`](src/layer1_bow_physics.py)
* **Audio Result**: [`audio/layer1_helmholtz_string.wav`](audio/layer1_helmholtz_string.wav)
* **Plot**: [`plots/layer1_comparison.png`](plots/layer1_comparison.png)
* **Command**: `python src/layer1_bow_physics.py`

Layer 1 implements finite bow-ribbon sinc filtering, string stiffness corner rounding, and attack "chiff" rosin friction noise, taming the harsh 8-bit buzzer into an organic vibrating string!
