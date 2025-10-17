import { useState, useEffect } from "react";
import "@/App.css";
import axios from "axios";
import { Plus, Trash2, RefreshCw, Activity, Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [nodes, setNodes] = useState([]);
  const [statuses, setStatuses] = useState({});
  const [newNodeAddress, setNewNodeAddress] = useState("");
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  // Load nodes on mount
  useEffect(() => {
    loadNodes();
  }, []);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      refreshStatuses();
    }, 30000);

    return () => clearInterval(interval);
  }, [nodes]);

  const loadNodes = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/nodes`);
      setNodes(response.data);
      if (response.data.length > 0) {
        await refreshStatuses();
      }
    } catch (error) {
      console.error("Error loading nodes:", error);
      toast.error("Failed to load nodes");
    } finally {
      setLoading(false);
    }
  };

  const refreshStatuses = async () => {
    try {
      setRefreshing(true);
      const response = await axios.get(`${API}/nodes/status/all`);
      const statusMap = {};
      response.data.forEach((status) => {
        statusMap[status.address] = status;
        
        // Show alert if node went offline
        if (status.status_changed) {
          toast.error(`Node ${status.address.substring(0, 8)}... went offline!`, {
            duration: 5000,
          });
        }
      });
      setStatuses(statusMap);
    } catch (error) {
      console.error("Error refreshing statuses:", error);
    } finally {
      setRefreshing(false);
    }
  };

  const addNode = async () => {
    if (!newNodeAddress.trim()) {
      toast.error("Please enter a node address");
      return;
    }

    try {
      await axios.post(`${API}/nodes`, {
        address: newNodeAddress.trim(),
      });
      toast.success("Node added successfully");
      setNewNodeAddress("");
      await loadNodes();
    } catch (error) {
      const message = error.response?.data?.detail || "Failed to add node";
      toast.error(message);
    }
  };

  const deleteNode = async (nodeId) => {
    try {
      await axios.delete(`${API}/nodes/${nodeId}`);
      toast.success("Node removed");
      await loadNodes();
    } catch (error) {
      toast.error("Failed to remove node");
    }
  };

  const getStatusBadge = (status) => {
    const variants = {
      online: "default",
      offline: "destructive",
      error: "secondary",
    };

    return (
      <Badge variant={variants[status] || "secondary"} data-testid={`status-badge-${status}`}>
        {status?.toUpperCase() || "UNKNOWN"}
      </Badge>
    );
  };

  const getJobStatusBadge = (jobStatus) => {
    if (!jobStatus) return null;

    const colors = {
      running: "bg-blue-500 text-white",
      queue: "bg-yellow-500 text-white",
      idle: "bg-gray-500 text-white",
    };

    return (
      <Badge className={colors[jobStatus] || ""} data-testid={`job-badge-${jobStatus}`}>
        {jobStatus?.toUpperCase()}
      </Badge>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl sm:text-5xl font-bold bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent mb-2" data-testid="app-title">
            Nosana Node Monitor
          </h1>
          <p className="text-base text-gray-600">Monitor your Nosana AI network nodes in real-time</p>
        </div>

        {/* Add Node Section */}
        <Card className="mb-8 border-blue-200 shadow-lg backdrop-blur-sm bg-white/90" data-testid="add-node-card">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Plus className="w-5 h-5" />
              Add New Node
            </CardTitle>
            <CardDescription>Enter your Nosana node address to start monitoring</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex gap-3">
              <Input
                data-testid="node-address-input"
                placeholder="Enter node address (e.g., 9DcLW6JkuanvWP2CbKsohChFWGCEiTnAGxA4xdAYHVNq)"
                value={newNodeAddress}
                onChange={(e) => setNewNodeAddress(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && addNode()}
                className="flex-1"
              />
              <Button onClick={addNode} className="bg-blue-600 hover:bg-blue-700" data-testid="add-node-button">
                <Plus className="w-4 h-4 mr-2" />
                Add Node
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Refresh Button */}
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold text-gray-700">Monitored Nodes ({nodes.length})</h2>
          <Button
            onClick={refreshStatuses}
            disabled={refreshing || nodes.length === 0}
            variant="outline"
            className="gap-2"
            data-testid="refresh-button"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </div>

        {/* Nodes Grid */}
        {loading ? (
          <div className="text-center py-12" data-testid="loading-indicator">
            <RefreshCw className="w-8 h-8 animate-spin mx-auto text-blue-600" />
            <p className="text-gray-600 mt-4">Loading nodes...</p>
          </div>
        ) : nodes.length === 0 ? (
          <Card className="text-center py-12 border-dashed" data-testid="no-nodes-message">
            <CardContent className="pt-6">
              <Activity className="w-16 h-16 mx-auto text-gray-400 mb-4" />
              <h3 className="text-lg font-semibold text-gray-700 mb-2">No Nodes Added</h3>
              <p className="text-gray-500">Add your first Nosana node to start monitoring</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {nodes.map((node) => {
              const status = statuses[node.address];
              return (
                <Card
                  key={node.id}
                  className="border-blue-100 shadow-lg hover:shadow-xl transition-shadow backdrop-blur-sm bg-white/95"
                  data-testid={`node-card-${node.id}`}
                >
                  <CardHeader className="pb-3">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <CardTitle className="text-lg flex items-center gap-2 break-all" data-testid={`node-address-${node.id}`}>
                          {node.address.substring(0, 8)}...{node.address.substring(node.address.length - 6)}
                        </CardTitle>
                      </div>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => deleteNode(node.id)}
                        className="text-red-500 hover:text-red-700 hover:bg-red-50"
                        data-testid={`delete-node-${node.id}`}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600 font-medium">Status:</span>
                        {status ? getStatusBadge(status.status) : <Badge variant="secondary">Loading...</Badge>}
                      </div>

                      {status?.job_status && (
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-gray-600 font-medium">Job Status:</span>
                          {getJobStatusBadge(status.job_status)}
                        </div>
                      )}

                      {status?.last_checked && (
                        <div className="flex items-center gap-2 text-xs text-gray-500 pt-2 border-t">
                          <Clock className="w-3 h-3" />
                          <span>Updated: {new Date(status.last_checked).toLocaleTimeString()}</span>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;