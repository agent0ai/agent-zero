import React, { createContext, useContext, useState, useEffect } from 'react';

interface User {
  id: number;
  username: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_superuser: boolean;
  roles: string[];
  permissions: string[];
  team: string | null;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<void>;
  hasPermission: (permission: string) => boolean;
  hasAnyPermission: (permissions: string[]) => boolean;
  hasAllPermissions: (permissions: string[]) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: React.ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const getAuthHeaders = () => {
    const token = localStorage.getItem('access_token');
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    };
  };

  const loadUser = async () => {
    const token = localStorage.getItem('access_token');
    const storedUser = localStorage.getItem('user');

    if (token && storedUser) {
      try {
        // Verify token is still valid
        const response = await fetch('/api/auth/me', {
          headers: getAuthHeaders(),
        });

        if (response.ok) {
          const data = await response.json();
          setUser(data.user);
        } else {
          // Token invalid, try to refresh
          await refreshToken();
        }
      } catch (error) {
        // Clear invalid auth data
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        setUser(null);
      }
    }

    setIsLoading(false);
  };

  useEffect(() => {
    loadUser();
  }, []);

  const login = async (username: string, password: string) => {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password }),
    });

    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.error || 'Login failed');
    }

    const data = await response.json();

    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    localStorage.setItem('user', JSON.stringify(data.user));

    setUser(data.user);
  };

  const logout = async () => {
    try {
      await fetch('/api/auth/logout', {
        method: 'POST',
        headers: getAuthHeaders(),
      });
    } catch (error) {
      // Continue with logout even if API call fails
    }

    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    setUser(null);
  };

  const refreshToken = async () => {
    const refresh_token = localStorage.getItem('refresh_token');

    if (!refresh_token) {
      throw new Error('No refresh token available');
    }

    const response = await fetch('/api/auth/refresh', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh_token }),
    });

    if (!response.ok) {
      throw new Error('Failed to refresh token');
    }

    const data = await response.json();

    localStorage.setItem('access_token', data.access_token);

    // Reload user data
    await loadUser();
  };

  const hasPermission = (permission: string): boolean => {
    if (!user) return false;
    if (user.is_superuser) return true;
    if (user.permissions.includes('*')) return true;
    return user.permissions.includes(permission);
  };

  const hasAnyPermission = (permissions: string[]): boolean => {
    if (!user) return false;
    if (user.is_superuser) return true;
    if (user.permissions.includes('*')) return true;
    return permissions.some((perm) => user.permissions.includes(perm));
  };

  const hasAllPermissions = (permissions: string[]): boolean => {
    if (!user) return false;
    if (user.is_superuser) return true;
    if (user.permissions.includes('*')) return true;
    return permissions.every((perm) => user.permissions.includes(perm));
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
    refreshToken,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// Protected Route Component
interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredPermission?: string;
  requiredPermissions?: string[];
  requireAll?: boolean;
  fallback?: React.ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requiredPermission,
  requiredPermissions,
  requireAll = false,
  fallback = <div>Access Denied</div>,
}) => {
  const { isAuthenticated, isLoading, hasPermission, hasAnyPermission, hasAllPermissions } = useAuth();

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (!isAuthenticated) {
    return <div>Please login to access this page</div>;
  }

  // Check single permission
  if (requiredPermission && !hasPermission(requiredPermission)) {
    return <>{fallback}</>;
  }

  // Check multiple permissions
  if (requiredPermissions) {
    const hasAccess = requireAll
      ? hasAllPermissions(requiredPermissions)
      : hasAnyPermission(requiredPermissions);

    if (!hasAccess) {
      return <>{fallback}</>;
    }
  }

  return <>{children}</>;
};
