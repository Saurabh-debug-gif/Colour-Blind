# 👁️ VisionIQ — Eye Health Suite

A clinical-grade vision screening web app built with Streamlit. VisionIQ offers two tools: an **Ishihara color blindness test** and a **binary-search Snellen visual acuity test** — all in your browser, no equipment needed.

---

## ✨ Features

### 🎨 Color Blindness Test
- Simulated Ishihara plates to detect red-green color deficiencies
- Detects **Protanopia** (red-blind) and **Deuteranopia** (green-blind)
- Upload any image to see it **daltonized** (color-corrected) for your specific deficiency

### 👁️ Visual Acuity Test (Binary Search Engine)
- Implements a **binary search algorithm** on the Snellen chart — finds your threshold in just 4–6 rows instead of reading all 12
- Screen **PPI calibration** using your screen size and resolution for physically accurate letter sizing
- Estimates your **diopter prescription** based on your result
- Full **Snellen reference chart** with your result highlighted
- Best-of-2 attempts per row for fair scoring

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/visioniq.git
cd visioniq/colorblind

# Install dependencies
pip install -r requirements.txt
```

### Running the App

```bash
streamlit run app.py
```

Then open your browser at `http://localhost:8501`

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| `streamlit` | Web app framework |
| `Pillow` | Image processing |
| `numpy` | Color matrix transformations |
| `matplotlib` | Plate image generation |

Install all at once:
```bash
pip install streamlit numpy pillow matplotlib
```

---

## 🗂️ Project Structure

```
colorblind/
├── app.py                  # Main Streamlit app & UI
├── plate_generator.py      # Generates Ishihara-style test plates
├── test_logic.py           # Color blindness detection logic
├── correction.py           # Daltonize image correction algorithm
├── acuity_generator.py     # Renders Snellen letter images at correct physical size
├── acuity_logic.py         # Binary search acuity engine + Snellen chart data
├── style.css               # Custom dark-theme UI styles
├── plates/                 # Pre-generated plate images
│   ├── normal.png
│   ├── protanopia.png
│   └── deuteranopia.png
└── requirements.txt
```

---

## 🔬 How the Binary Search Acuity Test Works

Standard Snellen tests read every line top-to-bottom. VisionIQ uses a **binary search** instead:

1. Start at the middle of the chart (20/40)
2. If you **pass** → jump up toward better vision
3. If you **fail** → jump down toward worse vision
4. Range narrows each round until only one line remains — that's your threshold

This finds your exact acuity in **4–6 rows** rather than 12, reducing eye fatigue and time.

> Based on methodology from Carkeet A. (2001) *"Modeling logMAR visual acuity scores"* and similar ETDRS staircase protocols.

---

## ⚠️ Disclaimer

VisionIQ is a **screening tool only** — not a substitute for a clinical eye exam. Real prescriptions require a phoropter exam by a licensed optometrist who also tests for astigmatism, presbyopia, and binocular balance. **See an eye care professional before purchasing glasses.**

---

## 🛠️ Built With

- [Streamlit](https://streamlit.io/) — Python web app framework
- [Pillow](https://pillow.readthedocs.io/) — Image processing
- [NumPy](https://numpy.org/) — Numerical computing

---

*Built with ♥ · VisionIQ*
