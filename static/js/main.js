/**
 * Menopause Wellness App — Main JavaScript
 *
 * Vanilla JS utilities for the entire app. No external libraries.
 *
 * Contents:
 *   1. DOM ready initialiser
 *   2. Flash message auto-dismiss (5 s fade-out)
 *   3. fetchJSON — POST helper for API endpoints
 *   4. Mobile sidebar toggle (responsive hamburger)
 *   5. Active nav item detection
 *   6. Form validation helpers
 *   7. Canvas chart drawing (dark theme)
 *       — drawLineChart(canvasId, labels, datasets)
 *       — drawBarChart(canvasId, labels, data, color)
 *   8. Smooth scroll for anchor links
 *   9. Toast notification system — showToast(message, type)
 */

/* ------------------------------------------------------------------ */
/*  0.  Constants & state                                              */
/* ------------------------------------------------------------------ */

const TOAST_DURATION = 4000;          // ms before toast auto-removes
const FLASH_DURATION = 5000;          // ms before flash fades out
const SIDEBAR_BREAKPOINT = 768;       // px
const GRID_OPACITY = 0.2;             // grid-line opacity for charts
const CHART_BG = '#1e1e2e';           // dark canvas background
const CHART_TEXT = '#ffffff';         // label / tick colour

/* ------------------------------------------------------------------ */
/*  1.  DOM ready initialiser                                         */
/* ------------------------------------------------------------------ */

document.addEventListener('DOMContentLoaded', function () {
    initFlashMessages();
    initSidebarToggle();
    initActiveNavItem();
    initSmoothScroll();
});

/* ------------------------------------------------------------------ */
/*  2.  Flash message auto-dismiss                                    */
/* ------------------------------------------------------------------ */

/**
 * Finds all flash-message elements, starts a fade-out timer on each,
 * then removes them from the DOM after the CSS transition completes.
 *
 * Expected markup:  <div class="flash-message">...</div>
 * CSS should define  .flash-message.fade-out { opacity: 0; transition: opacity 0.5s; }
 */
function initFlashMessages() {
    var flashes = document.querySelectorAll('.flash-message');
    if (!flashes.length) return;

    flashes.forEach(function (el) {
        setTimeout(function () {
            el.classList.add('fade-out');
            // Remove element after transition ends (0.5 s fade + small buffer)
            setTimeout(function () {
                if (el.parentNode) el.parentNode.removeChild(el);
            }, 600);
        }, FLASH_DURATION);
    });
}

/* ------------------------------------------------------------------ */
/*  3.  fetchJSON — POST helper                                       */
/* ------------------------------------------------------------------ */

/**
 * Sends a POST request with a JSON body to an API endpoint.
 *
 * @param {string}  url   — The endpoint URL (e.g. '/api/symptoms')
 * @param {Object}  data  — Plain object that will be JSON-stringified
 * @returns {Promise}     — Resolves with the parsed JSON response, or
 *                          rejects with an Error containing the status.
 *
 * Usage:
 *   fetchJSON('/api/save', { score: 42 })
 *     .then(function (result) { console.log(result); })
 *     .catch(function (err)   { console.error(err); });
 */
function fetchJSON(url, data) {
    return fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    }).then(function (response) {
        if (!response.ok) {
            // Attempt to read error detail from body
            return response.json().then(function (errData) {
                var msg = (errData && errData.error) || response.statusText;
                throw new Error(msg);
            }).catch(function () {
                // If body isn't valid JSON, throw generic error
                throw new Error('Request failed: ' + response.status);
            });
        }
        return response.json();
    });
}

/* ------------------------------------------------------------------ */
/*  4.  Mobile sidebar toggle                                         */
/* ------------------------------------------------------------------ */

/**
 * When the viewport is narrower than SIDEBAR_BREAKPOINT (768 px),
 * clicking the element with class '.sidebar-header' toggles the
 * sidebar open/closed by adding/removing a 'collapsed' class on the
 * sidebar element. Also listens for window resize to auto-collapse
 * when crossing the breakpoint.
 */
