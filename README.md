# SAMDANIEL — cinematic portfolio

The portfolio of Samdaniel, graphic & brand designer at Ichthus Creative, as
a cinematic scroll film. All WebGL, no frameworks and no build step. (Built on
the cinematic portfolio in `../cinematic-portofilo-main`, re-lettered and
re-written for this owner; that folder is left untouched.)

**Scene 1 — the opening.** Black screen → the man walks out of the dark → the
SAMDANIEL wordmark materialises behind him → chips, arrows and dots snap into
place → header draws itself in → the composition settles and breathes.

**Scene 2 — the creative universe.** The supplied film, played as the section:
the visitor scrolls into it, it arrives from black, and a veil breathes over
the 10-second loop point so the wrap is never seen as a cut. Decoding stops
whenever the section is off screen.

**Scene 3 — the time machine.** A warm black room → the timeline rail draws
itself → a giant clock resolves → six year cards arrive → the floor mechanism
turns → and then the visitor takes control: moving the cursor swings the clock
hand across 2021–2026, and whichever year it points at lights up.

## Where your content lives

| What | File |
|---|---|
| Name, roles, chips, nav, page title, every caption, footer links and © | `index.html` |
| The hero wordmark's letters (and its width : height) | `src/scene/type.js` (`TEXT`, `TARGET_RATIO`) |
| The six journey cards (2021–2026) | `src/scene3/layout3.js` (`YEARS`) |
| The twelve project screens: titles, categories, years, artwork | `public/projects/work.json`, then `python tools/reskin_s4.py` |
| The finale's giant wordmark (baked into the plate) | `tools/reletter_fin.py` (`WORD`), then run it |
| The finale's figure in front of the wordmark | `assets_src/fin_portrait.png`, then `python tools/place_fin.py` |
| The finale's second frame | `public/fin/frame2.jpg` (drop-in) |

## Before publishing

- **Contact details** in the footer bar of `index.html` are placeholders,
  matching the main portfolio's `src/content.js`: `hello@yourdomain.com`,
  Instagram `yourhandle`, bare Behance and LinkedIn links.
- **Project artwork.** The twelve screens show category motifs until you add
  real work: drop a landscape image in `public/projects/art/`, set its path as
  that project's `image` in `work.json`, re-run `python tools/reskin_s4.py`.
- **Journey copy** follows the main portfolio's journey and awards, which are
  still partly placeholders there too.

## Replacing the figure

- **Hero (walking figure):** done. `assets_src/v1.mp4` is now the owner's own
  walk, generated with Higgsfield. It came in at 1080×1920, 30 fps, and the
  site uses frames 0–171, the stretch before the feet leave the frame. To
  replace it, see *Replacing the videos later*.
- **Finale (portrait):** done. The figure in front of the wordmark is the
  owner's studio portrait, `assets_src/fin_portrait.png` (white backdrop).
  `python tools/place_fin.py` cuts it out, grades it into the red scene (rim
  light, darker floor) and writes `public/fin/man.png` + `fin.json`. To
  replace it, drop in another shot on a plain white backdrop, cut at the thighs
  or lower, and re-run; `HEAD_TOP` / `HEAD_X` at the top of the script place
  him. `Footer image.jpg` is still the source of the plate (wordmark + fog).
- **Finale frame 2:** done. `public/fin/frame2.jpg` is the owner's Ferrari shot
  (source PNG in `assets_src/frame2_ferrari.png`). Replace it, or delete it
  to end on a single frame.

## Not in the repository

The template's source material - the original model's footage, the GIREESH
artwork, the section reference images (`Footer image.jpg`, `section * image.jpg`,
`assets_src/v2.mp4`, `v3.mov`, `ref_*.jpg`, `assets_src/original_model/`) - stays
on the owner's machine and is never published (listed in `.git/info/exclude`).
The site does not load any of it; only the `tools/` that cut assets from those
references need it, so they run on that machine alone. Everything the site
serves is in `index.html`, `src/` and `public/`.

## Live site

GitHub Pages serves the `main` branch root:
https://samdaniel-s.github.io/Portfolio/ - push to `main` and it redeploys.
Every asset path is relative, and `.nojekyll` makes Pages serve the files as
they are.

## Run it

```bash
python tools/serve.py 5174
```

then open http://localhost:5174 (5173 is left to the main Vite portfolio).
Any static file server works in production — there is nothing to compile.

Review helpers (dev only):

- `?t=3.2` starts the timeline at 3.2s; `?t=end` jumps to the settled hero.
- `window.__shot('name')` in the console saves the current canvas to `shots/`.
- `window.__tune('wear', 0.5)` live-adjusts letter distressing
  (`wear`, `wearGain`, `wearScale`).

