export interface SearchResult {
  title: string;
  description: string;
  url: string;
}

export interface TaggedUrl {
  url: string;
  is_commercial: string;
  is_educational: string;
  educational_level: string;  
  audience: string;
  source_institution_type: string;
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
