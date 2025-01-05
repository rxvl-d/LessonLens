import * as React from "react";
import { 
  Box, 
  Typography, 
  Switch, 
  FormGroup, 
  FormControlLabel,
  Button,
  Paper,
  Divider
} from '@mui/material';
import { browserStorage } from '../../popup';
import { FeatureSettings, DEFAULT_SETTINGS } from '../../types/settings';

const SettingsPopup: React.FC = () => {
  const [settings, setSettings] = React.useState<FeatureSettings>(DEFAULT_SETTINGS);
  const [isLoading, setIsLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  // Load settings from storage on component mount
  React.useEffect(() => {
    const loadSettings = async () => {
      try {
        setIsLoading(true);
        const storage = await browserStorage.get('featureSettings');
        if (storage?.featureSettings) {
          setSettings(storage.featureSettings);
        } else {
          // If no settings found, use defaults
          await browserStorage.set({ featureSettings: DEFAULT_SETTINGS });
          setSettings(DEFAULT_SETTINGS);
        }
      } catch (error) {
        console.error('Failed to load settings:', error);
        setError('Failed to load settings. Please try again.');
      } finally {
        setIsLoading(false);
      }
    };

    loadSettings();
  }, []);

  // Handle setting changes
  const handleSettingChange = async (setting: keyof FeatureSettings) => {
    try {
      const newSettings = {
        ...settings,
        [setting]: !settings[setting]
      };
      
      // Update storage
      await browserStorage.set({ featureSettings: newSettings });
      
      // Update state
      setSettings(newSettings);
    } catch (error) {
      console.error('Failed to update settings:', error);
      setError('Failed to save settings. Please try again.');
    }
  };

  // Handle reset to defaults
  const handleReset = async () => {
    try {
      await browserStorage.set({ featureSettings: DEFAULT_SETTINGS });
      setSettings(DEFAULT_SETTINGS);
    } catch (error) {
      console.error('Failed to reset settings:', error);
      setError('Failed to reset settings. Please try again.');
    }
  };

  if (isLoading) {
    return (
      <Box sx={{ p: 2, width: 300, textAlign: 'center' }}>
        <Typography>Loading...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 2, width: 300 }}>
      <Typography variant="h6" gutterBottom>
        Search Enhancement Settings
      </Typography>
      
      {error && (
        <Typography color="error" sx={{ mb: 2 }}>
          {error}
        </Typography>
      )}

      <Paper elevation={2} sx={{ p: 2, mb: 2 }}>
        <FormGroup>
          <FormControlLabel
            control={
              <Switch
                checked={settings.showSerpOverview}
                onChange={() => handleSettingChange('showSerpOverview')}
              />
            }
            label="SERP Overview"
          />
          <Typography variant="caption" sx={{ pl: 4, mb: 1, color: 'text.secondary' }}>
            Shows a visualization of search result characteristics
          </Typography>

          {/* Nested Visualization Type Toggle */}
          <Box sx={{ pl: 4, mb: 1 }}>
            <FormControlLabel
              control={
                <Switch
                  checked={settings.useSunburstVisualization}
                  onChange={() => handleSettingChange('useSunburstVisualization')}
                  disabled={!settings.showSerpOverview}
                  size="small"
                />
              }
              label={
                <Typography variant="body2">
                  Use Sunburst View
                </Typography>
              }
            />
            <Typography variant="caption" sx={{ pl: 4, display: 'block', color: 'text.secondary' }}>
              Switch between Stacked Bar and Sunburst visualizations
            </Typography>
          </Box>

          <Divider sx={{ my: 1 }} />

          <FormControlLabel
            control={
              <Switch
                checked={settings.showMetadata}
                onChange={() => handleSettingChange('showMetadata')}
              />
            }
            label="Result Metadata"
          />
          <Typography variant="caption" sx={{ pl: 4, mb: 1, color: 'text.secondary' }}>
            Displays educational metadata for each search result
          </Typography>

          <Divider sx={{ my: 1 }} />

          <FormControlLabel
            control={
              <Switch
                checked={settings.showEnhancedSnippets}
                onChange={() => handleSettingChange('showEnhancedSnippets')}
              />
            }
            label="Enhanced Snippets"
          />
          <Typography variant="caption" sx={{ pl: 4, color: 'text.secondary' }}>
            Shows improved result descriptions with educational context
          </Typography>
        </FormGroup>
      </Paper>

      <Button
        fullWidth
        variant="outlined"
        onClick={handleReset}
        disabled={isLoading}
        size="small"
      >
        Reset to Defaults
      </Button>
    </Box>
  );
};

export default SettingsPopup;