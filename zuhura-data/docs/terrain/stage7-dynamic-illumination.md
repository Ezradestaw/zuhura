# Zuhura Mars Digital Twin — Dynamic Terrain Illumination & Hillshading

**Document Version:** 1.0.0  
**Phase:** Stage 7 Implementation  
**Module:** `zuhura.api.v1.illumination`  
**Endpoint:** `GET /api/v1/illumination/solar-position`  
**Applicability:** CesiumJS 3D Globe & Scientific Analysis Engines  

---

## 1. Overview and Scientific Separation

A critical principle of planetary scientific visualization is to **maintain a strict separation between physical radiometric measurements and interactive relief visualization**.

In Zuhura:
1. **Calibrated Physical Radiance**: Derived strictly from verified scientific instruments (e.g. THEMIS IR Band 9 brightness temperatures in Kelvin, or CTX calibrated radiance in $\text{W}\cdot\text{m}^{-2}\cdot\text{sr}^{-1}\cdot\mu\text{m}^{-1}$).
2. **Interactive Solar Hillshading**: A geometric lighting model using surface normal vectors to accentuate topographic morphology (fault scarps, crater rims, lava flow lobes). It must never be confused with or reported as actual in-situ solar irradiance.

---

## 2. Illumination Modes

### Mode 1: Physical Solar Ephemeris Model
Computes the true astronomical position of the Sun relative to an observer on Mars for a specified Martian season ($L_s$) and local true solar time ($t_{\text{solar}}$):

1. **Solar Declination ($\delta$)**:
   $$\sin\delta = \sin(\epsilon) \cdot \sin(L_s)$$
   where $\epsilon = 25.19^\circ$ is Mars axial obliquity.
2. **Hour Angle ($H$)**:
   $$H = (t_{\text{solar}} - 12.0) \times 15.0^\circ$$
3. **Solar Elevation ($\alpha$)**:
   $$\sin\alpha = \sin\phi \cdot \sin\delta + \cos\phi \cdot \cos\delta \cdot \cos H$$
4. **Solar Azimuth ($A$)**:
   $$\tan A = \frac{\sin H}{\cos H \sin\phi - \tan\delta \cos\phi}$$
5. **MCMF Sun Direction ($\hat{S}_{\text{MCMF}}$)**:
   Transformed from local East-North-Up (ENU) coordinates into planetocentric Mars Cartesian space.

### Mode 2: Interactive / Artistic Relief Visualization
Allows users to freely adjust solar azimuth ($0\text{--}360^\circ$) and elevation ($5\text{--}90^\circ$) to reveal subtle geological fault scarps, delta channel lobes, and crater rims.
- Returned metadata includes `mode: "interactive_visualization"` and an explicit scientific disclaimer.

---

## 3. WebGL Terrain Shading in CesiumJS

When `viewer.scene.globe.enableLighting = true` is active and terrain tiles provide `octvertexnormals`:
1. The Cesium vertex shader unpacks the oct-encoded normal vector $\vec{n}$.
2. The fragment shader calculates diffuse Lambertian illumination:
   $$I_{\text{diffuse}} = \max(0.0, \vec{n} \cdot \hat{S})$$
3. Topographic shadows and crest highlights are rendered in real time at 60 FPS directly on the GPU.
