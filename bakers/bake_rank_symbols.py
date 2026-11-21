r"""bake_rank_symbols.py -- bake retail KO national NP rank symbols from symbol_us/*.dxt.

Knight Online ships three sets of six NP rank tiers in `symbol_us/`, ordered by nation rank:

    tier 0   rank 1         Dragon (gold)
    tier 1   rank 2..4      Nazi / H (silver)
    tier 2   rank 5..10     Mirage / Sheriff (red)
    tier 3   rank 11..40    S (blue)
    tier 4   rank 41..100   M (green)
    tier 5   rank 101..200  K (bronze)

Each tier has three textures in `symbol_us/`:

    knights_0..5.png   <- s_0_20_0.dxt .. s_0_25_0.dxt  (16x16, gold-framed total-NP square)
    personal_0..5.png  <- s_0_30_0.dxt .. s_0_35_0.dxt  (16x16, borderless monthly-NP square)
    tier_0..5.png      <- s_0_40_0.dxt .. s_0_45_0.dxt  (64x64 texture; ribbon sits at 0..56 x 0..14)

The wide chat / ladder ribbons (`s_0_40_0`..`s_0_45_0`) are stored inside 64x64 power-of-two
textures with transparent padding below and to the right; all six are symmetrically centered
within `(0, 0, 56, 14)` (an exact 4:1 aspect ratio), so they are cropped to 56x14.

Output: <output>/ui/rank_symbol/{knights,personal,tier}_{0..5}.png

Usage:
    python bake.py --only rank-symbols
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from _paths import assets as _assets, ko as _ko  # noqa: E402
from ko_texture import decode_ntf  # noqa: E402

DEFAULT_KO = _ko()
DEFAULT_OUT = _assets() / "ui" / "rank_symbol"

TIERS = 6
RIBBON_CROP = (0, 0, 56, 14)

GROUPS: tuple[tuple[str, int, tuple[int, int, int, int] | None], ...] = (
    ("knights", 20, None),
    ("personal", 30, None),
    ("tier", 40, RIBBON_CROP),
)


def _find_symbol_dir(ko_dir: Path) -> Path | None:
    for name in ("symbol_us", "Symbol_us", "SYMBOL_US", "symbol", "Symbol"):
        candidate = ko_dir / name
        if candidate.is_dir() and (candidate / "s_0_20_0.dxt").exists():
            return candidate
    return None


def bake(ko_dir: Path, out_dir: Path) -> tuple[int, list[str]]:
    from PIL import Image

    sym_dir = _find_symbol_dir(ko_dir)
    if sym_dir is None:
        return 0, [f"symbol_us directory with s_0_20_0.dxt not found under {ko_dir}"]

    lookup = {p.name.lower(): p for p in sym_dir.iterdir() if p.is_file()}
    out_dir.mkdir(parents=True, exist_ok=True)

    baked = 0
    failed: list[str] = []

    for prefix, base_id, crop in GROUPS:
        for tier in range(TIERS):
            src_name = f"s_0_{base_id + tier}_0.dxt"
            src_path = lookup.get(src_name.lower())
            if src_path is None:
                failed.append(src_name)
                continue

            decoded = decode_ntf(src_path.read_bytes())
            if decoded is None:
                failed.append(f"{src_name} (decode failed)")
                continue

            width, height, rgba = decoded
            image = Image.frombytes("RGBA", (width, height), rgba.tobytes())
            if crop is not None:
                image = image.crop(crop)

            dst_path = out_dir / f"{prefix}_{tier}.png"
            image.save(dst_path, "PNG", optimize=True)
            baked += 1

    return baked, failed


def main() -> int:
    parser = argparse.ArgumentParser(description="Bake KO national NP rank symbols.")
    parser.add_argument("--ko", type=Path, default=DEFAULT_KO, help="retail KO root directory")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output directory for PNGs")
    args = parser.parse_args()

    total = len(GROUPS) * TIERS
    baked, failed = bake(args.ko, args.out)
    print(f"[rank-symbols] {baked}/{total} icons -> {args.out}")
    for entry in failed:
        print(f"[rank-symbols] missing: {entry}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
