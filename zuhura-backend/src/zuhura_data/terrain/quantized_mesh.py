"""
Zuhura Planetary Digital Twin - Mars Quantized-Mesh 1.0 Terrain Generator
Encodes raster digital elevation models into Cesium-compliant Quantized-Mesh 1.0 binary tiles (.terrain)
using the IAU/IAG 2015 Mars Biaxial Ellipsoid (a=3,396,190m, c=3,376,200m).

Specification Compliance:
- 88-byte Header with little-endian doubles and floats
- Quantized vertices (u, v, height) zig-zag delta encoded in [0, 32767]
- Triangle indices high-water mark delta compressed with vertex sequence ordering
- Edge vertex boundary arrays (West, South, East, North)
- Ellipsoid-scaled Horizon Occlusion Point M * D_scaled
- Optional Oct-Encoded Per-Vertex Normals extension (ID 1, octvertexnormals)
"""

import gzip
import io
import json
import math
import struct
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from osgeo import gdal

# IAU/IAG 2015 Mars Biaxial Ellipsoid
MARS_A = 3396190.0
MARS_C = 3376200.0
MARS_E2 = (MARS_A**2 - MARS_C**2) / (MARS_A**2)

# Extension IDs
EXT_OCT_VERTEX_NORMALS = 1
EXT_WATER_MASK = 2
EXT_METADATA = 4


def geodetic_to_cartesian(lat_deg: float, lon_deg: float, height_m: float) -> Tuple[float, float, float]:
    """
    Converts Mars geodetic coordinates to Mars-Centered, Mars-Fixed (MCMF) Cartesian coordinates.
    """
    lat_rad = math.radians(lat_deg)
    lon_rad = math.radians(lon_deg)
    
    sin_lat = math.sin(lat_rad)
    cos_lat = math.cos(lat_rad)
    sin_lon = math.sin(lon_rad)
    cos_lon = math.cos(lon_rad)
    
    N = MARS_A / math.sqrt(1.0 - MARS_E2 * sin_lat * sin_lat)
    X = (N + height_m) * cos_lat * cos_lon
    Y = (N + height_m) * cos_lat * sin_lon
    Z = (N * (1.0 - MARS_E2) + height_m) * sin_lat
    return X, Y, Z


def zigzag_encode(val: int) -> int:
    """Encode a signed integer into unsigned integer via zig-zag encoding."""
    return (val << 1) ^ (val >> 31)


def zigzag_decode(val: int) -> int:
    """Decode a zig-zag encoded unsigned integer to signed integer."""
    return (val >> 1) ^ (-(val & 1))


def compress_indices(indices: List[int]) -> bytes:
    """
    Compresses triangle indices using Cesium's High-Water Mark delta encoding.
    Decoder in Cesium: indices[i] = highest - code; if (code === 0) ++highest;
    """
    encoded = []
    highest = 0
    for idx in indices:
        code = highest - idx
        assert code >= 0, f"Negative code {code} for index {idx} with highest {highest}"
        encoded.append(code)
        if code == 0:
            highest += 1

    if max(indices) > 65536:
        return struct.pack(f"<{len(encoded)}I", *encoded)
    else:
        return struct.pack(f"<{len(encoded)}H", *encoded)


def decompress_indices(data_bytes: bytes, index_count: int, bytes_per_index: int = 2) -> List[int]:
    """
    Decompresses High-Water Mark encoded indices (matches Cesium decompressIndices_).
    """
    fmt = f"<{index_count}{'I' if bytes_per_index == 4 else 'H'}"
    raw_codes = struct.unpack(fmt, data_bytes)
    decoded = []
    highest = 0
    for code in raw_codes:
        idx = highest - code
        decoded.append(idx)
        if code == 0:
            highest += 1
    return decoded


