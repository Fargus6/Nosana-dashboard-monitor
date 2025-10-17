import { useState, useEffect } from "react";
import "@/App.css";
import axios from "axios";
import { Plus, Trash2, RefreshCw, Activity, ExternalLink, Edit2, Check, X, Eye, EyeOff, LogOut, Palette } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import { 
  sanitizeInput, 
  validateSolanaAddress, 
  validateEmail, 
  validatePassword,
  secureStorage,
  RateLimiter 
} from "@/utils/security";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Initialize rate limiters for client-side protection
const loginRateLimiter = new RateLimiter(5, 300000); // 5 attempts per 5 minutes
const apiRateLimiter = new RateLimiter(30, 60000); // 30 requests per minute

// Theme configurations
const themes = {
  default: {
    name: "Modern Blue",
    background: "min-h-screen bg-gradient-to-br from-slate-50 to-blue-50",
    card: "border-blue-200 shadow-lg backdrop-blur-sm bg-white/90",
    cardHover: "hover:shadow-xl",
    title: "bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent",
    button: "bg-blue-600 hover:bg-blue-700",
    buttonGradient: "bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700",
    badge: {
      online: "bg-green-500 text-white",
      offline: "bg-red-500 text-white",
      unknown: "bg-gray-400 text-white",
      running: "bg-blue-500 text-white",
      queue: "bg-yellow-500 text-white",
      idle: "bg-gray-500 text-white"
    }
  },
  neon80s: {
    name: "80s Neon",
    background: "min-h-screen bg-gradient-to-br from-gray-900 via-emerald-950 to-gray-900",
    card: "border-emerald-500 border-2 shadow-[0_0_15px_rgba(16,185,129,0.5)] backdrop-blur-sm bg-black/80",
    cardHover: "hover:shadow-[0_0_25px_rgba(16,185,129,0.8)]",
    title: "bg-gradient-to-r from-emerald-400 via-teal-400 to-cyan-400 bg-clip-text text-transparent",
    button: "bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 shadow-[0_0_10px_rgba(16,185,129,0.5)]",
    buttonGradient: "bg-gradient-to-r from-teal-400 to-emerald-500 hover:from-teal-500 hover:to-emerald-600 shadow-[0_0_10px_rgba(20,184,166,0.5)]",
    badge: {
      online: "bg-emerald-400 text-black shadow-[0_0_10px_rgba(52,211,153,0.6)]",
      offline: "bg-red-500 text-white shadow-[0_0_10px_rgba(239,68,68,0.6)]",
      unknown: "bg-gray-500 text-white shadow-[0_0_10px_rgba(107,114,128,0.6)]",
      running: "bg-cyan-400 text-black shadow-[0_0_10px_rgba(34,211,238,0.6)]",
      queue: "bg-yellow-400 text-black shadow-[0_0_10px_rgba(250,204,21,0.6)]",
      idle: "bg-teal-400 text-black shadow-[0_0_10px_rgba(45,212,191,0.6)]"
    },
    text: {
      primary: "text-emerald-200",
      secondary: "text-teal-300",
      muted: "text-emerald-300"
    }
  }
};

