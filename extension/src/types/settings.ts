export interface FeatureSettings {
  showSerpOverview: boolean;
  showMetadata: boolean;
  showEnhancedSnippets: boolean;
  useSunburstVisualization: boolean;
  showHybridSnippets: boolean;
  hybridSnippetConfig: HybridSnippetConfig;
}

export interface HybridSnippetConfig {
  maxMetadataFields: number;
  maxQuestions: number;
}

// Default settings
export const DEFAULT_SETTINGS: FeatureSettings = {
  showSerpOverview: true,
  showMetadata: true,
  showEnhancedSnippets: true,
  useSunburstVisualization: false,
  showHybridSnippets: false,
  hybridSnippetConfig: {
    maxMetadataFields: 3,
    maxQuestions: 2
  }
};