import { EnhancedSnippet, EnhancedSnippetResult, MetadataResult, SearchResult, Summary, SummaryResult, SummaryV4, WithURLs } from '../types/summary';
import { StudySettings } from '../types/study';

export class APIService {
  public static async getSummary(query: string, results: SearchResult[]): Promise<SummaryV4> {
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
        { type: 'fetchMetadata', results},
        (response) => {
          if (response.success) {
            resolve(response.data);
          } else {
            reject(new Error(response.error));
          }
        }
      );
    });
  }

  public static async getEnhancedSnippets(results: SearchResult[], query: string): Promise<EnhancedSnippetResult[]> {
    return new Promise((resolve, reject) => {
      chrome.runtime.sendMessage(
        { type: 'fetchEnhancedSnippets', results, query},
        (response) => {
          if (response.success) {
            resolve(response.data);
          } else {
            reject(new Error(response.error));
          }
        }
      );
    });
  }

  static async getStudySettings(profileId: string): Promise<StudySettings> {
    return new Promise((resolve, reject) => {
      chrome.runtime.sendMessage(
        { 
          type: 'fetchStudySettings', 
          profileId 
        },
        response => {
          if (response && response.success) {
            resolve(response.data);
          } else {
            reject(new Error(response?.error || 'Failed to fetch study settings'));
          }
        }
      );
    });
  }
}