function App() {
  const [nodes, setNodes] = useState([]);
  const [newNodeAddress, setNewNodeAddress] = useState("");
  const [newNodeName, setNewNodeName] = useState("");
  const [loading, setLoading] = useState(false);
  const [editingNode, setEditingNode] = useState(null);
  const [editData, setEditData] = useState({});
  const [autoRefreshing, setAutoRefreshing] = useState(false);
  const [hiddenAddresses, setHiddenAddresses] = useState(new Set());
  const [hiddenBalances, setHiddenBalances] = useState(new Set());
  
  // Auth states
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [authLoading, setAuthLoading] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  
  // Theme state
  const [currentTheme, setCurrentTheme] = useState("default");
  const theme = themes[currentTheme];
  const [nextRefresh, setNextRefresh] = useState(null);

  // Load theme preference on mount
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme && themes[savedTheme]) {
      setCurrentTheme(savedTheme);
    }
  }, []);

  const toggleTheme = () => {
    const newTheme = currentTheme === "default" ? "neon80s" : "default";
    setCurrentTheme(newTheme);
    localStorage.setItem('theme', newTheme);
    toast.success(`Switched to ${themes[newTheme].name} theme!`);
  };

  // Check if user is logged in on mount
  useEffect(() => {
    // Check for Google OAuth session_id in URL fragment
    const hash = window.location.hash;
    if (hash.includes('session_id=')) {
      const sessionId = hash.split('session_id=')[1].split('&')[0];
      handleGoogleAuth(sessionId);
      return;
    }

    const token = secureStorage.get('token');
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      verifyToken();
    }
  }, []);

  useEffect(() => {
    if (isAuthenticated) {
      loadNodes();
    }
  }, [isAuthenticated]);

  // Update countdown display every minute
  useEffect(() => {
    if (!nextRefresh) return;

    const countdownInterval = setInterval(() => {
      setNextRefresh(prevTime => prevTime); // Force re-render
    }, 60000); // Update display every minute

    return () => clearInterval(countdownInterval);
  }, [nextRefresh]);
  useEffect(() => {
    if (!isAuthenticated || nodes.length === 0) {
      setNextRefresh(null);
      return;
    }

    // Set initial next refresh time
    const initialTime = new Date(Date.now() + 120000);
    setNextRefresh(initialTime);

    const autoRefreshInterval = setInterval(() => {
      console.log("Auto-refreshing node status...");
      autoRefreshAllNodes(true); // Silent refresh
      
      // Update next refresh time
      const nextTime = new Date(Date.now() + 120000);
      setNextRefresh(nextTime);
    }, 120000); // 2 minutes

    return () => {
      clearInterval(autoRefreshInterval);
      setNextRefresh(null);
    };
  }, [isAuthenticated, nodes.length]);

  // Hide all addresses by default when nodes load
  useEffect(() => {
    if (nodes.length > 0) {
      const allNodeIds = new Set(nodes.map(node => node.id));
      setHiddenAddresses(allNodeIds);
      setHiddenBalances(allNodeIds); // Also hide balances by default
    }
  }, [nodes.length]);

  const verifyToken = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`);
      setCurrentUser(response.data);
      setIsAuthenticated(true);
    } catch (error) {
      secureStorage.remove('token');
      delete axios.defaults.headers.common['Authorization'];
      setIsAuthenticated(false);
      console.error("Token verification failed:", error);
    }
  };

  const handleGoogleAuth = async (sessionId) => {
    try {
      setAuthLoading(true);
      // Validate session ID format
      if (!sessionId || sessionId.length < 10) {
        throw new Error("Invalid session ID");
      }
      
      const response = await axios.post(`${API}/auth/google`, null, {
        params: { session_id: sanitizeInput(sessionId) }
      });
      
      const token = response.data.access_token;
      secureStorage.set('token', token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      
      setIsAuthenticated(true);
      toast.success("Signed in with Google successfully!");
      
      // Clean URL
      window.history.replaceState({}, document.title, window.location.pathname);
    } catch (error) {
      toast.error("Google sign-in failed");
      console.error("Google auth error:", error);
    } finally {
      setAuthLoading(false);
    }
  };

  const handleGoogleSignIn = () => {
    const redirectUrl = window.location.origin;
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  const handleRegister = async () => {
    // Sanitize inputs
    const sanitizedEmail = sanitizeInput(email).toLowerCase().trim();
    const sanitizedPassword = password; // Don't sanitize password, just validate
    
    // Validate email
    if (!validateEmail(sanitizedEmail)) {
      toast.error("Please enter a valid email address");
      return;
    }
    
    // Validate password strength
    const passwordValidation = validatePassword(sanitizedPassword);
    if (!passwordValidation.isValid) {
      toast.error(passwordValidation.errors[0]); // Show first error
      return;
    }

    // Check rate limit
    const rateLimitCheck = loginRateLimiter.checkLimit('register');
    if (!rateLimitCheck.allowed) {
      toast.error(`Too many registration attempts. Please wait ${rateLimitCheck.resetIn} seconds.`);
      return;
    }

    try {
      setAuthLoading(true);
      const response = await axios.post(`${API}/auth/register`, { 
        email: sanitizedEmail, 
        password: sanitizedPassword 
      });
      const token = response.data.access_token;
      
      secureStorage.set('token', token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      
      setIsAuthenticated(true);
      setCurrentUser({ email: sanitizedEmail });
      toast.success("Account created successfully!");
      setEmail("");
      setPassword("");
      
      // Reset rate limit on success
      loginRateLimiter.reset('register');
    } catch (error) {
      const errorMessage = error.response?.data?.detail || "Registration failed";
      toast.error(errorMessage);
      console.error("Registration error:", error);
    } finally {
      setAuthLoading(false);
    }
  };

  const handleLogin = async () => {
    // Sanitize inputs
    const sanitizedEmail = sanitizeInput(email).toLowerCase().trim();
    const sanitizedPassword = password;
    
    // Validate email
    if (!validateEmail(sanitizedEmail)) {
      toast.error("Please enter a valid email address");
      return;
    }
    
    if (!sanitizedPassword) {
      toast.error("Please enter your password");
      return;
    }

    // Check rate limit
    const rateLimitCheck = loginRateLimiter.checkLimit('login');
    if (!rateLimitCheck.allowed) {
      toast.error(`Too many login attempts. Please wait ${rateLimitCheck.resetIn} seconds.`);
      return;
    }

    try {
      setAuthLoading(true);
      const formData = new FormData();
      formData.append('username', sanitizedEmail);
      formData.append('password', sanitizedPassword);
      
      const response = await axios.post(`${API}/auth/login`, formData);
      const token = response.data.access_token;
      
      secureStorage.set('token', token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      
      setIsAuthenticated(true);
      setCurrentUser({ email: sanitizedEmail });
      toast.success("Logged in successfully!");
      setEmail("");
      setPassword("");
      
      // Reset rate limit on successful login
      loginRateLimiter.reset('login');
    } catch (error) {
      const errorMessage = error.response?.data?.detail || "Login failed";
      toast.error(errorMessage);
      console.error("Login error:", error);
    } finally {
      setAuthLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
    setIsAuthenticated(false);
    setCurrentUser(null);
    setNodes([]);
    toast.success("Logged out successfully");
  };

  const loadNodes = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/nodes`);
      setNodes(response.data);
    } catch (error) {
      console.error("Error loading nodes:", error);
      if (error.response?.status === 401) {
        handleLogout();
      } else {
        toast.error("Failed to load nodes");
      }
    } finally {
      setLoading(false);
    }
  };

  const autoRefreshAllNodes = async (silent = false) => {
    try {
      setAutoRefreshing(true);
      if (!silent) {
        toast.info("Checking node status from Solana blockchain...");
      }
      
      const response = await axios.post(`${API}/nodes/refresh-all-status`);
      
      if (response.data.updated > 0) {
        if (!silent) {
          toast.success(`Updated ${response.data.updated} nodes from blockchain!`);
        }
        
        // Check for offline nodes after refresh
        const updatedNodes = await axios.get(`${API}/nodes`);
        const offlineNodes = updatedNodes.data.filter(node => {
          const oldNode = nodes.find(n => n.id === node.id);
          return oldNode && oldNode.status !== 'offline' && node.status === 'offline';
        });
        
        // Show offline alerts
        offlineNodes.forEach(node => {
          toast.error(`⚠️ Node ${node.name || node.address.substring(0, 8) + '...'} went OFFLINE!`, {
            duration: 10000,
          });
        });
        
        await loadNodes();
      } else {
        if (!silent) {
          toast.warning("No nodes updated");
        }
      }
      
      if (response.data.errors && response.data.errors.length > 0) {
        if (!silent) {
          toast.error(`${response.data.errors.length} nodes had errors`);
        }
      }
    } catch (error) {
      console.error("Error auto-refreshing:", error);
      if (!silent) {
        toast.error("Failed to auto-refresh node status");
      }
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

  const toggleBalanceVisibility = (nodeId) => {
    setHiddenBalances(prev => {
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

  const formatBalance = (balance, nodeId) => {
    if (hiddenBalances.has(nodeId)) {
      return "••••••";
    }
    return balance?.toFixed(2) || "0.00";
  };

  const getStatusBadge = (status) => {
    return (
      <Badge className={theme.badge[status] || theme.badge.unknown} data-testid={`status-badge-${status}`}>
        {status?.toUpperCase() || "UNKNOWN"}
      </Badge>
    );
  };

  const getJobStatusBadge = (jobStatus) => {
    if (!jobStatus) return null;

    return (
      <Badge className={theme.badge[jobStatus] || ""} data-testid={`job-badge-${jobStatus}`}>
        {jobStatus?.toUpperCase()}
      </Badge>
    );
  };

  // Login/Register UI
  if (!isAuthenticated) {
    return (
      <div className={theme.background + " flex items-center justify-center p-4"}>
        {/* Pixelated tech background for neon theme */}
        {currentTheme === "neon80s" && <div className="tech-pattern-bg"></div>}
        
        {/* Theme Toggle Button */}
        <Button
          onClick={toggleTheme}
          variant="outline"
          size="icon"
          className="fixed top-4 right-4 z-50"
          title={`Switch to ${currentTheme === "default" ? "80s Neon" : "Modern Blue"} theme`}
          data-testid="theme-toggle"
        >
          <Palette className="w-4 h-4" />
        </Button>

        <Card className={theme.card + " w-full max-w-md shadow-xl"}>
          <CardHeader className="text-center">
            <CardTitle className={theme.title + " text-2xl sm:text-3xl font-bold mb-2"}>
              Nosana Node Monitor
            </CardTitle>
            <CardDescription className={currentTheme === "neon80s" ? theme.text.muted : ""}>
              Login or create an account to monitor your nodes
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="login" className="w-full">
              <TabsList className="grid w-full grid-cols-2 mb-4">
                <TabsTrigger value="login">Login</TabsTrigger>
                <TabsTrigger value="register">Register</TabsTrigger>
              </TabsList>
              
              <TabsContent value="login">
                <div className="space-y-4">
                  <div>
                    <Input
                      type="email"
                      placeholder="Email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      onKeyPress={(e) => e.key === "Enter" && handleLogin()}
                      data-testid="login-email"
                    />
                  </div>
                  <div>
                    <Input
                      type="password"
                      placeholder="Password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      onKeyPress={(e) => e.key === "Enter" && handleLogin()}
                      data-testid="login-password"
                    />
                  </div>
                  <Button
                    onClick={handleLogin}
                    disabled={authLoading}
                    className={"w-full " + theme.button}
                    data-testid="login-button"
                  >
                    {authLoading ? "Logging in..." : "Login"}
                  </Button>
                  
                  <div className="relative">
                    <div className="absolute inset-0 flex items-center">
                      <span className="w-full border-t" />
                    </div>
                    <div className="relative flex justify-center text-xs uppercase">
                      <span className="bg-white px-2 text-gray-500">Or continue with</span>
                    </div>
                  </div>
                  
                  <Button
                    onClick={handleGoogleSignIn}
                    variant="outline"
                    className={"w-full " + (currentTheme === "neon80s" ? "text-white hover:text-emerald-300 border-emerald-500" : "")}
                    data-testid="google-signin-button"
                  >
                    <svg className="mr-2 h-4 w-4" viewBox="0 0 24 24">
                      <path
                        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                        fill="#4285F4"
                      />
                      <path
                        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                        fill="#34A853"
                      />
                      <path
                        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                        fill="#FBBC05"
                      />
                      <path
                        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                        fill="#EA4335"
                      />
                    </svg>
                    Sign in with Google
                  </Button>
                </div>
              </TabsContent>
              
              <TabsContent value="register">
                <div className="space-y-4">
                  <div>
                    <Input
                      type="email"
                      placeholder="Email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      onKeyPress={(e) => e.key === "Enter" && handleRegister()}
                      data-testid="register-email"
                    />
                  </div>
                  <div>
                    <Input
                      type="password"
                      placeholder="Password (min 6 characters)"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      onKeyPress={(e) => e.key === "Enter" && handleRegister()}
                      data-testid="register-password"
                    />
                  </div>
                  <Button
                    onClick={handleRegister}
                    disabled={authLoading}
                    className={"w-full " + theme.buttonGradient}
                    data-testid="register-button"
                  >
                    {authLoading ? "Creating account..." : "Create Account"}
                  </Button>
                  
                  <div className="relative">
                    <div className="absolute inset-0 flex items-center">
                      <span className="w-full border-t" />
                    </div>
                    <div className="relative flex justify-center text-xs uppercase">
                      <span className="bg-white px-2 text-gray-500">Or continue with</span>
                    </div>
                  </div>
                  
                  <Button
                    onClick={handleGoogleSignIn}
                    variant="outline"
                    className={"w-full " + (currentTheme === "neon80s" ? "text-white hover:text-emerald-300 border-emerald-500" : "")}
                    data-testid="google-register-button"
                  >
                    <svg className="mr-2 h-4 w-4" viewBox="0 0 24 24">
                      <path
                        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                        fill="#4285F4"
                      />
                      <path
                        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                        fill="#34A853"
                      />
                      <path
                        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                        fill="#FBBC05"
                      />
                      <path
                        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                        fill="#EA4335"
                      />
                    </svg>
                    Sign up with Google
                  </Button>
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Main App UI (after login)
  return (
    <div className={theme.background}>
      {/* Pixelated tech background for neon theme */}
      {currentTheme === "neon80s" && <div className="tech-pattern-bg"></div>}
      
      {/* Theme Toggle Button */}
      <Button
        onClick={toggleTheme}
        variant="outline"
        size="icon"
        className="fixed top-4 right-16 z-50"
        title={`Switch to ${currentTheme === "default" ? "80s Neon" : "Modern Blue"} theme`}
        data-testid="theme-toggle"
      >
        <Palette className="w-4 h-4" />
      </Button>

      <div className="container mx-auto px-3 sm:px-4 py-4 sm:py-8 max-w-7xl relative z-10">
        {/* Header with Logout */}
        <div className="mb-4 sm:mb-8 flex justify-between items-start">
          <div>
            <h1 className={theme.title + " text-3xl sm:text-4xl lg:text-5xl font-bold mb-2"} data-testid="app-title">
              Nosana Node Monitor
            </h1>
            <p className={"text-sm sm:text-base " + (currentTheme === "neon80s" ? theme.text.secondary : "text-gray-600")}>
              Monitor your Nosana AI network nodes in real-time
            </p>
          </div>
          <div className="flex flex-col items-end gap-2">
            <p className={"text-xs sm:text-sm " + (currentTheme === "neon80s" ? theme.text.muted : "text-gray-600")}>
              {currentUser?.email}
            </p>
            <Button
              onClick={handleLogout}
              variant="outline"
              size="sm"
              className="gap-2"
              data-testid="logout-button"
            >
              <LogOut className="w-3 h-3 sm:w-4 sm:h-4" />
              <span className="hidden sm:inline">Logout</span>
            </Button>
          </div>
        </div>

        {/* Add Node Section */}
        <Card className={theme.card + " mb-4 sm:mb-8 shadow-lg"} data-testid="add-node-card">
          <CardHeader className="pb-3 sm:pb-6">
            <CardTitle className={"flex items-center gap-2 text-base sm:text-lg " + (currentTheme === "neon80s" ? theme.text.primary : "")}>
              <Plus className="w-4 h-4 sm:w-5 sm:h-5" />
              Add New Node
            </CardTitle>
            <CardDescription className={currentTheme === "neon80s" ? theme.text.muted + " text-xs sm:text-sm" : "text-xs sm:text-sm"}>
              Enter your Nosana node address and optional name
            </CardDescription>
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
                <Button onClick={addNode} className={theme.button + " h-10 sm:h-auto px-3 sm:px-4"} data-testid="add-node-button">
                  <Plus className="w-4 h-4 sm:mr-2" />
                  <span className="hidden sm:inline">Add</span>
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 mb-4 sm:mb-6">
          <div>
            <h2 className={"text-lg sm:text-xl font-semibold " + (currentTheme === "neon80s" ? theme.text.primary : "text-gray-700")}>
              Your Nodes ({nodes.length})
            </h2>
            {nextRefresh && (
              <p className={"text-xs mt-1 " + (currentTheme === "neon80s" ? theme.text.muted : "text-gray-500")}>
                🔄 Auto-refresh in {Math.ceil((nextRefresh - new Date()) / 1000 / 60)} min
              </p>
            )}
          </div>
          <div className="flex gap-2 w-full sm:w-auto">
            <Button
              onClick={autoRefreshAllNodes}
              disabled={autoRefreshing || nodes.length === 0}
              className={"flex-1 sm:flex-none gap-2 text-xs sm:text-sm h-9 sm:h-10 " + theme.buttonGradient}
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

        {/* Rest of the nodes display code remains the same */}
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
                  className={theme.card + " " + theme.cardHover + " transition-shadow"}
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
                          <CardTitle className={"text-base sm:text-lg mb-1 " + (currentTheme === "neon80s" ? theme.text.primary : "")} data-testid={`node-name-${node.id}`}>
                            {node.name || "Unnamed Node"}
                          </CardTitle>
                        )}
                        <p className={"text-xs font-mono break-all " + (currentTheme === "neon80s" ? theme.text.muted : "text-gray-500")} data-testid={`node-address-${node.id}`}>
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
                  <CardContent className="pt-2 sm:pt-4">
                    {isEditing ? (
                      <div className="space-y-3">
                        <div>
                          <label className="text-xs sm:text-sm font-medium text-gray-600 mb-1 block">Status</label>
                          <Select
                            value={editData.status}
                            onValueChange={(value) => setEditData({ ...editData, status: value })}
                          >
                            <SelectTrigger data-testid={`edit-status-${node.id}`} className="h-9 sm:h-10 text-sm">
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
                          <label className="text-xs sm:text-sm font-medium text-gray-600 mb-1 block">Job Status</label>
                          <Select
                            value={editData.job_status}
                            onValueChange={(value) => setEditData({ ...editData, job_status: value })}
                          >
                            <SelectTrigger data-testid={`edit-job-status-${node.id}`} className="h-9 sm:h-10 text-sm">
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
                          <label className="text-xs sm:text-sm font-medium text-gray-600 mb-1 block">Notes</label>
                          <Textarea
                            value={editData.notes}
                            onChange={(e) => setEditData({ ...editData, notes: e.target.value })}
                            placeholder="Add notes..."
                            rows={2}
                            className="text-sm"
                            data-testid={`edit-notes-${node.id}`}
                          />
                        </div>
                        <div className="flex gap-2 pt-2">
                          <Button
                            onClick={() => saveEdit(node.id)}
                            className={"flex-1 bg-green-600 hover:bg-green-700 h-9 sm:h-10 text-sm " + (currentTheme === "neon80s" ? "shadow-[0_0_10px_rgba(74,222,128,0.5)]" : "")}
                            data-testid={`save-edit-${node.id}`}
                          >
                            <Check className="w-3 h-3 sm:w-4 sm:h-4 mr-2" />
                            Save
                          </Button>
                          <Button
                            onClick={cancelEdit}
                            variant="outline"
                            className="flex-1 h-9 sm:h-10 text-sm"
                            data-testid={`cancel-edit-${node.id}`}
                          >
                            <X className="w-3 h-3 sm:w-4 sm:h-4 mr-2" />
                            Cancel
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <div className="space-y-2 sm:space-y-3">
                        <div className="flex justify-between items-center">
                          <span className={"text-xs sm:text-sm font-medium " + (currentTheme === "neon80s" ? theme.text.secondary : "text-gray-600")}>
                            Status:
                          </span>
                          {getStatusBadge(node.status)}
                        </div>

                        {node.job_status && (
                          <div className="flex justify-between items-center">
                            <span className={"text-xs sm:text-sm font-medium " + (currentTheme === "neon80s" ? theme.text.secondary : "text-gray-600")}>
                              Job Status:
                            </span>
                            {getJobStatusBadge(node.job_status)}
                          </div>
                        )}

                        {/* Balances Section */}
                        <div className="pt-2 border-t space-y-2">
                          <div className="flex justify-between items-center">
                            <span className={"text-xs font-medium " + (currentTheme === "neon80s" ? theme.text.secondary : "text-gray-600")}>
                              NOS Balance:
                            </span>
                            <div className="flex items-center gap-2">
                              <span className={"text-xs font-mono " + (currentTheme === "neon80s" ? theme.text.primary : "text-gray-700")}>
                                {formatBalance(node.nos_balance, node.id)} NOS
                              </span>
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => toggleBalanceVisibility(node.id)}
                                className={"h-6 w-6 " + (currentTheme === "neon80s" ? "text-white hover:text-emerald-300" : "")}
                                title={hiddenBalances.has(node.id) ? "Show balances" : "Hide balances"}
                              >
                                {hiddenBalances.has(node.id) ? (
                                  <EyeOff className="w-3 h-3" />
                                ) : (
                                  <Eye className="w-3 h-3" />
                                )}
                              </Button>
                            </div>
                          </div>
                          
                          <div className="flex justify-between items-center">
                            <span className={"text-xs font-medium " + (currentTheme === "neon80s" ? theme.text.secondary : "text-gray-600")}>
                              SOL Balance:
                            </span>
                            <span className={"text-xs font-mono " + (currentTheme === "neon80s" ? theme.text.primary : "text-gray-700")}>
                              {formatBalance(node.sol_balance, node.id)} SOL
                            </span>
                          </div>
                        </div>

                        {/* Stats Section */}
                        <div className="pt-2 border-t space-y-2">
                          {node.total_jobs !== null && node.total_jobs !== undefined && (
                            <div className="flex justify-between items-center">
                              <span className={"text-xs font-medium " + (currentTheme === "neon80s" ? theme.text.secondary : "text-gray-600")}>
                                Total Jobs:
                              </span>
                              <span className={"text-xs font-semibold " + (currentTheme === "neon80s" ? theme.text.primary : "text-gray-700")}>
                                {node.total_jobs}
                              </span>
                            </div>
                          )}
                          
                          {node.availability_score !== null && node.availability_score !== undefined && (
                            <div className="flex justify-between items-center">
                              <span className={"text-xs font-medium " + (currentTheme === "neon80s" ? theme.text.secondary : "text-gray-600")}>
                                Availability:
                              </span>
                              <span className={"text-xs font-semibold " + (currentTheme === "neon80s" ? theme.text.primary : "text-gray-700")}>
                                {node.availability_score.toFixed(1)}%
                              </span>
                            </div>
                          )}
                        </div>

                        {node.notes && (
                          <div className="pt-2 border-t">
                            <p className={"text-xs italic " + (currentTheme === "neon80s" ? theme.text.muted : "text-gray-500")}>
                              {node.notes}
                            </p>
                          </div>
                        )}

                        <div className={"text-xs pt-2 border-t " + (currentTheme === "neon80s" ? theme.text.muted : "text-gray-400")}>
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