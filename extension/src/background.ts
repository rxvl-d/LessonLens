import { CHROME, FIREFOX } from "./constants";

// Detect if the browser is Firefox or Chrome
const isFirefox = typeof browser !== 'undefined';
const isChrome = typeof chrome !== 'undefined' && !isFirefox;

export const browserName = typeof browser === 'undefined' ? typeof chrome === 'undefined' ?
  null : CHROME : FIREFOX;
const root = browserName === FIREFOX ? browser : chrome;

// Create context menu for settings access
function createContextMenu() {
  const contextMenuId = "lessonlens-settings";

  if (isFirefox) {
    root.contextMenus.create({
      id: contextMenuId,
      title: "LessonLens Settings",
      contexts: ["browser_action"]
    });
  } else if (isChrome) {
    root.contextMenus.create({
      id: contextMenuId,
      title: "LessonLens Settings",
      contexts: ["action"]
    });
  }
}

// Initialize context menu
if (isFirefox) {
  browser.runtime.onInstalled.addListener(createContextMenu);
  browser.contextMenus.onClicked.addListener(contextMenuClicked);
} else if (isChrome) {
  chrome.runtime.onInstalled.addListener(createContextMenu);
  chrome.contextMenus.onClicked.addListener(contextMenuClicked);
}

function contextMenuClicked(info, tab) {
  if (info.menuItemId === "lessonlens-settings") {
    // Open the popup
    if (isFirefox) {
      browser.browserAction.openPopup();
    } else if (isChrome) {
      chrome.action.openPopup();
    }
  }
}

// API endpoint configuration
const API_ROOT = 'http://localhost:5000/api';
// const API_ROOT = 'http://134.209.200.220:5000/api';

// Handle API requests from content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === 'fetchSummary') {
    fetch(API_ROOT + '/summary', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ results: request.results, query: request.query })
    })
    .then(response => response.json())
    .then(data => {
      sendResponse({ success: true, data });
    })
    .catch(error => {
      sendResponse({ success: false, error: error.message });
    });
    
    return true; // Will respond asynchronously
  }

  if (request.type === 'fetchMetadata') {
    fetch(API_ROOT + '/metadata', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ results: request.results })
    })
    .then(response => response.json())
    .then(data => {
      sendResponse({ success: true, data });
    })
    .catch(error => {
      sendResponse({ success: false, error: error.message });
    });
    
    return true;
  }

  if (request.type === 'fetchEnhancedSnippets') {
    fetch(API_ROOT + '/enhanced-snippets', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ results: request.results, query: request.query})
    })
    .then(response => response.json())
    .then(data => {
      sendResponse({ success: true, data });
    })
    .catch(error => {
      sendResponse({ success: false, error: error.message });
    });
    
    return true;
  }
});

// Initialize default settings if not present
chrome.runtime.onInstalled.addListener(async () => {
  const storage = await root.storage.local.get('featureSettings');
  if (!storage.featureSettings) {
    await root.storage.local.set({
      featureSettings: {
        showSerpOverview: true,
        showMetadata: true,
        showEnhancedSnippets: true
      }
    });
  }
});