function initSidebarToggle() {
    var sidebar = document.querySelector('.sidebar');
    var header = document.querySelector('.sidebar-header');
    if (!sidebar || !header) return;

    // Click handler — only active on small screens
    function handleClick(e) {
        if (window.innerWidth < SIDEBAR_BREAKPOINT) {
            e.preventDefault();
            sidebar.classList.toggle('collapsed');
        }
    }

    header.addEventListener('click', handleClick);

    // Resize handler — auto-collapse when going below breakpoint
    var resizeTimer;
    window.addEventListener('resize', function () {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function () {
            if (window.innerWidth < SIDEBAR_BREAKPOINT) {
                sidebar.classList.add('collapsed');
            } else {
                sidebar.classList.remove('collapsed');
            }
        }, 150);
    });

    // Initial state
    if (window.innerWidth < SIDEBAR_BREAKPOINT) {
        sidebar.classList.add('collapsed');
    }
}

/* ------------------------------------------------------------------ */
/*  5.  Active nav item detection                                     */
/* ------------------------------------------------------------------ */

/**
 * Loops through every anchor inside a <nav> element and adds the class
 * 'active' to the link whose href best matches the current URL path.
 * Falls back to the first link if no match is found.
 */
function initActiveNavItem() {
    var nav = document.querySelector('nav');
    if (!nav) return;

    var currentPath = window.location.pathname;
    var links = nav.querySelectorAll('a');
    var matchFound = false;
    var firstLink = null;

    links.forEach(function (a) {
        if (!firstLink) firstLink = a;
        a.classList.remove('active');

        // Get the path portion of the link's href
        var linkPath;
        try {
            linkPath = new URL(a.href).pathname;
        } catch (e) {
            // Relative href that isn't a full URL
            linkPath = a.getAttribute('href') || '';
        }

        // Strip trailing slashes for comparison
        var cleanLink = linkPath.replace(/\/+$/, '');
        var cleanPath = currentPath.replace(/\/+$/, '');

        if (cleanLink === cleanPath) {
            a.classList.add('active');
            matchFound = true;
        }
    });

    // If no exact match, style the link whose path is a prefix
    if (!matchFound) {
        links.forEach(function (a) {
            var linkPath;
            try {
                linkPath = new URL(a.href).pathname;
            } catch (e) {
                linkPath = a.getAttribute('href') || '';
            }
            var cleanLink = linkPath.replace(/\/+$/, '');
            if (cleanLink && currentPath.indexOf(cleanLink) === 0) {
                a.classList.add('active');
            }
        });
    }
}

/* ------------------------------------------------------------------ */
/*  6.  Form validation helpers                                       */
/* ------------------------------------------------------------------ */

/**
 * Validation utility — attach rules to form elements and call
 * validateForm(formEl) on submit.
 *
 * Data attributes on input elements:
 *   data-validate   — rule name: 'required', 'email', 'min:N', 'max:N'
 *   data-msg        — custom error message (optional)
 *
 * Example:
 *   <input type="text" data-validate="required" data-msg="Name is required">
 *   <input type="email" data-validate="email">
 *   <input type="number" data-validate="min:1|max:100">
 */

/**
 * Validates a single field based on its data-validate attribute.
 * Returns an error string, or an empty string if valid.
 */
function validateField(field) {
    var rules = (field.getAttribute('data-validate') || '').split('|');
    var customMsg = field.getAttribute('data-msg') || '';
    var value = field.value.trim();
    var error = '';

    rules.forEach(function (rule) {
        if (!rule) return;

        if (rule === 'required' && value === '') {
            error = customMsg || 'This field is required.';
        } else if (rule === 'email' && value !== '') {
            // Simple email regex (catches most common patterns)
            if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
                error = customMsg || 'Please enter a valid email address.';
            }
        } else if (rule.indexOf('min:') === 0) {
            var minVal = parseFloat(rule.split(':')[1]);
            if (value !== '' && (isNaN(value) || parseFloat(value) < minVal)) {
                error = customMsg || 'Value must be at least ' + minVal + '.';
            }
        } else if (rule.indexOf('max:') === 0) {
            var maxVal = parseFloat(rule.split(':')[1]);
            if (value !== '' && (isNaN(value) || parseFloat(value) > maxVal)) {
                error = customMsg || 'Value must be at most ' + maxVal + '.';
            }
        }
    });

    return error;
}

