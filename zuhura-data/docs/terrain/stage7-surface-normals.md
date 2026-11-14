# Zuhura Mars Digital Twin — Oct-Encoded Surface Normal Vectors

**Document Version:** 1.0.0  
**Phase:** Stage 7 Implementation  
**Extension Name:** `octvertexnormals` (Quantized-Mesh Extension ID: 1)  
**Standard Reference:** CesiumJS Quantized-Mesh Specification Extension 1  

---

## 1. Overview and Purpose

To enable dynamic sun-angle illumination, shadows, and hardware-accelerated relief shading on the 3D Mars globe, each vertex of a terrain mesh requires a 3D unit surface normal vector $\vec{n} = (n_x, n_y, n_z)$.

Storing uncompressed 32-bit floating-point normal vectors requires:
$$3 \times 4\text{ bytes} = 12\text{ bytes per vertex}$$
For a $33 \times 33$ grid ($1,089$ vertices), this would add $13,068\text{ bytes}$ ($\sim 65\%$ overhead) to every tile.

Cesium solves this using **Octahedral Projection (Oct-Encoding)**, which compresses each 3D normal vector into **two 8-bit unsigned bytes** (2 bytes per vertex), achieving an $83\%$ reduction in normals storage while maintaining an angular error of less than $1.0^\circ$.

---

## 2. Mathematical Definition

Octahedral encoding projects a 3D unit sphere onto an octahedron, which is then unfolded into a $[-1, 1] \times [-1, 1]$ square and quantized into unsigned bytes $[0, 255]$:

### 2.1 Forward Compression (Encoder):
Given normalized $\vec{n} = (x, y, z)$ with $x^2 + y^2 + z^2 = 1$:
$$L_1 = |x| + |y| + |z|$$
$$o_x = \frac{x}{L_1}, \quad o_y = \frac{y}{L_1}$$
If $z < 0$:
$$o_x = (1.0 - |o_y|) \cdot \text{sign}(o_x)$$
$$o_y = (1.0 - |o_x|) \cdot \text{sign}(o_y)$$

### 2.2 Quantization to 8-Bit SNORM:
$$u = \text{round}\left((\text{clip}(o_x, -1.0, 1.0) \cdot 0.5 + 0.5) \times 255.0\right)$$
$$v = \text{round}\left((\text{clip}(o_y, -1.0, 1.0) \cdot 0.5 + 0.5) \times 255.0\right)$$

### 2.3 Decompression in Shader (WebGL):
$$\tilde{x} = \frac{u}{255.0} \times 2.0 - 1.0, \quad \tilde{y} = \frac{v}{255.0} \times 2.0 - 1.0$$
$$\tilde{z} = 1.0 - (|\tilde{x}| + |\tilde{y}|)$$
If $\tilde{z} < 0$:
$$t = 1.0 - |\tilde{y}|; \quad \tilde{y} = (1.0 - |\tilde{x}|) \cdot \text{sign}(\tilde{y}); \quad \tilde{x} = t \cdot \text{sign}(\tilde{x})$$
$$\vec{n} = \text{normalize}(\tilde{x}, \tilde{y}, \tilde{z})$$

---

## 3. Binary Extension Format

The extension is appended directly after the north edge index array in the `.terrain` file:

| Byte Offset | Type | Field | Description |
|---|---|---|---|
| `+0` | `uint8` | `extensionId` | Extension identifier = `1` (`OCT_VERTEX_NORMALS`) |
| `+1` | `uint32` | `extensionLength` | Byte length = `2 * vertexCount` (little-endian) |
| `+5` | `uint8[2 * N]` | `encodedNormals` | Interleaved pairs `(u0, v0, u1, v1, ...)` |

---

## 4. CesiumJS Client Negotiation

In `layer.json`, the presence of normal vectors is declared:
```json
{
  "extensions": [
    "octvertexnormals"
  ]
}
```

When initializing Cesium terrain:
```javascript
Cesium.CesiumTerrainProvider.fromUrl('/api/v1/tiles/terrain/global', {
  ellipsoid: MARS_ELLIPSOID,
  requestVertexNormals: true,
});
```
Cesium inspects `layer.json`, recognizes `"octvertexnormals"`, requests the extension, and binds the normal buffers into its WebGL terrain shader for real-time directional shading.
