import { Client } from '@nosana/sdk';
import express from 'express';

const app = express();
const PORT = 3001;

// Initialize Nosana client
const nosana = new Client('mainnet');

app.get('/check-node/:address', async (req, res) => {
  try {
    const nodeAddress = req.params.address;
    
    console.log(`Checking node: ${nodeAddress}`);
    
    // Get node information
    let nodeInfo;
    try {
      nodeInfo = await nosana.nodes.get(nodeAddress);
      console.log('Node info:', nodeInfo);
    } catch (e) {
      console.log('Could not fetch node info:', e.message);
    }
    
    // Try to get jobs for this node
    let jobs = [];
    let jobStatus = 'idle';
    
    try {
      // Get jobs associated with the node
      const jobAccounts = await nosana.jobs.list();
      
      // Filter jobs for this specific node
      if (jobAccounts && jobAccounts.length > 0) {
        for (const job of jobAccounts.slice(0, 50)) {
          try {
            const jobDetails = await nosana.jobs.get(job.publicKey.toString());
            
            // Check if job is associated with this node
            if (jobDetails && jobDetails.node === nodeAddress) {
              jobs.push(jobDetails);
              
              // Determine job status based on state
              if (jobDetails.state === 'RUNNING' || jobDetails.state === 1) {
                jobStatus = 'running';
              } else if (jobDetails.state === 'QUEUED' || jobDetails.state === 0) {
                jobStatus = 'queue';
              }
            }
          } catch (jobErr) {
            // Skip jobs we can't fetch
            continue;
          }
        }
      }
    } catch (e) {
      console.log('Error fetching jobs:', e.message);
    }
    
    res.json({
      success: true,
      node: nodeAddress,
      jobStatus: jobStatus,
      activeJobs: jobs.length,
      nodeInfo: nodeInfo || null
    });
    
  } catch (error) {
    console.error('Error:', error);
    res.json({
      success: false,
      error: error.message,
      jobStatus: 'idle'
    });
  }
});

app.listen(PORT, () => {
  console.log(`Nosana SDK service running on port ${PORT}`);
});
