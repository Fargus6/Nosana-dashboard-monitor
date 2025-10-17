import DOMPurify from 'dompurify';

/**
 * Sanitize HTML content to prevent XSS attacks
 * @param {string} dirty - The unsanitized HTML string
 * @returns {string} - The sanitized HTML string
 */
export const sanitizeHtml = (dirty) => {
  if (!dirty) return '';
  return DOMPurify.sanitize(dirty, {
    ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'br'],
    ALLOWED_ATTR: ['href', 'target'],
  });
};

/**
 * Sanitize text input to remove dangerous characters
 * @param {string} input - The unsanitized input string
 * @returns {string} - The sanitized string
 */
export const sanitizeInput = (input) => {
  if (!input) return '';
  // Remove HTML tags and trim
  return input.replace(/<[^>]*>/g, '').trim();
};

/**
 * Validate Solana address format
 * @param {string} address - The address to validate
 * @returns {boolean} - True if valid, false otherwise
 */
export const validateSolanaAddress = (address) => {
  if (!address || typeof address !== 'string') return false;
  // Solana addresses are base58 encoded and typically 32-44 characters
  const solanaAddressRegex = /^[1-9A-HJ-NP-Za-km-z]{32,44}$/;
  return solanaAddressRegex.test(address);
};

/**
 * Validate email format
 * @param {string} email - The email to validate
 * @returns {boolean} - True if valid, false otherwise
 */
export const validateEmail = (email) => {
  if (!email || typeof email !== 'string') return false;
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email.toLowerCase());
};

/**
 * Validate password strength
 * @param {string} password - The password to validate
 * @returns {object} - Object with isValid and errors
 */
export const validatePassword = (password) => {
  const errors = [];
  
  if (!password || password.length < 8) {
    errors.push('Password must be at least 8 characters long');
  }
  if (!/[A-Z]/.test(password)) {
    errors.push('Password must contain at least one uppercase letter');
  }
  if (!/[a-z]/.test(password)) {
    errors.push('Password must contain at least one lowercase letter');
  }
  if (!/\d/.test(password)) {
    errors.push('Password must contain at least one number');
  }
  
  return {
    isValid: errors.length === 0,
    errors,
  };
};

/**
 * Secure storage helpers with encryption simulation
 */
export const secureStorage = {
  set: (key, value) => {
    try {
      // In production, consider encrypting sensitive data
      localStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
      console.error('Error saving to storage:', error);
    }
  },
  
  get: (key) => {
    try {
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) : null;
    } catch (error) {
      console.error('Error reading from storage:', error);
      return null;
    }
  },
  
  remove: (key) => {
    try {
      localStorage.removeItem(key);
    } catch (error) {
      console.error('Error removing from storage:', error);
    }
  },
  
  clear: () => {
    try {
      localStorage.clear();
    } catch (error) {
      console.error('Error clearing storage:', error);
    }
  },
};

/**
 * Rate limiting helper for client-side operations
 */
export class RateLimiter {
  constructor(maxAttempts = 5, windowMs = 60000) {
    this.maxAttempts = maxAttempts;
    this.windowMs = windowMs;
    this.attempts = new Map();
  }

  /**
   * Check if action is allowed
   * @param {string} key - Unique identifier for the action
   * @returns {object} - Object with allowed status and remaining attempts
   */
  checkLimit(key) {
    const now = Date.now();
    const attemptData = this.attempts.get(key) || { count: 0, resetTime: now + this.windowMs };

    // Reset if window has passed
    if (now > attemptData.resetTime) {
      attemptData.count = 0;
      attemptData.resetTime = now + this.windowMs;
    }

    if (attemptData.count >= this.maxAttempts) {
      const waitTime = Math.ceil((attemptData.resetTime - now) / 1000);
      return {
        allowed: false,
        remaining: 0,
        resetIn: waitTime,
      };
    }

    attemptData.count++;
    this.attempts.set(key, attemptData);

    return {
      allowed: true,
      remaining: this.maxAttempts - attemptData.count,
      resetIn: Math.ceil((attemptData.resetTime - now) / 1000),
    };
  }

  /**
   * Reset rate limit for a key
   * @param {string} key - Unique identifier for the action
   */
  reset(key) {
    this.attempts.delete(key);
  }
}

/**
 * CSRF Token management (for future implementation)
 */
export const csrfToken = {
  get: () => {
    // In production, this would fetch from server
    return secureStorage.get('csrf_token');
  },
  
  set: (token) => {
    secureStorage.set('csrf_token', token);
  },
  
  clear: () => {
    secureStorage.remove('csrf_token');
  },
};