## How the transparent video works (the part people ask about)

The original footage is a person on a white studio backdrop. The white is
removed **offline** by `tools/matte.py` (border-connected background modelling,
fractional-coverage estimation for hair, motion-adaptive temporal smoothing),
and the result is packed into a normal H.264/VP9 video that is **double width:
colour on the left half, alpha matte on the right half**.

At runtime the WebGL compositor samples both halves and rebuilds true
per-pixel transparency. This works in every browser — including Safari, which
supports neither WebM alpha nor Windows-encodable HEVC alpha — and it means
there is never a white rectangle, ever.

The compositor also does the integration work: film grain, vignette, a red
ember behind the type, a contact shadow cast onto the letters, red rim light
gated to the rows where the wordmark actually passes behind him, and a
dissolve at the video's loop point so the cut is never visible.

## Replacing the videos later

1. Drop the new file into `assets_src/` (e.g. `v1.mp4`). It needs a
   white/light backdrop, a fixed camera, the subject roughly centred, and the
   feet in frame. Any size from 720×1280 up and any frame rate works; the
   clip's own frame rate is kept.
2. Adjust `CLIPS` in `tools/build_media.py` if the name or usable frame range
   changed. The two spare clips from the original shoot are still listed there,
   commented out, with working matte presets in `tools/matte.py`.
3. Rebuild (`--clips` skips the textures and the scene-2 film):

   ```bash
   python tools/build_media.py --clips
   python tools/track.py
   ```

   A new clip usually needs its preset in `tools/matte.py` re-tuned:
   `lo`/`hi`/`bg_thr`/`fg_thr` for the backdrop, `pinhole` for shoe shine,
   `drop_islands` and `floor_guard` for floor marks. Test on single frames
   with `frame_alpha` first; a full pass at 1080p takes minutes.

That regenerates `public/media/*` (packed clips, posters, `manifest.json` with
per-frame subject tracking — the site anchors the man by his *feet*, not by the
video rectangle, which is why his scale holds while he walks toward camera).

## Scene 2: the film, and the parked procedural version

The section plays `public/media/universe.mp4` — the reference footage with one
edit: its baked "PRODUCT DESIGNER" caption is filled out by
`tools/clean_film.py` (tracked frame to frame, since it rides the camera move,
and inpainted stroke by stroke), re-encoded at CRF 18 with the audio dropped
and faststart. The owner's role returns as a live DOM caption in that corner
(`.universe__role`). `src/scene2/boot2.js` is the whole runtime: entrance,
loop-seam veil, visibility-gated decoding.

Everything below describes the PROCEDURAL WebGL room built to the same
reference (universe.js, cards.js, ribbon.js, particles.js, shaders2.js). It is
parked, not deleted — restore boot2.js's old implementation to bring back the
live, pointer-reactive variant.

Everything is one WebGL canvas, pinned with `position: sticky` inside a
190svh section so there is scroll travel for the camera dolly.

**The twelve cards are reconstructions, not a flat collage.** Each card's
centre, apparent width and aspect were measured off the supplied artwork; depth
is then *inferred* from apparent size (a card drawn large in the poster is a
card near the camera) and the world position is solved so the projection puts it
back where the poster had it. That is why parallax, the dolly and the hover tilt
all behave correctly — the depths are physically consistent rather than guessed.
It also re-fits at any viewport aspect instead of cropping.

**The materialisation is one event.** There is deliberately no per-card stagger
anywhere: `mat` is a single scalar every card reads. The only per-card variation
is in *how* each one travels once it already exists, which reads as choreography
rather than as a queue of fades. The sequence is time-based, triggered when the
section scrolls into view — tying it to scroll offset would let a fast flick
skip the moment the brief cares about most, and a slow drag would smear it into
exactly the one-by-one reveal it is not supposed to be.

**The ribbon is a light-painting, not a shape.** Rebuilt against the supplied
motion reference: a parametric HEAD travels the room (an orbit around the figure
with slower incommensurate drifts layered on, so the path never visibly
repeats), and the strip is rebuilt every frame from the last ~7.5 seconds of
where the head has been. The trail cools white → salmon → dark red as it ages;
the length is what lets it close loops and cross itself. Because the trail
weaves in depth, the strip carries per-vertex world z and is submitted in three
depth-gated passes — behind the figure, between him and the card shell, and over
the cards. The head also lights the room: the wall blushes and the floor catches
a streak beneath it, and the embers near it flare.

