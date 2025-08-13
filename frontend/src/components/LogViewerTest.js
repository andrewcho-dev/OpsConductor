import React from 'react';
import { Box, Typography, Button, Card, CardContent } from '@mui/material';
import { useNavigate } from 'react-router-dom';

const LogViewerTest = () => {
  const navigate = useNavigate();

  const testPatterns = [
    { pattern: 'J20250000001', description: 'Specific Job' },
    { pattern: 'J20250000001.0001', description: 'Specific Execution' },
    { pattern: 'J20250000001.0001.0001', description: 'Specific Branch' },
    { pattern: 'J20250000001.0001.0001.0001', description: 'Specific Action' },
    { pattern: 'J2025*', description: 'All 2025 Jobs' },
    { pattern: '*.0001', description: 'All First Executions' },
    { pattern: '*.*.0001', description: 'All First Branches' },
    { pattern: 'setup', description: 'Text Search' }
  ];

  const testLogViewer = (pattern) => {
    navigate('/log-viewer', { state: { searchPattern: pattern } });
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Log Viewer Test
      </Typography>
      
      <Typography variant="body1" sx={{ mb: 3 }}>
        Test the Log Viewer with different search patterns:
      </Typography>

      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 2 }}>
        {testPatterns.map((test, index) => (
          <Card key={index}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                {test.description}
              </Typography>
              <Typography variant="body2" color="textSecondary" sx={{ mb: 2, fontFamily: 'monospace' }}>
                {test.pattern}
              </Typography>
              <Button
                variant="contained"
                onClick={() => testLogViewer(test.pattern)}
                fullWidth
              >
                Test Pattern
              </Button>
            </CardContent>
          </Card>
        ))}
      </Box>

      <Box sx={{ mt: 4 }}>
        <Button
          variant="outlined"
          onClick={() => navigate('/log-viewer')}
          size="large"
        >
          Open Log Viewer (Empty)
        </Button>
      </Box>
    </Box>
  );
};

export default LogViewerTest;