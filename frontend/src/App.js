import { useState, useEffect } from "react";
import "@/App.css";
import axios from "axios";
import { Plus, Trash2, RefreshCw, Activity, ExternalLink, Edit2, Check, X, Eye, EyeOff, LogOut, Moon, Bell, BellOff, Settings } from "lucide-react";
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
import { messaging, getToken, onMessage, VAPID_KEY } from "@/firebase";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Initialize rate limiters for client-side protection
const loginRateLimiter = new RateLimiter(5, 300000); // 5 attempts per 5 minutes
const apiRateLimiter = new RateLimiter(30, 60000); // 30 requests per minute

// Theme configurations
const themes = {
  default: {
    name: "Dark Mode",
    background: "min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900",
    card: "border-blue-500/30 shadow-lg backdrop-blur-sm bg-slate-800/90",
    cardHover: "hover:shadow-xl hover:shadow-blue-500/20",
    title: "bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent",
    button: "bg-blue-600 hover:bg-blue-700 text-white",
    buttonGradient: "bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 text-white",
    badge: {
      online: "bg-green-500 text-white",
      offline: "bg-red-500 text-white",
      unknown: "bg-gray-400 text-white",
      running: "bg-blue-500 text-white",
      queue: "bg-yellow-500 text-white",
      idle: "bg-gray-500 text-white"
    },
    text: {
      primary: "text-white",
      secondary: "text-slate-300",
      muted: "text-slate-400"
    },
    control: {
      button: "bg-slate-700 border-slate-600 text-white hover:bg-slate-600",
      dropdown: "bg-slate-700 border-slate-600 text-white"
    }
  },
  neon80s: {
    name: "80s Neon",
    background: "min-h-screen bg-gradient-to-br from-gray-900 via-emerald-950 to-gray-900",
    card: "border-emerald-500 border-2 shadow-[0_0_15px_rgba(16,185,129,0.5)] backdrop-blur-sm bg-black/80",
    cardHover: "hover:shadow-[0_0_25px_rgba(16,185,129,0.8)]",
    title: "bg-gradient-to-r from-emerald-400 via-teal-400 to-cyan-400 bg-clip-text text-transparent",
    button: "bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 shadow-[0_0_10px_rgba(16,185,129,0.5)] text-white",
    buttonGradient: "bg-gradient-to-r from-teal-400 to-emerald-500 hover:from-teal-500 hover:to-emerald-600 shadow-[0_0_10px_rgba(20,184,166,0.5)] text-black",
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
    },
    control: {
      button: "bg-emerald-900/50 border-emerald-500 text-emerald-200 hover:bg-emerald-800/50",
      dropdown: "bg-emerald-900/50 border-emerald-500 text-emerald-200"
    }
  },
  cyber: {
    name: "Cyber",
    background: "min-h-screen bg-[#0a0e27]",
    card: "border-[#00ff00] border-2 shadow-[0_0_30px_rgba(0,255,0,0.3)] backdrop-blur-sm bg-[rgba(10,14,39,0.8)] cyberpunk-font-body",
    cardHover: "hover:shadow-[0_0_40px_rgba(0,255,0,0.6)] hover:border-[#00ff00]",
    title: "text-white cyberpunk-font-heading",
    button: "bg-gradient-to-br from-[#ffffff] to-[#e0e0e0] border-2 border-[#ffffff] text-black shadow-[0_0_20px_rgba(255,255,255,0.6)] hover:shadow-[0_0_30px_rgba(255,255,255,0.8)] hover:bg-gradient-to-br hover:from-[#ffffff] hover:to-[#cccccc] cyberpunk-font-heading font-bold",
    buttonGradient: "bg-gradient-to-br from-[#00f0ff] to-[#00ff00] border-2 border-[#ffff00] text-white shadow-[0_0_25px_rgba(0,240,255,0.7)] hover:shadow-[0_0_35px_rgba(0,255,0,0.9)] cyberpunk-font-heading font-bold",
    badge: {
      online: "bg-[#00ff00] text-black shadow-[0_0_20px_#00ff00] font-bold uppercase",
      offline: "bg-[#ff0000] text-white shadow-[0_0_20px_#ff0000] font-bold uppercase animate-pulse",
      unknown: "bg-gray-500 text-white shadow-[0_0_15px_gray] font-bold uppercase",
      running: "bg-[#00f0ff] text-black shadow-[0_0_20px_#00f0ff] font-bold uppercase",
      queue: "bg-[#ffff00] text-black shadow-[0_0_20px_#ffff00] font-bold uppercase",
      idle: "bg-[#888] text-white shadow-[0_0_15px_#888] font-bold uppercase"
    },
    text: {
      primary: "text-white cyberpunk-font-body",
      secondary: "text-white/90 cyberpunk-font-body",
      muted: "text-white/50 cyberpunk-font-body"
    },
    control: {
      button: "bg-transparent border-[#00ff00] border-2 text-[#00f0ff] hover:bg-[#00ff00]/20 hover:shadow-[0_0_20px_rgba(0,255,0,0.6)] cyberpunk-font-heading font-bold",
      dropdown: "bg-[rgba(0,0,0,0.5)] border-[#00ff00] border-2 text-[#00f0ff] cyberpunk-font-body"
    }
  }
};