def compute_horizon_occlusion_point(
    cartesian_positions: List[Tuple[float, float, float]],
    center_pos: Tuple[float, float, float]
) -> Tuple[float, float, float]:
    """
    Computes the Horizon Occlusion Point in ellipsoid-scaled coordinates (magnitude ~ 1.0 - 2.0).
    Follows Cesium EllipsoidalOccluder.computeHorizonCullingPointFromPositions.
    """
    # Scale center direction to unit-sphere space
    dc_x = center_pos[0] / MARS_A
    dc_y = center_pos[1] / MARS_A
    dc_z = center_pos[2] / MARS_C
    d_len = math.sqrt(dc_x**2 + dc_y**2 + dc_z**2)
    if d_len == 0:
        return 0.0, 0.0, 0.0
    dx, dy, dz = dc_x / d_len, dc_y / d_len, dc_z / d_len

    max_mag = 0.0
    for p in cartesian_positions:
        sx = p[0] / MARS_A
        sy = p[1] / MARS_A
        sz = p[2] / MARS_C
        r2 = sx**2 + sy**2 + sz**2
        r = math.sqrt(r2)
        r = max(1.0, r)
        r2 = max(1.0, r2)

        ux, uy, uz = sx / r, sy / r, sz / r
        cos_alpha = ux * dx + uy * dy + uz * dz
        # Cross product magnitude
        cx = uy * dz - uz * dy
        cy = uz * dx - ux * dz
        cz = ux * dy - uy * dx
        sin_alpha = math.sqrt(cx**2 + cy**2 + cz**2)

        cos_beta = 1.0 / r
        sin_beta = math.sqrt(r2 - 1.0) / r
        denom = cos_alpha * cos_beta - sin_alpha * sin_beta
        if denom > 0:
            mag = 1.0 / denom
            if mag > max_mag:
                max_mag = mag

    if max_mag > 0:
        return dx * max_mag, dy * max_mag, dz * max_mag
    return dx, dy, dz


def oct_encode_normal(nx: float, ny: float, nz: float) -> Tuple[int, int]:
    """
    Octahedral encoding of a unit normal vector into two unsigned bytes [0, 255].
    Follows Cesium AttributeCompression.octEncode.
    """
    l1 = abs(nx) + abs(ny) + abs(nz)
    if l1 == 0:
        return 128, 128
    ox = nx / l1
    oy = ny / l1
    if nz < 0:
        sx = 1.0 if ox >= 0 else -1.0
        sy = 1.0 if oy >= 0 else -1.0
        ox, oy = (1.0 - abs(oy)) * sx, (1.0 - abs(ox)) * sy

    u = int(round((max(-1.0, min(1.0, ox)) * 0.5 + 0.5) * 255.0))
    v = int(round((max(-1.0, min(1.0, oy)) * 0.5 + 0.5) * 255.0))
    return u, v


def oct_decode_normal(u: int, v: int) -> Tuple[float, float, float]:
    """
    Decodes an oct-encoded normal vector back to a 3D unit vector.
    Follows Cesium AttributeCompression.octDecode.
    """
    x = (u / 255.0) * 2.0 - 1.0
    y = (v / 255.0) * 2.0 - 1.0
    z = 1.0 - (abs(x) + abs(y))
    if z < 0:
        ox = x
        oy = y
        sx = 1.0 if ox >= 0 else -1.0
        sy = 1.0 if oy >= 0 else -1.0
        x = (1.0 - abs(oy)) * sx
        y = (1.0 - abs(ox)) * sy
    mag = math.sqrt(x**2 + y**2 + z**2)
    if mag == 0:
        return 0.0, 0.0, 1.0
    return x / mag, y / mag, z / mag


