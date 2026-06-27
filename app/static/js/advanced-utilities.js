/* ============================================================================
   INDUSTRIAL-GRADE JAVASCRIPT UTILITIES
   Advanced Interactions, State Management & Real-Time Features
   ============================================================================ */

/**
 * API Service - Unified HTTP Client
 */
class APIService {
    constructor(baseURL = '/api') {
        this.baseURL = baseURL;
        this.defaultHeaders = {
            'Content-Type': 'application/json'
        };
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                ...this.defaultHeaders,
                ...options.headers
            },
            ...options
        };

        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || `HTTP ${response.status}`);
            }
            
            return response.json();
        } catch (error) {
            console.error(`API Error: ${endpoint}`, error);
            throw error;
        }
    }

    get(endpoint, options) {
        return this.request(endpoint, { method: 'GET', ...options });
    }

    post(endpoint, data, options) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data),
            ...options
        });
    }

    put(endpoint, data, options) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data),
            ...options
        });
    }

    delete(endpoint, options) {
        return this.request(endpoint, { method: 'DELETE', ...options });
    }
}

const apiService = new APIService();

/**
 * Notification System - Toast Notifications
 */
class NotificationManager {
    constructor() {
        this.container = document.createElement('div');
        this.container.className = 'notification-container';
        document.body.appendChild(this.container);
        this.notifications = [];
    }

