from __future__ import annotations

from pathlib import Path

import yaml
from PIL import Image, ImageChops

from embod.model.manifest import FixtureAssertionSet


def load_fixture_assertions(path: Path) -> FixtureAssertionSet:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Fixture assertion file must decode to a mapping")
    return FixtureAssertionSet.model_validate(raw)


def image_difference(left: Path, right: Path) -> float:
    left_image = Image.open(left).convert("RGB")
    right_image = Image.open(right).convert("RGB")
    diff = ImageChops.difference(left_image, right_image)
    histogram = diff.histogram()
    scale = sum(value * (index % 256) for index, value in enumerate(histogram))
    max_value = left_image.width * left_image.height * 255 * 3
    return scale / max_value
