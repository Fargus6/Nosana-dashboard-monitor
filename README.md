# Nosana Node Monitor

A web application to monitor and manage your Nosana AI network nodes in one centralized dashboard.

## Features

- **Add Multiple Nodes**: Add all your Nosana nodes with custom names
- **Manual Status Management**: Update node status (Online/Offline/Unknown)
- **Job Status Tracking**: Track job status (Running/Queue/Idle)
- **Offline Alerts**: Get toast notifications when nodes go offline
- **Notes**: Add custom notes for each node
- **Direct Dashboard Links**: Quick access to each node's Nosana dashboard
- **Responsive Design**: Beautiful, modern UI with blue/cyan color scheme

## How to Use

### Adding Nodes

1. Enter an optional node name in the first input field
2. Enter your Nosana node address in the second field
3. Click the "Add" button
4. Your node will appear in the dashboard below

### Updating Node Status

1. Click the edit icon (pencil) on any node card
2. Update:
   - Node name
   - Status (Online/Offline/Unknown)
   - Job Status (Running/Queue/Idle)
   - Add notes
3. Click "Save" to update

### Getting Alerts

When you change a node's status from any status to "Offline", you'll receive a toast notification alerting you that the node went offline.

### Viewing Node Dashboard

Click the external link icon (↗) on any node card to open the official Nosana dashboard for that node in a new tab.

### Deleting Nodes

Click the trash icon to remove a node from your monitoring dashboard.

## Technical Stack

- **Frontend**: React with Tailwind CSS and Shadcn UI components
- **Backend**: FastAPI (Python)
- **Database**: MongoDB
- **Font**: Space Grotesk for a modern tech aesthetic

## API Endpoints

- `POST /api/nodes` - Add a new node
- `GET /api/nodes` - Get all nodes
- `PUT /api/nodes/{node_id}` - Update node details
- `DELETE /api/nodes/{node_id}` - Delete a node
- `GET /api/nodes/{address}/dashboard` - Get dashboard link

## Your Nodes

Your three nodes have been added to the system:
1. 9DcLW6JkuanvWP2CbKsohChFWGCEiTnAGxA4xdAYHVNq
2. 9hsWPkJUBiDQnc2p7dKi2gMKHp6LwscA6Z5qAF8NGsyV
3. 7Qm8JnTZRs7MbE1hXX3jAEvKfBwv421mRkszBsbfhihH

## Note

Since the Nosana dashboard doesn't provide a public API for node status, this app uses manual status updates. You'll need to check the official Nosana dashboard and update your nodes' status in this app accordingly.