// Matrix Rain Effect Component
const MatrixRain = () => {
  useEffect(() => {
    const characters = '01アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン';
    const columns = Math.floor(window.innerWidth / 20);
    const matrixContainer = document.getElementById('matrix-rain');
    
    if (!matrixContainer) return;
    
    // Clear existing columns
    matrixContainer.innerHTML = '';
    
    for (let i = 0; i < columns; i++) {
      const column = document.createElement('div');
      column.className = 'matrix-column';
      column.style.left = `${i * 20}px`;
      column.style.animationDuration = `${Math.random() * 10 + 15}s`;
      column.style.animationDelay = `${Math.random() * 5}s`;
      
      let text = '';
      const lineCount = Math.floor(Math.random() * 20) + 10;
      for (let j = 0; j < lineCount; j++) {
        text += characters[Math.floor(Math.random() * characters.length)] + '\n';
      }
      column.textContent = text;
      
      matrixContainer.appendChild(column);
    }
  }, []);
  
  return <div id="matrix-rain" className="matrix-bg"></div>;
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
  const [serverStatus, setServerStatus] = useState('online'); // online, waking, offline
  
  // Theme state
  const [currentTheme, setCurrentTheme] = useState("default");
  const theme = themes[currentTheme];
  const [nextRefresh, setNextRefresh] = useState(null);
  
  // Auto-refresh interval state (in milliseconds)
  const [refreshInterval, setRefreshInterval] = useState(120000); // Default 2 minutes
  
  // Refresh interval options
  const refreshIntervalOptions = [
    { label: "1 minute", value: 60000 },
    { label: "2 minutes", value: 120000 },
    { label: "3 minutes", value: 180000 },
    { label: "10 minutes", value: 600000 }
  ];

  // Notification states
  const [notificationsEnabled, setNotificationsEnabled] = useState(false);
  const [notificationPreferences, setNotificationPreferences] = useState({
    notify_offline: true,
    notify_online: true,
    notify_job_started: true,
    notify_job_completed: true,
    vibration: true,
    sound: true
  });
  const [showSettings, setShowSettings] = useState(false);

  // Load theme and refresh interval preference on mount
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme && themes[savedTheme]) {
      setCurrentTheme(savedTheme);
    }
    
    const savedInterval = localStorage.getItem('refreshInterval');
    if (savedInterval) {
      setRefreshInterval(parseInt(savedInterval));
    }
  }, []);

  const handleThemeChange = (newTheme) => {
    setCurrentTheme(newTheme);
    localStorage.setItem('theme', newTheme);
    toast.success(`Switched to ${themes[newTheme].name} theme!`);
  };
  
  const handleRefreshIntervalChange = (newInterval) => {
    setRefreshInterval(newInterval);
    localStorage.setItem('refreshInterval', newInterval.toString());
    const option = refreshIntervalOptions.find(opt => opt.value === newInterval);
    toast.success(`Auto-refresh set to ${option.label}`);
  };

  // Notification Functions
  const requestNotificationPermission = async () => {
    try {
      if (!messaging) {
        toast.error("Notifications not supported in this browser");
        return;
      }

      console.log("Requesting notification permission...");
      const permission = await Notification.requestPermission();
      
      if (permission === 'granted') {
        console.log('Notification permission granted');
        
        // Register service worker
        if ('serviceWorker' in navigator) {
          console.log("Registering service worker...");
          
          // First, unregister any existing service workers
          const existingRegistrations = await navigator.serviceWorker.getRegistrations();
          for (let registration of existingRegistrations) {
            if (registration.active?.scriptURL.includes('firebase-messaging-sw')) {
              console.log("Unregistering old service worker...");
              await registration.unregister();
            }
          }
          
          // Register new service worker
          const registration = await navigator.serviceWorker.register('/firebase-messaging-sw.js', {
            scope: '/'
          });
          
          console.log('Service Worker registered:', registration);
          
          // Wait for service worker to be ready
          await navigator.serviceWorker.ready;
          console.log('Service Worker ready');
          
          // Additional wait to ensure service worker is fully active
          let activeWorker = registration.active || registration.installing || registration.waiting;
          if (activeWorker && activeWorker.state !== 'activated') {
            await new Promise((resolve) => {
              activeWorker.addEventListener('statechange', (e) => {
                if (e.target.state === 'activated') {
                  resolve();
                }
              });
            });
          }
          
          console.log('Getting FCM token...');
          
          // Get FCM token with retry logic
          let token = null;
          let retries = 3;
          
          while (!token && retries > 0) {
            try {
              token = await getToken(messaging, { 
                vapidKey: VAPID_KEY,
                serviceWorkerRegistration: registration
              });
              
              if (token) {
                console.log('FCM Token obtained:', token.substring(0, 20) + '...');
                break;
              }
            } catch (err) {
              console.warn(`Token attempt failed (${retries} retries left):`, err);
              retries--;
              if (retries > 0) {
                await new Promise(resolve => setTimeout(resolve, 1000)); // Wait 1 second before retry
              }
            }
          }
          
          if (token) {
            // Register token with backend
            console.log('Registering token with backend...');
            await axios.post(`${API}/notifications/register-token`, null, {
              params: { token }
            });
            
            setNotificationsEnabled(true);
            toast.success("Push notifications enabled!");
            
            // Load preferences
            loadNotificationPreferences();
          } else {
            throw new Error("Failed to obtain FCM token after retries");
          }
        } else {
          throw new Error("Service Workers not supported in this browser");
        }
      } else {
        toast.error("Notification permission denied");
      }
    } catch (error) {
      console.error('Error enabling notifications:', error);
      toast.error("Failed to enable notifications: " + error.message);
    }
  };

  const loadNotificationPreferences = async () => {
    try {
      const response = await axios.get(`${API}/notifications/preferences`);
      setNotificationPreferences(response.data);
    } catch (error) {
      console.error('Error loading preferences:', error);
    }
  };

  const saveNotificationPreferences = async (prefs) => {
    try {
      await axios.post(`${API}/notifications/preferences`, prefs);
      setNotificationPreferences(prefs);
      toast.success("Notification preferences saved!");
    } catch (error) {
      console.error('Error saving preferences:', error);
      toast.error("Failed to save preferences");
    }
  };

  const sendTestNotification = async () => {
    try {
      const response = await axios.post(`${API}/notifications/test`);
      toast.success(`Test notification sent to ${response.data.sent} device(s)`);
    } catch (error) {
      console.error('Error sending test notification:', error);
      toast.error(error.response?.data?.detail || "Failed to send test notification");
    }
  };

  // Setup axios interceptor separately
  useEffect(() => {
    const interceptor = axios.interceptors.response.use(
      (response) => response,
      (error) => {
        // Don't logout on network errors (server might be waking up)
        if (!error.response) {
          console.log("Network error - server might be sleeping");
          toast.error("Connection issue. Retrying...", { duration: 2000 });
          return Promise.reject(error);
        }
        
        // Only logout on actual unauthorized errors (invalid token)
        // Not on server startup/wakeup issues
        if (error.response?.status === 401 && isAuthenticated) {
          // Check if it's a real auth error (not server waking up)
          const isAuthEndpoint = error.config?.url?.includes('/auth/');
          if (!isAuthEndpoint) {
            // For protected endpoints, just show error, don't logout immediately
            console.log("Auth error on protected endpoint - might be server waking up");
            return Promise.reject(error);
          }
        }
        
        // Handle rate limiting
        if (error.response?.status === 429) {
          toast.error("Too many requests. Please slow down.");
        }
        
        return Promise.reject(error);
      }
    );
    
    // Cleanup interceptor on unmount
    return () => {
      axios.interceptors.response.eject(interceptor);
    };
  }, [isAuthenticated]);

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
      
      // Check if notifications are already enabled
      if (Notification.permission === 'granted') {
        setNotificationsEnabled(true);
        loadNotificationPreferences();
      }
    }
  }, [isAuthenticated]);

  // Setup foreground notification listener
  useEffect(() => {
    if (!messaging || !isAuthenticated) return;

    const unsubscribe = onMessage(messaging, (payload) => {
      console.log('Foreground notification received:', payload);
      
      const title = payload.notification?.title || 'Notification';
      const body = payload.notification?.body || '';
      
      // Show toast notification
      toast.info(
        <div>
          <div className="font-semibold">{title}</div>
          <div className="text-sm">{body}</div>
        </div>,
        { duration: 5000 }
      );
      
      // Vibrate if enabled
      if (notificationPreferences.vibration && 'vibrate' in navigator) {
        navigator.vibrate([200, 100, 200]);
      }
      
      // Reload nodes to show updated status
      loadNodes();
    });

    return () => unsubscribe();
  }, [messaging, isAuthenticated, notificationPreferences]);

  // Keep-alive heartbeat to prevent backend from sleeping
  useEffect(() => {
    if (!isAuthenticated) return;

    const keepAlive = setInterval(async () => {
      try {
        // Ping health endpoint to keep backend alive
        await axios.get(`${API}/health`, { timeout: 5000 });
        setServerStatus('online');
        console.log("Keep-alive ping successful");
      } catch (error) {
        console.log("Keep-alive ping failed (server might be sleeping):", error.message);
        setServerStatus('waking');
      }
    }, 45000); // Every 45 seconds

    return () => clearInterval(keepAlive);
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

    // Set initial next refresh time using dynamic interval
    const initialTime = new Date(Date.now() + refreshInterval);
    setNextRefresh(initialTime);

    const autoRefreshInterval = setInterval(() => {
      console.log("Auto-refreshing node status and GUI...");
      // Refresh both blockchain data AND GUI
      autoRefreshAllNodes(true); // Silent blockchain refresh
      
      // Update next refresh time
      const nextTime = new Date(Date.now() + refreshInterval);
      setNextRefresh(nextTime);
    }, refreshInterval); // Use dynamic interval

    return () => {
      clearInterval(autoRefreshInterval);
      setNextRefresh(null);
    };
  }, [isAuthenticated, nodes.length, refreshInterval]); // Add refreshInterval dependency

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
      // Only logout on actual auth errors, not network issues
      if (error.response?.status === 401) {
        // Token is invalid or expired
        secureStorage.remove('token');
        delete axios.defaults.headers.common['Authorization'];
        setIsAuthenticated(false);
        console.error("Token verification failed - invalid token");
      } else {
        // Network error or server waking up - don't logout
        console.log("Token verification failed due to network issue:", error.message);
      }
    }
  };

  const handleGoogleAuth = async (sessionId) => {
    try {
      setAuthLoading(true);
      // Validate session ID format (but don't sanitize - it's a secure token)
      if (!sessionId || sessionId.length < 10) {
        throw new Error("Invalid session ID");
      }
      
      const response = await axios.post(`${API}/auth/google`, null, {
        params: { session_id: sessionId }  // Don't sanitize tokens/session IDs
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
    secureStorage.remove('token');
    delete axios.defaults.headers.common['Authorization'];
    setIsAuthenticated(false);
    setCurrentUser(null);
    setNodes([]);
    toast.success("Logged out successfully");
  };

  const loadNodes = async (retryCount = 0) => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/nodes`, {
        timeout: 15000 // 15 second timeout
      });
      setNodes(response.data);
    } catch (error) {
      console.error("Error loading nodes:", error);
      
      // Retry on network error (server might be waking up)
      if (!error.response && retryCount < 2) {
        console.log(`Retrying loadNodes (attempt ${retryCount + 1}/2)...`);
        toast.info("Reconnecting...", { duration: 2000 });
        setTimeout(() => loadNodes(retryCount + 1), 3000);
        return;
      }
      
      if (error.response?.status === 401) {
        // Don't auto-logout, just show error
        console.log("401 error - but not auto-logging out");
        toast.error("Session may have expired. Try refreshing the page.", { duration: 5000 });
      } else if (!error.response) {
        toast.error("Server is sleeping. Please wait a moment.", { duration: 3000 });
      } else {
        toast.error("Failed to load nodes");
      }
    } finally {
      setLoading(false);
    }
  };

  const autoRefreshAllNodes = async (silent = false, retryCount = 0) => {
    try {
      setAutoRefreshing(true);
      if (!silent) {
        toast.info("Checking node status from Solana blockchain...");
      }
      
      const response = await axios.post(`${API}/nodes/refresh-all-status`, {}, {
        timeout: 30000 // 30 second timeout
      });
      
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
      
      // Retry logic for network errors (server waking up)
      if (!error.response && retryCount < 2) {
        console.log(`Retrying auto-refresh (attempt ${retryCount + 1}/2)...`);
        if (!silent) {
          toast.info("Server waking up, retrying...", { duration: 2000 });
        }
        // Wait 3 seconds and retry
        setTimeout(() => autoRefreshAllNodes(silent, retryCount + 1), 3000);
        return;
      }
      
      if (!silent) {
        const errorMsg = !error.response 
          ? "Server is sleeping. Please wait and try again." 
          : "Failed to auto-refresh node status";
        toast.error(errorMsg);
      }
    } finally {
      setAutoRefreshing(false);
    }
  };

  const addNode = async () => {
    const sanitizedAddress = sanitizeInput(newNodeAddress).trim();
    const sanitizedName = sanitizeInput(newNodeName).trim();
    
    if (!sanitizedAddress) {
      toast.error("Please enter a node address");
      return;
    }
    
    // Validate Solana address format
    if (!validateSolanaAddress(sanitizedAddress)) {
      toast.error("Invalid Solana address format. Please check and try again.");
      return;
    }
    
    // Check rate limit
    const rateLimitCheck = apiRateLimiter.checkLimit('addNode');
    if (!rateLimitCheck.allowed) {
      toast.error(`Too many requests. Please wait ${rateLimitCheck.resetIn} seconds.`);
      return;
    }

    try {
      await axios.post(`${API}/nodes`, {
        address: sanitizedAddress,
        name: sanitizedName || null,
      });
      toast.success("Node added successfully");
      setNewNodeAddress("");
      setNewNodeName("");
      await loadNodes();
    } catch (error) {
      const message = error.response?.data?.detail || "Failed to add node";
      toast.error(message);
      console.error("Add node error:", error);
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
        {/* Background effects for themes */}
        {currentTheme === "neon80s" && <div className="tech-pattern-bg"></div>}
        {currentTheme === "cyber" && (
          <>
            <MatrixRain />
            <div className="cyberpunk-grid-bg"></div>
            <div className="cyberpunk-corner-glow-left"></div>
            <div className="cyberpunk-corner-glow-right"></div>
            <div className="cyberpunk-scanline"></div>
          </>
        )}
        
        {/* Theme Selector */}
        <div className="fixed top-4 right-4 z-50">
          <Select value={currentTheme} onValueChange={handleThemeChange}>
            <SelectTrigger data-testid="theme-selector" className={"w-[140px] h-10 text-sm gap-2 " + theme.control.dropdown}>
              <Moon className="w-4 h-4" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent className={theme.control.dropdown}>
              <SelectItem value="default" data-testid="theme-dark-mode">Dark Mode</SelectItem>
              <SelectItem value="neon80s" data-testid="theme-80s-neon">80s Neon</SelectItem>
              <SelectItem value="cyber" data-testid="theme-cyber">Cyber</SelectItem>
            </SelectContent>
          </Select>
        </div>

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
      {/* Background effects for themes */}
      {currentTheme === "neon80s" && <div className="tech-pattern-bg"></div>}
      {currentTheme === "cyber" && (
        <>
          <MatrixRain />
          <div className="cyberpunk-grid-bg"></div>
          <div className="cyberpunk-corner-glow-left"></div>
          <div className="cyberpunk-corner-glow-right"></div>
          <div className="cyberpunk-scanline"></div>
        </>
      )}

      <div className="container mx-auto px-3 sm:px-4 py-4 sm:py-8 max-w-7xl relative z-10">
        {/* Header with all controls */}
        <div className="mb-4 sm:mb-8">
          {/* Top row: Title and Controls */}
          <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-3 sm:gap-4">
            {/* Left: Title */}
            <div className="flex-1">
              <h1 
                className={theme.title + " text-2xl sm:text-4xl lg:text-5xl font-bold mb-1 sm:mb-2 " + (currentTheme === "cyber" ? "cyberpunk-glitch uppercase tracking-wider" : "")} 
                data-testid="app-title"
                data-text={currentTheme === "cyber" ? "NOSANA NODE MONITOR" : ""}
              >
                {currentTheme === "cyber" ? "NOSANA NODE MONITOR" : "Nosana Node Monitor"}
              </h1>
              <p className={"text-xs sm:text-base " + theme.text.secondary + (currentTheme === "cyber" ? " uppercase tracking-wide" : "")}>
                {currentTheme === "cyber" ? "// Real-time AI Network Surveillance //" : "Monitor your Nosana AI network nodes in real-time"}
              </p>
            </div>
            
            {/* Right: All Controls (stacked on mobile, row on desktop) */}
            <div className="flex flex-col items-stretch sm:items-end gap-2">
              {/* Email */}
              <p className={"text-xs sm:text-sm text-right " + theme.text.muted}>
                {currentUser?.email}
              </p>
              
              {/* Control Buttons Row */}
              <div className="flex items-center gap-2 flex-wrap">
                {/* Theme Selector */}
                <Select value={currentTheme} onValueChange={handleThemeChange}>
                  <SelectTrigger data-testid="theme-selector" className={"w-[110px] sm:w-[140px] h-8 sm:h-9 text-xs sm:text-sm gap-1 " + theme.control.dropdown}>
                    <Moon className="w-3 h-3 sm:w-4 sm:h-4" />
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className={theme.control.dropdown}>
                    <SelectItem value="default" data-testid="theme-dark-mode">Dark Mode</SelectItem>
                    <SelectItem value="neon80s" data-testid="theme-80s-neon">80s Neon</SelectItem>
                    <SelectItem value="cyber" data-testid="theme-cyber">Cyber</SelectItem>
                  </SelectContent>
                </Select>
                
                {/* Notifications Button */}
                <Button
                  onClick={() => setShowSettings(!showSettings)}
                  variant="outline"
                  size="sm"
                  className={"h-8 sm:h-9 px-2 sm:px-3 " + theme.control.button}
                  title="Notification Settings"
                >
                  {notificationsEnabled ? (
                    <Bell className="w-3 h-3 sm:w-4 sm:h-4" />
                  ) : (
                    <BellOff className="w-3 h-3 sm:w-4 sm:h-4" />
                  )}
                </Button>
                
                {/* Auto-refresh interval selector */}
                <Select value={refreshInterval.toString()} onValueChange={(val) => handleRefreshIntervalChange(parseInt(val))}>
                  <SelectTrigger className={"w-[100px] sm:w-[130px] h-8 sm:h-9 text-xs sm:text-sm " + theme.control.dropdown}>
                    <SelectValue placeholder="Refresh" />
                  </SelectTrigger>
                  <SelectContent className={theme.control.dropdown}>
                    {refreshIntervalOptions.map((option) => (
                      <SelectItem key={option.value} value={option.value.toString()}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                
                {/* Logout Button */}
                <Button
                  onClick={handleLogout}
                  variant="outline"
                  size="sm"
                  className={"gap-1 sm:gap-2 h-8 sm:h-9 px-2 sm:px-3 " + theme.control.button}
                  data-testid="logout-button"
                >
                  <LogOut className="w-3 h-3 sm:w-4 sm:h-4" />
                  <span className="text-xs sm:text-sm">Logout</span>
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* Notification Settings Modal */}
        {showSettings && (
          <Card className={theme.card + " mb-4 sm:mb-8 shadow-lg"}>
            <CardHeader>
              <CardTitle className={"flex items-center gap-2 " + theme.text.primary}>
                <Settings className="w-5 h-5" />
                Notification Settings
              </CardTitle>
              <CardDescription className={theme.text.secondary}>
                Configure push notifications for node status changes
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {!notificationsEnabled ? (
                <div className="text-center py-8">
                  <Bell className={"w-16 h-16 mx-auto mb-4 " + theme.text.muted} />
                  <h3 className={"text-lg font-semibold mb-2 " + theme.text.primary}>
                    Enable Push Notifications
                  </h3>
                  <p className={"mb-4 " + theme.text.secondary}>
                    Get instant alerts when your nodes go offline or start jobs
                  </p>
                  <Button
                    onClick={requestNotificationPermission}
                    className={theme.buttonGradient}
                  >
                    <Bell className="w-4 h-4 mr-2" />
                    Enable Notifications
                  </Button>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className={"p-4 rounded-lg " + (currentTheme === "neon80s" ? "bg-emerald-900/20 border border-emerald-500/30" : "bg-green-50 border border-green-200")}>
                    <p className={"text-sm font-medium " + theme.text.primary}>
                      ✅ Push notifications are enabled
                    </p>
                  </div>

                  {/* Notification Preferences */}
                  <div className="space-y-3">
                    <h4 className={"font-semibold " + theme.text.primary}>
                      Notify me when:
                    </h4>
                    
                    {[
                      { key: 'notify_offline', label: '⚠️ Node goes offline', description: 'Alert when a node stops responding' },
                      { key: 'notify_online', label: '✅ Node comes back online', description: 'Alert when a node reconnects' },
                      { key: 'notify_job_started', label: '🚀 Job started', description: 'Alert when a node begins processing' },
                      { key: 'notify_job_completed', label: '✅ Job completed', description: 'Alert when a job finishes' }
                    ].map((pref) => (
                      <label key={pref.key} className="flex items-start gap-3 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={notificationPreferences[pref.key]}
                          onChange={(e) => {
                            const newPrefs = { ...notificationPreferences, [pref.key]: e.target.checked };
                            saveNotificationPreferences(newPrefs);
                          }}
                          className="mt-1"
                        />
                        <div className="flex-1">
                          <div className={"font-medium " + theme.text.primary}>{pref.label}</div>
                          <div className={"text-xs " + theme.text.muted}>{pref.description}</div>
                        </div>
                      </label>
                    ))}
                  </div>

                  {/* Sound & Vibration */}
                  <div className="space-y-3">
                    <h4 className={"font-semibold " + theme.text.primary}>
                      Notification Settings:
                    </h4>
                    
                    <label className="flex items-center gap-3 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={notificationPreferences.vibration}
                        onChange={(e) => {
                          const newPrefs = { ...notificationPreferences, vibration: e.target.checked };
                          saveNotificationPreferences(newPrefs);
                        }}
                      />
                      <div>
                        <div className={"font-medium " + theme.text.primary}>📳 Vibration</div>
                        <div className={"text-xs " + theme.text.muted}>Vibrate on notifications</div>
                      </div>
                    </label>

                    <label className="flex items-center gap-3 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={notificationPreferences.sound}
                        onChange={(e) => {
                          const newPrefs = { ...notificationPreferences, sound: e.target.checked };
                          saveNotificationPreferences(newPrefs);
                        }}
                      />
                      <div>
                        <div className={"font-medium " + theme.text.primary}>🔔 Sound</div>
                        <div className={"text-xs " + theme.text.muted}>Play sound on notifications</div>
                      </div>
                    </label>
                  </div>

                  {/* Test Notification */}
                  <div className="pt-4 border-t">
                    <Button
                      onClick={sendTestNotification}
                      variant="outline"
                      className="w-full"
                    >
                      🔔 Send Test Notification
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Add Node Section */}
        <Card className={theme.card + " mb-4 sm:mb-8 shadow-lg"} data-testid="add-node-card">
          <CardHeader className="pb-3 sm:pb-6">
            <CardTitle className={"flex items-center gap-2 text-base sm:text-lg " + (currentTheme === "neon80s" || currentTheme === "cyber" ? theme.text.primary : "")}>
              <Plus className="w-4 h-4 sm:w-5 sm:h-5" />
              Add New Node
            </CardTitle>
            <CardDescription className={(currentTheme === "neon80s" || currentTheme === "cyber") ? "text-white/70 text-xs sm:text-sm" : "text-xs sm:text-sm"}>
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
            <h2 className={"text-lg sm:text-xl font-semibold " + theme.text.primary}>
              Your Nodes ({nodes.length})
            </h2>
            {nextRefresh && (
              <p className={"text-xs mt-1 " + theme.text.muted}>
                🔄 Next auto-refresh in {Math.max(0, Math.ceil((nextRefresh - new Date()) / 1000 / 60))} min
              </p>
            )}
          </div>
          <div className="flex gap-2 w-full sm:w-auto">
            <Button
              onClick={() => autoRefreshAllNodes(false)}
              disabled={autoRefreshing || nodes.length === 0}
              className={"flex-1 sm:flex-none gap-2 text-xs sm:text-sm h-9 sm:h-10 " + theme.buttonGradient}
              data-testid="auto-refresh-button"
            >
              <RefreshCw className={`w-3 h-3 sm:w-4 sm:h-4 ${autoRefreshing ? "animate-spin" : ""}`} />
              <span className="hidden sm:inline">Refresh from Blockchain</span>
              <span className="sm:hidden">Blockchain</span>
            </Button>
            <Button
              onClick={() => loadNodes()}
              variant="outline"
              disabled={loading}
              className="gap-2 text-xs sm:text-sm h-9 sm:h-10 px-3"
              data-testid="refresh-button"
            >
              <RefreshCw className={`w-3 h-3 sm:w-4 sm:h-4 ${loading ? "animate-spin" : ""}`} />
              <span className="hidden sm:inline">Reload GUI</span>
              <span className="sm:hidden">GUI</span>
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
              <Activity className={"w-16 h-16 mx-auto mb-4 " + theme.text.muted} />
              <h3 className={"text-lg font-semibold mb-2 " + theme.text.primary}>No Nodes Added</h3>
              <p className={theme.text.secondary}>Add your first Nosana node to start monitoring</p>
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
                          <CardTitle className={"text-base sm:text-lg mb-1 " + (currentTheme === "neon80s" || currentTheme === "cyber" ? theme.text.primary : "")} data-testid={`node-name-${node.id}`}>
                            {node.name || "Unnamed Node"}
                          </CardTitle>
                        )}
                        <p className={"text-xs font-mono break-all " + theme.text.muted} data-testid={`node-address-${node.id}`}>
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
                              className={"h-8 w-8 sm:h-10 sm:w-10 " + (currentTheme === "cyber" ? "text-white hover:text-[#00ff00] hover:bg-[#00ff00]/10" : "text-gray-500 hover:text-gray-700 hover:bg-gray-50")}
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
                          <span className={"text-xs sm:text-sm font-medium " + theme.text.secondary}>
                            Status:
                          </span>
                          {getStatusBadge(node.status)}
                        </div>

                        {node.job_status && (
                          <div className="flex justify-between items-center">
                            <span className={"text-xs sm:text-sm font-medium " + theme.text.secondary}>
                              Job Status:
                            </span>
                            {getJobStatusBadge(node.job_status)}
                          </div>
                        )}

                        {/* Balances Section */}
                        <div className="pt-2 border-t space-y-2">
                          <div className="flex justify-between items-center">
                            <span className={"text-xs font-medium " + theme.text.secondary}>
                              NOS Balance:
                            </span>
                            <div className="flex items-center gap-2">
                              <span className={"text-xs font-mono " + theme.text.primary}>
                                {formatBalance(node.nos_balance, node.id)} NOS
                              </span>
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => toggleBalanceVisibility(node.id)}
                                className={"h-6 w-6 " + (currentTheme === "neon80s" ? "text-white hover:text-emerald-300" : currentTheme === "cyber" ? "text-white hover:text-[#00ff00]" : "")}
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
                            <span className={"text-xs font-medium " + theme.text.secondary}>
                              SOL Balance:
                            </span>
                            <span className={"text-xs font-mono " + theme.text.primary}>
                              {formatBalance(node.sol_balance, node.id)} SOL
                            </span>
                          </div>
                        </div>

                        {/* Stats Section */}
                        <div className="pt-2 border-t space-y-2">
                          {node.total_jobs !== null && node.total_jobs !== undefined && (
                            <div className="flex justify-between items-center">
                              <span className={"text-xs font-medium " + theme.text.secondary}>
                                Total Jobs:
                              </span>
                              <span className={"text-xs font-semibold " + theme.text.primary}>
                                {node.total_jobs}
                              </span>
                            </div>
                          )}
                          
                          {node.availability_score !== null && node.availability_score !== undefined && (
                            <div className="flex justify-between items-center">
                              <span className={"text-xs font-medium " + theme.text.secondary}>
                                Availability:
                              </span>
                              <span className={"text-xs font-semibold " + theme.text.primary}>
                                {node.availability_score.toFixed(1)}%
                              </span>
                            </div>
                          )}
                        </div>

                        {node.notes && (
                          <div className="pt-2 border-t">
                            <p className={"text-xs italic " + theme.text.muted}>
                              {node.notes}
                            </p>
                          </div>
                        )}

                        <div className={"text-xs pt-2 border-t " + theme.text.muted}>
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