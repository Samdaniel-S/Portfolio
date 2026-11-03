// Scene four's measured geometry — every number read off the supplied
// reference (section 4 image.jpg, 1600x900), which is the source of truth.
// The card sprites and the environment plate are cut from that image by
// tools/extract_s4.py; this module records where each piece goes back.
//
// Coordinates are reference-frame pixels. fitCover() maps the frame onto the
// viewport the way the plate shader does (cover: fill, centre-anchored), so
// the DOM cards and the canvas can never drift apart.

export const FRAME = [1600, 900];

// box/depth/tint come from public/projects/layout4.json (extract_s4.py); the
// titles mirror public/projects/work.json, which boot4 reads at runtime and
// tools/reskin_s4.py draws onto the screens - edit the manifest, not these.

export const CARDS = [
  { id: 'p01_timeless', title: 'Red Sea Motors',
    box: [228, 60, 375, 354], depth: 0.45,
    tint: [0.313, 0.336, 0.384] },
  { id: 'p02_game', title: 'AI Agents',
    box: [69, 235, 345, 296], depth: 0.25,
    tint: [0.246, 0.278, 0.319] },
  { id: 'p03_build', title: 'Ichthus Creative',
    box: [568, 48, 464, 286], depth: 0.6,
    tint: [0.428, 0.308, 0.309] },
  { id: 'p04_driven', title: 'Pondicherry Cabs',
    box: [992, 69, 370, 330], depth: 0.45,
    tint: [0.291, 0.279, 0.282] },
  { id: 'p05_ideas', title: 'AI Chatbots',
    box: [394, 345, 229, 209], depth: 0.8,
    tint: [0.422, 0.329, 0.261] },
  { id: 'p06_sound', title: 'Automations',
    box: [571, 384, 181, 172], depth: 0.9,
    tint: [0.348, 0.34, 0.353] },
  { id: 'p07_food', title: 'Web Apps',
    box: [701, 391, 199, 165], depth: 1.0,
    tint: [0.342, 0.239, 0.213] },
  { id: 'p08_travel', title: '3D & WebGL',
    box: [851, 382, 193, 177], depth: 0.9,
    tint: [0.274, 0.341, 0.391] },
  { id: 'p09_space', title: 'Online Stores',
    box: [992, 345, 229, 210], depth: 0.8,
    tint: [0.361, 0.3, 0.281] },
  { id: 'p10_play', title: 'XPath Forte',
    box: [1200, 223, 337, 318], depth: 0.3,
    tint: [0.469, 0.325, 0.259] },
  { id: 'p11_cleaner', title: 'KMS Global Enterprises',
    box: [135, 470, 332, 245], depth: 0.1,
    tint: [0.326, 0.35, 0.272] },
  { id: 'p12_steps', title: 'Bistro’96',
    box: [1135, 473, 334, 245], depth: 0.1,
    tint: [0.344, 0.328, 0.315] },
];

// the central figure: crop box in frame px (his lighting is baked in)
export const PERSON = { x: 718, y: 483, w: 160, h: 335 };

// the floor's lit ellipses (centre x, centre y, rx, ry) and the overhead ring,
// used by the live glints the canvas draws over the baked plate
export const FLOOR_OUT = [798, 735, 372, 80];
export const FLOOR_IN = [798, 741, 240, 57];
export const RING = [802, 34, 392, 148];

/** Cover-fit the reference frame onto a viewport. */
export function fitCover(w, h) {
  const s = Math.max(w / FRAME[0], h / FRAME[1]);
  return { s, ox: (w - FRAME[0] * s) / 2, oy: (h - FRAME[1] * s) / 2 };
}

// --------------------------------------------------------------------------
// Portrait is a recomposition, not a crop: cover-fitting a 16:9 amphitheatre
// to a phone leaves only the centre quarter on screen. The plate still cover-
// fits (floor, circle and haze survive centred), and a curated set of cards
// restacks into a column that keeps the reference hierarchy: hero screen up
// top, the small row over the figure, the two green closers at his feet.
// Entries: card index -> centre x/y (viewport fractions), width (vw fraction).
// --------------------------------------------------------------------------
export const PORTRAIT = new Map([
  [2, { cx: 0.50, cy: 0.235, w: 0.80 }],   // build
  [0, { cx: 0.235, cy: 0.385, w: 0.50 }],  // timeless
  [3, { cx: 0.77, cy: 0.39, w: 0.48 }],    // driven
  [6, { cx: 0.325, cy: 0.53, w: 0.29 }],   // food
  [7, { cx: 0.675, cy: 0.53, w: 0.29 }],   // travel
  [10, { cx: 0.20, cy: 0.815, w: 0.48 }],  // cleaner
  [11, { cx: 0.80, cy: 0.815, w: 0.48 }],  // steps
]);
