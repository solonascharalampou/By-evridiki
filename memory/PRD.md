# BY EVRIDIKI – Bakery Website PRD

## Original Problem Statement
The user has a bakery website and wants to fix layout/design issues, mobile view problems, and perform code cleanup. They also want to add pictures to their existing menu cards. The user's goal is to keep the current mobile menu style but improve the overall visual quality.

## Product Requirements
- Fix layout, design, and mobile responsiveness of `index.html`
- Add image slots to the menu cards and integrate images provided by the user
- Optimize and clean up the existing HTML/CSS/JS single-file structure

## Architecture
- **Type**: Vanilla HTML/CSS/JS (monolithic single-file)
- **Main file**: `/app/frontend/public/index.html` (~2321 lines)
- **Custom images**: `/app/frontend/public/images/img01.png` through `img16.png`
- React layer is bypassed; webpack-dev-server serves public/ directly
- **Patched file**: `/app/frontend/node_modules/react-scripts/config/webpackDevServer.config.js`

## What's Been Implemented

### Session 1 (Previous Fork)
- Fixed frontend dev server crash: patched react-scripts webpack-dev-server for `setupMiddlewares` incompatibility
- Applied initial layout/design structural patches
- Verified frontend running via screenshot

## What's Been Implemented

### Session 1 (Previous Fork)
- Fixed frontend dev server crash: patched react-scripts webpack-dev-server for `setupMiddlewares` incompatibility
- Applied initial layout/design structural patches
- Verified frontend running via screenshot

### Session 2 (June 22, 2026)
- Received and extracted user's zip of 16 custom bakery photos
- Renamed images from screenshot filenames to `img01.png`–`img16.png`
- Fixed `safeImageUrl()` to accept relative paths starting with `/`
- Changed image rendering from JavaScript lazy-load to direct inline `background-image` CSS
- Mapped all 16 user photos to correct menu items via `MENU_IMAGE_OVERRIDES`
- Fixed webpack-dev-server caching by restarting frontend supervisor

### Session 3 (June 22, 2026 — Backend)
- Built FastAPI backend with MongoDB (motor) for product management
- Endpoints: GET/POST/PUT/DELETE `/api/products`, PATCH `/api/products/{id}/toggle-pop`, POST `/api/admin/login`
- JWT authentication for admin routes (48-hour tokens)
- Auto-seeded 31 default products on startup if DB is empty
- Updated Chef's Portal login to use `/api/admin/login` (JWT-based)
- Updated all portal product operations (add/edit/delete/toggle-pop) to use API
- Products now persist across devices and browsers via MongoDB
- Chef's Portal: login, product list with thumbnails, add/edit/delete — all working

## Backlog / Future Tasks

### P1
- Verify/adjust Savoury section scroll (Peinirli and Sandwich visible)
- Test all category tabs (Cakes, Desserts, Cookies, Bakery, Frozen, Custom)
- Verify Greek language (`ΕΛ`) toggle still works with images

### P2
- Consider adding photos for items without photos: Brownie Cheese, Cinnamon/Orange Cookies, Focaccia, Bagel, Pasta, Frozen items, Custom Cakes
- Code cleanup / formatting pass on index.html if needed

## Menu Items Without Photos (can be added later)
- Brownie Cheese 90g
- Butter Almond Kourabiedes
- Cinnamon Cookies 200g
- Orange Cookies 200g
- Rustic Olive Pie 300g
- Focaccia 179g
- Thessaloniki Bagel 100g
- Oven-Baked Pasta 400g
- All frozen items except through shared photos
- Custom Celebration Cakes

## Key Technical Notes
- DO NOT convert to React app
- `public/` directory is served directly by webpack dev server
- After changing `index.html`, restart frontend supervisor if changes don't appear: `sudo supervisorctl restart frontend`
- Images are in `/app/frontend/public/images/` and served at `/images/imgXX.png`
- `safeImageUrl()` accepts: `data:image/`, `https?://`, and `/` (relative) paths
