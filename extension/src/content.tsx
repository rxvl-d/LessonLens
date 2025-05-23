import { CHROME, FIREFOX } from './constants';
import StorageManager from "./content/storageManager";
import { SearchEngineConfig } from "./types";
import * as config from "./config";
import './content.scss';
import { FeatureSettings, DEFAULT_SETTINGS } from './types/settings';
import * as React from 'react';
import * as ReactDOM from 'react-dom';
import StackedSearchResultsOverlay from "./components/SearchResultsOverlay/StackedSearchResultsOverlay";
import SunburstSearchResultsOverlay from "./components/SearchResultsOverlay/SunburstSearchResultsOverlay";
import { APIService } from "./services/api";
import { SearchResult, MetadataResult, EnhancedSnippetResult } from "./types/summary";
import SearchResultMetadata from './components/SearchResultMetadata/SearchResultMetadata';
import HybridSnippet from './components/HybridSnippetComponent/HybridSnippetComponent';

// Initialize storage manager
const storageManager = new StorageManager();
let overlayRoot: HTMLDivElement | null = null;

// Determine search engine and apply right config
const searchEngine = (location.host.match(/([^.]+)\.\w{2,3}(?:\.\w{2})?$/) || [])[1];
const searchEngineConfig: SearchEngineConfig = config[searchEngine];

function replaceSnippet(result: Element, enhancedSnippet: EnhancedSnippetResult, searchEngine:string): void {
  let snippetElement: Element | null = null;

  switch(searchEngine) {
    case 'google':
      snippetElement = result.querySelector('div[style*="webkit-line-clamp"]');
      break;
    case 'duckduckgo':
      snippetElement = result.querySelector('.result__snippet');
      break;
    case 'bing':
      snippetElement = result.querySelector('.b_caption p');
      break;
    case 'yahoo':
      snippetElement = result.querySelector('.compText');
      break;
    case 'yandex':
      snippetElement = result.querySelector('.TextContainer');
      break;
    default:
      snippetElement = result.querySelector('p, .description, .snippet');
  }
  
  if (snippetElement) {
    snippetElement.innerHTML = enhancedSnippet.enhanced_snippet;
    snippetElement.classList.add('lessonlens_enhanced_snippet');
    (snippetElement as HTMLElement).style.webkitLineClamp = '10'
  }
}

function extractQuery(): string {
  const queryElement = document.querySelector('textarea[aria-label="Suche"]') || document.querySelector('textarea[aria-label="Search"]');
  if (queryElement) {
    return queryElement.textContent || '';
  }
  return '';
}

function extractSearchResults(searchEngine: string): Array<[Element, SearchResult | null]> {
  const config = searchEngineConfig;
  
  const resultElements = document.querySelectorAll(
    config.resultSelector
  );
  
  return Array.from(resultElements).map((result: Element) => {
    try {
      let titleElement: Element | null = null;
      let descriptionElement: Element | null = null;

      switch(searchEngine) {
        case 'google':
          titleElement = result.querySelector('h3');
          descriptionElement = result.querySelector('div[style*="webkit-line-clamp"]');
          break;
        case 'duckduckgo':
          titleElement = result.querySelector('h2');
          descriptionElement = result.querySelector('.result__snippet');
          break;
        case 'bing':
          titleElement = result.querySelector('h2');
          descriptionElement = result.querySelector('.b_caption p');
          break;
        case 'yahoo':
          titleElement = result.querySelector('h3');
          descriptionElement = result.querySelector('.compText');
          break;
        case 'yandex':
          titleElement = result.querySelector('h2');
          descriptionElement = result.querySelector('.TextContainer');
          break;
        default:
          titleElement = result.querySelector('h2, h3');
          descriptionElement = result.querySelector('p, .description, .snippet');
      }
      
      const title = titleElement?.textContent?.trim() || '';
      const description = descriptionElement?.textContent?.trim() || '';
      const url = (result.querySelector('a')?.href || '').trim();
      
      if (title || description) {
        return [result, { title, description, url }];
      } else {
        return [result, null];
      }
    } catch (e) {
      console.warn('Error extracting result:', e);
      return [result, null];
    }
  });
}

// Process one result
function processResult(
  r: Element, 
  settings: FeatureSettings,
  position?: number,
  resultMetadata?: MetadataResult,
  resultEnhancedSnippet?: EnhancedSnippetResult
): void {
  try {
    const result = r as HTMLElement;
    result.classList.add('lessonlens_result', 'lessonlens_result-' + searchEngine);

    if (resultMetadata && resultEnhancedSnippet && settings.showHybridSnippets) {
      // Create hybrid view when both are available
      const hybridContainer = document.createElement('div');
      result.parentElement.appendChild(hybridContainer);

      ReactDOM.render(
        <HybridSnippet 
          metadata={resultMetadata}
          enhancedSnippet={resultEnhancedSnippet}
          config={settings.hybridSnippetConfig}  // Access the config from settings
        />,
        hybridContainer
      );
    } else {
      // Original separate handling
      if (resultMetadata && (result.parentElement.tagName != "BLOCK-COMPONENT")) {
        const metadataContainer = document.createElement('div');
        metadataContainer.classList.add('lessonlens_result_metadata')
        result.parentElement.appendChild(metadataContainer);

        ReactDOM.render(
          <SearchResultMetadata isOpen={position == 0} metadata={resultMetadata} />,
          metadataContainer
        );
      }

      if (resultEnhancedSnippet) {
        replaceSnippet(result, resultEnhancedSnippet, searchEngine);
      }
    }
  } catch (e) {
    console.warn('Error processing result:', e);
  }
}

