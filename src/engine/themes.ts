export interface ThemeColors {
  label: string;
  name: string;
  key: 'aurora_night' | 'aurora_warm' | 'aurora_cool';
  // Background & Ambient
  ambientGradient: string;
  bloomColor1: string;
  bloomColor2: string;
  bloomColor3: string;
  bg: string;
  bg2: string;
  fg: string;
  fg_muted: string;
  // Glass Cards & Panels
  glassCard: string;
  glassPanel: string;
  glassPanel2: string;
  glassBorder: string;
  glassShadow: string;
  glassInnerGlow: string;
  // Interactive Elements
  accent: string;
  accentGradient: string;
  accent_fg: string;
  accentGlow: string;
  button: string;
  button_hover: string;
  select: string;
  entry_bg: string;
  // Status & Verdicts
  ok: string;          // Sure
  progress: string;
  review: string;      // Review
  warn: string;        // Probably
  unsure: string;      // Unsure
  error: string;
}

export const AURORA_NIGHT: ThemeColors = {
  label: "Aurora Night",
  name: "Aurora Night (Midnight Slate)",
  key: "aurora_night",
  ambientGradient: "radial-gradient(ellipse at 20% 20%, rgba(68, 77, 128, 0.45) 0%, transparent 50%), radial-gradient(ellipse at 80% 80%, rgba(35, 45, 80, 0.5) 0%, transparent 60%), radial-gradient(ellipse at 60% 30%, rgba(76, 52, 108, 0.35) 0%, transparent 50%), #0e121e",
  bloomColor1: "rgba(107, 130, 196, 0.35)",
  bloomColor2: "rgba(120, 85, 170, 0.3)",
  bloomColor3: "rgba(60, 95, 140, 0.25)",
  bg: "#0e121e",
  bg2: "#161b29",
  fg: "#e4eaf4",
  fg_muted: "#8c97ad",
  glassCard: "rgba(25, 30, 46, 0.78)",
  glassPanel: "rgba(22, 26, 40, 0.72)",
  glassPanel2: "rgba(32, 38, 58, 0.65)",
  glassBorder: "rgba(255, 255, 255, 0.11)",
  glassShadow: "0 25px 60px -15px rgba(0, 0, 0, 0.65), 0 0 2px rgba(255, 255, 255, 0.08)",
  glassInnerGlow: "inset 0 1px 1px 0 rgba(255, 255, 255, 0.12)",
  accent: "#6b82c4",
  accentGradient: "linear-gradient(135deg, #6882c8 0%, #866bb8 100%)",
  accent_fg: "#ffffff",
  accentGlow: "0 6px 20px rgba(107, 130, 196, 0.45)",
  button: "rgba(42, 50, 75, 0.7)",
  button_hover: "rgba(55, 65, 96, 0.85)",
  select: "rgba(107, 130, 196, 0.22)",
  entry_bg: "rgba(17, 21, 33, 0.75)",
  ok: "#5ec99b",
  progress: "#6b82c4",
  review: "#e2a958",
  warn: "#e5b15d",
  unsure: "#d96e6e",
  error: "#e06868",
};

