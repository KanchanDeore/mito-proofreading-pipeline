# Mitochondria Proofreading Data Preparation Pipeline
### Weilab — Boston College

This pipeline automates the preprocessing of mitochondria EM data for proofreading in Cellable.

---

## What This Pipeline Does

| Step | Description |
|------|-------------|
| Step 1 | Converts raw image (`.h5`) → `.tif` |
| Step 2 | Converts pc1 mask (`.h5`) → `.tif` |
| Step 3 | Applies pc1 masking (keeps only mitochondria overlapping pc1 region) |
| Step 4 | Processes images — **downsample** OR **crop into 4 quadrants** |
| Step 5 | Saves outputs to a folder |
| Step 6 | Uploads to Google Drive via rclone |

---

## Requirements

```bash
conda activate base
pip install tifffile h5py scikit-image numpy
```

Also requires **rclone** configured with Google Drive:
```bash
rclone config
```

---

## How To Use (3 Simple Steps!)

### Step 1 — Fill in your file paths
Open `pipeline.py` and fill in the paths at the top of the file:

```python
# Path to folder containing raw images and pc1 masks
RAW_DATA_DIR = '/your/path/to/data'

# Path to folder containing prediction files
PREDICTIONS_DIR = '/your/path/to/predictions'

# Path where you want to save the output
OUTPUT_DIR = '/your/path/to/output'

# Your Google Drive rclone remote
GDRIVE_REMOTE = 'your_remote:folder_name'
```

### Step 2 — Choose your processing mode
```python
# Choose 'downsample' or 'crop'
PROCESSING_MODE = 'downsample'

# If downsampling, set your target size (default: 1024)
DOWNSAMPLE_SIZE = 1024
```

### Step 3 — Run the pipeline!
```bash
conda activate base
python3 pipeline.py
```

---

## Processing Modes

### Downsample Mode
Resizes images to a smaller size (recommended for Cellable performance).

```python
PROCESSING_MODE = 'downsample'
DOWNSAMPLE_SIZE = 1024   # Change to 512, 1024, or 2048
```

Output files:
```
volume_name_im_1024.tif
volume_name_im_mask_1024.tif
```

### Crop Mode
Splits images into 4 quadrants for easier annotation.

```python
PROCESSING_MODE = 'crop'
```

Output files:
```
volume_name_Q1_TL_im.tif       volume_name_Q1_TL_im_mask.tif
volume_name_Q2_TR_im.tif       volume_name_Q2_TR_im_mask.tif
volume_name_Q3_BL_im.tif       volume_name_Q3_BL_im_mask.tif
volume_name_Q4_BR_im.tif       volume_name_Q4_BR_im_mask.tif
```

---

## Output Summary
After running, the pipeline prints a summary:
```
╔══════════════════════════════════════════════════════════╗
║                    PIPELINE COMPLETE                     ║
╠══════════════════════════════════════════════════════════╣
║  Completed : 25                                          ║
║  Skipped   : 0                                           ║
║  Failed    : 0                                           ║
║  Output    : /your/output/path                           ║
╚══════════════════════════════════════════════════════════╝
```

---

## File Structure on Cluster
```
/projects/weilab/dataset/mito/cerebellum/test/p0/
├── 0-256_10240-12288_11264-13312_im.h5          ← raw image
├── 0-256_10240-12288_11264-13312_mask_pc1.h5    ← pc1 mask
└── ...

/projects/weilab/liupeng/data/raw/mito/wilson19/p0/
├── 0-256_10240-12288_11264-13312_im/
│   ├── 0-256_10240-12288_11264-13312_im_xy.tif  ← prediction
│   └── ...
└── ...
```

---

## Authors
- **Kanchan Sadashiv Deore** — Weilab, Boston College
- Guided by **Peng Liu** and **Prof. Donglai Wei**