**The figure is only a shape.** His silhouette was lifted from the artwork with
grabCut; his red rim light is generated at runtime from the core's position, so
he responds to the scene instead of carrying a baked highlight from a
photograph. That is what stops him reading as a cut-out.

Cost: ~0.3 ms of CPU per frame for 28 quads, 900 embers, and the trail rebuilt
every frame.

### Tuning scene 2

- `window.__uni` — the live scene (cards, pointer, hovered index).
- `window.__shot2('name', 9)` — render at t = 9s and save to `shots/`.
- Beats live in `src/scene2/timeline2.js`; card geometry in `cards.js`.

## Scene 3: how it is put together

WebGL draws the room, the reflective floor and its turning ring mechanism, the
clock, the timeline rail and the figure. The six year cards are **DOM**, unlike
scene two's tool cards — each carries real body copy that has to stay crisp,
selectable and reachable by a screen reader, and each is a real `<button>`, so
keyboard and touch support come almost free. They are positioned by JS from the
same fitted geometry the canvas draws with, so the two layers cannot drift.

**The timeline is a measured circle.** The six nodes were located by detecting
their glow in the reference, and a least-squares circle fit through them closed
to within ±3px — so it is rebuilt as a real arc rather than a spline through
eyeballed points.

**The cursor→year mapping is the section.** Raw cursor-x would be wrong: the
timeline descends across the frame, so the same x means different years
depending on how high the pointer sits. The cursor is instead projected onto the
polyline through the card centres, which yields a CONTINUOUS position along the
timeline. Verified: aiming at each card centre reads exactly 0…5; halfway
between two cards reads exactly x.5; and aiming 160px ABOVE the rail still picks
the right year, which is the case plain cursor-x gets wrong. The hand reads that
continuum (so it can sit between years and moves with inertia), while the cards
read its rounded value. The hand sweeps 113.5° from 2021 to 2026.

**The clock is the reference's clock.** A shaded ball pivot with two hands
hanging from it like a set of dividers 74° apart — the beam leg carrying the
bright primary hand, and an ornate companion with a pierced screw-head ornament
partway down and a needle tip. The beam is a cone with a hot core that lands as
a red flood exactly on the active year's node (`uTarget`), so the clock reads
as PROJECTING light into the timeline rather than merely pointing at it.

**The figure is lit the reference's way** — not brightened. A warm pool on the
floor behind him (the room pass knows where he stands via `uFig`), rim light
wrapping both edges, a faint floor bounce up his legs, and the nearest ring
arcs drawn in a separate pass IN FRONT of his shoes so he stands inside the
floor mechanism, not on a printed backdrop.

**He stands in front of his journey.** On a desktop frame the figure and the
near ring arcs render on a second, transparent WebGL canvas stacked OVER the
DOM card deck — slightly left of centre, a step nearer than the ring centre,
his silhouette crossing the card edges rather than sitting buried behind them.
The layer is `pointer-events: none`, so the cards under him stay hoverable and
clickable. Portrait keeps him on the main canvas behind the single staged card
(there the card is the content), and a browser that refuses a second context
simply falls back to the same.

**Control is handed over, not switched.** During the intro the sequence owns the
hand; afterwards the pointer does. The two are blended on a `handAuthority`
ramp, so the hand never jumps at the moment the scene goes live.

**Portrait is a different composition**, not a scaled one: mapped straight onto
a tall screen the arc collapses into a 60px band with all six cards on top of
each other. On a phone the timeline stands up — the years become a vertical rail
of tap targets down the left, and one card at a time holds the stage beside it.

Cost: ~0.1 ms of CPU per frame (six fullscreen shader passes).

### Tuning scene 3

- `window.__chrono` — the live scene; set `.targetU` (0–5) to drive the hand.
- `window.__shot3('name', 9)` — render at t = 9s and save to `shots/`.
- Beats in `src/scene3/timeline3.js`; all measured geometry in `layout3.js`.

## Scene 4: how it is put together

The project universe is the supplied reference image rebuilt as living
layers, so fidelity is exact by construction rather than by imitation.
`tools/extract_s4.py` cuts the reference apart: the twelve project screens
become sprites (each cropped on its measured outline plus its own rim glow,
with the figure's occlusion inpainted and any nearer card's overlap removed,
so nothing ghosts when the deck moves), the creator becomes a matted sprite
with the reference's lighting baked in, and what remains — floor, wet
reflections, circle, overhead structure, corner slabs — becomes the
environment plate.

