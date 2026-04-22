#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║         MITOCHONDRIA PROOFREADING DATA PREPARATION PIPELINE                 ║
║         Weilab - Boston College                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

HOW TO USE:
    1. Fill in the FILE PATHS section below with your actual paths
    2. Run: python3 pipeline.py
    3. Follow the on-screen prompts!

REQUIREMENTS:
    conda activate base
    pip install tifffile h5py scikit-image numpy

AUTHORS:
    Kanchan Sadashiv Deore (Weilab, Boston College)
    Guided by Peng Liu and Prof. Donglai Wei
"""

# ==============================================================================
# ★ FILL IN YOUR FILE PATHS HERE — THIS IS THE ONLY THING YOU NEED TO CHANGE!
# ==============================================================================

# Path to folder containing raw images (_im.h5) and pc masks
RAW_DATA_DIR = '/projects/weilab/dataset/mito/cerebellum/test/p0'

# Path to folder containing prediction files (_im_xy.tif, _im_xz.tif, etc.)
PREDICTIONS_DIR = '/projects/weilab/liupeng/data/raw/mito/wilson19/p0'

# Path where you want to save the processed output files
OUTPUT_DIR = '/projects/weilab/dataset/mito/cerebellum/test/p0/pipeline_output'

# Your Google Drive rclone remote name and folder
# Format: 'your_remote_name:folder_name_on_drive'
GDRIVE_REMOTE = 'workdrive:p0_processed'

# ==============================================================================
# DO NOT EDIT BELOW THIS LINE
# ==============================================================================

import os
import sys
import h5py
import numpy as np
import tifffile as tiff
import subprocess
from pathlib import Path

try:
    from skimage.transform import resize
except ImportError:
    print("ERROR: scikit-image not installed. Run: pip install scikit-image")
    sys.exit(1)


def print_banner():
    print('\n╔══════════════════════════════════════════════════════════╗')
    print('║     MITOCHONDRIA PROOFREADING PIPELINE - Weilab          ║')
    print('╚══════════════════════════════════════════════════════════╝\n')


def ask_prediction_file(vol, pred_dir):
    """Ask user which prediction file to use as segmentation."""
    vol_dir = pred_dir / f'{vol}_im'
    options = {
        '1': f'{vol}_im_xy.tif',
        '2': f'{vol}_im_xz.tif',
        '3': f'{vol}_im_yz.tif',
        '4': f'{vol}_im_consensus.tif',
    }
    print('\n┌──────────────────────────────────────────────────────────┐')
    print('│  Choose the prediction file to use as segmentation       │')
    print('├──────────────────────────────────────────────────────────┤')
    for key, fname in options.items():
        exists = '✓ found' if (vol_dir / fname).exists() else '✗ not found'
        print(f'│  Press {key} → {fname[:45]:<45}({exists}) │')
    print('│  Press 0 → Skip this volume                              │')
    print('└──────────────────────────────────────────────────────────┘')
    while True:
        choice = input('  Your choice (0/1/2/3/4): ').strip()
        if choice == '0':
            return None
        if choice in options:
            path = vol_dir / options[choice]
            if path.exists():
                return path
            else:
                print(f'  WARNING: File not found. Please choose another option.')
        else:
            print('  Invalid input. Please enter 0, 1, 2, 3 or 4.')


def ask_apply_mask(vol, raw_dir):
    """Ask user whether to apply a pc mask and which one."""
    # Find all available mask files for this volume
    mask_files = sorted(raw_dir.glob(f'{vol}_mask*.h5'))
    if not mask_files:
        print(f'  No mask files found for {vol}. Skipping mask step.')
        return None

    print('\n┌──────────────────────────────────────────────────────────┐')
    print('│  Apply a PC mask to crop mitochondria instances?         │')
    print('├──────────────────────────────────────────────────────────┤')
    for i, mf in enumerate(mask_files, 1):
        print(f'│  Press {i} → {mf.name[:50]:<50}│')
    print('│  Press 0 → Skip masking                                  │')
    print('└──────────────────────────────────────────────────────────┘')
    while True:
        choice = input(f'  Your choice (0-{len(mask_files)}): ').strip()
        if choice == '0':
            return None
        if choice.isdigit() and 1 <= int(choice) <= len(mask_files):
            return mask_files[int(choice) - 1]
        print(f'  Invalid input. Please enter 0 to {len(mask_files)}.')


def ask_relabel():
    """Ask user whether to relabel instances sequentially after masking."""
    print('\n┌──────────────────────────────────────────────────────────┐')
    print('│  Relabel instances sequentially after masking?           │')
    print('│  (After masking, some label numbers get removed and      │')
    print('│   labels are no longer in sequence e.g. 1,4,7,12...      │')
    print('│   Relabeling makes them sequential: 1,2,3,4...)          │')
    print('├──────────────────────────────────────────────────────────┤')
    print('│  Press 1 → Yes, relabel sequentially (recommended)       │')
    print('│  Press 0 → No, keep original label numbers               │')
    print('└──────────────────────────────────────────────────────────┘')
    while True:
        choice = input('  Your choice (0/1): ').strip()
        if choice in ['0', '1']:
            return choice == '1'
        print('  Invalid input. Please enter 0 or 1.')


def ask_processing_mode():
    print('\n┌──────────────────────────────────────────────────────────┐')
    print('│  Choose your image processing mode                       │')
    print('├──────────────────────────────────────────────────────────┤')
    print('│  Press 1 → Downsample images (resize to smaller size)    │')
    print('│  Press 2 → Split images into 4 quadrants                 │')
    print('│  Press 0 → Skip (masking/relabeling only)                │')
    print('└──────────────────────────────────────────────────────────┘')
    while True:
        choice = input('  Your choice (0/1/2): ').strip()
        if choice in ['0', '1', '2']:
            return choice
        print('  Invalid input. Please enter 0, 1 or 2.')


def ask_downsample_size():
    print('\n┌──────────────────────────────────────────────────────────┐')
    print('│  Choose your downsample size                             │')
    print('├──────────────────────────────────────────────────────────┤')
    print('│  Press 1 → 512  x 512  (smallest, fastest)               │')
    print('│  Press 2 → 1024 x 1024 (recommended for Cellable)        │')
    print('│  Press 3 → 2048 x 2048 (larger, slower)                  │')
    print('│  Press 4 → Custom size (enter your own)                  │')
    print('└──────────────────────────────────────────────────────────┘')
    while True:
        choice = input('  Your choice (1/2/3/4): ').strip()
        if choice == '1':
            return 512
        elif choice == '2':
            return 1024
        elif choice == '3':
            return 2048
        elif choice == '4':
            size = input('  Enter custom size (e.g. 768): ').strip()
            if size.isdigit() and int(size) > 0:
                return int(size)
            print('  Invalid size. Please enter a positive number.')
        else:
            print('  Invalid input. Please enter 1, 2, 3 or 4.')


def ask_upload_to_gdrive():
    print('\n┌──────────────────────────────────────────────────────────┐')
    print('│  Upload to Google Drive?                                 │')
    print('├──────────────────────────────────────────────────────────┤')
    print('│  Press 1 → Yes, upload to Google Drive                   │')
    print('│  Press 0 → No, skip upload                               │')
    print('└──────────────────────────────────────────────────────────┘')
    while True:
        choice = input('  Your choice (0/1): ').strip()
        if choice in ['0', '1']:
            return choice == '1'
        print('  Invalid input. Please enter 0 or 1.')


def confirm_settings(mode, size, upload):
    mode_str = {
        '0': 'No resize (masking/relabeling only)',
        '1': f'Downsample to {size}x{size}',
        '2': 'Crop into 4 quadrants'
    }
    print('\n┌──────────────────────────────────────────────────────────┐')
    print('│  CONFIRM YOUR SETTINGS                                   │')
    print('├──────────────────────────────────────────────────────────┤')
    print(f'│  Processing mode : {mode_str[mode]:<38}│')
    print(f'│  Input directory : {RAW_DATA_DIR[:38]:<38}│')
    print(f'│  Output directory: {OUTPUT_DIR[:38]:<38}│')
    print(f'│  Upload to Drive : {"Yes" if upload else "No":<38}│')
    print('└──────────────────────────────────────────────────────────┘')
    while True:
        choice = input('\n  Press 1 to confirm and start, 0 to cancel: ').strip()
        if choice == '1':
            return True
        elif choice == '0':
            return False
        print('  Invalid input. Please enter 0 or 1.')


def convert_h5_to_array(h5_path):
    with h5py.File(h5_path, 'r') as f:
        return f['main'][:]


def apply_pc_mask(inst, mask, background_label=0, mask_threshold=0.0, min_overlap=1):
    region = mask > mask_threshold
    labels_in_region = inst[region]
    labels, counts = np.unique(labels_in_region, return_counts=True)
    keep = labels[(labels != background_label) & (counts >= min_overlap)]
    out = inst.copy()
    if keep.size == 0:
        out[...] = background_label
    else:
        keep_set = set(map(int, keep.tolist()))
        out[~np.isin(out, list(keep_set))] = background_label
    return out, len(keep)


def relabel_sequential(inst, background_label=0):
    """Relabel instances sequentially starting from 1."""
    out = np.zeros_like(inst)
    unique_labels = np.unique(inst)
    unique_labels = unique_labels[unique_labels != background_label]
    for new_id, old_id in enumerate(unique_labels, start=1):
        out[inst == old_id] = new_id
    print(f'  Relabeled {len(unique_labels)} instances sequentially (1 to {len(unique_labels)})')
    return out


def downsample_volume(volume, target_size, is_mask=False):
    return resize(
        volume,
        (volume.shape[0], target_size, target_size),
        order=0 if is_mask else 1,
        preserve_range=True,
        anti_aliasing=False if is_mask else True
    ).astype(volume.dtype)


def crop_into_quadrants(volume, vol_name, output_dir, suffix):
    _, h, w = volume.shape
    mh, mw = h // 2, w // 2
    quadrants = {
        'Q1_TL': volume[:, :mh, :mw],
        'Q2_TR': volume[:, :mh, mw:],
        'Q3_BL': volume[:, mh:, :mw],
        'Q4_BR': volume[:, mh:, mw:],
    }
    for qname, qdata in quadrants.items():
        out_path = output_dir / f'{vol_name}_{qname}{suffix}.tif'
        tiff.imwrite(str(out_path), qdata)
        print(f'  Saved: {out_path.name}')


def upload_to_gdrive(output_dir, gdrive_remote):
    print(f'\nUploading to Google Drive: {gdrive_remote}')
    result = subprocess.run(
        ['rclone', 'copy', str(output_dir), gdrive_remote, '--progress'],
        capture_output=False
    )
    if result.returncode == 0:
        print('Upload complete!')
    else:
        print('Upload failed! Please run manually:')
        print(f'rclone copy {output_dir} {gdrive_remote} --progress')


def main():
    print_banner()

    # Global settings asked once
    print('=== GLOBAL SETTINGS (applied to all volumes) ===\n')
    mode   = ask_processing_mode()
    size   = ask_downsample_size() if mode == '1' else None
    upload = ask_upload_to_gdrive()

    if not confirm_settings(mode, size, upload):
        print('\nCancelled. Exiting.')
        sys.exit(0)

    raw_dir  = Path(RAW_DATA_DIR)
    pred_dir = Path(PREDICTIONS_DIR)
    out_dir  = Path(OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    pc1_files = sorted(raw_dir.glob('*_mask*.h5'))
    # Get unique volume names
    volumes = []
    seen = set()
    for f in sorted(raw_dir.glob('*_im.h5')):
        vol = f.name.replace('_im.h5', '')
        if vol not in seen:
            volumes.append(vol)
            seen.add(vol)

    print(f'\nFound {len(volumes)} volumes to process.\n')

    completed = skipped = failed = 0

    for i, vol in enumerate(volumes, 1):
        print(f'\n{"="*60}')
        print(f'[{i}/{len(volumes)}] Volume: {vol}')
        print(f'{"="*60}')

        im_h5 = raw_dir / f'{vol}_im.h5'
        if not im_h5.exists():
            print(f'  WARNING: Raw image not found, skipping.')
            failed += 1
            continue

        # Ask per-volume settings
        pred_path = ask_prediction_file(vol, pred_dir)
        if pred_path is None:
            print(f'  Skipping volume.\n')
            skipped += 1
            continue

        mask_path = ask_apply_mask(vol, raw_dir)
        do_relabel = ask_relabel() if mask_path else False

        try:
            # Load raw image
            print(f'\n  Loading raw image...')
            raw = convert_h5_to_array(im_h5)
            print(f'  Raw image shape: {raw.shape}')

            # Load prediction
            print(f'  Loading prediction: {pred_path.name}')
            inst = tiff.imread(str(pred_path))
            print(f'  Prediction shape: {inst.shape}')

            # Apply mask if chosen
            if mask_path:
                print(f'  Applying mask: {mask_path.name}')
                mask = convert_h5_to_array(mask_path)
                if inst.shape != mask.shape:
                    print(f'  WARNING: Shape mismatch inst={inst.shape} mask={mask.shape}, skipping mask.')
                else:
                    inst, n_kept = apply_pc_mask(inst, mask)
                    print(f'  Kept {n_kept} mitochondria instances after masking.')

            # Relabel if chosen
            if do_relabel:
                print(f'  Relabeling instances sequentially...')
                inst = relabel_sequential(inst)

            # Process images
            if mode == '0':
                tiff.imwrite(str(out_dir / f'{vol}_im.tif'),      raw)
                tiff.imwrite(str(out_dir / f'{vol}_im_mask.tif'), inst)
                print(f'  Saved: {vol}_im.tif')
                print(f'  Saved: {vol}_im_mask.tif')

            elif mode == '1':
                print(f'  Downsampling to {size}x{size}...')
                raw_ds  = downsample_volume(raw,  size, is_mask=False)
                inst_ds = downsample_volume(inst, size, is_mask=True)
                tiff.imwrite(str(out_dir / f'{vol}_im_{size}.tif'),      raw_ds)
                tiff.imwrite(str(out_dir / f'{vol}_im_mask_{size}.tif'), inst_ds)
                print(f'  Saved: {vol}_im_{size}.tif')
                print(f'  Saved: {vol}_im_mask_{size}.tif')

            elif mode == '2':
                print(f'  Cropping into 4 quadrants...')
                crop_into_quadrants(raw,  vol, out_dir, '_im')
                crop_into_quadrants(inst, vol, out_dir, '_im_mask')

            completed += 1
            print(f'\n  Volume complete!')

        except Exception as e:
            print(f'  ERROR: {e}')
            failed += 1

    # Summary
    print('\n╔══════════════════════════════════════════════════════════╗')
    print('║                    PIPELINE COMPLETE                     ║')
    print('╠══════════════════════════════════════════════════════════╣')
    print(f'║  Completed : {completed:<44}║')
    print(f'║  Skipped   : {skipped:<44}║')
    print(f'║  Failed    : {failed:<44}║')
    print(f'║  Output    : {str(out_dir)[:44]:<44}║')
    print('╚══════════════════════════════════════════════════════════╝')

    if upload:
        upload_to_gdrive(out_dir, GDRIVE_REMOTE)


if __name__ == '__main__':
    main()
