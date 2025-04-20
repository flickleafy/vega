# Vectorized color operations for batch processing

from typing import List
from vega_common.utils.color_utils import (
    calculate_color_distance,
    normalize_rgb_values,
    rgb_to_hsv,
    hsv_to_rgb,
)


def normalize_multiple_colors(colors: List[List[int]]) -> List[List[int]]:
    """
    Normalize multiple RGB colors at once.

    Args:
        colors (List[List[int]]): List of RGB colors

    Returns:
        List[List[int]]: List of normalized RGB colors
    """
    return [normalize_rgb_values(color) for color in colors]


def vectorized_rgb_to_hsv(rgb_colors: List[List[int]]) -> List[List[int]]:
    """
    Convert multiple RGB colors to HSV format at once.

    Args:
        rgb_colors (List[List[int]]): List of RGB colors

    Returns:
        List[List[int]]: List of HSV colors
    """
    if not rgb_colors:
        return []

    return [rgb_to_hsv(color) for color in rgb_colors]


def vectorized_hsv_to_rgb(hsv_colors: List[List[int]]) -> List[List[int]]:
    """
    Convert multiple HSV colors to RGB format at once.

    Args:
        hsv_colors (List[List[int]]): List of HSV colors

    Returns:
        List[List[int]]: List of RGB colors
    """
    if not hsv_colors:
        return []

    results = []
    for hsv in hsv_colors:
        try:
            rgb = hsv_to_rgb(hsv)
            results.append(rgb)
        except IndexError:
            # Handle invalid HSV colors
            results.append([0, 0, 0])

    return results


def batch_color_distance(base_color: List[int], colors: List[List[int]]) -> List[float]:
    """
    Calculate the perceptual distance between a base color and multiple colors.

    Args:
        base_color (List[int]): The base RGB color to compare against
        colors (List[List[int]]): List of RGB colors to compare with base color

    Returns:
        List[float]: List of perceptual distances
    """
    if not colors or len(base_color) < 3:
        return []

    return [calculate_color_distance(base_color, color) for color in colors]