export const AURORA_WARM: ThemeColors = {
  label: "Aurora Warm",
  name: "Aurora Warm (Blush Peach & Lilac)",
  key: "aurora_warm",
  ambientGradient: "radial-gradient(ellipse at 15% 15%, rgba(255, 200, 190, 0.6) 0%, transparent 55%), radial-gradient(ellipse at 85% 25%, rgba(230, 195, 245, 0.55) 0%, transparent 60%), radial-gradient(ellipse at 50% 85%, rgba(200, 215, 255, 0.5) 0%, transparent 60%), #f8f1ec",
  bloomColor1: "rgba(247, 157, 151, 0.45)",
  bloomColor2: "rgba(228, 141, 165, 0.4)",
  bloomColor3: "rgba(185, 175, 240, 0.35)",
  bg: "#f7f1ec",
  bg2: "#efe7e0",
  fg: "#2e2520",
  fg_muted: "#7c6f66",
  glassCard: "rgba(255, 255, 255, 0.72)",
  glassPanel: "rgba(255, 255, 255, 0.62)",
  glassPanel2: "rgba(253, 246, 241, 0.78)",
  glassBorder: "rgba(255, 255, 255, 0.75)",
  glassShadow: "0 25px 55px -12px rgba(220, 170, 185, 0.38), 0 0 2px rgba(255, 255, 255, 0.9)",
  glassInnerGlow: "inset 0 1px 2px 0 rgba(255, 255, 255, 0.9)",
  accent: "#f7928e",
  accentGradient: "linear-gradient(135deg, #f79d97 0%, #e48da5 50%, #b392e2 100%)",
  accent_fg: "#ffffff",
  accentGlow: "0 6px 20px rgba(247, 146, 142, 0.42)",
  button: "rgba(255, 255, 255, 0.8)",
  button_hover: "rgba(255, 255, 255, 0.95)",
  select: "rgba(247, 157, 151, 0.22)",
  entry_bg: "rgba(255, 255, 255, 0.75)",
  ok: "#4fa876",
  progress: "#f7928e",
  review: "#d98f3b",
  warn: "#d49742",
  unsure: "#cf6666",
  error: "#d95555",
};

export const AURORA_COOL: ThemeColors = {
  label: "Aurora Cool",
  name: "Aurora Cool (Mint & Periwinkle)",
  key: "aurora_cool",
  ambientGradient: "radial-gradient(ellipse at 20% 15%, rgba(195, 210, 255, 0.65) 0%, transparent 55%), radial-gradient(ellipse at 80% 25%, rgba(185, 240, 225, 0.55) 0%, transparent 60%), radial-gradient(ellipse at 50% 85%, rgba(220, 210, 250, 0.5) 0%, transparent 60%), #eef3f8",
  bloomColor1: "rgba(107, 140, 220, 0.4)",
  bloomColor2: "rgba(110, 210, 185, 0.35)",
  bloomColor3: "rgba(165, 140, 225, 0.35)",
  bg: "#eef3f8",
  bg2: "#e4ecf4",
  fg: "#222c38",
  fg_muted: "#667485",
  glassCard: "rgba(255, 255, 255, 0.75)",
  glassPanel: "rgba(255, 255, 255, 0.65)",
  glassPanel2: "rgba(240, 246, 252, 0.8)",
  glassBorder: "rgba(255, 255, 255, 0.8)",
  glassShadow: "0 25px 55px -12px rgba(160, 185, 215, 0.38), 0 0 2px rgba(255, 255, 255, 0.9)",
  glassInnerGlow: "inset 0 1px 2px 0 rgba(255, 255, 255, 0.95)",
  accent: "#6b8cae",
  accentGradient: "linear-gradient(135deg, #7496be 0%, #7db9ae 50%, #958dc7 100%)",
  accent_fg: "#ffffff",
  accentGlow: "0 6px 20px rgba(107, 140, 174, 0.4)",
  button: "rgba(255, 255, 255, 0.85)",
  button_hover: "rgba(255, 255, 255, 0.98)",
  select: "rgba(107, 140, 174, 0.22)",
  entry_bg: "rgba(255, 255, 255, 0.8)",
  ok: "#45a37e",
  progress: "#6b8cae",
  review: "#bf8e3b",
  warn: "#c4923e",
  unsure: "#c76464",
  error: "#cc5252",
};

export const THEMES: Record<string, ThemeColors> = {
  aurora_night: AURORA_NIGHT,
  aurora_warm: AURORA_WARM,
  aurora_cool: AURORA_COOL,
};

export function getTheme(key: string = "aurora_night"): ThemeColors {
  return THEMES[key] || AURORA_NIGHT;
}
