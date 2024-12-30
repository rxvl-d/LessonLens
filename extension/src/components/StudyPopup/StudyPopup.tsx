import * as React from "react";
import { TextField, Button, Paper, Typography, Box } from '@mui/material';
import { browserStorage } from '../../popup';
import { StudyTask, StudySettings } from "../../types/study";
import { APIService } from "../../services/api";

const StudyPopup: React.FC = () => {
  const [profileId, setProfileId] = React.useState<string>('');
  const [settings, setSettings] = React.useState<StudySettings | null>(null);
  const [currentTaskIndex, setCurrentTaskIndex] = React.useState(0);
  const [isLoading, setIsLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    const initializeFromStorage = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        const storage = await browserStorage.get(null); // Get all storage
        console.log('Raw storage:', storage);

        // Handle nested structure
        const studySettings = storage?.studySettings;
        const currentTaskIndex = storage?.currentTaskIndex ?? 0;
        const profileId = storage?.profileId ?? '';

        if (typeof profileId === 'string') {
          setProfileId(profileId);
        }
        
        // Check if studySettings exists and has the expected structure
        if (studySettings && 
            typeof studySettings === 'object' && 
            'tasks' in studySettings && 
            Array.isArray(studySettings.tasks)) {
          setSettings(studySettings);
          
          if (typeof currentTaskIndex === 'number' && 
              currentTaskIndex >= 0 && 
              currentTaskIndex < studySettings.tasks.length) {
            setCurrentTaskIndex(currentTaskIndex);
          } else {
            setCurrentTaskIndex(0);
            await browserStorage.set({ 
              currentTaskIndex: 0
            });
          }
        }
      } catch (error) {
        console.error('Failed to load from storage:', error);
        setError('Failed to load study settings. Please try again.');
      } finally {
        setIsLoading(false);
      }
    };

    initializeFromStorage();
  }, []);

  const handleSubmit = async () => {
    if (!profileId.trim()) {
      setError('Please enter a valid Profile ID');
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      console.log('Submitting with profileId:', profileId);
      const newSettings = await APIService.getStudySettings(profileId);
      
      // Validate received settings
      if (!newSettings || !Array.isArray(newSettings.tasks) || newSettings.tasks.length === 0) {
        throw new Error('Invalid study settings received');
      }

      // Update state
      setSettings(newSettings);
      setCurrentTaskIndex(0);

      // Update storage with nested structure
      await Promise.all([
        browserStorage.set({ 
           studySettings: newSettings 
        }),
        browserStorage.set({ 
           currentTaskIndex: 0 
        }),
        browserStorage.set({ 
           profileId 
        })
      ]);

      console.log('Study started successfully');
    } catch (error) {
      console.error('Failed to fetch study settings:', error);
      setError('Failed to start study. Please check your Profile ID and try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleTaskComplete = async () => {
    if (!settings || !settings.tasks) return;

    try {
      const nextIndex = currentTaskIndex + 1;
      
      if (nextIndex < settings.tasks.length) {
        setCurrentTaskIndex(nextIndex);
        await browserStorage.set({ 
           currentTaskIndex: nextIndex
        });
      } else {
        // Study is complete
        await Promise.all([
          browserStorage.set({  studySettings: null }),
          browserStorage.set({  currentTaskIndex: 0 }),
          browserStorage.set({  profileId: '' })
        ]);
        setSettings(null);
        setCurrentTaskIndex(0);
        setProfileId('');
      }
    } catch (error) {
      console.error('Failed to update task progress:', error);
      setError('Failed to update progress. Please try again.');
    }
  };

  const handleReset = async () => {
    try {
      setIsLoading(true);
      await Promise.all([
        browserStorage.set({ studySettings: null }),
        browserStorage.set({ currentTaskIndex: 0 }),
        browserStorage.set({ profileId: '' })
      ]);
      setSettings(null);
      setCurrentTaskIndex(0);
      setProfileId('');
    } catch (error) {
      console.error('Failed to reset study:', error);
      setError('Failed to reset study. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <Box sx={{ p: 2, width: 300, textAlign: 'center' }}>
        <Typography>Loading...</Typography>
      </Box>
    );
  }

  // Show study input screen only if no settings or empty settings
  if (!settings?.tasks?.length) {
    return (
      <Box sx={{ p: 2, width: 300 }}>
        <Typography variant="h6" gutterBottom>
          Study Profile
        </Typography>
        {error && (
          <Typography color="error" sx={{ mb: 2 }}>
            {error}
          </Typography>
        )}
        <TextField
          fullWidth
          label="Profile ID"
          value={profileId}
          onChange={(e) => setProfileId(e.target.value)}
          margin="normal"
          error={!!error}
          disabled={isLoading}
          placeholder="Enter your profile ID"
          inputProps={{
            'aria-label': 'Profile ID',
          }}
        />
        <Button 
          fullWidth 
          variant="contained" 
          onClick={handleSubmit}
          disabled={!profileId.trim() || isLoading}
          sx={{ mt: 2 }}
        >
          Start Study
        </Button>
      </Box>
    );
  }

  // Ensure we have valid current task
  const currentTask = settings.tasks[currentTaskIndex];
  if (!currentTask) {
    return (
      <Box sx={{ p: 2, width: 300 }}>
        <Typography color="error">
          Error: Invalid task state. Please restart the study.
        </Typography>
        <Button 
          fullWidth 
          variant="contained" 
          onClick={handleReset}
          sx={{ mt: 2 }}
        >
          Restart Study
        </Button>
      </Box>
    );
  }

  const isLastTask = currentTaskIndex === settings.tasks.length - 1;

  return (
    <Box sx={{ p: 2, width: 300 }}>
      {error && (
        <Typography color="error" sx={{ mb: 2 }}>
          {error}
        </Typography>
      )}
      <Typography variant="h6" gutterBottom>
        Task {currentTaskIndex + 1} of {settings.tasks.length}
      </Typography>
      <Paper elevation={2} sx={{ p: 2, mb: 2 }}>
        <Typography>
          <div dangerouslySetInnerHTML={{__html: currentTask.search_task}}></div>
        </Typography>
      </Paper>
      <Button 
        fullWidth 
        variant="contained" 
        onClick={handleTaskComplete}
        disabled={isLoading}
        sx={{ mb: 1 }}
      >
        {isLastTask ? 'Complete Study' : 'Next Task'}
      </Button>
      <Button
        fullWidth
        variant="outlined"
        onClick={handleReset}
        disabled={isLoading}
        color="secondary"
        size="small"
      >
        Reset Study
      </Button>
    </Box>
  );
};

export default StudyPopup;