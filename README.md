# 📼 VHS Photo Recovery <!-- omit in toc -->

This tool attempts to recover individual photographs from videos of slideshows, with particular focus on digitised VHS recordings.

This tool:

- identifies sections of video that are likely to represent a single image
- samples several frames from each picture
- optionally aligns frames, and combines them with a temporal median to reduce moving VHS
interference
- outputs restored images
- outputs artifacts to help you check that the video was processed correctly

🚧 WIP: post-extraction image processing:. An additional command to:
- remove camera display overlays
- sharpen recovered images
- store the resulting images to a separate directory, without modifying the original extracted images.

## ⚠️ Important privacy notice <!-- omit in toc -->

This repository's `.gitignore` ignores several common video formats, and all directories containing files (including images) that it generates by default, to reduce the chance of publishing private photographs.

However not all video format are ignored, and directories/files that you create may not be ignored.

If you are running this repo as a developer, **always
review your staged changes before pushing to check that you aren't accidentally uploading your private media**.

## Table of contents <!-- omit in toc -->

- [Compatible video formats](#compatible-video-formats)
- [Installation](#installation)
  - [1. Download the project from GitHub](#1-download-the-project-from-github)
  - [2. Install uv](#2-install-uv)
  - [3. Install Python](#3-install-python)
  - [4. Install dependencies](#4-install-dependencies)
- [Running the extractor](#running-the-extractor)
- [Reviewing extracted images](#reviewing-extracted-images)
- [Tuning extraction](#tuning-extraction)
- [Manuallay adjusting boundaries](#manuallay-adjusting-boundaries)
  - [1. Manually set boundaries](#1-manually-set-boundaries)
  - [2. Boundary tuning](#2-boundary-tuning)
- [How extraction works](#how-extraction-works)
- [Known limitations](#known-limitations)
- [WIP: Post-extraction image enhancement](#wip-post-extraction-image-enhancement)
- [Linting and formatting](#linting-and-formatting)
- [Licence](#licence)


## Compatible video formats

This tool has only been tested with `.mp4` files.  
Based on the file types supported by the dependencies of this tool, I suspect it will work with several other file types, but this should be tested:  
`.avi`, `.mkv`, `.mov`, `.m4v`, `.mpeg`/`.mpg`.  
Success may depend on the encoding of the video file.

## Installation

### 1. Download the project from GitHub

### 2. Install uv

UV is the the Python project/package manager used by this tool.
[Install it using the official documentation](https://docs.astral.sh/uv/getting-started/installation/).

Check installation with `uv --version`. If `uv` isn't recognised, start a new terminal and retry the command there.

### 3. Install Python

From project root run:

```bash
uv python install 3.13
```

### 4. Install dependencies

From project root run:

```bash
uv sync
```

This will:

- create `.venv`
- install dependencies from `pyproject.toml`
- create/update `uv.lock`

## Running the extractor

Run the following command in terminal from this project's root directory:

```bash
uv run vhs-recover "<path to your video file>"
```

eg. `uv run vhs-recover "user/jake/movies/slidesow.mp4"`

**🪄 Tip:** You can quickly add the file path to the terminal command by dragging the file into the terminal.

The terminal will show the extractor's progress.

## Reviewing extracted images

Extracted images and other artifacts are stored in `output/<video-name>-<timestamp>`.

Several artifacts are generated:

```text
output/<video file name & timestamp>/
├── restorations/       # lossless reconstructed images
├── jpgs/               # .jpg copies of reconstructed images
├── scenes.csv          # boundary times used to generate images
├── contact-sheet.jpg   # contact sheet of recovered images
└── comparison-frames/  # a single frame of each processed scene
```

You can check extraction quality in the following ways:

- See `restorations/` for extracted images
- Compare `restorations/` to `comparison-frames/` to see if restoration has improved image quality
- Look at `contact-sheet.jpg` to quickly scan for missed photos, low quality restorations, transition frames etc


## Tuning extraction

The following arguments can be used to tune extraction.

```bash
## View all available arguments
uv run vhs-recover --help

# Boundary detection threshold.
# Lower value = find more scene boundaries. May add false positives.
# Higher value = find fewer boundaries. May miss more images.
uv run vhs-recover slideshow.mp4 --threshold 20

# Trim a length of video form the start and end of the boundary.
# Lower value = less transition frames in restored image. May be less effective at reducing distortion.
uv run vhs-recover slideshow.mp4 --trim 0.8

# Sample more frames within the boundary
uv run vhs-recover slideshow.mp4 --frames 31

# Choose a custom output directory
uv run vhs-recover slideshow.mp4 --output output/my-test

# Turn off small-shift alignment. SSA corrects the slight movement between video frames to create a sharper restoration.
uv run vhs-recover slideshow.mp4 --no-align
```

## Manuallay adjusting boundaries

A boundary is the start and end time of a scene (a section of video that's converted into a image). `scenes.csv` is a table of the boundaries that were used to generate each image.

This tool automatically estimates boundaries. They can be inaccurate, especially for low quality videos and those with transition effects.

Boundaries can be adjusted in several ways to try and extract a better quality image.

### 1. Manually set boundaries

Either use the `scenes.csv` file from a previous run of the video file, or generate a new one with:

```bash
uv run vhs-recover "/path/to/slideshow.mp4" --detect-only
```

Open `scenes.csv` in a spreadsheet or text editor.

Adjust the times so that they accurately frame the images in the video.

Then run the recovery command, passing in the new `scenes.csv` file:

```bash
uv run vhs-recover "<path to video>" --scenes "<path to scenes.csv>"
```

### 2. Boundary tuning

Adjust the `threshold` and `trim` parameters to adjust automatically generated scene boundaries. See the **Command arguments** section above for instructions.

## How extraction works

`pipeline.py` invokes each of the following processes in order:

1. `scenes.py`: PySceneDetect identifies scenes and records
   scene boundaries in `scenes.csv`.
2. `frames.py`: OpenCV samples frames within scene boundaries.
3. `alignment.py`: OpenCV ECC estimates small translations between frames.
4. `restoration.py`: NumPy calculates a pixel-wise median of aligned frames.
5. `export.py`: OpenCV writes PNG + JPG images and a thumbnail contact sheet.

`cli.py` handles command line arguments that invoke the pipeline.

## Known limitations

- Transitions (especially fades and dissolves) may be treated as photographs.
- Very dark scenes may be exported as black pictures.
- Large vertical picture rolls, tracking faults and individually misaligned
  scan lines are not corrected.

## WIP: Post-extraction image enhancement
An initial version of an image enhancement process has been created.
Currently this performs two operations:
- Using inpaint, and image & mask parameters provided by the user, remove camera overlays (such as the photo number) from pre-defined regions of the image.
- Apply a gentle unsharp mask to try and improve the clarity of soft images

The inpaint process requires all images in the processed directory to have the same dimensions, and to have overlay/s in the same location/s of the image. Inpaint quality is limited: surrounding colours will be matched well, but patterns will be matched poorly,.

To use this feature you'll need to configure a mask:
- In `/inpaint-masks`, make a copy of `inpaint-mask.example.json`, Name the copy something suitable. Adjust the parameters for your image set: 
  - `image_dimensions`: The width and height of the images (pixels). All images in the set should have the same dimensions.
  - `mask_regions`: The x & y coordinates needed to calculate the rectangular area to inpaint, in this order: `x-min`, `y-min`, `x-max`, `y-max` (left, top, right, bottom).  
    You can specify any number of mask regions. The example has two.

To try the mask on the first image in a set of extracted images:

```bash
uv run vhs-enhance "output/<directory name>/restorations" --inpaint-mask "inpaint-masks/<mask file name>.json" --preview
```

This will generate:
- a single enhanced image
- `before-after.jpg`: a side-by-side comparison of the before/after images
- `overlay-mask.png`: shows the regions selected for inpainting

To then process all images in the directory, run:

```bash
uv run vhs-enhance "output/<directory name>/restorations"
```

You can adjust the level of sharpening with a flag.

```bash
uv run vhs-enhance "output/<directory name>/restorations" --strength 0.15
```

The default value is 0.35. Set it to 0 to disable sharpening.


## Linting and formatting

```bash
# Check for issues:
uv run ruff check .

# Fix issues:
uv run ruff check . --fix

# Format:
uv run ruff format .
```

## Licence

See [LICENSE.tst](LICENSE.txt).
