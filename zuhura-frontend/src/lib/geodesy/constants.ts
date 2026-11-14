/**
 * Mars Geodetic Constants (IAU/IAG 2015 WGCCRE)
 */
export const MARS_SEMI_MAJOR_A = 3396190.0; // Equatorial radius (m)
export const MARS_SEMI_MINOR_C = 3376200.0; // Polar radius (m)
export const MARS_FLATTENING = (MARS_SEMI_MAJOR_A - MARS_SEMI_MINOR_C) / MARS_SEMI_MAJOR_A;
export const MARS_MEAN_RADIUS_M = 3389500.0; // Volumetric mean radius (m)

export const MARS_AREOID_DATUM = 'Mars Areoid (MOLA GMM-2B)';
export const MARS_PRIME_MERIDIAN_FEATURE = 'Airy-0 Crater (0.0° Longitude)';
