export interface Summary {
  educational_levels: { [key: string]: number };
  resource_types: { [key: string]: number };
  topics: { [key: string]: number };
}

export interface SearchResult {
  title: string;
  description: string;
  url: string;
}

export interface TaggedUrl {
  // Base fields (always present)
  url: string;
  is_commercial: string;
  is_educational: string;
  source_institution: string[];
  educational_level: string;  
  subject?: string;
  audience?: string;
  source_institution_type?: string;
  learning_resource_type?: string[];
  
  // Worksheet specific
  is_worksheet?: string;
  has_step_instructions?: string;
  includes_solutions?: string;
  
  // Experiment specific
  is_experiment?: string;
  contains_demonstration_terms?: string;
  contains_hands_on_terms?: string;
  contains_equipment_mentions?: string[];
  
  // Teaching method specific
  learning_type_coverage?: string[];
  differentiation_level?: string;
  includes_visual_aids?: string;
  teaching_method_type?: string[];
  difficulty_adjustment?: string;
  
  // Assessment specific
  assessment_type?: string;
  includes_visuals?: string;
  scoring_guide_included?: string;
  question_types?: string[];
  time_requirement?: string;
  
  // Didactic concept specific
  includes_analogies?: string;
  teaching_approach?: string[];
  visualization_tools?: string;
  complexity_level?: string;
  curriculum_alignment?: string;
  
  // Modeling activity specific
  model_type?: string[];
  activity_duration?: string;
  materials_required?: string;
  student_interaction_level?: string;
  creativity_elements?: string[];
}

// List of all possible fields as strings
export const SummaryAllFields = [
  "is_commercial",
  "is_educational",
  "educational_level",
  "subject",
  "audience",
  "source_institution_type",
  "learning_resource_type",
  "is_worksheet",
  "has_step_instructions",
  "includes_solutions",
  "format_type",
  "is_experiment",
  "contains_demonstration_terms",
  "contains_hands_on_terms",
  "contains_equipment_mentions",
  "learning_type_coverage",
  "differentiation_level",
  "includes_visual_aids",
  "teaching_method_type",
  "difficulty_adjustment",
  "assessment_type",
  "includes_visuals",
  "scoring_guide_included",
  "question_types",
  "time_requirement",
  "includes_analogies",
  "teaching_approach",
  "visualization_tools",
  "complexity_level",
  "curriculum_alignment",
  "model_type",
  "activity_duration",
  "materials_required",
  "student_interaction_level",
  "creativity_elements"
];


export interface AttributeImportance {
  attribute: string; 
  importance : number;
}

export interface SummaryV3 {
  attribute_importances: AttributeImportance[];
  tagged_urls: TaggedUrl[];
}

export interface SummaryV4 {
  attribute_importances: AttributeImportance[];
  tagged_urls: TaggedUrl[];
  query_type: string;
}

export interface SummaryResult extends SearchResult {
  is_commercial: boolean;
  educational_news_sales: string;
  audience: string;
  source_institution_type: string;
  education_level: string;
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

export interface Metadata {
  educationalLevel: string[];
  resourceType: string[];
  subject: string[];
}

export interface EnhancedSnippet {
  enhancedSnippet: string;
}

export interface WithURL<T> {
  url: string;
  data: T;
}

export interface WithURLs<T>{
  results: WithURL<T>[];
}