def encode_quantized_mesh(
    elevation_grid: np.ndarray,
    lon_min: float,
    lat_min: float,
    lon_max: float,
    lat_max: float,
    min_height: Optional[float] = None,
    max_height: Optional[float] = None,
    include_normals: bool = True
) -> bytes:
    """
    Encodes an (N, N) elevation array into Cesium Quantized-Mesh 1.0 binary format.
    Includes:
      - 88-byte Header with MCMF coordinates and ellipsoid-scaled horizon occlusion
      - Vertex sequence re-ordering for true High-Water Mark encoding
      - Zig-zag delta encoded quantized vertices [0, 32767]
      - High-water mark encoded triangle indices with 2-byte alignment
      - Edge indices (West, South, East, North)
      - Optional Oct-encoded per-vertex surface normals extension (ID 1)
    """
    rows, cols = elevation_grid.shape

    if min_height is None:
        min_height = float(np.nanmin(elevation_grid))
    if max_height is None:
        max_height = float(np.nanmax(elevation_grid))

    if max_height <= min_height:
        max_height = min_height + 1.0

    # 1. Compute 3D Cartesian coordinates for all vertices and surface normals
    cartesian_grid = np.zeros((rows, cols, 3), dtype=np.float64)
    raw_vertex_list = []

    for r in range(rows):
        lat = lat_min + (r / (rows - 1)) * (lat_max - lat_min)
        v_norm = int(round((r / (rows - 1)) * 32767.0))
        for c in range(cols):
            lon = lon_min + (c / (cols - 1)) * (lon_max - lon_min)
            u_norm = int(round((c / (cols - 1)) * 32767.0))
            elev = float(elevation_grid[r, c])
            if np.isnan(elev):
                elev = min_height
            elev_norm = int(round(np.clip((elev - min_height) / (max_height - min_height), 0.0, 1.0) * 32767.0))

            X, Y, Z = geodetic_to_cartesian(lat, lon, elev)
            cartesian_grid[r, c] = [X, Y, Z]
            raw_vertex_list.append({
                "u": u_norm,
                "v": v_norm,
                "h": elev_norm,
                "pos": (X, Y, Z),
                "grid_rc": (r, c)
            })

    # Compute Normals on grid
    normals_grid = np.zeros((rows, cols, 3), dtype=np.float64)
    for r in range(rows):
        for c in range(cols):
            c_prev = max(0, c - 1)
            c_next = min(cols - 1, c + 1)
            r_prev = max(0, r - 1)
            r_next = min(rows - 1, r + 1)

            v_u = cartesian_grid[r, c_next] - cartesian_grid[r, c_prev]
            v_v = cartesian_grid[r_next, c] - cartesian_grid[r_prev, c]

            norm = np.cross(v_u, v_v)
            norm_len = np.linalg.norm(norm)
            if norm_len > 0:
                norm = norm / norm_len
            else:
                norm = np.array([0.0, 0.0, 1.0])

            # Ensure normal points outward
            if np.dot(norm, cartesian_grid[r, c]) < 0:
                norm = -norm

            normals_grid[r, c] = norm
            idx = r * cols + c
            raw_vertex_list[idx]["norm"] = norm

    # Center is mean of all 3D surface vertices
    center_x = float(np.mean(cartesian_grid[:, :, 0]))
    center_y = float(np.mean(cartesian_grid[:, :, 1]))
    center_z = float(np.mean(cartesian_grid[:, :, 2]))
    center_pos = (center_x, center_y, center_z)

    # Bounding sphere radius enclosing all vertices
    diffs = cartesian_grid - np.array([center_x, center_y, center_z])
    dist_sq = np.sum(diffs**2, axis=-1)
    bs_radius = float(math.sqrt(np.max(dist_sq)))

    # Horizon Occlusion Point in ellipsoid-scaled space
    all_positions = [v["pos"] for v in raw_vertex_list]
    hop_x, hop_y, hop_z = compute_horizon_occlusion_point(all_positions, center_pos)

    # 2. Quad Triangulation (CCW winding)
    raw_triangles = []
    for r in range(rows - 1):
        for c in range(cols - 1):
            i0 = r * cols + c
            i1 = r * cols + (c + 1)
            i2 = (r + 1) * cols + c
            i3 = (r + 1) * cols + (c + 1)

            # Two triangles per quad
            raw_triangles.extend([i0, i1, i2])
            raw_triangles.extend([i1, i3, i2])

    # 3. High-Water Mark Re-ordering:
    # Order vertices in the exact order they first appear in triangles
    old_to_new = {}
    ordered_vertices = []
    reordered_triangles = []

    for old_idx in raw_triangles:
        if old_idx not in old_to_new:
            new_idx = len(ordered_vertices)
            old_to_new[old_idx] = new_idx
            ordered_vertices.append(raw_vertex_list[old_idx])
        reordered_triangles.append(old_to_new[old_idx])

    vertex_count = len(ordered_vertices)
    triangle_count = len(reordered_triangles) // 3

    # 4. Zig-Zag Delta Encoding for Vertices
    def compress_channel(vals: List[int]) -> bytes:
        out = []
        prev = 0
        for val in vals:
            diff = val - prev
            out.append(zigzag_encode(diff))
            prev = val
        return struct.pack(f"<{len(out)}H", *out)

    u_bytes = compress_channel([v["u"] for v in ordered_vertices])
    v_bytes = compress_channel([v["v"] for v in ordered_vertices])
    h_bytes = compress_channel([v["h"] for v in ordered_vertices])

    # 5. High-Water Mark Encoding for Triangle Indices
    tri_bytes = compress_indices(reordered_triangles)

    # 6. Edge Vertex Indices (seams) mapped through old_to_new
    west_indices = [old_to_new[r * cols] for r in range(rows)]
    south_indices = [old_to_new[c] for c in range(cols)]
    east_indices = [old_to_new[r * cols + (cols - 1)] for r in range(rows)]
    north_indices = [old_to_new[(rows - 1) * cols + c] for c in range(cols)]

    bytes_per_index = 4 if vertex_count > 65536 else 2

    def pack_edge(indices: List[int]) -> bytes:
        idx_type = "I" if bytes_per_index == 4 else "H"
        return struct.pack("<I", len(indices)) + struct.pack(f"<{len(indices)}{idx_type}", *indices)

    # 7. Assemble Core Tile Data
    header = struct.pack(
        "<dddffddddddd",
        center_x, center_y, center_z,
        min_height, max_height,
        center_x, center_y, center_z, bs_radius,
        hop_x, hop_y, hop_z
    )

    core_bytes = (
        header +
        struct.pack("<I", vertex_count) +
        u_bytes +
        v_bytes +
        h_bytes
    )

    # Check alignment before triangle count and indices
    pos = len(core_bytes)
    if pos % bytes_per_index != 0:
        pad_len = bytes_per_index - (pos % bytes_per_index)
        core_bytes += b"\x00" * pad_len

    core_bytes += (
        struct.pack("<I", triangle_count) +
        tri_bytes +
        pack_edge(west_indices) +
        pack_edge(south_indices) +
        pack_edge(east_indices) +
        pack_edge(north_indices)
    )

    # 8. Optional Oct-Encoded Per-Vertex Normals Extension (Extension ID 1)
    if include_normals:
        normal_bytes = bytearray()
        for v in ordered_vertices:
            norm = v["norm"]
            ou, ov = oct_encode_normal(norm[0], norm[1], norm[2])
            normal_bytes.append(ou)
            normal_bytes.append(ov)

        ext_len = len(normal_bytes)
        ext_header = struct.pack("<BI", EXT_OCT_VERTEX_NORMALS, ext_len)
        core_bytes += ext_header + bytes(normal_bytes)

    return core_bytes