// Process results function
// Process results function
async function processResults(settings: FeatureSettings): Promise<void> {
  const results = extractSearchResults(searchEngine);
  const query = extractQuery();
  const non_null_results = results.flatMap(([_, r]) => r ? [r] : []);

  // Fetch metadata if needed for any feature
  let metadata: MetadataResult[] = [];
  if (settings.showMetadata || settings.showHybridSnippets) {
    try {
      metadata = await APIService.getMetadata(non_null_results);
    } catch (error) {
      console.error('Error fetching metadata:', error);
    }
  }

  // Fetch enhanced snippets if needed for any feature
  let enhancedSnippets: EnhancedSnippetResult[] = [];
  if (settings.showEnhancedSnippets || settings.showHybridSnippets) {
    try {
      enhancedSnippets = await APIService.getEnhancedSnippets(non_null_results, query);
    } catch (error) {
      console.error('Error fetching enhanced snippets:', error);
    }
  }

  // Process each result with appropriate data
  results.forEach(([r, searchResult]) => {
    if (!searchResult) return;

    const [resultMetadata] = metadata
      .map(m => [m] as const)
      .find(([m]) => m.url === searchResult.url) ?? [undefined];
      
    const enhancedSnippet = enhancedSnippets
      .find(m => m.url === searchResult.url);

    // Only process if we have the data needed for the enabled features
    if ((settings.showMetadata && resultMetadata) ||
        (settings.showEnhancedSnippets && enhancedSnippet) ||
        (settings.showHybridSnippets && resultMetadata && enhancedSnippet)) {
      console.log(settings)
      processResult(r, settings, 0, resultMetadata, enhancedSnippet);
    }
  });

  // SERP overview processing
  if (settings.showSerpOverview && non_null_results.length > 0) {
    try {
      const summary = await APIService.getSummary(query, non_null_results);
      if (!overlayRoot) {
        overlayRoot = document.createElement('div');
        overlayRoot.id = 'lessonlens-results-overlay';
        document.body.appendChild(overlayRoot);
      }

      ReactDOM.render(
        settings.useSunburstVisualization ? (
          <SunburstSearchResultsOverlay 
            summary={summary} 
            onClose={() => {
              if (overlayRoot && overlayRoot.parentNode) {
                overlayRoot.parentNode.removeChild(overlayRoot);
              }
            }} 
          />
        ) : (
          <StackedSearchResultsOverlay 
            summary={summary} 
            onClose={() => {
              if (overlayRoot && overlayRoot.parentNode) {
                overlayRoot.parentNode.removeChild(overlayRoot);
              }
            }} 
          />
        ),
        overlayRoot
      );
    } catch (error) {
      console.error('Error fetching summary:', error);
    }
  }
}

const browserName = typeof browser === 'undefined' ? typeof chrome === 'undefined' ?
  null : CHROME : FIREFOX;

export let browserStorage: any;

switch (browserName) {
  case FIREFOX:
    browserStorage = browser.storage.local;
    break;
  case CHROME:
    browserStorage = (chrome.storage as any).promise.local;
    break;
  default:
    browserStorage = null;
}

// Initial setup and processing
browserStorage.get('featureSettings')
  .then((storage: any) => {
    const settings = storage?.featureSettings || DEFAULT_SETTINGS;
    
    // Initial process results
    processResults(settings);

    // Re-process results on page load if it wasn't done initially
    if (document.readyState !== 'complete') {
      window.addEventListener('load', () => {
        // processResults(settings);
      });
    }

    // Process results on DOM change
    const targets = document.querySelectorAll(searchEngineConfig.observerSelector);
    targets.forEach(target => {
      const observer = new MutationObserver(() => {
        // processResults(settings);
      });
      if (target) observer.observe(target, { childList: true });
    });

    // Process results on storage change event
    storageManager.oryginalBrowserStorage.onChanged.addListener((changes: any) => {
      if (changes.featureSettings) {
        const newSettings = changes.featureSettings.newValue || DEFAULT_SETTINGS;
        processResults(newSettings);
      }
    });

    // Process results on add new page by AutoPagerize extension
    document.addEventListener("AutoPagerize_DOMNodeInserted", () => {
      // processResults(settings);
    }, false);
  });