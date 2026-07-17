// The shadow DOM cannot inherit the Streamlit host's :root variables, so the workspace component
// generates its own CSS custom properties from the shared design-token source (sirin/ui/tokens.json).
// Host chrome, native widgets, and this component therefore render identical palette/type/font values.
import tokens from "../../../tokens.json"

type ThemeName = "light" | "dark"

function themeVars(theme: ThemeName): Record<string, string> {
  const p = tokens.palette[theme]
  const ramp = tokens.spanRamp[theme]
  return {
    "--canvas": p.canvas,
    "--surface": p.surface,
    "--surface-solid": p.card,
    "--ink": p.ink,
    "--muted": p.muted,
    "--faint": p.faint,
    "--line": p.line,
    "--line-strong": p.lineStrong,
    "--brand": p.brand,
    "--brand-bright": p.brandBright,
    "--brand-wash": p.brandWash,
    "--safe": p.safe,
    "--safe-wash": p.safeWash,
    "--warning": p.warning,
    "--warning-wash": p.warningWash,
    "--risk-ink": p.riskInk,
    "--risk-wash": p.riskWash,
    "--focus": p.focus,
    "--shadow": p.shadowRaised,
    "--shadow-whisper": p.shadowCard,
    "--span-wash-low": ramp.washLow,
    "--span-wash-high": ramp.washHigh,
    "--span-line-low": ramp.lineLow,
    "--span-line-high": ramp.lineHigh,
    "--span-safe": ramp.safe,
  }
}

function typeVars(): Record<string, string> {
  const out: Record<string, string> = {}
  for (const [role, spec] of Object.entries(tokens.type)) {
    out[`--text-${role}-size`] = spec.size
    out[`--text-${role}-weight`] = String(spec.weight)
    out[`--text-${role}-line`] = spec.lineHeight
    out[`--text-${role}-tracking`] = spec.tracking
  }
  return out
}

function staticVars(): Record<string, string> {
  return {
    "--font-sans": tokens.fonts.sans,
    "--font-mono": tokens.fonts.mono,
    "--radius-card": tokens.radii.card,
    "--radius-input": tokens.radii.input,
    "--radius-panel": tokens.radii.panel,
    "--radius-pill": tokens.radii.pill,
    "--dur-fast": tokens.motion.duration.fast,
    "--dur-mid": tokens.motion.duration.mid,
    "--dur-slow": tokens.motion.duration.slow,
    "--ease-standard": tokens.motion.easing.standard,
    "--ease-entrance": tokens.motion.easing.entrance,
    ...typeVars(),
  }
}

function block(selector: string, vars: Record<string, string>): string {
  const body = Object.entries(vars)
    .map(([name, value]) => `  ${name}: ${value};`)
    .join("\n")
  return `${selector} {\n${body}\n}`
}

export const componentTokenCss: string = [
  block(".sirin-component-root", { ...staticVars(), ...themeVars("light") }),
  block(".sirin-workspace[data-theme='dark']", themeVars("dark")),
].join("\n\n")