**The screens show the owner's work.** `tools/reskin_s4.py` keeps everything
about each sprite that belongs to the room (outline, curvature, rim light,
trims) and replaces what is on the glass: each project from
`public/projects/work.json` is drawn flat in the reference's screen grammar
(mark and nav, serif title, meta line, EXPLORE pill, art from the right) and
projected into the screen's outline by homography, two planes for the bowed
screens. The art is the project's own image when `work.json` names one, a
category motif in the scene's crimson/amber until then. Sprites are written at
2x for crisper titles. The outlines in `extract_s4.py` trace each screen's rim
(re-measured for this: the first pass sat up to ~80px off on tilted screens),
and the clean faces the re-skin starts from are kept in
`assets_src/projects_ref/`. `boot4` reads the card titles from the same
manifest.

**The canvas lights the plate rather than painting a room** (`F4_ROOM`): a
staged blackout wakes zone by zone — overhead structure first, floor circle
ignition with a travelling spark, full exposure only once the deck has
assembled — plus live extras riding the baked pixels: breathing glints on the
floor ellipses, rim shimmer on the ring, a wet-floor grain that keeps the
reflections moving, pointer parallax and a scroll dolly.

**The cards are DOM buttons wearing the sprites**, placed through the same
`fitCover()` mapping the shader samples with, so canvas and DOM cannot
drift. The entrance is one system: depth-sorted far row first, each card
rising from below with rotation, blur→sharp and a small overshoot
(`popEase`), then an infinite dephased float. Pointer moves the whole
universe by depth — near flanks hardest, the far row least, the deck yawing
a couple of degrees, the figure countering — and hovering a card lifts it
toward the camera while its siblings ease back.

**Portrait is a recomposition** (`layout4.PORTRAIT`): the plate still
cover-fits so the floor circle and figure survive centred, and a curated
seven-card column keeps the hierarchy — hero screen up top, small row over
his shoulders, the two green closers at his feet.

### Tuning scene 4

- `window.__gallery` — the live scene; `.gallery.dolly`, `.gallery.par`.
- `window.__shot4('name', 9)` — render the environment canvas at t = 9s.
- Beats in `src/scene4/timeline4.js`; sprite boxes + depths in `layout4.js`.

## The finale: how it is put together

The closing shot IS the reference (`Footer image.jpg`), split into breathing
layers by `tools/extract_fin.py`: the smoking man is GrabCut-matted out of
the artwork (his pose, grade, rim and cigarette are the reference's own
pixels — the drifting smoke deliberately stays with the background), and
everything else — the giant wordmark, the red fog — becomes the plate, with
the man diffusion-filled away and the baked captions blanked so the live DOM
set can type itself in. Both layers share one cover mapping, so they can
never drift.

**The wordmark is re-lettered** by `tools/reletter_fin.py` (run after
`extract_fin.py`): the reference's word is read from its own paint (red-channel
local contrast sorts stroke from gap at every height), the whole word box and
the man are replaced by fog filled from the gaps, and SAMDANIEL is set in Anton
on the old cap line and baseline, lit by a smooth fit of the old strokes'
cream→crimson fall-off and wearing a crackle tile cut from their clean
interiors. Because the old word is gone from behind him, `extract_fin.py`'s
matte is strict about colour above the baseline: he is neutral, the backdrop
is red or cream, so no sliver of the old letters rides along in `man.png`.

**The figure is the owner's own** since `tools/place_fin.py` (run after
`extract_fin.py`, which still writes the reference model into `man.png`): a
studio portrait matted off its white backdrop, graded down into the scene's
exposure, rimmed in the wordmark's light (cream-pink high, crimson low) and
sunk into the black of the lower frame past its edge.

**The reveal is staged in the plate shader** (`F6_PLATE`): a dim ember world
comes up first (uGlow), then the bright content — gated by its own
luminance — surfaces through the fog and sharpens from a five-tap blur
(uWord): the title card emerges through smoke rather than fading in. A slow
breathing pulse, a whisper of drifting live fog and film grain keep the
photograph from freezing. The man rises in on the front canvas with a few
pixels of parallax against the plate; a quiet red veil drifts over him.
The captions, quote and functional row (contact, socials, copyright) hold
the edges, exactly where the reference puts them.

**Frame 2.** The footer holds a second still: past the settled first frame,
extra scroll room (the section is 240svh, pinned) slides the supplied image
in from the LEFT — damped scroll progress through a smootherstep, entering
blurred and darkened, its leading edge shadowing frame 1, which is nudged
aside and dimmed beneath; the functional row stays on top throughout. The
still is `public/fin/frame2.jpg` (the loader also accepts
`footer 2nd image.jpg` in the project root); replace the file and reload to
swap the ending — nothing else to wire.

### Tuning the finale

- `window.__finale` — the live scene; `window.__shot6('name', 7)`.
- Beats in `src/scene6/timeline6.js`; the man's box in `public/fin/fin.json`.

