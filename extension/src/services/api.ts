import { EnhancedSnippetResult, MetadataResult, SearchResult, Summary } from '../types/summary';

export class APIService {
  public static async getSummary(query: string, results: SearchResult[]): Promise<Summary> {
    return new Promise((resolve, reject) => {
      chrome.runtime.sendMessage(
        { 
          type: 'fetchSummary', 
          query,
          results,
        },
        response => {
          if (response && response.success) {
            resolve(response.data);
          } else {
            reject(new Error(response?.error || 'Failed to fetch summary'));
          }
        }
      );
    });
  }

  public static async getMetadata(results: SearchResult[]): Promise<MetadataResult[]> {
    return new Promise((resolve, reject) => {
      chrome.runtime.sendMessage(
        { 
          type: 'fetchMetadata', 
          results
        },
        response => {
          if (response && response.success) {
            resolve(response.data);
          } else {
            reject(new Error(response?.error || 'Failed to fetch metadata'));
          }
        }
      );
    });
  }

  public static async getEnhancedSnippets(
    results: SearchResult[], 
    query: string
  ): Promise<EnhancedSnippetResult[]> {
    return new Promise((resolve, reject) => {
      chrome.runtime.sendMessage(
        { 
          type: 'fetchEnhancedSnippets', 
          results, 
          query
        },
        response => {
          if (response && response.success) {
            resolve(response.data);
          } else {
            reject(new Error(response?.error || 'Failed to fetch enhanced snippets'));
          }
        }
      );
    });
  }
}