# String AI website

Static GitHub Pages site for `stringaiapp.com` (`CNAME`). No framework build or hosting migration. `consent/`, `reset-password/`, existing videos, and legal/store destinations retain their existing roles.

## Screenshots

The landing page uses the approved September 12 cream/charcoal/gold-ring posters: lesson once in the hero, then mission, piece, progress, habit, and library once in the gallery. The poster already contains its device frame and gold halo, so the website adds neither another frame nor rotation/cropping.

Source owner: `../string-ai-app/store-assets/screenshots/compose.mjs` and its canonical `out/play-phone/{en,ko}/` PNGs. The phone canvas is 1080×1920; the same approved six-panel design serves the website. Website files are derived, never alternative UI illustrations.

```sh
python3 scripts/sync-store-images.py
python3 -m http.server 8090 --bind 127.0.0.1
```

`sync-store-images.py` uses the existing local Pillow/WebP runtime. It reads twelve canonical PNGs, records their SHA-256 hashes in `assets/screenshots/manifest.json`, and generates 432×768 and 864×1536 WebP variants. Both sizes preserve the exact 9:16 ratio and only downsample. Quality 90 retains UI text; the browser chooses a variant through `srcset`/`sizes`. One shared PNG serves the app icon. Content-hashed filenames permit caching and change when pixels change; stale derivatives in the generator-owned directory are removed on regeneration.

The script also owns the marked image map and six static image URLs in `index.html`. Do not edit generated filenames by hand. `applyLang()` changes text, alt text, `src`, and `srcset` together. Default with JavaScript is English; the Korean HTML and Korean images remain coherent without JavaScript. Localized poster text and localized source app captures are separate: a legacy source lacking a Korean capture remains its documented original until a real replacement is captured.

## September 19 completion

- All six panels use the approved final gold-ring layout. Duplicate feature-image crops and embedded base64 images were removed; landing HTML fell from 869,392 to 36,773 bytes.
- Final Chromium checks at 320 and 1280 pixels in English and Korean confirm six unique panels, correct language image selection, the unchanged 9:16 image ratio, and no horizontal overflow. The earlier September 12 layout also passed at 390 and 768 pixels.
- The lesson uses the approved student photo and actual iPhone Done pixels. The composition recipe and original source hashes live in the app repository; no replacement app controls were invented. All 12 canonical PNG hashes are recorded in the website manifest.
- The approved Korean and English privacy copy distinguishes temporary lesson media from Practice Room videos the user saves on-device. No performance audio or video is uploaded by this image update.
- Publishing follows this repository's existing GitHub Pages main-branch deployment. This does not submit app builds, store screenshots, or OTA updates.

## 1.0.4 copy preparation — 2026-10-31

The landing source now describes four classes, lesson questions and unit checks, teacher-assigned class homework, and My Scores import/edit/full-score/split-piece flows. Korean uses 5가지 연주 요소; English retains axis. The app repository mirror is `../string-ai-app/docs/site/index.html`.

This is a local preparation commit, not a publication. Class homework and the latest My Scores flows must be available in the released app before publishing these claims. Run the app repository’s `legal:review-gate -- --strict` before a website push. Store text uploads belong to the submission session.

Existing screenshots and their manifests are unchanged. Capture actual 1.0.4 screens only after that version is ready; the shot list and code evidence are in `../string-ai-app/docs/STORE_WEBSITE_REFRESH_1.0.4.md`. Do not run the image sync script during this copy-only update.
