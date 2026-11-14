# Zuhura Mars Digital Twin — Mars Quantized-Mesh 1.0 Specification Compliance

**Document Version:** 1.0.0  
**Phase:** Stage 7 Implementation  
**Module:** `zuhura_data.terrain.quantized_mesh`  
**Target Consumer:** CesiumJS 1.121+ / `@cesium/engine`  
**Datum:** IAU/IAG 2015 Mars Biaxial Ellipsoid ($a=3,396,190\text{ m}, c=3,376,200\text{ m}$)  
**Topographic Reference:** MOLA GMM-3 Areoid  

---

## 1. Overview and Engineering Background

Cesium's **Quantized-Mesh 1.0** binary specification is the industry-standard terrain streaming format for 3D planetary globes. However, almost all commercial terrain generators (e.g. Cesium Ion terrain pipeline, `ctb-tile`) hardcode Earth's **WGS84 ellipsoid** ($a=6,378,137\text{ m}$). Applying Earth-hardcoded tools to Mars results in:
1. Complete failure of horizon occlusion culling (tiles erroneously culled behind the horizon).
2. Severe curvature distortion (Mars radius is $53\%$ of Earth).
3. Incorrect tile center vectors and bounding volume spheres.

To provide an authoritative Mars digital twin foundation, Zuhura implements a pure-Python terrain encoder strictly adhering to the IAU/IAG 2015 Mars Biaxial Ellipsoid.

---

## 2. Binary Layout Specification

A Quantized-Mesh 1.0 tile consists of contiguous binary sections serialized in little-endian format:

```
+-------------------------------------------------------------+
| 88-Byte Quantized-Mesh Header                               |
| - Center MCMF (double[3], 24B)                              |
| - Min/Max Height (float[2], 8B)                             |
| - Bounding Sphere Center & Radius (double[4], 32B)          |
| - Horizon Occlusion Point in Scaled Space (double[3], 24B)  |
+-------------------------------------------------------------+
| Vertex Count (uint32, 4B)                                   |
| - U buffer: uint16[vertexCount], Zig-Zag Delta Encoded      |
| - V buffer: uint16[vertexCount], Zig-Zag Delta Encoded      |
| - Height buffer: uint16[vertexCount], Zig-Zag Delta Encoded |
+-------------------------------------------------------------+
| 2/4-Byte Alignment Padding (if needed)                      |
+-------------------------------------------------------------+
| Triangle Count (uint32, 4B)                                 |
| - Triangle Indices: uint16[3 * triangleCount]               |
|   Encoded via High-Water Mark Delta Scheme                  |
+-------------------------------------------------------------+
| Edge Vertex Boundary Lists                                  |
| - West:  uint32 count + uint16[count]                       |
| - South: uint32 count + uint16[count]                       |
| - East:  uint32 count + uint16[count]                       |
| - North: uint32 count + uint16[count]                       |
+-------------------------------------------------------------+
| Optional Extensions (Appended)                              |
| - Oct-Encoded Per-Vertex Normals (ID 1, 1B + 4B + 2*N B)    |
| - Watermask (ID 2, optional)                                |
| - Metadata (ID 4, optional)                                 |
+-------------------------------------------------------------+
```

---

## 3. Vertex Ordering and High-Water Mark Compression

CesiumJS decodes triangle indices using:
```javascript
let highest = 0;
for (let i = 0; i < indices.length; ++i) {
    const code = indices[i];
    indices[i] = highest - code;
    if (code === 0) {
        ++highest;
    }
}
```

### The Invariant:
Because `code` is an unsigned 16-bit integer ($\ge 0$) and `code === 0` increments `highest` by only $1$, an index $X$ cannot be introduced unless $X = \text{highest}$.

### The Zuhura Solution:
Zuhura's encoder performs **topological sequence reordering**:
1. Vertices are gathered into an ordered pool in the exact order they first appear in the triangle list.
2. For any index $X$:
   - If $X$ is visited for the first time, its new index in the reordered pool is $\text{highest}$. Hence $\text{code} = \text{highest} - X = 0$, and $\text{highest}$ increments by 1.
   - If $X$ was already visited, its index is $< \text{highest}$. Hence $\text{code} = \text{highest} - X > 0$.
3. Edge vertex lists are automatically mapped through the same reordering lookup `mapping[old_idx]`.

This guarantees $100\%$ zero-error decompression in CesiumJS without any out-of-range index errors or scrambled meshes.

---

## 4. Horizon Occlusion Point Calculation

The horizon occlusion point is used by Cesium's `EllipsoidalOccluder` to cull terrain tiles hidden behind the curvature of the planet.

In Cesium, the horizon occlusion point must be expressed in **ellipsoid-scaled coordinates**:
$$P_{\text{scaled}} = \left(\frac{X}{a}, \frac{Y}{a}, \frac{Z}{c}\right)$$
For each vertex $P$, let $r = \|P_{\text{scaled}}\|$, $\cos\beta = 1/r$, $\sin\beta = \sqrt{r^2-1}/r$, $\cos\alpha = P_{\text{dir}} \cdot D_{\text{scaled}}$, $\sin\alpha = \|P_{\text{dir}} \times D_{\text{scaled}}\|$.
The candidate magnitude is:
$$M = \frac{1}{\cos(\alpha + \beta)} = \frac{1}{\cos\alpha \cos\beta - \sin\alpha \sin\beta}$$
The horizon occlusion point vector is:
$$\vec{H} = M_{\max} \cdot \hat{D}_{\text{scaled}}$$

For regional tiles, $\|\vec{H}\| \approx 1.001\text{--}1.05$. In Stage 6, raw Cartesian meters ($\|\vec{H}\| \approx 3.4 \times 10^6$) were used, triggering false horizon culling. In Stage 7, ellipsoid-scaled coordinates are calculated, ensuring tiles remain visible at all camera angles.

---

## 5. Tile Map Service (TMS) Tiling Scheme

Tiles are addressed using standard TMS coordinates:
- At zoom level $z$: $n_y = 2^z$, $n_x = 2 \cdot 2^z$.
- $x = 0$ corresponds to $-180^\circ$ East; $x = n_x - 1$ corresponds to $+180^\circ$ East.
- $y = 0$ corresponds to the South Pole ($-90^\circ$); $y = n_y - 1$ corresponds to the North Pole ($+90^\circ$).
- Storage layout: `{z}/{x}/{y}.terrain`.
