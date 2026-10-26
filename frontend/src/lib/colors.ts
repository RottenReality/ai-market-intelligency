// Categorical series colours (validated palette, slots 1-3: readable together and for CVD).
export const SERIES_COLORS = ['#2a78d6', '#eb6834', '#1baf7a'] as const

// More than three overlapping series stop being readable (and distinguishable by colour).
export const MAX_RADAR_SERIES = SERIES_COLORS.length
