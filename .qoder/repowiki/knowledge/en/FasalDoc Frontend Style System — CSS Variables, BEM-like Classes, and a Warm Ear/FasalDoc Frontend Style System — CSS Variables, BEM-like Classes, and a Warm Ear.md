---
kind: frontend_style
name: FasalDoc Frontend Style System — CSS Variables, BEM-like Classes, and a Warm Earthy Palette
category: frontend_style
scope:
    - '**'
source_files:
    - frontend/src/styles/tokens.css
    - frontend/src/styles/global.css
    - frontend/package.json
    - frontend/index.html
---

## What system/approach is used

The FasalDoc frontend uses a **plain-CSS design-token + global stylesheet** approach built on top of React/Vite. There is no CSS-in-JS library, no component-scoped CSS framework (no Tailwind, Styled Components, etc.), and no build-time CSS processor beyond what Vite provides. All visual styling lives in two files under `frontend/src/styles/`:
- `tokens.css` — a single `:root` block declaring the entire design token surface.
- `global.css` — one large stylesheet that applies tokens to base elements, layout shells, and every screen/component via class selectors.

The project's `package.json` lists only `react`, `react-dom`, `vite`, `typescript`, and the React Vite plugin as dependencies — confirming that styling is intentionally dependency-free.

## Key files and packages

- `frontend/src/styles/tokens.css` — Design tokens (colors, fonts, radii, shadows, spacing constants).
- `frontend/src/styles/global.css` — Global resets, base typography, layout shell, and all component/screen styles (~1645 lines).
- `frontend/index.html` — Imports both CSS files so they are available app-wide.
- `frontend/package.json` — Confirms zero UI libraries; styling is hand-authored CSS.

## Architecture and conventions

### Design tokens (`tokens.css`)
All colors, fonts, radii, shadows, and sizing constants are declared as CSS custom properties on `:root`:
- **Palette**: greens (`--green`, `--green-dark`, `--green-soft`, `--green-outline`), browns (`--brown`, `--brown-dark`, `--brown-soft`), cream (`--cream`), background (`--bg`), surface (`--surface`).
- **Semantic tones**: `--danger`, `--danger-bg`, `--amber`, `--amber-bg` for error/warning states.
- **Typography**: Latin font stack defaults to `'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif`; Urdu overrides use `'Noto Nastaliq Urdu'` via an `html.lang-ur` selector.
- **Elevation & shape**: `--radius-card: 18px`, `--radius-control: 12px`; two shadow tokens `--shadow-card` and `--shadow-pop`.
- **Layout/accessibility**: `--content-width: 600px` constrains screens; `--tap-target: 48px` enforces minimum touch target size.

### Global stylesheet (`global.css`) structure
Styles are organized by section with clear comment headers: base/reset → shell → navbar → buttons → home → upload → error box → analyzing → result → confidence → follow-up chat → footer → auth screens → dashboard → camera modal → voice overlay → privacy notice → responsive breakpoints.

### Naming convention
Class names follow a **BEM-inspired flat naming scheme** without a preprocessor:
- Block: `.btn`, `.card`, `.uploader`, `.chat`, `.camera-modal`, `.voice-overlay`
- Element: `.btn--primary`, `.uploader__empty`, `.chat__messages`, `.camera-modal__capture`
- State modifiers: `.uploader--dragover`, `.confidence--high`, `.question-input__mic--active`, `.auth-field input:focus`
- Screen-level wrappers: `.screen`, `.app-shell`, `.app-main`, `.auth-screen`, `.dashboard`

There are no CSS modules, no scoped styles, and no utility-first classes — every rule targets a named class.

### Theme application patterns
- Base element reset: `* { box-sizing: border-box }`, `body` uses `var(--bg)` and `var(--ink)`, images constrained with `max-width: 100%`.
- Language switching: `html.lang-ur` selectors override font family and line-height globally, including per-component overrides like `.hero__headline` and `.diagnosis-card__name`.
- Focus accessibility: a global `:focus-visible` rule draws a green outline using `--green` and `--tap-target`-sized controls.
- Reduced motion: a `@media (prefers-reduced-motion: reduce)` block disables animations/transitions site-wide.

### Responsive strategy
Responsive behavior is handled via `min-width` media queries at `720px` and `900px` inside `global.css`. The layout shifts from single-column mobile-first grids to multi-column layouts (e.g., hero grid, steps grid, dashboard actions). Content width expands from the default `--content-width` (600px) to 680px at 900px+. No max-width breakpoints or fluid typography frameworks are used; `clamp()` is applied sparingly for headline sizes.

### Component-style reuse
Reusable visual primitives are defined once and reused across screens:
- Buttons: `.btn` base with `.btn--primary`, `.btn--secondary`, `.btn--ghost` variants.
- Cards: `.card` base with semantic variants like `.diagnosis-card`, `.advice-card`, `.action-card`.
- Inputs: shared focus ring pattern using `border-color: var(--green)` plus `box-shadow: 0 0 0 4px var(--green-outline)`.
- Modals: `.camera-modal` and `.voice-overlay` share fixed-position overlay patterns with dark backgrounds and centered content.

## Conventions and constraints

Observed conventions enforced by the codebase:
1. **All colors must come from `tokens.css` variables** — no hard-coded hex values appear outside the token file in `global.css`.
2. **Touch targets must be at least `var(--tap-target)` (48px)** — button and input components consistently apply this minimum height.
3. **Card radius is uniform** — `--radius-card: 18px` is used for cards, image frames, and containers; control inputs use `--radius-control: 12px`.
4. **Language-aware typography** — when `html` has class `lang-ur`, Urdu font stacks and larger line-heights are applied globally and overridden per component where needed.
5. **Screen content is centered and constrained** — `.screen` wraps page content with `max-width: var(--content-width)` and `margin-inline: auto`.
6. **Animations respect user preference** — `prefers-reduced-motion` kills all animations and transitions.
7. **No external CSS framework** — the absence of Tailwind, Bootstrap, or similar in `package.json` means all styling is authored manually in `global.css`.
8. **Component styles live in the global stylesheet, not per-file** — there are no component-scoped CSS files; all styling is centralized in `global.css`.