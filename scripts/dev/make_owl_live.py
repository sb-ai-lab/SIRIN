"""Turn the owl animation MP4 into the transparent looping WebP the workspace header uses.

The source renders the owl over pure black, which makes the matte ambiguous by luma alone: the
owl's own dark linework (pupils, outlines, the magnifier rim) sits at roughly the same luma as
the backdrop, so any threshold low enough to clear the backdrop also eats the linework. The owl
is one solid blob, so connectivity resolves it instead -- fill the silhouette and everything
inside is opaque no matter how dark it is.

The frame holds two kinds of thing and they cannot share a rule. The owl is an opaque object and
wants a binary matte. The sparkles are additive glow -- a bright core inside a wide halo fading
to black -- and want alpha proportional to luma; make them opaque and their dark halo renders as
a black blob. BODY_LUMA has to sit above the glow, or a sparkle whose halo laps onto the owl
merges into its silhouette and gets filled in as one of those blobs.

Order matters. Keying happens at the source's native resolution and the downscale comes after:
Lanczos overshoots at the owl/black boundary, and keying an already-downscaled frame freezes
that ringing into opaque black specks around the edge. Keyed first, the downscale is what
supplies the edge antialiasing.

    python scripts/dev/make_owl_live.py
"""
from __future__ import annotations

import glob
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

ASSETS = Path(__file__).resolve().parents[2] / 'sirin' / 'ui' / 'assets'
SOURCE = ASSETS / 'animation_logo.mp4'
TARGET = ASSETS / 'owl_live.webp'

# The header renders this at 46 CSS px and nothing else consumes it, so 96px is exactly 2x retina
# and every pixel above that is weight fetched mid-run for nothing (128px cost 662KB against 439KB
# here for no visible difference). Frame count and SIZE drive the file; QUALITY barely moves it --
# 70 -> 40 saved only 15% -- so keep quality high and spend the budget on resolution.
SIZE = 96
FPS = 10
QUALITY = 60

# Luma above this is solid owl. Sits deliberately above the sparkle glow -- see the module note.
BODY_LUMA = 0.25
# Luma above this is drawn light rather than backdrop (the backdrop measures ~0.004).
GLOW_LUMA = 0.02

PREVIEW_BACKDROPS = {'light': (246, 245, 243), 'dark': (24, 22, 28)}


def key_frame(path: str) -> Image.Image:
    rgb = np.asarray(Image.open(path).convert('RGB')).astype(np.float32) / 255.0
    luma = rgb.max(axis=2)
    labels, count = ndimage.label(luma > BODY_LUMA)
    if count == 0:
        raise SystemExit(f'{path}: no owl found above BODY_LUMA')
    sizes = ndimage.sum(np.ones_like(labels), labels, range(1, count + 1))
    owl = ndimage.binary_fill_holes(labels == int(np.argmax(sizes)) + 1)

    # Extend owl colour outward so the downscale blends owl-into-owl at the rim rather than
    # pulling the black backdrop in and ringing it into a dark fringe.
    nearest = ndimage.distance_transform_edt(~owl, return_distances=False, return_indices=True)
    glow_alpha = np.where(luma > GLOW_LUMA, luma, 0.0)
    alpha = np.where(owl, 1.0, glow_alpha)
    lit = np.maximum(alpha, GLOW_LUMA)[..., None]
    rgba = np.concatenate([
        np.where(owl[..., None], rgb[nearest[0], nearest[1]], np.clip(rgb / lit, 0.0, 1.0)),
        alpha[..., None],
    ], axis=2)
    return Image.fromarray((rgba * 255).astype(np.uint8), 'RGBA').resize((SIZE, SIZE), Image.LANCZOS)


def extract_frames(directory: str) -> list[Image.Image]:
    subprocess.run(
        ['ffmpeg', '-v', 'error', '-i', str(SOURCE), '-vf', f'fps={FPS}', '-vsync', '0', f'{directory}/%03d.png'],
        check=True,
    )
    return [key_frame(path) for path in sorted(glob.glob(f'{directory}/*.png'))]


def write_previews(frame: Image.Image, directory: Path) -> None:
    for name, backdrop in PREVIEW_BACKDROPS.items():
        canvas = Image.new('RGB', frame.size, backdrop)
        canvas.paste(frame, (0, 0), frame)
        canvas.save(directory / f'owl_live_preview_{name}.png')


def main() -> None:
    with tempfile.TemporaryDirectory() as directory:
        frames = extract_frames(directory)
        # The source does not loop: its last frame is as far from its first as the middle is,
        # so it snaps on repeat. Play it back and forth instead, without repeating either end.
        loop = frames + frames[-2:0:-1]
        loop[0].save(
            TARGET, save_all=True, append_images=loop[1:],
            duration=round(1000 / FPS), loop=0, quality=QUALITY, method=6,
        )
        preview_dir = Path(tempfile.mkdtemp(prefix='owl_live_'))
        write_previews(frames[len(frames) // 2], preview_dir)
    print(f'{TARGET} <- {len(loop)} frames, {TARGET.stat().st_size / 1024:.0f} KB')
    print(f'previews: {preview_dir}')


if __name__ == '__main__':
    main()