def decode_quantized_mesh(data: bytes) -> Dict[str, Any]:
    """
    Fully parses and validates a Quantized-Mesh 1.0 binary tile buffer.
    Verifies 88-byte header, vertex decompression, triangle indices, edge lists, and extensions.
    """
    if len(data) < 88:
        raise ValueError(f"Tile binary too short ({len(data)} bytes, expected >= 88).")

    pos = 0
    (
        cx, cy, cz,
        min_h, max_h,
        bcx, bcy, bcz, bradius,
        hx, hy, hz
    ) = struct.unpack("<dddffddddddd", data[pos:pos+88])
    pos += 88

    vertex_count = struct.unpack("<I", data[pos:pos+4])[0]
    pos += 4

    # Decompress U, V, Height
    u_raw = struct.unpack(f"<{vertex_count}H", data[pos:pos + vertex_count*2])
    pos += vertex_count * 2
    v_raw = struct.unpack(f"<{vertex_count}H", data[pos:pos + vertex_count*2])
    pos += vertex_count * 2
    h_raw = struct.unpack(f"<{vertex_count}H", data[pos:pos + vertex_count*2])
    pos += vertex_count * 2

    u_dec = []
    v_dec = []
    h_dec = []
    u_c, v_c, h_c = 0, 0, 0
    for i in range(vertex_count):
        u_c += zigzag_decode(u_raw[i])
        v_c += zigzag_decode(v_raw[i])
        h_c += zigzag_decode(h_raw[i])
        u_dec.append(u_c)
        v_dec.append(v_c)
        h_dec.append(h_c)

    # Alignment check
    bytes_per_index = 4 if vertex_count > 65536 else 2
    if pos % bytes_per_index != 0:
        pos += bytes_per_index - (pos % bytes_per_index)

    triangle_count = struct.unpack("<I", data[pos:pos+4])[0]
    pos += 4
    tri_len_bytes = triangle_count * 3 * bytes_per_index
    tri_decomp = decompress_indices(data[pos:pos+tri_len_bytes], triangle_count * 3, bytes_per_index)
    pos += tri_len_bytes

    # Edges
    edges = {}
    for name in ["west", "south", "east", "north"]:
        edge_cnt = struct.unpack("<I", data[pos:pos+4])[0]
        pos += 4
        edge_fmt = f"<{edge_cnt}{'I' if bytes_per_index == 4 else 'H'}"
        edge_indices = struct.unpack(edge_fmt, data[pos:pos + edge_cnt * bytes_per_index])
        pos += edge_cnt * bytes_per_index
        edges[name] = list(edge_indices)

    # Extensions
    extensions = []
    while pos < len(data):
        ext_id = struct.unpack("<B", data[pos:pos+1])[0]
        pos += 1
        ext_len = struct.unpack("<I", data[pos:pos+4])[0]
        pos += 4
        ext_data = data[pos:pos+ext_len]
        pos += ext_len

        ext_info = {"id": ext_id, "length": ext_len}
        if ext_id == EXT_OCT_VERTEX_NORMALS:
            ext_info["type"] = "octvertexnormals"
            ext_info["normals_count"] = ext_len // 2
        elif ext_id == EXT_WATER_MASK:
            ext_info["type"] = "watermask"
        elif ext_id == EXT_METADATA:
            ext_info["type"] = "metadata"
        extensions.append(ext_info)

    return {
        "header": {
            "center": [cx, cy, cz],
            "min_height_m": min_h,
            "max_height_m": max_h,
            "bounding_sphere": {"center": [bcx, bcy, bcz], "radius": bradius},
            "horizon_occlusion_point": [hx, hy, hz]
        },
        "vertex_count": vertex_count,
        "triangle_count": triangle_count,
        "u_span": [min(u_dec), max(u_dec)],
        "v_span": [min(v_dec), max(v_dec)],
        "height_span": [min(h_dec), max(h_dec)],
        "triangles_sample": tri_decomp[:9],
        "edges": {k: len(v) for k, v in edges.items()},
        "extensions": extensions,
        "total_bytes": len(data)
    }


