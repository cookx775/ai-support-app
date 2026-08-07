import re
import unittest
from pathlib import Path


CSS_PATH = Path(__file__).parents[1] / "assets" / "lesson.css"


def _declarations(css: str, selector: str) -> dict[str, str]:
    match = re.search(rf"(?:^|\}})\s*{re.escape(selector)}\s*\{{([^}}]+)\}}", css, re.MULTILINE)
    if not match:
        return {}
    return {
        name.strip(): value.strip()
        for declaration in match.group(1).split(";")
        if ":" in declaration
        for name, value in [declaration.split(":", 1)]
    }


def _resolve_color(css: str, value: str) -> str:
    variable = re.fullmatch(r"var\((--[-\w]+)\)", value)
    if not variable:
        return value
    root = _declarations(css, ":root")
    return root[variable.group(1)]


def _relative_luminance(hex_color: str) -> float:
    channels = [int(hex_color[index : index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [
        channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4
        for channel in channels
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast_ratio(foreground: str, background: str) -> float:
    light, dark = sorted(
        (_relative_luminance(foreground), _relative_luminance(background)), reverse=True
    )
    return (light + 0.05) / (dark + 0.05)


class LessonCssTests(unittest.TestCase):
    def test_code_inside_pre_keeps_readable_contrast(self) -> None:
        css = CSS_PATH.read_text()
        pre = _declarations(css, "pre")
        code = _declarations(css, "code")
        nested = _declarations(css, "pre code")

        foreground = nested.get("color", code.get("color", pre["color"]))
        background = nested.get("background", code.get("background", pre["background"]))
        if background == "transparent":
            background = pre["background"]
        if foreground == "inherit":
            foreground = pre["color"]

        contrast = _contrast_ratio(
            _resolve_color(css, foreground),
            _resolve_color(css, background),
        )
        self.assertGreaterEqual(
            contrast,
            4.5,
            f"pre code contrast is only {contrast:.2f}:1",
        )


if __name__ == "__main__":
    unittest.main()
