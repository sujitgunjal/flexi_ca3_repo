from app.decision.schemas.decision import TASKS


def render_reliability_svg(report: dict) -> str:
    width = 640
    height = 280 + 150 * len(TASKS)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#f7f5f0"/>',
        '<text x="24" y="32" font-family="Georgia, serif" font-size="20" fill="#1c1917">'
        "Reliability: confidence vs accuracy</text>",
        '<text x="24" y="54" font-family="Consolas, monospace" font-size="12" fill="#57534e">'
        "Raw confidence is dashed. Calibrated confidence is solid. "
        "The dotted line is perfect calibration.</text>",
    ]

    for task_index, task in enumerate(TASKS):
        top = 80 + task_index * 150
        parts.append(_panel(task, report[task], left=24, top=top))

    parts.append("</svg>")
    return "\n".join(parts)


def _panel(task: str, task_report: dict, left: int, top: int) -> str:
    plot_left = left + 36
    plot_top = top + 24
    size = 110
    parts = [
        f'<text x="{left}" y="{top + 14}" font-family="Consolas, monospace" '
        f'font-size="14" fill="#1c1917">{task}</text>',
        f'<rect x="{plot_left}" y="{plot_top}" width="{size}" height="{size}" '
        'fill="#fff" stroke="#d6d3d1"/>',
        _line(
            plot_left,
            plot_top + size,
            plot_left + size,
            plot_top,
            "#a8a29e",
            dashed=True,
        ),
    ]

    for series, color, dashed in (
        ("raw", "#b45309", True),
        ("calibrated", "#0f766e", False),
    ):
        points = _series_points(
            task_report[series]["reliability"],
            plot_left,
            plot_top,
            size,
        )
        if len(points) >= 2:
            rendered = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
            dash = ' stroke-dasharray="4 3"' if dashed else ""
            parts.append(
                f'<polyline fill="none" stroke="{color}" stroke-width="2"{dash} '
                f'points="{rendered}"/>'
            )
        for x_pos, y_pos in points:
            parts.append(
                f'<circle cx="{x_pos:.1f}" cy="{y_pos:.1f}" r="2.5" fill="{color}"/>'
            )

    raw_brier = task_report["raw"]["brier_score"]
    calibrated_brier = task_report["calibrated"]["brier_score"]
    parts.append(
        f'<text x="{plot_left + size + 16}" y="{plot_top + 18}" '
        'font-family="Consolas, monospace" font-size="12" fill="#44403c">'
        f"Raw Brier {raw_brier}</text>"
    )
    parts.append(
        f'<text x="{plot_left + size + 16}" y="{plot_top + 38}" '
        'font-family="Consolas, monospace" font-size="12" fill="#0f766e">'
        f"Calibrated Brier {calibrated_brier}</text>"
    )
    parts.append(
        f'<text x="{plot_left + size + 16}" y="{plot_top + 58}" '
        'font-family="Consolas, monospace" font-size="12" fill="#b45309">'
        "Dashed = raw</text>"
    )
    return "\n".join(parts)


def _series_points(
    bins: list[dict],
    left: int,
    top: int,
    size: int,
) -> list[tuple[float, float]]:
    points = []
    for item in bins:
        if item["mean_confidence"] is None or item["accuracy"] is None:
            continue
        x_pos = left + item["mean_confidence"] * size
        y_pos = top + size - item["accuracy"] * size
        points.append((x_pos, y_pos))
    return points


def _line(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    color: str,
    dashed: bool = False,
) -> str:
    dash = ' stroke-dasharray="2 3"' if dashed else ""
    return (
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
        f'stroke="{color}" stroke-width="1"{dash}/>'
    )
