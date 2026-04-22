# Mitochondria Proofreading Pipeline

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-active-brightgreen.svg)

An automated pipeline for preprocessing mitochondria EM data for proofreading in Cellable.

---

## Quick Start

```bash
conda activate base
pip install -r requirements.txt
python3 pipeline.py
```

---

## What This Pipeline Does

| Step | Description |
|------|-------------|
| Step 1 | Loads raw image (`.h5`) |
| Step 2 | Loads pc mask (`.h5`) |
| Step 3 | Choose prediction file: `_xy`, `_xz`, `_yz`, or `_consensus` |
| Step 4 | Apply pc mask (optional) — keeps only mitochondria overlapping the mask region |
| Step 5 | Relabel instances sequentially (optional) |
| Step 6 | Process images — downsample OR crop into 4 quadrants |
| Step 7 | Save outputs to a folder |
| Step 8 | Upload to Google Drive (optional) |

---

## Requirements

```bash
conda activate base
pip install -r requirements.txt
```

Or install manually:
```bash
pip install tifffile h5py scikit-image numpy
```

Also requires **rclone** configured with Google Drive (only if uploading):
```bash
rclone config
```

---

## How To Use

### Step 1 — Fill in your file paths
Open `pipeline.py` and fill in only these 4 paths at the top:

```python
# Path to folder containing raw images and pc masks
RAW_DATA_DIR = '/your/path/to/raw/data'

# Path to folder containing prediction files
PREDICTIONS_DIR = '/your/path/to/predictions'

# Path where you want to save the output
OUTPUT_DIR = '/your/path/to/output'

# Your Google Drive rclone remote
GDRIVE_REMOTE = 'your_remote:folder_name'
```

### Step 2 — Run the pipeline
```bash
python3 pipeline.py
```

### Step 3 — Follow the prompts
The pipeline will guide you through every option interactively.

---

## Interactive Options

When you run the pipeline, it will ask you for each volume:

**Choose prediction file:**
```
Press 1 → _im_xy.tif        (xy plane prediction)
Press 2 → _im_xz.tif        (xz plane prediction)
Press 3 → _im_yz.tif        (yz plane prediction)
Press 4 → _im_consensus.tif (consensus prediction)
Press 0 → Skip this volume
```

**Apply pc mask:**
```
Lists all available mask files (pc1, pc2, etc.)
Press the number to select a mask
Press 0 → Skip masking
```

**Relabel instances:**
```
Press 1 → Yes (recommended — makes labels sequential: 1,2,3,4...)
Press 0 → No  (keeps original label numbers)
```

**Processing mode:**
```
Press 1 → Downsample (resize to smaller size)
Press 2 → Crop into 4 quadrants (Q1_TL, Q2_TR, Q3_BL, Q4_BR)
Press 0 → Skip (masking/relabeling only)
```

**Downsample size:**
```
Press 1 → 512  x 512  (smallest, fastest)
Press 2 → 1024 x 1024 (recommended for Cellable)
Press 3 → 2048 x 2048 (larger, slower)
Press 4 → Custom size
```

**Upload to Google Drive:**
```
Press 1 → Yes
Press 0 → No
```

---

## Expected File Structure

```
RAW_DATA_DIR/
├── volume_name_im.h5              # raw image
├── volume_name_mask_pc1.h5        # pc1 mask
├── volume_name_mask_pc2.h5        # pc2 mask (if available)
└── ...

PREDICTIONS_DIR/
├── volume_name_im/
│   ├── volume_name_im_xy.tif      # xy prediction
│   ├── volume_name_im_xz.tif      # xz prediction
│   ├── volume_name_im_yz.tif      # yz prediction
│   └── volume_name_im_consensus.tif
└── ...
```

---

## Output Files

**Downsample mode:**
```
volume_name_im_1024.tif
volume_name_im_mask_1024.tif
```

**Crop mode:**
```
volume_name_Q1_TL_im.tif        volume_name_Q1_TL_im_mask.tif
volume_name_Q2_TR_im.tif        volume_name_Q2_TR_im_mask.tif
volume_name_Q3_BL_im.tif        volume_name_Q3_BL_im_mask.tif
volume_name_Q4_BR_im.tif        volume_name_Q4_BR_im_mask.tif
```

---

## Troubleshooting

| Error | Solution |
|-------|----------|
| `ModuleNotFoundError: tifffile` | Run `conda activate base` first |
| `ModuleNotFoundError: skimage` | Run `pip install scikit-image` |
| `rclone: command not found` | Install rclone: `conda install rclone` |
| `Shape mismatch` | Prediction and mask files have different dimensions |
| `No mask files found` | Check that mask files follow the `*_mask*.h5` naming pattern |

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| v1.0 | Apr 2026 | Initial release |
| v1.1 | Apr 2026 | Added interactive prompts, relabeling, multiple mask support |
| v1.2 | Apr 2026 | Added prediction file selection, crop mode |

---

## Contact

If you run into any issues, feel free to open a GitHub issue.

---

## License

MIT License — feel free to use and modify.