    show(message, type = 'info', duration = 3000) {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <i class="fas fa-${this._getIcon(type)}"></i>
            <div class="notification-content">
                <div class="notification-title">${this._getTitle(type)}</div>
                <div class="notification-message">${message}</div>
            </div>
        `;
        
        this.container.appendChild(notification);
        this.notifications.push({ element: notification, timeout: null });
        
        // Auto-dismiss
        if (duration > 0) {
            const timeout = setTimeout(() => {
                this.close(notification);
            }, duration);
            
            this.notifications[this.notifications.length - 1].timeout = timeout;
        }
        
        return notification;
    }

    success(message, duration) {
        return this.show(message, 'success', duration);
    }

    error(message, duration) {
        return this.show(message, 'error', duration);
    }

    warning(message, duration) {
        return this.show(message, 'warning', duration);
    }

    info(message, duration) {
        return this.show(message, 'info', duration);
    }

    close(notification) {
        notification.classList.add('closing');
        setTimeout(() => {
            notification.remove();
            this.notifications = this.notifications.filter(n => n.element !== notification);
        }, 300);
    }

    _getIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        return icons[type] || icons.info;
    }

    _getTitle(type) {
        const titles = {
            success: 'Success',
            error: 'Error',
            warning: 'Warning',
            info: 'Information'
        };
        return titles[type] || titles.info;
    }
}

const notifyMgr = new NotificationManager();

/**
 * Modal Dialog Manager
 */
class ModalManager {
    static show(options) {
        const {
            title = 'Dialog',
            content = '',
            buttons = [{ label: 'Close', action: 'close', type: 'secondary' }],
            size = 'md',
            onClose = null
        } = options;

        const backdrop = document.createElement('div');
        backdrop.className = 'modal-backdrop show';
        
        const modal = document.createElement('div');
        modal.className = `modal modal-${size}`;
        
        let buttonsHTML = '';
        buttons.forEach((btn, idx) => {
            const btnClass = `btn btn-${btn.type || 'primary'}`;
            buttonsHTML += `
                <button class="${btnClass}" data-action="${btn.action}" data-index="${idx}">
                    ${btn.label}
                </button>
            `;
        });

        modal.innerHTML = `
            <div class="modal-header">
                <h3 class="modal-title">${title}</h3>
                <button class="modal-close">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="modal-body">
                ${content}
            </div>
            <div class="modal-footer">
                ${buttonsHTML}
            </div>
        `;

        backdrop.appendChild(modal);
        document.body.appendChild(backdrop);

        // Event handlers
        const closeBtn = modal.querySelector('.modal-close');
        closeBtn.addEventListener('click', () => {
            this.close(backdrop, onClose);
        });

        backdrop.addEventListener('click', (e) => {
            if (e.target === backdrop) {
                this.close(backdrop, onClose);
            }
        });

        const buttonElements = modal.querySelectorAll('button[data-action]');
        buttonElements.forEach((btn) => {
            btn.addEventListener('click', () => {
                const action = btn.dataset.action;
                const index = parseInt(btn.dataset.index);
                
                if (buttons[index].callback) {
                    buttons[index].callback();
                }
                
                if (action !== 'stay') {
                    this.close(backdrop, onClose);
                }
            });
        });

        return { backdrop, modal };
    }

    static close(backdrop, callback) {
        backdrop.classList.remove('show');
        setTimeout(() => {
            backdrop.remove();
            if (callback) callback();
        }, 300);
    }
}

/**
 * Form Validator
 */
class FormValidator {
    static rules = {
        required: (value) => !!value || 'This field is required',
        email: (value) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value) || 'Invalid email address',
        minLength: (min) => (value) => value.length >= min || `Minimum ${min} characters required`,
        maxLength: (max) => (value) => value.length <= max || `Maximum ${max} characters allowed`,
        numeric: (value) => /^\d+$/.test(value) || 'Only numbers are allowed',
        alphanumeric: (value) => /^[a-zA-Z0-9]+$/.test(value) || 'Only letters and numbers are allowed',
        url: (value) => /^https?:\/\/.+/.test(value) || 'Invalid URL format',
        phone: (value) => /^\d{7,}$/.test(value.replace(/\D/g, '')) || 'Invalid phone number'
    };

    static validate(form, schema) {
        let isValid = true;
        const errors = {};

        Object.entries(schema).forEach(([fieldName, rules]) => {
            const field = form.querySelector(`[name="${fieldName}"]`);
            if (!field) return;

            const value = field.value.trim();
            const fieldRules = Array.isArray(rules) ? rules : [rules];

            fieldRules.forEach((rule) => {
                let validator;
                let message;

                if (typeof rule === 'function') {
                    validator = rule;
                } else if (typeof rule === 'string') {
                    validator = this.rules[rule];
                } else if (rule.rule) {
                    validator = typeof rule.rule === 'string' 
                        ? this.rules[rule.rule] 
                        : rule.rule;
                    message = rule.message;
                }

                if (validator) {
                    const result = validator(value);
                    if (result !== true) {
                        isValid = false;
                        errors[fieldName] = message || result;
                    }
                }
            });
        });

        return { isValid, errors };
    }

    static displayErrors(form, errors) {
        // Clear previous errors
        form.querySelectorAll('.form-error').forEach(el => el.remove());

        // Display new errors
        Object.entries(errors).forEach(([fieldName, message]) => {
            const field = form.querySelector(`[name="${fieldName}"]`);
            if (field) {
                const errorEl = document.createElement('div');
                errorEl.className = 'form-error';
                errorEl.textContent = message;
                field.parentNode.insertAdjacentElement('afterend', errorEl);
                field.classList.add('error');
            }
        });
    }
}

/**
 * Theme Manager - Dark Mode Support
 */
class ThemeManager {
    constructor() {
        this.theme = localStorage.getItem('theme') || 'light';
        this.apply();
    }

    toggle() {
        this.theme = this.theme === 'light' ? 'dark' : 'light';
        localStorage.setItem('theme', this.theme);
        this.apply();
    }

    apply() {
        if (this.theme === 'dark') {
            document.documentElement.style.colorScheme = 'dark';
            document.body.classList.add('theme-dark');
        } else {
            document.documentElement.style.colorScheme = 'light';
            document.body.classList.remove('theme-dark');
        }
    }

    isDark() {
        return this.theme === 'dark';
    }
}

const themeManager = new ThemeManager();

function buildModuleBackgroundSvg(config) {
        const svg = `
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1920 1080" preserveAspectRatio="xMidYMid slice">
    <defs>
        <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stop-color="${config.base1}"/>
            <stop offset="100%" stop-color="${config.base2}"/>
        </linearGradient>
        <radialGradient id="glow1" cx="20%" cy="18%" r="45%">
            <stop offset="0%" stop-color="${config.accent1}" stop-opacity="0.55"/>
            <stop offset="100%" stop-color="${config.accent1}" stop-opacity="0"/>
        </radialGradient>
        <radialGradient id="glow2" cx="82%" cy="20%" r="42%">
            <stop offset="0%" stop-color="${config.accent2}" stop-opacity="0.45"/>
            <stop offset="100%" stop-color="${config.accent2}" stop-opacity="0"/>
        </radialGradient>
        <radialGradient id="glow3" cx="30%" cy="82%" r="40%">
            <stop offset="0%" stop-color="${config.accent3}" stop-opacity="0.32"/>
            <stop offset="100%" stop-color="${config.accent3}" stop-opacity="0"/>
        </radialGradient>
    </defs>
    <rect width="1920" height="1080" fill="url(#bg)"/>
    <rect width="1920" height="1080" fill="url(#glow1)"/>
    <rect width="1920" height="1080" fill="url(#glow2)"/>
    <rect width="1920" height="1080" fill="url(#glow3)"/>
    <g opacity="0.18" fill="none" stroke="${config.wave}" stroke-width="2">
        <path d="M-10 300 C 300 150 620 430 960 280 C 1260 150 1530 360 1930 240"/>
        <path d="M-20 620 C 260 430 620 770 960 620 C 1320 460 1580 700 1940 560"/>
        <path d="M-20 860 C 300 710 580 950 940 820 C 1280 700 1520 880 1940 760"/>
    </g>
    <text x="94%" y="85%" text-anchor="end" font-family="Segoe UI, Arial" font-size="160" fill="${config.iconColor}" opacity="0.32">${config.icon}</text>
</svg>`;
        return `url("data:image/svg+xml;utf8,${encodeURIComponent(svg)}")`;
}

function getModuleBackgroundConfig(path) {
        const modules = [
                { key: ['/patient-data', '/vitals'], icon: '🩺', base1: '#f1f8ff', base2: '#eefdf7', accent1: '#60a5fa', accent2: '#2dd4bf', accent3: '#93c5fd', wave: '#38bdf8', iconColor: '#0ea5e9' },
                { key: ['/records', '/reports'], icon: '📋', base1: '#f8fbff', base2: '#f2f7ff', accent1: '#7aa2ff', accent2: '#60a5fa', accent3: '#bfdbfe', wave: '#3b82f6', iconColor: '#2563eb' },
                { key: ['/results', '/predictions'], icon: '📈', base1: '#f4fbff', base2: '#f3fffb', accent1: '#22d3ee', accent2: '#34d399', accent3: '#67e8f9', wave: '#06b6d4', iconColor: '#0891b2' },
                { key: ['/health-score'], icon: '💚', base1: '#f3fff7', base2: '#f0fdf9', accent1: '#22c55e', accent2: '#10b981', accent3: '#86efac', wave: '#16a34a', iconColor: '#15803d' },
                { key: ['/health-trends'], icon: '📊', base1: '#f2f9ff', base2: '#f6f3ff', accent1: '#38bdf8', accent2: '#818cf8', accent3: '#a5b4fc', wave: '#6366f1', iconColor: '#4f46e5' },
                { key: ['/alerts'], icon: '🚨', base1: '#fff7f7', base2: '#fffaf5', accent1: '#fb7185', accent2: '#fb923c', accent3: '#fca5a5', wave: '#ef4444', iconColor: '#dc2626' },
                { key: ['/emergency-sos'], icon: '🆘', base1: '#fff4f5', base2: '#fff7fb', accent1: '#f43f5e', accent2: '#fb7185', accent3: '#fda4af', wave: '#e11d48', iconColor: '#be123c' },
                { key: ['/doctor-booking', '/doctors', '/appointments'], icon: '👨‍⚕️', base1: '#f4faff', base2: '#eefcff', accent1: '#60a5fa', accent2: '#22d3ee', accent3: '#93c5fd', wave: '#0ea5e9', iconColor: '#0284c7' },
                { key: ['/chatbot', '/ai-assistant'], icon: '🤖', base1: '#f6f5ff', base2: '#f2fbff', accent1: '#a78bfa', accent2: '#38bdf8', accent3: '#c4b5fd', wave: '#8b5cf6', iconColor: '#7c3aed' },
                { key: ['/family-members'], icon: '👨‍👩‍👧', base1: '#fffaf5', base2: '#fff7fb', accent1: '#f59e0b', accent2: '#f472b6', accent3: '#fcd34d', wave: '#ec4899', iconColor: '#db2777' },
                { key: ['/mental-health'], icon: '🧠', base1: '#f7f5ff', base2: '#f5fbff', accent1: '#a78bfa', accent2: '#60a5fa', accent3: '#c4b5fd', wave: '#6366f1', iconColor: '#4f46e5' },
                { key: ['/events'], icon: '📅', base1: '#f8fff4', base2: '#f3fff9', accent1: '#84cc16', accent2: '#34d399', accent3: '#bef264', wave: '#22c55e', iconColor: '#16a34a' },
                { key: ['/medical-report'], icon: '🧾', base1: '#f8faff', base2: '#f3f8ff', accent1: '#93c5fd', accent2: '#60a5fa', accent3: '#dbeafe', wave: '#3b82f6', iconColor: '#2563eb' },
                { key: ['/symptom-analyzer'], icon: '🧬', base1: '#f3fffe', base2: '#f5f9ff', accent1: '#2dd4bf', accent2: '#38bdf8', accent3: '#99f6e4', wave: '#14b8a6', iconColor: '#0f766e' },
                { key: ['/settings'], icon: '⚙️', base1: '#f8fafc', base2: '#f1f5f9', accent1: '#94a3b8', accent2: '#60a5fa', accent3: '#cbd5e1', wave: '#64748b', iconColor: '#475569' }
        ];

        const matched = modules.find(m => m.key.some(route => path.startsWith(route)));
        if (matched) {
                return matched;
        }

        return { icon: '🏥', base1: '#fff7fb', base2: '#f4fcff', accent1: '#ff69b4', accent2: '#22d3ee', accent3: '#f9a8d4', wave: '#0ea5e9', iconColor: '#0284c7' };
}

/**
 * Module background image (all modules except dashboard)
 * Uses module-related generated SVG images and full-screen fit.
 */
function applyModuleBackgroundImage() {
    const path = (window.location.pathname || '').toLowerCase();
    const isDashboardRoute = path === '/dashboard' || path === '/dashboard-v2' || path === '/v2/dashboard';

    if (isDashboardRoute || !document.body) {
        return;
    }

    // Add class for robust CSS override across modules with heavy inline styles.
    document.body.classList.add('module-bg-active');

    const config = getModuleBackgroundConfig(path);
    const svgImage = buildModuleBackgroundSvg(config);
    const imageMap = {
        '/patient-data': '/static/images/modules/patient-data-bg.avif',
        '/vitals': '/static/images/modules/vitals-bg.avif',
        '/records': '/static/images/modules/records-bg.avif',
        '/reports': '/static/images/modules/reports-bg.avif',
        '/results': '/static/images/modules/results-bg.avif',
        '/predictions': '/static/images/modules/predictions-bg.avif',
        '/health-score': '/static/images/modules/health-score-bg.avif',
        '/health-trends': '/static/images/modules/health-trends-bg.avif',
        '/alerts': '/static/images/modules/alerts-bg.avif',
        '/emergency-sos': '/static/images/modules/emergency-sos-bg.avif',
        '/doctor-booking': '/static/images/modules/doctor-booking-bg.avif',
        '/doctors': '/static/images/modules/doctors-bg.avif',
        '/appointments': '/static/images/modules/appointments-bg.avif',
        '/chatbot': '/static/images/modules/chatbot-bg.avif',
        '/ai-assistant': '/static/images/modules/ai-assistant-bg.avif',
        '/family-members': '/static/images/modules/family-members-bg.avif',
        '/mental-health': '/static/images/modules/mental-health-bg.avif',
        '/events': '/static/images/modules/events-bg.avif',
        '/medical-report': '/static/images/modules/medical-report-bg.avif',
        '/symptom-analyzer': '/static/images/modules/symptom-analyzer-bg.avif',
        '/settings': '/static/images/modules/settings-bg.avif'
    };

    const imagePath = imageMap[path] || '/static/images/module-bg.avif';
    const composedBg = `linear-gradient(rgba(255,255,255,0.28), rgba(255,255,255,0.28)), url('${imagePath}'), ${svgImage}`;

    // Keep inline styles as an additional safety net.
    document.body.style.backgroundImage = composedBg;
    document.body.style.backgroundSize = 'cover';
    document.body.style.backgroundPosition = 'center center';
    document.body.style.backgroundRepeat = 'no-repeat';
    document.body.style.backgroundAttachment = 'fixed';

    // Inject a single global style override for non-dashboard module pages.
    if (!document.getElementById('module-bg-override-style')) {
        const style = document.createElement('style');
        style.id = 'module-bg-override-style';
        style.textContent = `
            body.module-bg-active {
                background-image: ${composedBg} !important;
                background-size: cover !important;
                background-position: center center !important;
                background-repeat: no-repeat !important;
                background-attachment: fixed !important;
                min-height: 100vh !important;
            }

            /* Let the page-level container show the shared background image */
            body.module-bg-active > .container,
            body.module-bg-active > .main-container,
            body.module-bg-active > .page-container,
            body.module-bg-active > .content-wrapper,
            body.module-bg-active > .app-container {
                background: transparent !important;
                min-height: 100vh !important;
            }

            body.module-bg-active::before,
            body.module-bg-active::after {
                display: none !important;
            }
        `;
        document.head.appendChild(style);
    }

    // Ensure CSS override gets module-specific image (dynamic per route).
    document.body.style.setProperty('background-image', `${composedBg}`, 'important');
}

/**
 * Utility Functions
 */
const Utils = {
    /**
     * Format number as currency
     */
    formatCurrency(value, currency = 'USD') {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: currency
        }).format(value);
    },

    /**
     * Format date
     */
    formatDate(date, format = 'MMM DD, YYYY') {
        const d = new Date(date);
        const month = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][d.getMonth()];
        const day = d.getDate();
        const year = d.getFullYear();
        
        return format.replace('MMM', month).replace('DD', day).replace('YYYY', year);
    },

    /**
     * Debounce function
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * Throttle function
     */
    throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },

    /**
     * Deep clone object
     */
    deepClone(obj) {
        if (obj === null || typeof obj !== 'object') return obj;
        if (obj instanceof Date) return new Date(obj.getTime());
        if (obj instanceof Array) return obj.map(item => this.deepClone(item));
        if (obj instanceof Object) {
            const clonedObj = {};
            for (let key in obj) {
                if (obj.hasOwnProperty(key)) {
                    clonedObj[key] = this.deepClone(obj[key]);
                }
            }
            return clonedObj;
        }
    },

    /**
     * Get URL parameters
     */
    getQueryParam(param) {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get(param);
    },

    /**
     * Generate unique ID
     */
    generateId() {
        return '_' + Math.random().toString(36).substr(2, 9);
    },

    /**
     * Copy to clipboard
     */
    copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(() => {
            notifyMgr.success('Copied to clipboard!', 2000);
        }).catch(() => {
            notifyMgr.error('Failed to copy');
        });
    },

    /**
     * Sleep (for async operations)
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    },

    /**
     * Check if element is in viewport
     */
    isInViewport(element) {
        const rect = element.getBoundingClientRect();
        return (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
            rect.right <= (window.innerWidth || document.documentElement.clientWidth)
        );
    }
};

/**
 * DOM Helper Functions
 */
const DOM = {
    /**
     * Create element with attributes
     */
    create(tag, attributes = {}, innerHTML = '') {
        const element = document.createElement(tag);
        Object.entries(attributes).forEach(([key, value]) => {
            if (key === 'class') {
                element.className = value;
            } else if (key.startsWith('data-')) {
                element.dataset[key.slice(5)] = value;
            } else {
                element.setAttribute(key, value);
            }
        });
        if (innerHTML) element.innerHTML = innerHTML;
        return element;
    },

    /**
     * Query selector with error handling
     */
    qs(selector) {
        return document.querySelector(selector);
    },

    /**
     * Query selector all
     */
    qsAll(selector) {
        return document.querySelectorAll(selector);
    },

    /**
     * Add event listeners with delegation
     */
    on(element, event, selector, handler) {
        if (typeof selector === 'function') {
            handler = selector;
            selector = null;
        }

        if (!selector) {
            element.addEventListener(event, handler);
        } else {
            element.addEventListener(event, (e) => {
                if (e.target.matches(selector)) {
                    handler.call(e.target, e);
                }
            });
        }
    },

    /**
     * Add class
     */
    addClass(element, className) {
        element.classList.add(className);
    },

    /**
     * Remove class
     */
    removeClass(element, className) {
        element.classList.remove(className);
    },

    /**
     * Toggle class
     */
    toggleClass(element, className) {
        element.classList.toggle(className);
    },

    /**
     * Show element
     */
    show(element) {
        element.style.display = '';
    },

    /**
     * Hide element
     */
    hide(element) {
        element.style.display = 'none';
    }
};

/**
 * Initialization Utility
 */
document.addEventListener('DOMContentLoaded', () => {
    applyModuleBackgroundImage();

    // Initialize tooltips
    document.querySelectorAll('[data-tooltip]').forEach(el => {
        el.addEventListener('mouseenter', (e) => {
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.textContent = el.dataset.tooltip;
            el.appendChild(tooltip);
        });
    });
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        APIService,
        NotificationManager,
        ModalManager,
        FormValidator,
        ThemeManager,
        Utils,
        DOM
    };
}