def decode_quantized_mesh_header(data: bytes) -> Dict[str, Any]:
    """Backward-compatible header extractor."""
    decoded = decode_quantized_mesh(data)
    h = decoded["header"]
    return {
        "center": h["center"],
        "min_height_m": h["min_height_m"],
        "max_height_m": h["max_height_m"],
        "bounding_sphere": h["bounding_sphere"],
        "horizon_occlusion": h["horizon_occlusion_point"],
        "vertex_count": decoded["vertex_count"],
        "total_bytes": decoded["total_bytes"]
    }


def generate_jezero_quantized_mesh_tiles(
    dem_path: Path,
    output_dir: Path,
    include_normals: bool = True
) -> Dict[str, Any]:
    """
    Generates Cesium-compliant quantized-mesh terrain tiles and layer.json
    for Jezero Crater from the regional MOLA DEM.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    ds = gdal.Open(str(dem_path))
    assert ds is not None, f"Failed to open DEM: {dem_path}"

    gt = ds.GetGeoTransform()
    band = ds.GetRasterBand(1)
    elev_arr = band.ReadAsArray()
    ds = None

    min_h = float(elev_arr.min())
    max_h = float(elev_arr.max())

    # Subsample to standard 33x33 tile grid
    from PIL import Image
    im = Image.fromarray(elev_arr)
    im_resized = im.resize((33, 33), Image.Resampling.BILINEAR)
    grid_33 = np.array(im_resized, dtype=np.float32)

    # Encode Jezero tile
    # Scheme: Cesium GeographicTilingScheme (2x1 at level 0)
    # lon: 76.5 to 78.5, lat: 18.0 to 19.0
    z = 9
    n_y = 2 ** z
    n_x = 2 * n_y
    d_lon = 360.0 / n_x
    d_lat = 180.0 / n_y
    x_tile = int((77.5 + 180.0) / d_lon)

    # TMS y-coordinate: counts from South Pole (-90) upward
    y_tms = int((18.5 - (-90.0)) / d_lat)
    # XYZ y-coordinate: counts from North Pole (+90) downward
    y_xyz = int((90.0 - 18.5) / d_lat)

    tile_bytes = encode_quantized_mesh(
        grid_33,
        lon_min=76.5, lat_min=18.0,
        lon_max=78.5, lat_max=19.0,
        min_height=min_h, max_height=max_h,
        include_normals=include_normals
    )

    # Write tile to disk for both TMS and XYZ naming for seamless compatibility
    tile_dir = output_dir / str(z) / str(x_tile)
    tile_dir.mkdir(parents=True, exist_ok=True)

    terrain_file_tms = tile_dir / f"{y_tms}.terrain"
    with open(terrain_file_tms, "wb") as f:
        f.write(tile_bytes)

    # Also keep y_xyz for backwards compatibility if requested directly
    terrain_file_xyz = tile_dir / f"{y_xyz}.terrain"
    with open(terrain_file_xyz, "wb") as f:
        f.write(tile_bytes)

    # Write layer.json metadata
    layer_json = {
        "tilejson": "2.1.0",
        "format": "quantized-mesh-1.0",
        "version": "1.0.0",
        "name": "Zuhura Mars Jezero Regional Terrain",
        "description": "Cesium quantized-mesh 1.0 terrain tiles generated from MOLA MEG128 regional DEM referenced to MOLA GMM-3 areoid.",
        "scheme": "tms",
        "ellipsoid": {
            "name": "IAU/IAG 2015 Mars Biaxial Ellipsoid",
            "semiMajorAxis": MARS_A,
            "semiMinorAxis": MARS_C
        },
        "bounds": [76.5, 18.0, 78.5, 19.0],
        "minzoom": 0,
        "maxzoom": 9,
        "extensions": ["octvertexnormals"] if include_normals else [],
        "available": [
            [{"startX": 0, "endX": 1, "startY": 0, "endY": 0}],
            [{"startX": x_tile, "endX": x_tile, "startY": y_tms, "endY": y_tms}]
        ],
        "tiles": ["{z}/{x}/{y}.terrain"]
    }

    layer_file = output_dir / "layer.json"
    with open(layer_file, "w", encoding="utf-8") as f:
        json.dump(layer_json, f, indent=2)

    return {
        "terrain_file": str(terrain_file_tms),
        "layer_file": str(layer_file),
        "tile_bytes": len(tile_bytes),
        "zoom": z,
        "tile_coords": {"z": z, "x": x_tile, "y": y_tms},
        "elevation_bounds_m": [min_h, max_h],
        "header_info": decode_quantized_mesh_header(tile_bytes)
    }
