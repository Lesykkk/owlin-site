---
paths:
  - "frontend/src/**/*.css"
  - "frontend/src/**/*.jsx"
---

# Frontend colors

All colors live in `frontend/src/index.css` as CSS variables. In components and CSS modules use
`var(--…)` only, never hex or `rgb()` values.

## Text, from brightest to dimmest

| Variable | Value | Use for |
|---|---|---|
| `--color-text-strong` | `#ffffff` | most important text: titles, buttons, active menu item |
| `--color-text` | `#f0edf9` | main body text, the default |
| `--color-text-soft` | `#c9c2dc` | secondary but readable: feature lists, badges, chips, steps |
| `--color-text-muted` | `#a39bb8` | descriptions, subtitles, helper explanations |
| `--color-text-faint` | `#796f8a` | quietest: small captions, labels, game names, footer |

The less important the text, the dimmer the level. Take the nearest level, do not skip one for a shade.

## Accent and status

| Variable | Value | Use for |
|---|---|---|
| `--color-accent` | `#a585ef` | brand purple: "Owlin", active elements, links |
| `--color-accent-soft` | `#c3a5fa` | lighter accent: hover, icons, labels on accent |
| `--color-eyebrow` | `#bba6e6` | section eyebrows only ("Made for ETS2 & ATS") |
| `--color-danger` | `#ff718f` | errors, rejected, destructive actions |
| `--color-notice` | `#ffd60a` | background of the site-wide announcement strip (free promotions) |
| `--color-notice-text` | `#0a0a0a` | text on the announcement strip |

## Borders and lines

| Variable | Value | Use for |
|---|---|---|
| `--color-line` | `#272037` | dividers and calm outlines (the common choice) |
| `--color-line-soft` | white 5% | thinnest rules (games strip) |
| `--color-border-subtle` | white 7% | thin border of cards and badges |
| `--color-border` | `#4a3870` | outline of interactive elements: fields, buttons, pickers |
| `--color-border-active` | `#5a3f8a` | selected / highlighted element |
| `--color-border-accent-soft` | accent 30% | purple border on hover or selection |
| `--color-danger-soft` | danger 30% | border of an error / rejected element |

## Backgrounds

| Variable | Value | Use for |
|---|---|---|
| `--color-bg` | `#07050d` | page background |
| `--color-panel` | `#100c19` | panels |
| `--color-surface-deep` | `#0c0916` | darkest surface: header, screenshot window |
| `--color-surface-raised` | `#1d1630` | raised surface: upload zone, profile header |
| `--color-fill-subtle` | white 1.6% | barely visible fill of cards and fields |
| `--color-scrollbar` | `#3b3254` | scrollbar thumb |
| `--color-scrollbar-hover` | `#55477a` | scrollbar thumb on hover |
| `--gradient-card` | gradient | card background |
| `--gradient-button` | gradient | primary purple buttons |

## Rules

1. Need a color? Look in the tables first. If one fits, use it. If none fits, add a variable to
   `index.css` named after its role, instead of writing a hex value in a module.
2. A local `rgba(...)` is allowed only for a one-off effect (shadow, glow, spinner), never for a color
   that repeats.
3. Name variables by role (`text-faint`, `border-active`), not by shade.
4. When a value in `index.css` changes, update the tables here in the same commit.
