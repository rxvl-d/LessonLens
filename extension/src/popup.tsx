import * as React from 'react';
import * as ReactDOM from 'react-dom';
import browserStorageMock from './mock/BrowserStorageMock';
import { createTheme, ThemeProvider } from '@mui/material/styles';
import { blueGrey, deepOrange } from '@mui/material/colors';
import { CacheProvider } from "@emotion/react";
import { TssCacheProvider } from "tss-react";
import createCache from "@emotion/cache";
import { CHROME, FIREFOX } from './constants';
import 'chrome-storage-promise';
import StudyPopup from './components/StudyPopup/StudyPopup';


const theme = createTheme({
  colorSchemes: {
    light: {
      palette: {
        primary: {
          main: blueGrey[700],
          light: '#718792',
          dark: '#1c313a',
          contrastText: '#ffffff',
        },
        secondary: {
          main: deepOrange['A700'],
          light: '#ff6434',
          dark: '#a30000',
          contrastText: '#ffffff'
        },
        text: {
          primary: '#444',
          secondary: '#888',
        }
      },
    },
    dark: {
      palette: {
        primary: {
          main: blueGrey[200],
          light: '#718792',
          dark: '#1c313a',
          contrastText: '#ffffff',
        },
        secondary: {
          main: deepOrange['A200'],
          light: '#ff6434',
          dark: '#a30000',
          contrastText: '#ffffff'
        },
        text: {
          primary: '#ccc',
          secondary: '#888',
        }
      },
    },
  },
});

/*
 * Detect browser name
 */
export const browserName = typeof browser === 'undefined' ? typeof chrome === 'undefined' ?
  null : CHROME : FIREFOX;

/*
 * This constant stores a reference to browser.storage.sync or chrome.storage.sync object.
 * In normal browser window browser/chrome objects are not accesible.
 * In this case the constant stores a reference to a browser storage mock object.
 */
export let browserStorage: any;

switch (browserName) {
  case FIREFOX:
    browserStorage = browser.storage.local;
    break;
  case CHROME:
    browserStorage = (chrome.storage as any).promise.local;
    break;
  default:
    browserStorage = new browserStorageMock();
}

const muiCache = createCache({
    "key": "mui",
    "prepend": true
});

const tssCache = createCache({
    "key": "tss"
});

ReactDOM.render(
  <CacheProvider value={muiCache}>
    <TssCacheProvider value={tssCache}> 
      <ThemeProvider theme={theme} defaultMode="system">
        <StudyPopup />
      </ThemeProvider>
    </TssCacheProvider>
  </CacheProvider>,
  document.getElementById('root') as HTMLElement
);