/**
 * Validates an entire form. Returns true if valid, false otherwise.
 * On validation failure it also:
 *   - adds an '.is-invalid' class to invalid fields
 *   - removes '.is-invalid' from valid fields
 *   - prepends (or updates) a small error element after the field
 *
 * @param {HTMLElement} formEl — The <form> element to validate
 * @returns {boolean}
 */
function validateForm(formEl) {
    var fields = formEl.querySelectorAll('[data-validate]');
    var isValid = true;

    fields.forEach(function (field) {
        var err = validateField(field);
        removeFieldError(field);

        if (err) {
            isValid = false;
            field.classList.add('is-invalid');
            showFieldError(field, err);
        } else {
            field.classList.remove('is-invalid');
        }
    });

    return isValid;
}

/**
 * Appends a small error message element after the given field.
 */
function showFieldError(field, message) {
    var errEl = document.createElement('span');
    errEl.className = 'field-error';
    errEl.textContent = message;
    field.parentNode.insertBefore(errEl, field.nextSibling);
}

/**
 * Removes the error message element after the given field, if any.
 */
function removeFieldError(field) {
    var next = field.nextElementSibling;
    if (next && next.classList.contains('field-error')) {
        next.parentNode.removeChild(next);
    }
}

/* ------------------------------------------------------------------ */
/*  7.  Canvas chart drawing (dark theme)                             */
/* ------------------------------------------------------------------ */

/**
 * Shared helpers for all Canvas charts.
 */

/**
 * Draws the dark-themed chart background with grid lines.
 *
 * @param {CanvasRenderingContext2D} ctx
 * @param {number} w  — canvas width
 * @param {number} h  — canvas height
 * @param {number} gridCount — number of horizontal grid divisions
 */
function drawChartBackground(ctx, w, h, gridCount) {
    // Fill background
    ctx.fillStyle = CHART_BG;
    ctx.fillRect(0, 0, w, h);

    // Grid lines
    ctx.strokeStyle = 'rgba(255, 255, 255, ' + GRID_OPACITY + ')';
    ctx.lineWidth = 1;
    ctx.setLineDash([]);

    var step = h / (gridCount + 1);
    for (var i = 0; i <= gridCount; i++) {
        var y = step * (i + 0.5);
        ctx.beginPath();
        ctx.moveTo(60, y);
        ctx.lineTo(w - 20, y);
        ctx.stroke();
    }
}

/**
 * Draws text label on the dark chart canvas.
 */
function drawChartLabel(ctx, text, x, y, align) {
    ctx.fillStyle = CHART_TEXT;
    ctx.font = '12px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
    ctx.textAlign = align || 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(text, x, y);
}

/* ---------- drawLineChart ----------------------------------------- */

/**
 * Draws a multi-dataset line chart on a <canvas> element.
 *
 * @param {string}   canvasId  — id attribute of the <canvas> element
 * @param {string[]} labels    — X-axis labels (e.g. ['Mon','Tue','Wed'])
 * @param {Object[]} datasets  — Array of dataset objects:
 *   @param {string}   datasets[].label  — Legend label
 *   @param {number[]} datasets[].data   — Y values (same length as labels)
 *   @param {string}   datasets[].color  — CSS colour string for the line
 *
 * Example:
 *   drawLineChart('myChart', ['Jan','Feb'], [
 *     { label: 'Score', data: [3, 7], color: '#ff6b9d' }
 *   ]);
 */
