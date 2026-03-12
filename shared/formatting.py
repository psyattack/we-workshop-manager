def human_readable_size(size_bytes: int) -> str:
    value = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if value < 1024.0:
            return f"{value:.1f} {unit}"
        value /= 1024.0
    return f"{value:.1f} PB"


def format_bytes_short(num_bytes: int) -> str:
    if num_bytes <= 0:
        return "0B"
    if num_bytes < 1024:
        return f"{num_bytes}B"
    if num_bytes < 1024 ** 2:
        value = num_bytes / 1024
        return f"{value:.0f}KB" if value >= 10 else f"{value:.1f}KB"
    if num_bytes < 1024 ** 3:
        value = num_bytes / (1024 ** 2)
        return f"{value:.0f}MB" if value >= 10 else f"{value:.1f}MB"

    value = num_bytes / (1024 ** 3)
    return f"{value:.1f}GB"


def hex_to_rgba(hex_color: str, alpha: int = 255) -> str:
    normalized = hex_color.lstrip("#")
    if len(normalized) != 6:
        return hex_color

    red = int(normalized[0:2], 16)
    green = int(normalized[2:4], 16)
    blue = int(normalized[4:6], 16)
    return f"rgba({red}, {green}, {blue}, {alpha})"