## Layout truth

Every position in `src/scene/layout.js` was **measured off the supplied
reference art**, not eyeballed: word ink box 3.31%→96.75% × cap 27.0%→80.2%,
chip and dot positions likewise. The wordmark is rendered live (self-hosted
Anton, horizontally solved to a width:cap ratio — 3.6 for SAMDANIEL; the
reference's 7-letter word measured 3.121, which would squeeze nine letters to
spindly stems) into a glyph atlas, surfaced with a seamless distress tile
synthesised from the supplied artwork's own scratches (`public/tex/grunge.png`).

## Map

```
index.html                 markup: header, furniture, boot veil
src/main.js                boot gate, clock, cues, pointer, reduced-motion
src/scene/timeline.js      every beat of the opening, in seconds
src/scene/layout.js        reference-measured geometry, responsive fitting
src/scene/type.js          glyph atlas + per-letter metrics
src/scene/furniture.js     DOM layer wiring (welcome, chips, arrows, dots, rule)
src/gl/stage.js            draw order + composition parameters
src/gl/shaders.js          plate / letters / figure / shadow / post GLSL
src/lib/clip.js            packed-video element, loop-seam dissolve
src/scene2/boot2.js        scene-2 lifecycle: visibility, pointer, scroll
src/scene2/universe.js     draw order and composition parameters
src/scene2/cards.js        measured card layout + per-frame pose
src/scene2/ribbon.js       the red energy curve, split around the figure
src/scene2/particles.js    embers and floating debris
src/scene2/timeline2.js    every beat of the universe sequence
src/gl/shaders2.js         environment / ring / card / ribbon / ember GLSL
src/lib/mat4.js            perspective + model matrices
tools/matte.py             background removal (offline)
tools/build_media.py       media pipeline: mattes, textures, manifest
tools/track.py             per-frame subject boxes into the manifest
src/scene6/boot6.js        finale lifecycle, captions, parallax
src/scene6/finale.js       finale canvases: staged plate + matted man + veil
tools/extract_fin.py       cuts the footer reference into plate + man
tools/reletter_fin.py      sets the owner's name into the finale plate
tools/place_fin.py         mattes + grades the owner's portrait into the finale
src/scene6/timeline6.js    every beat of the closing shot
src/scene4/boot4.js        scene-4 lifecycle, entrance, parallax, hover
src/scene4/gallery.js      scene-4 canvas: plate lighting + post
src/scene4/layout4.js      sprite boxes, depths, portrait recomposition
src/scene4/timeline4.js    every beat of the project-universe sequence
src/scene3/boot3.js        scene-3 lifecycle, cursor->year mapping, card DOM
src/scene3/chrono.js       draw order and composition parameters
src/scene3/layout3.js      measured arc, card placement, timeAt() mapping
src/scene3/timeline3.js    every beat of the time-machine sequence
src/gl/shaders3.js         room / clock / rail / figure GLSL
tools/extract_logos.py     lifts the 12 tool logos out of the section-2 art
tools/extract_figure.py    lifts the central figure's silhouette
tools/extract_s3.py        lifts the 6 year photos + figure from the section-3 art
tools/extract_s4.py        cuts the section-4 reference into plate + sprites
tools/reskin_s4.py         puts the projects in work.json on the 12 screens
tools/clean_film.py        lifts the baked job title out of the scene-2 film
tools/extract_s5.py        cuts the section-5 reference (section removed; kept to regenerate)
tools/encode_cert.py       mattes + packs the walking man (section removed; kept to regenerate)
tools/serve.py             dev server (no-store + screenshot endpoint)
assets_src/                originals, untouched
```

Re-extract scene-2 artwork with:

```bash
python tools/extract_logos.py
python tools/extract_figure.py
python tools/extract_s3.py
```

## Two hard-won environment notes

`overflow-x: hidden` on body promotes it to a scroll container, which silently
breaks every `position: sticky` pin in the scenes — the canvas scrolls away and
leaves bare background. It is `overflow-x: clip` for exactly that reason; do not
"simplify" it back.

## A note on the GLSL

The shaders live inside JS template literals, so a stray backtick in a comment
silently ends the string and takes the whole module graph down. If the page goes
blank after a shader edit, syntax-check first:

```bash
for f in src/**/*.js; do cp "$f" /tmp/c.mjs && node --check /tmp/c.mjs || echo "$f"; done
```

Further sections continue below the universe: add them inside `main.flow` with
a solid background and normal document flow takes over from there. The hero is a
fixed full-viewport layer behind `.flow`, and its video decoding is stopped
automatically once it scrolls out of view.
