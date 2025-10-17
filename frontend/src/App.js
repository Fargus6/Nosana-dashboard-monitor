import { useState, useEffect } from "react";
import "@/App.css";
import axios from "axios";
import { Plus, Trash2, RefreshCw, Activity, ExternalLink, Edit2, Check, X, Eye, EyeOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [nodes, setNodes] = useState([]);
  const [newNodeAddress, setNewNodeAddress] = useState("");
  const [newNodeName, setNewNodeName] = useState("");
  const [loading, setLoading] = useState(false);
  const [editingNode, setEditingNode] = useState(null);
  const [editData, setEditData] = useState({});
  const [autoRefreshing, setAutoRefreshing] = useState(false);
  const [hiddenAddresses, setHiddenAddresses] = useState(new Set());

  useEffect(() => {
    loadNodes();
  }, []);

  const loadNodes = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/nodes`);
      setNodes(response.data);
    } catch (error) {
      console.error("Error loading nodes:", error);
      toast.error("Failed to load nodes");
    } finally {
      setLoading(false);
    }
  };

  const autoRefreshAllNodes = async () => {
    try {
      setAutoRefreshing(true);
      toast.info("Checking node status from Solana blockchain...");
      
      const response = await axios.post(`${API}/nodes/refresh-all-status`);
      
      if (response.data.updated > 0) {
        toast.success(`Updated ${response.data.updated} nodes from blockchain!`);
        await loadNodes();
      } else {
        toast.warning("No nodes updated");
      }
      
      if (response.data.errors && response.data.errors.length > 0) {
        toast.error(`${response.data.errors.length} nodes had errors`);
      }
    } catch (error) {
      console.error("Error auto-refreshing:", error);
      toast.error("Failed to auto-refresh node status");
    } finally {
      setAutoRefreshing(false);
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
        name: newNodeName.trim() || null,
      });
      toast.success("Node added successfully");
      setNewNodeAddress("");
      setNewNodeName("");
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

  const startEdit = (node) => {
    setEditingNode(node.id);
    setEditData({
      status: node.status,
      job_status: node.job_status || "idle",
      notes: node.notes || "",
      name: node.name || "",
    });
  };

  const cancelEdit = () => {
    setEditingNode(null);
    setEditData({});
  };

  const saveEdit = async (nodeId) => {
    try {
      await axios.put(`${API}/nodes/${nodeId}`, editData);
      
      // Show alert if status changed to offline
      const node = nodes.find(n => n.id === nodeId);
      if (node.status !== "offline" && editData.status === "offline") {
        toast.error(`Node ${node.name || node.address.substring(0, 8) + '...'} is now offline!`, {
          duration: 5000,
        });
      }
      
      toast.success("Node updated");
      setEditingNode(null);
      setEditData({});
      await loadNodes();
    } catch (error) {
      toast.error("Failed to update node");
    }
  };

  const openDashboard = (address) => {
    window.open(`https://dashboard.nosana.com/host/${address}`, "_blank");
  };

  const toggleAddressVisibility = (nodeId) => {
    setHiddenAddresses(prev => {
      const newSet = new Set(prev);
      if (newSet.has(nodeId)) {
        newSet.delete(nodeId);
      } else {
        newSet.add(nodeId);
      }
      return newSet;
    });
  };

  const formatAddress = (address, nodeId) => {
    if (hiddenAddresses.has(nodeId)) {
      return "••••••••••••••••••••••••••••••••••••••••";
    }
    return address;
  };

  const getStatusBadge = (status) => {
    const styles = {
      online: "bg-green-500 text-white",
      offline: "bg-red-500 text-white",
      unknown: "bg-gray-400 text-white",
    };

    return (
      <Badge className={styles[status] || styles.unknown} data-testid={`status-badge-${status}`}>
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
      <div className="container mx-auto px-3 sm:px-4 py-4 sm:py-8 max-w-7xl">
        {/* Header */}
        <div className="mb-4 sm:mb-8">
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent mb-2" data-testid="app-title">
            Nosana Node Monitor
          </h1>
          <p className="text-sm sm:text-base text-gray-600">Track and manage your Nosana AI network nodes</p>
        </div>

        {/* Add Node Section */}
        <Card className="mb-4 sm:mb-8 border-blue-200 shadow-lg backdrop-blur-sm bg-white/90" data-testid="add-node-card">
          <CardHeader className="pb-3 sm:pb-6">
            <CardTitle className="flex items-center gap-2 text-base sm:text-lg">
              <Plus className="w-4 h-4 sm:w-5 sm:h-5" />
              Add New Node
            </CardTitle>
            <CardDescription className="text-xs sm:text-sm">Enter your Nosana node address and optional name</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col gap-2 sm:gap-3">
              <Input
                data-testid="node-name-input"
                placeholder="Node name (optional)"
                value={newNodeName}
                onChange={(e) => setNewNodeName(e.target.value)}
                className="text-sm sm:text-base h-10 sm:h-auto"
              />
              <div className="flex gap-2">
                <Input
                  data-testid="node-address-input"
                  placeholder="Node address"
                  value={newNodeAddress}
                  onChange={(e) => setNewNodeAddress(e.target.value)}
                  onKeyPress={(e) => e.key === "Enter" && addNode()}
                  className="flex-1 text-sm sm:text-base h-10 sm:h-auto"
                />
                <Button onClick={addNode} className="bg-blue-600 hover:bg-blue-700 h-10 sm:h-auto px-3 sm:px-4" data-testid="add-node-button">
                  <Plus className="w-4 h-4 sm:mr-2" />
                  <span className="hidden sm:inline">Add</span>
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 mb-4 sm:mb-6">
          <h2 className="text-lg sm:text-xl font-semibold text-gray-700">Your Nodes ({nodes.length})</h2>
          <div className="flex gap-2 w-full sm:w-auto">
            <Button
              onClick={autoRefreshAllNodes}
              disabled={autoRefreshing || nodes.length === 0}
              className="flex-1 sm:flex-none gap-2 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 text-xs sm:text-sm h-9 sm:h-10"
              data-testid="auto-refresh-button"
            >
              <RefreshCw className={`w-3 h-3 sm:w-4 sm:h-4 ${autoRefreshing ? "animate-spin" : ""}`} />
              <span className="hidden sm:inline">Auto-Refresh from Blockchain</span>
              <span className="sm:hidden">Auto-Refresh</span>
            </Button>
            <Button
              onClick={loadNodes}
              variant="outline"
              className="gap-2 text-xs sm:text-sm h-9 sm:h-10 px-3"
              data-testid="refresh-button"
            >
              <RefreshCw className="w-3 h-3 sm:w-4 sm:h-4" />
              <span className="hidden sm:inline">Reload</span>
            </Button>
          </div>
        </div>

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
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
            {nodes.map((node) => {
              const isEditing = editingNode === node.id;
              return (
                <Card
                  key={node.id}
                  className="border-blue-100 shadow-lg hover:shadow-xl transition-shadow backdrop-blur-sm bg-white/95"
                  data-testid={`node-card-${node.id}`}
                >
                  <CardHeader className="pb-2 sm:pb-3">
                    <div className="flex justify-between items-start gap-2 sm:gap-3">
                      <div className="flex-1 min-w-0">
                        {isEditing ? (
                          <Input
                            value={editData.name}
                            onChange={(e) => setEditData({ ...editData, name: e.target.value })}
                            placeholder="Node name"
                            className="mb-2 text-sm sm:text-base h-9 sm:h-auto"
                            data-testid={`edit-name-${node.id}`}
                          />
                        ) : (
                          <CardTitle className="text-base sm:text-lg mb-1" data-testid={`node-name-${node.id}`}>
                            {node.name || "Unnamed Node"}
                          </CardTitle>
                        )}
                        <p className="text-xs text-gray-500 font-mono break-all" data-testid={`node-address-${node.id}`}>
                          {formatAddress(node.address, node.id)}
                        </p>
                      </div>
                      <div className="flex gap-1">
                        {!isEditing && (
                          <>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => toggleAddressVisibility(node.id)}
                              className="text-gray-500 hover:text-gray-700 hover:bg-gray-50 h-8 w-8 sm:h-10 sm:w-10"
                              data-testid={`toggle-address-${node.id}`}
                              title={hiddenAddresses.has(node.id) ? "Show address" : "Hide address"}
                            >
                              {hiddenAddresses.has(node.id) ? (
                                <EyeOff className="w-3 h-3 sm:w-4 sm:h-4" />
                              ) : (
                                <Eye className="w-3 h-3 sm:w-4 sm:h-4" />
                              )}
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => openDashboard(node.address)}
                              className="text-blue-500 hover:text-blue-700 hover:bg-blue-50 h-8 w-8 sm:h-10 sm:w-10"
                              data-testid={`open-dashboard-${node.id}`}
                            >
                              <ExternalLink className="w-3 h-3 sm:w-4 sm:h-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => startEdit(node)}
                              className="text-gray-500 hover:text-gray-700 hover:bg-gray-50 h-8 w-8 sm:h-10 sm:w-10"
                              data-testid={`edit-node-${node.id}`}
                            >
                              <Edit2 className="w-3 h-3 sm:w-4 sm:h-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => deleteNode(node.id)}
                              className="text-red-500 hover:text-red-700 hover:bg-red-50 h-8 w-8 sm:h-10 sm:w-10"
                              data-testid={`delete-node-${node.id}`}
                            >
                              <Trash2 className="w-3 h-3 sm:w-4 sm:h-4" />
                            </Button>
                          </>
                        )}
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    {isEditing ? (
                      <div className="space-y-3">
                        <div>
                          <label className="text-sm font-medium text-gray-600 mb-1 block">Status</label>
                          <Select
                            value={editData.status}
                            onValueChange={(value) => setEditData({ ...editData, status: value })}
                          >
                            <SelectTrigger data-testid={`edit-status-${node.id}`}>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="online">Online</SelectItem>
                              <SelectItem value="offline">Offline</SelectItem>
                              <SelectItem value="unknown">Unknown</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <div>
                          <label className="text-sm font-medium text-gray-600 mb-1 block">Job Status</label>
                          <Select
                            value={editData.job_status}
                            onValueChange={(value) => setEditData({ ...editData, job_status: value })}
                          >
                            <SelectTrigger data-testid={`edit-job-status-${node.id}`}>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="running">Running</SelectItem>
                              <SelectItem value="queue">Queue</SelectItem>
                              <SelectItem value="idle">Idle</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <div>
                          <label className="text-sm font-medium text-gray-600 mb-1 block">Notes</label>
                          <Textarea
                            value={editData.notes}
                            onChange={(e) => setEditData({ ...editData, notes: e.target.value })}
                            placeholder="Add notes..."
                            rows={2}
                            data-testid={`edit-notes-${node.id}`}
                          />
                        </div>
                        <div className="flex gap-2 pt-2">
                          <Button
                            onClick={() => saveEdit(node.id)}
                            className="flex-1 bg-green-600 hover:bg-green-700 text-sm sm:text-base h-9 sm:h-10"
                            data-testid={`save-edit-${node.id}`}
                          >
                            <Check className="w-3 h-3 sm:w-4 sm:h-4 sm:mr-2" />
                            <span className="hidden sm:inline">Save</span>
                            <span className="sm:hidden">✓</span>
                          </Button>
                          <Button
                            onClick={cancelEdit}
                            variant="outline"
                            className="flex-1 text-sm sm:text-base h-9 sm:h-10"
                            data-testid={`cancel-edit-${node.id}`}
                          >
                            <X className="w-3 h-3 sm:w-4 sm:h-4 sm:mr-2" />
                            <span className="hidden sm:inline">Cancel</span>
                            <span className="sm:hidden">✕</span>
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <div className="space-y-2 sm:space-y-3">
                        <div className="flex justify-between items-center">
                          <span className="text-xs sm:text-sm text-gray-600 font-medium">Status:</span>
                          {getStatusBadge(node.status)}
                        </div>

                        {node.job_status && (
                          <div className="flex justify-between items-center">
                            <span className="text-xs sm:text-sm text-gray-600 font-medium">Job Status:</span>
                            {getJobStatusBadge(node.job_status)}
                          </div>
                        )}

                        {node.notes && (
                          <div className="pt-2 border-t">
                            <p className="text-xs text-gray-500 italic break-words">{node.notes}</p>
                          </div>
                        )}

                        <div className="text-xs text-gray-400 pt-2 border-t">
                          Updated: {new Date(node.last_updated).toLocaleString()}
                        </div>
                      </div>
                    )}
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