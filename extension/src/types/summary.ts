export interface SearchResult {
  title: string;
  description: string;
  url: string;
}

export interface ConfidenceLabel {
  label: string;
  confidence: number;
}

export interface TaggedUrl {
  url: string;
  is_commercial: ConfidenceLabel;
  is_educational: ConfidenceLabel;
  educational_level: ConfidenceLabel;  
  audience: ConfidenceLabel;
  source_institution_type: ConfidenceLabel;
}

// List of all possible fields as strings
export const SummaryAllFields = [
  "is_commercial",
  "is_educational",
  "educational_level",
  "audience",
  "source_institution_type"
];


export interface AttributeImportance {
  attribute: string; 
  importance : number;
}

export interface Summary {
  attribute_importances: AttributeImportance[];
  tagged_urls: TaggedUrl[];
  query_type: string;
}

export interface MetadataResult extends SearchResult {
  assesses: string;
  teaches: string;
  educational_level: string[];
  educational_role: string[];
  educational_use: string[];
  learning_resource_type: string[];
}

export interface EnhancedSnippetResult extends SearchResult {
  content: string;
  enhanced_snippet: string;
}

interface HybridSnippetConfig {
  maxMetadataFields: number;  // How many metadata fields to show
  maxQuestions: number;       // How many Q&A pairs to show
  priorityFields: string[];   // Which metadata fields to prioritize
}

interface HybridSnippetResult extends SearchResult {
  metadata: MetadataResult;
  enhancedSnippet: EnhancedSnippetResult;
}