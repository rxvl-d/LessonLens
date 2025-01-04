import { FeatureSettings, DEFAULT_SETTINGS } from '../types/settings';

export default class {
  storage = {
    featureSettings: DEFAULT_SETTINGS,
    // We can keep any other mock data needed for testing here
  };

  set(value: any): void {
    const storageCopy = { ...this.storage };
    const objectName = Object.keys(value)[0];
    storageCopy[objectName] = value[objectName];
    this.storage = storageCopy;
  }

  get(key: string | null): Promise<any> {
    return new Promise((resolve, reject) => {
      // If no key provided, return all storage
      if (key === null) {
        resolve(this.storage);
        return;
      }

      // If key exists, return that specific value
      if (key in this.storage) {
        const storageObject = {};
        storageObject[key] = this.storage[key];
        resolve(storageObject);
        return;
      }

      // If key doesn't exist, resolve with empty object (matching browser behavior)
      resolve({});
    });
  }

  // Add a helper method to simulate storage changes
  simulateStorageChange(changes: { [key: string]: { newValue: any, oldValue: any } }): void {
    Object.entries(changes).forEach(([key, change]) => {
      if (change.newValue !== undefined) {
        this.storage[key] = change.newValue;
      } else {
        delete this.storage[key];
      }
    });
  }
}