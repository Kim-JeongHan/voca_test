/**
 * VocaAuth - Authentication module for Voca Test
 *
 * Features:
 * - JWT token management (localStorage)
 * - Login/Register/Logout
 * - Auth header injection
 * - Token validation
 */
const VocaAuth = (() => {
    // Configuration
    const CONFIG = {
        apiUrl: 'https://vocatest-production.up.railway.app/api/v1/auth',
        tokenKey: 'voca_auth_token',
        userKey: 'voca_auth_user',
    };

    // State
    let currentUser = null;

    // ==================== Token Management ====================

    function saveToken(token) {
        localStorage.setItem(CONFIG.tokenKey, token);
    }

    function getToken() {
        return localStorage.getItem(CONFIG.tokenKey);
    }

    function removeToken() {
        localStorage.removeItem(CONFIG.tokenKey);
        localStorage.removeItem(CONFIG.userKey);
        currentUser = null;
    }

    function saveUser(user) {
        localStorage.setItem(CONFIG.userKey, JSON.stringify(user));
        currentUser = user;
    }

    function getStoredUser() {
        const userJson = localStorage.getItem(CONFIG.userKey);
        if (userJson) {
            try {
                return JSON.parse(userJson);
            } catch (e) {
                return null;
            }
        }
        return null;
    }

    // ==================== Auth Headers ====================

    function getAuthHeaders() {
        const token = getToken();
        if (token) {
            return {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            };
        }
        return {
            'Content-Type': 'application/json',
        };
    }

    // ==================== API Calls ====================

    async function register(username, email, password) {
        try {
            const response = await fetch(`${CONFIG.apiUrl}/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, email, password }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Registration failed');
            }

            return { success: true, user: data };
        } catch (error) {
            console.error('Registration error:', error);
            return { success: false, error: error.message };
        }
    }

    async function login(username, password) {
        try {
            const response = await fetch(`${CONFIG.apiUrl}/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Login failed');
            }

            // Save token
            saveToken(data.access_token);

            // Fetch and save user info
            const userResult = await getCurrentUser();
            if (userResult.success) {
                saveUser(userResult.user);
            }

            return { success: true, token: data.access_token };
        } catch (error) {
            console.error('Login error:', error);
            return { success: false, error: error.message };
        }
    }

    async function logout() {
        removeToken();
        return { success: true };
    }

    async function getCurrentUser() {
        const token = getToken();
        if (!token) {
            return { success: false, error: 'Not authenticated' };
        }

        try {
            const response = await fetch(`${CONFIG.apiUrl}/me`, {
                method: 'GET',
                headers: getAuthHeaders(),
            });

            if (!response.ok) {
                if (response.status === 401) {
                    removeToken();
                    return { success: false, error: 'Token expired' };
                }
                throw new Error('Failed to get user info');
            }

            const user = await response.json();
            currentUser = user;
            saveUser(user);
            return { success: true, user };
        } catch (error) {
            console.error('Get user error:', error);
            return { success: false, error: error.message };
        }
    }

    async function requestPasswordReset(email) {
        try {
            const response = await fetch(`${CONFIG.apiUrl}/password-reset`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Password reset request failed');
            }

            return { success: true, message: data.message };
        } catch (error) {
            console.error('Password reset error:', error);
            return { success: false, error: error.message };
        }
    }

    async function confirmPasswordReset(token, newPassword) {
        try {
            const response = await fetch(`${CONFIG.apiUrl}/password-reset/confirm`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ token, new_password: newPassword }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Password reset failed');
            }

            return { success: true, message: data.message };
        } catch (error) {
            console.error('Password reset confirm error:', error);
            return { success: false, error: error.message };
        }
    }

    // ==================== State Helpers ====================

    function isLoggedIn() {
        return !!getToken();
    }

    function getUser() {
        if (currentUser) {
            return currentUser;
        }
        return getStoredUser();
    }

    // ==================== Initialization ====================

    async function init() {
        const token = getToken();
        if (token) {
            // Validate token by fetching user
            const result = await getCurrentUser();
            if (!result.success) {
                console.log('Token invalid, clearing auth state');
                removeToken();
            }
        }
    }

    // Public API
    return {
        init,
        register,
        login,
        logout,
        getCurrentUser,
        requestPasswordReset,
        confirmPasswordReset,
        isLoggedIn,
        getUser,
        getToken,
        getAuthHeaders,
    };
})();
