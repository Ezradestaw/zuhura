"""
Focal morphometry (roughness, TRI, TPI).
Implements neighborhood focal indices: Terrain Roughness Index (TRI),
Topographic Position Index (TPI), focal relief, and standard deviation.
"""

from typing import Any, Dict
import numpy as np


def calculate_tri_roughness(window: np.ndarray) -> float:
    """
    Computes the Terrain Roughness Index (Riley et al., 1999).
    Calculates the root-mean-square elevation difference between the center cell
    and all surrounding cells in the window.
    TRI = sqrt( mean( (z_i - z_0)^2 ) )
    """
    arr = np.asarray(window, dtype=np.float64)
    if arr.ndim != 2 or arr.shape[0] < 3 or arr.shape[1] < 3:
        raise ValueError(f"Focal window must be at least 3x3, got {arr.shape}")

    cy, cx = arr.shape[0] // 2, arr.shape[1] // 2
    center_val = arr[cy, cx]

    # Create mask excluding center cell
    mask = np.ones(arr.shape, dtype=bool)
    mask[cy, cx] = False

    neighbors = arr[mask]
    diff_sq = (neighbors - center_val) ** 2
    tri = np.sqrt(np.mean(diff_sq))
    return round(float(tri), 2)


def calculate_tpi(window: np.ndarray) -> float:
    """
    Computes the Topographic Position Index (Weiss, 2001).
    Calculates the difference between the center cell elevation and the average
    elevation of its surrounding neighborhood.
    TPI = z_0 - mean(z_neighbors)
    Positive TPI indicates local ridges/hills; negative TPI indicates valleys/depressions.
    """
    arr = np.asarray(window, dtype=np.float64)
    if arr.ndim != 2 or arr.shape[0] < 3 or arr.shape[1] < 3:
        raise ValueError(f"Focal window must be at least 3x3, got {arr.shape}")

    cy, cx = arr.shape[0] // 2, arr.shape[1] // 2
    center_val = arr[cy, cx]

    mask = np.ones(arr.shape, dtype=bool)
    mask[cy, cx] = False

    mean_neighbor = np.mean(arr[mask])
    tpi = center_val - mean_neighbor
    return round(float(tpi), 2)


def classify_tpi(tpi_val: float) -> str:
    """
    Classifies landform position based on TPI value in meters (standard Weiss 2001 thresholds).
    """
    if tpi_val > 15.0:
        return "ridge_crest"
    elif tpi_val > 5.0:
        return "upper_slope"
    elif -5.0 <= tpi_val <= 5.0:
        return "flat_plain"
    elif tpi_val < -15.0:
        return "canyon_or_pit"
    else:
        return "lower_slope_or_depression"


def calculate_focal_relief(window: np.ndarray) -> float:
    """
    Computes local elevation range (maximum - minimum elevation) within the focal window.
    """
    arr = np.asarray(window, dtype=np.float64)
    relief = np.max(arr) - np.min(arr)
    return round(float(relief), 2)


def calculate_focal_statistics(window: np.ndarray) -> Dict[str, Any]:
    """
    Computes a comprehensive suite of focal statistics across a neighborhood kernel.
    """
    arr = np.asarray(window, dtype=np.float64)
    cy, cx = arr.shape[0] // 2, arr.shape[1] // 2
    center_val = float(arr[cy, cx])

    min_val = float(np.min(arr))
    max_val = float(np.max(arr))
    mean_val = float(np.mean(arr))
    median_val = float(np.median(arr))
    std_dev = float(np.std(arr))
    relief = max_val - min_val

    tri = calculate_tri_roughness(arr)
    tpi = calculate_tpi(arr)
    tpi_class = classify_tpi(tpi)

    return {
        "kernel_dimensions": [int(arr.shape[0]), int(arr.shape[1])],
        "cell_count": int(arr.size),
        "center_elevation_m": round(center_val, 1),
        "min_elevation_m": round(min_val, 1),
        "max_elevation_m": round(max_val, 1),
        "mean_elevation_m": round(mean_val, 1),
        "median_elevation_m": round(median_val, 1),
        "std_dev_m": round(std_dev, 2),
        "local_relief_m": round(relief, 1),
        "tri_roughness_m": tri,
        "tpi_m": tpi,
        "tpi_classification": tpi_class,
    }