function drawLineChart(canvasId, labels, datasets) {
    var canvas = document.getElementById(canvasId);
    if (!canvas) return;

    var ctx = canvas.getContext('2d');
    var w = canvas.width;
    var h = canvas.height;
    var pad = { top: 30, right: 20, bottom: 40, left: 60 };
    var plotW = w - pad.left - pad.right;
    var plotH = h - pad.top - pad.bottom;

    // Find data range
    var allValues = [];
    datasets.forEach(function (ds) { allValues = allValues.concat(ds.data); });
    var yMin = Math.min.apply(null, allValues);
    var yMax = Math.max.apply(null, allValues);
    var yRange = yMax - yMin || 1;  // avoid division by zero
    var gridCount = 4;

    drawChartBackground(ctx, w, h, gridCount);

    // Y-axis labels
    for (var i = 0; i <= gridCount; i++) {
        var val = yMin + (yRange * i / gridCount);
        var yPos = pad.top + plotH - (i / gridCount) * plotH;
        drawChartLabel(ctx, val.toFixed(1), pad.left - 8, yPos, 'right');
    }

    // X-axis labels
    var xStep = plotW / (labels.length - 1 || 1);
    labels.forEach(function (label, idx) {
        var xPos = pad.left + idx * xStep;
        drawChartLabel(ctx, label, xPos, h - pad.bottom + 16, 'center');
    });

    // Draw each dataset
    datasets.forEach(function (ds) {
        ctx.strokeStyle = ds.color;
        ctx.lineWidth = 2.5;
        ctx.lineJoin = 'round';
        ctx.setLineDash([]);

        ctx.beginPath();
        ds.data.forEach(function (val, idx) {
            var x = pad.left + idx * xStep;
            var y = pad.top + plotH - ((val - yMin) / yRange) * plotH;
            if (idx === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        });
        ctx.stroke();

        // Draw dots
        ds.data.forEach(function (val, idx) {
            var x = pad.left + idx * xStep;
            var y = pad.top + plotH - ((val - yMin) / yRange) * plotH;
            ctx.fillStyle = ds.color;
            ctx.beginPath();
            ctx.arc(x, y, 4, 0, Math.PI * 2);
            ctx.fill();
            ctx.strokeStyle = CHART_BG;
            ctx.lineWidth = 1.5;
            ctx.stroke();
        });
    });

    // Draw legend
    drawChartLegend(ctx, w, pad.top, datasets);
}

/* ---------- drawBarChart ------------------------------------------ */

/**
 * Draws a single-dataset bar chart on a <canvas> element.
 *
 * @param {string}   canvasId  — id attribute of the <canvas> element
 * @param {string[]} labels    — X-axis labels
 * @param {number[]} data      — Y values (same length as labels)
 * @param {string}   color     — CSS colour for all bars
 *
 * Example:
 *   drawBarChart('myChart', ['A','B','C'], [10, 25, 8], '#cba6f7');
 */
function drawBarChart(canvasId, labels, data, color) {
    var canvas = document.getElementById(canvasId);
    if (!canvas) return;

    var ctx = canvas.getContext('2d');
    var w = canvas.width;
    var h = canvas.height;
    var pad = { top: 30, right: 20, bottom: 40, left: 60 };
    var plotW = w - pad.left - pad.right;
    var plotH = h - pad.top - pad.bottom;

    var yMax = Math.max.apply(null, data) || 1;
    var gridCount = 4;

    drawChartBackground(ctx, w, h, gridCount);

    // Y-axis labels
    for (var i = 0; i <= gridCount; i++) {
        var val = (yMax * i) / gridCount;
        var yPos = pad.top + plotH - (i / gridCount) * plotH;
        drawChartLabel(ctx, val.toFixed(1), pad.left - 8, yPos, 'right');
    }

    // Bars
    var barCount = data.length;
    var barWidth = Math.min(plotW / barCount * 0.65, 60);
    var gap = (plotW - barWidth * barCount) / (barCount + 1);

    data.forEach(function (val, idx) {
        var barH = (val / yMax) * plotH;
        var x = pad.left + gap + idx * (barWidth + gap);
        var y = pad.top + plotH - barH;

        // Bar rectangle
        ctx.fillStyle = color;
        ctx.shadowColor = 'rgba(0,0,0,0.3)';
        ctx.shadowBlur = 4;
        ctx.shadowOffsetY = 2;
        ctx.fillRect(x, y, barWidth, barH);
        ctx.shadowColor = 'transparent';

        // Value on top of bar
        drawChartLabel(ctx, val.toString(), x + barWidth / 2, y - 8, 'center');
    });

    // X-axis labels
    data.forEach(function (_, idx) {
        var xPos = pad.left + gap + idx * (barWidth + gap) + barWidth / 2;
        drawChartLabel(ctx, labels[idx], xPos, h - pad.bottom + 16, 'center');
    });
}

/* ---------- Chart legend helper ----------------------------------- */

/**
 * Draws a small legend in the top-right area of a chart.
 */
function drawChartLegend(ctx, canvasWidth, topOffset, datasets) {
    var x = canvasWidth - 20;
    var y = topOffset + 10;

    datasets.forEach(function (ds) {
        var textWidth = ctx.measureText(ds.label).width;
        x -= (textWidth + 30);

        // Colour swatch
        ctx.fillStyle = ds.color;
        ctx.fillRect(x, y - 4, 12, 12);

        // Label
        drawChartLabel(ctx, ds.label, x + 18, y + 1, 'left');

        y += 0; // single row; if more datasets spill, they stack
    });
}

/* ------------------------------------------------------------------ */
/*  8.  Smooth scroll for anchor links                                */
/* ------------------------------------------------------------------ */

/**
 * Intercepts clicks on same-page anchor links (href="#..." or
 * href="page.html#...") and scrolls smoothly to the target element.
 */
function initSmoothScroll() {
    document.addEventListener('click', function (e) {
        var anchor = e.target.closest('a');
        if (!anchor) return;

        var href = anchor.getAttribute('href');
        if (!href || href.charAt(0) !== '#') return;
        // Ignore links with only "#" or "#!"
        if (href === '#' || href.indexOf('#!') === 0) return;

        var targetId = href.substring(1);
        var target = document.getElementById(targetId);
        if (!target) return;

        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
}

/* ------------------------------------------------------------------ */
/*  9.  Toast notification system                                     */
/* ------------------------------------------------------------------ */

/**
 * Displays a toast notification at the bottom-right of the viewport.
 *
 * @param {string} message — The text to display
 * @param {string} type    — One of 'success', 'error', 'warning'
 *
 * Example:
 *   showToast('Profile saved!', 'success');
 */
function showToast(message, type) {
    // Ensure toast container exists
    var container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.style.cssText =
            'position:fixed;bottom:20px;right:20px;z-index:10000;' +
            'display:flex;flex-direction:column-reverse;gap:8px;' +
            'max-width:360px;';
        document.body.appendChild(container);
    }

    // Create toast element
    var toast = document.createElement('div');
    toast.className = 'toast toast--' + (type || 'info');

    // Colour mapping
    var colours = {
        success: { bg: '#2d8a4e', icon: '✓' },
        error:   { bg: '#c0392b', icon: '✗' },
        warning: { bg: '#b8860b', icon: '⚠' }
    };
    var cfg = colours[type] || { bg: '#555555', icon: 'ℹ' };

    toast.style.cssText =
        'background:' + cfg.bg + ';color:#fff;padding:12px 16px;' +
        'border-radius:8px;box-shadow:0 4px 12px rgba(0,0,0,0.3);' +
        'display:flex;align-items:center;gap:10px;font-size:14px;' +
        'line-height:1.4;opacity:0;transform:translateY(10px);' +
        'transition:opacity 0.3s ease, transform 0.3s ease;' +
        'cursor:pointer;';

    toast.innerHTML = '<span style="font-weight:700;margin-right:2px;">' +
        cfg.icon + '</span> ' + escapeHtml(message);

    container.appendChild(toast);

    // Trigger entrance animation (next frame)
    requestAnimationFrame(function () {
        toast.style.opacity = '1';
        toast.style.transform = 'translateY(0)';
    });

    // Auto-remove
    var removeTimer = setTimeout(function () {
        dismissToast(toast);
    }, TOAST_DURATION);

    // Click to dismiss early
    toast.addEventListener('click', function () {
        clearTimeout(removeTimer);
        dismissToast(toast);
    });
}

/**
 * Animates a toast out and removes it from the DOM.
 */
function dismissToast(toast) {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    setTimeout(function () {
        if (toast.parentNode) toast.parentNode.removeChild(toast);
    }, 300);
}

/* ------------------------------------------------------------------ */
/*  Utility: escape HTML to prevent XSS in toast messages             */
/* ------------------------------------------------------------------ */

function escapeHtml(str) {
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
}
