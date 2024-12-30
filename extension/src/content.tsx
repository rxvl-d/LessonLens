import { CHROME, FIREFOX } from './constants';
import StorageManager from "./content/storageManager";
import { SearchEngineConfig, DisplayStyle } from "./types";
import * as config from "./config";
import './content.scss';
import { StudySettings } from './types/study';
import * as React from 'react';
import * as ReactDOM from 'react-dom';
import { ResizeObserver } from './mock/ResizeObserver';
import SearchResultsOverlay from "./components/SearchResultsOverlay/SearchResultsOverlay";
import { APIService } from "./services/api";
import { EnhancedSnippet, Metadata, WithURL, SearchResult, MetadataResult, EnhancedSnippetResult } from "./types/summary";
import SearchResultMetadata from './components/SearchResultMetadata/SearchResultMetadata';

// Initialize storage manager
const storageManager = new StorageManager();
let overlayRoot: HTMLDivElement | null = null;

let studySettings: StudySettings;
let currentTaskIndex: number;

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
  
  // Get all result elements
  const resultElements = document.querySelectorAll(
    config.resultSelector
  );
  
  return Array.from(resultElements).map((result: Element) => {
    try {
      let titleElement: Element | null = null;
      let descriptionElement: Element | null = null;

      // Extract title and description based on search engine
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
      
      // Only add results that have either a title or description
      if (title || description) {
        return [result, { title, description, url }];
      } else {
        return [result, null ];
      }
    } catch (e) {
      console.warn('Error extracting result:', e);
      return [result, null];
    }
  });
}

// Process one result
function processResult (
  r: Element, 
  position?: number,
  resultMetadata?: MetadataResult,
  resultEnhancedSnippet?: EnhancedSnippetResult
): DisplayStyle | null {
  let displayStyle: DisplayStyle | null = null;
  try {
    const result = r as HTMLElement;
    result.classList.add('lessonlens_result', 'lessonlens_result-' + searchEngine);

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
  } catch (e) {
    console.warn(e);
    // Try to process result again - Might need this
    // if (++processResultsAttempt <= 3) {
    //   setTimeout(() => {
    //     processResult(r, domainList, options, processResultsAttempt, resultMetadata);
    //   }, 100 * Math.pow(processResultsAttempt, 3));
    // }
  }
  return displayStyle;
}

// Process results function
async function processResults (studySettings: StudySettings, currentTask: number): Promise<void> {

  const results = extractSearchResults(searchEngine);
  const query = extractQuery();
  const flags = studySettings.tasks[currentTask].feature_flags;
  const relevance_dimensions = studySettings.tasks[currentTask].relevance_dimensions;
  const task = studySettings.tasks[currentTask].search_task;
  const showSnippets = flags.includes('snippets');
  const showMetadata = flags.includes('metadata');
  const showSummary = flags.includes('summary');
  const non_null_results = results.flatMap(([_, r]) => r? [r] : [])
  if (showSummary) {

    try {
      const summary = await APIService.getSummary(query, task, non_null_results);
      // Create overlay root if it doesn't exist
      if (!overlayRoot) {
        overlayRoot = document.createElement('div');
        overlayRoot.id = 'lessonlens-results-overlay';
        document.body.appendChild(overlayRoot);
      }

      // Render SearchResultsOverlay
      ReactDOM.render(
        <SearchResultsOverlay summary={summary} onClose={() => {
          if (overlayRoot && overlayRoot.parentNode) {
            overlayRoot.parentNode.removeChild(overlayRoot);
          }
        }} />,
        overlayRoot
      );
    } catch (error) {
      console.error('Error fetching summary:', error);
    }

  }

  // Fetch metadata for all results at once
  if (showMetadata) {
    try {
      const metadata = await APIService.getMetadata(non_null_results);
      results.forEach(([r, searchResult]) => {
        const [resultMetadata, index] = metadata
          .map((m: MetadataResult, index) => [m, index] as const)
          .find(([m]) => m.url === searchResult?.url) ?? [undefined, -1];
        processResult(r, index, resultMetadata, null);
      });
    } catch (error) {
      console.error('Error fetching metadata:', error);
    }
  }
  if (showSnippets) {
    try {
      const enhancedSnippets = await APIService.getEnhancedSnippets(non_null_results, relevance_dimensions);
      results.forEach(([r, searchResult]) => {
        const resultMetadata = enhancedSnippets.find(
          (m: EnhancedSnippetResult) => m.url === searchResult?.url
        );
        processResult(r, null, null, resultMetadata);
      });
    } catch (error) {
      console.error('Error fetching enhanced snippets:', error);
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

browserStorage.get(null)
  .then((o: any) => {
    studySettings = o && o.studySettings as StudySettings;
    currentTaskIndex = o && (o.currentTaskIndex || 0) as number;
    // Initial process results
    processResults(studySettings, currentTaskIndex);

    // Re-process results on page load if it wasn't done initially
    if (document.readyState !== 'complete') {
      window.addEventListener('load', () => {
        // Removed due to the summary getting the updated snippets issue
        // processResults(studySettings, currentTaskIndex);
      });
    }

    // Process results on DOM change
    const targets = document.querySelectorAll(searchEngineConfig.observerSelector);
    targets.forEach(target => {
      const observer = new MutationObserver(function () {
        processResults(studySettings, currentTaskIndex);
      });
      if (target) observer.observe(target, { childList: true });
    });

    // Process results on storage change event
    storageManager.oryginalBrowserStorage.onChanged.addListener((storage: any) => {
      studySettings = (storage.studySettings && storage.studySettings.newValue) || studySettings;
      currentTaskIndex = (storage.currentTaskIndex && storage.currentTaskIndex.newValue) || currentTaskIndex;
      processResults(studySettings, currentTaskIndex);
    });

    // Process results on add new page by AutoPagerize extension
    document.addEventListener("AutoPagerize_DOMNodeInserted", function () {
      processResults(studySettings, currentTaskIndex);
    }, false);

    if (searchEngineConfig.ajaxResults) {

      // Observe resize event on result wrapper
      // let isResized: any;
      // const resizeObserver = new ResizeObserver(() => {
      //   window.clearTimeout( isResized );
      //   isResized = setTimeout(() => {
      //     processResults(studySettings, currentTaskIndex);
      //   }, 500);
      // });

      // const resultsWrappers = document.querySelectorAll(searchEngineConfig.observerSelector);
      // resultsWrappers.forEach(resultsWrapper => {
      //   resizeObserver.observe(resultsWrapper);
      // });

    }
  });
