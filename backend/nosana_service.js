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
    
    let jobStatus = 'idle';
    let activeJobCount = 0;
    
    try {
      // List all jobs from the network
      const allJobs = await nosana.jobs.list();
      console.log(`Found ${allJobs.length} total jobs on network`);
      
      // Filter and check jobs for this specific node
      if (allJobs && allJobs.length > 0) {
        for (const jobAccount of allJobs.slice(0, 100)) {
          try {
            const jobPubkey = jobAccount.publicKey.toString();
            const jobData = await nosana.jobs.get(jobPubkey);
            
            // Check if this job belongs to our node
            if (jobData && jobData.node) {
              const jobNodeAddress = jobData.node.toString();
              
              if (jobNodeAddress === nodeAddress) {
                activeJobCount++;
                
                // Check job state
                // State: 0 = Queued, 1 = Running, 2 = Done/Stopped
                if (jobData.state === 1) {
                  jobStatus = 'running';
                  console.log(`Found RUNNING job for node ${nodeAddress.substring(0, 8)}...`);
                } else if (jobData.state === 0 && jobStatus !== 'running') {
                  jobStatus = 'queue';
                  console.log(`Found QUEUED job for node ${nodeAddress.substring(0, 8)}...`);
                }
              }
            }
          } catch (jobErr) {
            // Skip individual job errors
            continue;
          }
        }
      }
      
      console.log(`Node ${nodeAddress.substring(0, 8)}... has ${activeJobCount} active jobs, status: ${jobStatus}`);
      
    } catch (e) {
      console.log('Error querying jobs:', e.message);
    }
    
    res.json({
      success: true,
      node: nodeAddress,
      jobStatus: jobStatus,
      activeJobs: activeJobCount
    });
    
  } catch (error) {
    console.error('Error:', error);
    res.json({
      success: false,
      error: error.message,
      jobStatus: 'idle',
      activeJobs: 0
    });
  }
});

app.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'nosana-sdk' });
});

app.listen(PORT, () => {
  console.log(`Nosana SDK service running on port ${PORT}`);
});
