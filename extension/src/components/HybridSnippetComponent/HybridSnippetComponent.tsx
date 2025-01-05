import * as React from 'react';
import { MetadataResult, EnhancedSnippetResult } from '../../types/summary';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

interface Props {
  metadata: MetadataResult;
  enhancedSnippet: EnhancedSnippetResult;
  config: {
    maxMetadataFields: number;
    maxQuestions: number;
  };
}

const MetadataPill = ({ text }: { text: string }) => (
  <span className="metadata-pill">
    {text}
  </span>
);

const MetadataSection = ({ label, items }: { label: string; items: string | string[] }) => {
  return (
    <div className="metadata-section">
      <span className="section-header">{label}</span>
      <span className="metadata-pills">
        {(!items || (Array.isArray(items) && items.length === 0)) ? 
          <MetadataPill text="None"/> :
          typeof items === 'string' 
            ? <MetadataPill text={items} />
            : items.map((item, index) => (
                <MetadataPill key={index} text={item} />
              ))
        }
      </span>
    </div>
  );
};

const HybridSnippet: React.FC<Props> = ({ metadata, enhancedSnippet, config }) => {
  const [isExpanded, setIsExpanded] = React.useState(true);
  
  // Order metadata fields by most commonly useful first
  const metadataFields = [
    { label: "Educational Level", value: metadata.educational_level },
    { label: "Teaches", value: metadata.teaches },
    { label: "Learning Resource Type", value: metadata.learning_resource_type },
    { label: "Educational Use", value: metadata.educational_use },
    { label: "Educational Audience", value: metadata.educational_role }
  ].slice(0, config.maxMetadataFields);

  // Extract Q&A content from enhanced snippet
  const enhancedContent = enhancedSnippet.enhanced_snippet;

  return (
    <div className="lessonlens_hybrid_snippet">
      <div 
        className="hybrid-header"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <span className="header-text">Resource Details</span>
        <ExpandMoreIcon 
          className={`expand-icon ${isExpanded ? 'expanded' : ''}`}
          fontSize="small"
        />
      </div>
      
      <div className={`hybrid-content ${isExpanded ? 'expanded' : ''}`}>
        {/* Metadata Section */}
        <div className="hybrid-metadata">
          {metadataFields.map((field, index) => (
            <MetadataSection 
              key={index}
              label={field.label}
              items={field.value}
            />
          ))}
        </div>
        
        {/* Enhanced Content Section */}
        <div className="hybrid-qa">
          <div 
            className="qa-content"
            dangerouslySetInnerHTML={{ __html: enhancedContent }}
          />
        </div>
      </div>
    </div>
  );
};

export default HybridSnippet;