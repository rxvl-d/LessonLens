export interface FeatureSettings {
  showSerpOverview: boolean;
  showMetadata: boolean;
  showEnhancedSnippets: boolean;
  useSunburstVisualization: boolean;
}

// Default settings
export const DEFAULT_SETTINGS: FeatureSettings = {
  showSerpOverview: true,
  showMetadata: true,
  showEnhancedSnippets: true,
  useSunburstVisualization: false,
};