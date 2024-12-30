import * as React from 'react';
import { MetadataResult } from '../../types/summary';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

const MetadataPill = ({ text }: { text: string }) => (
  <span className="metadata-pill">
    {text}
  </span>
);

const MetadataSection = ({ label, items }: { label: string; items: string | string[] }) => {
  
  return (
    <div className="metadata-section">
      <div className="section-header">{label}</div>
      <div className="metadata-pills">
        { (!items || (Array.isArray(items) && items.length === 0)) ? <MetadataPill text={"None"}/> :
        typeof items === 'string' 
          ? <MetadataPill text={items} />
          : items.map((item, index) => (
              <MetadataPill key={index} text={item} />
            ))
        }
      </div>
    </div>
  );
};

interface Props {
  isOpen: boolean;
  metadata: MetadataResult;
}

const SearchResultMetadata: React.FC<Props> = ({ isOpen, metadata }) => {
  const [isExpanded, setIsExpanded] = React.useState(true);

  return (
    <div>
      <div 
        className="metadata-header"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <span className="header-text">Metadata</span>
        <ExpandMoreIcon 
          className={`expand-icon ${isExpanded ? 'expanded' : ''}`}
          fontSize="small"
        />
      </div>
      
      <div className={`metadata-content ${isExpanded ? 'expanded' : ''}`}>
        {/* <MetadataSection label="Assesses" items={metadata.assesses} /> */}
        <MetadataSection label="Teaches" items={metadata.teaches} />
        <MetadataSection label="Educational Level" items={metadata.educational_level} />
        <MetadataSection label="Educational Audience" items={metadata.educational_role} />
        <MetadataSection label="Educational Use" items={metadata.educational_use} />
        <MetadataSection label="Learning Resource Type" items={metadata.learning_resource_type} />
      </div>
    </div>
  );
};

export default SearchResultMetadata;