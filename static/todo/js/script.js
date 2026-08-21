// ==============================================================================
//  CORE APPLICATION JAVASCRIPT
//  Handles global layout, custom UI components, modals, and AJAX interactions.
// ==============================================================================

document.addEventListener('DOMContentLoaded', () => {
    setupWaveBackground();
    setupMobileMenu();
    setupGlobalSearch();
    updateDateTime();
    setupAddTaskModal();
    setupEditTaskModal();
    setupCustomDropdowns();
    setupPWA();
    setupAlertAutoDismiss();

    // Update the date/time display every minute
    setInterval(updateDateTime, 60000);
});

// Global expose so onclick="openAddTaskModal()" and "openAddProjectModal()" work from HTML
window.openAddTaskModal = function() {
    const taskModal = document.getElementById('add-task-modal');
    if (taskModal) {
        taskModal.style.display = 'flex';
        const titleInput = taskModal.querySelector('input[name="title"]');
        if (titleInput) titleInput.focus();
    }
};

window.openAddProjectModal = function() {
    const projModal = document.getElementById('category-modal');
    if (projModal) {
        projModal.style.display = 'flex';
        const nameInput = projModal.querySelector('input[name="name"]');
        if (nameInput) nameInput.focus();
    } else {
        window.location.href = '/categories/';
    }
};

/**
 * Global Toast Notification System
 */
window.showToast = function(message, type = 'success', duration = 3500) {
    let toastContainer = document.getElementById('global-toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'global-toast-container';
        toastContainer.style.cssText = 'position: fixed; bottom: 24px; right: 24px; z-index: 9999999; display: flex; flex-direction: column; gap: 10px; pointer-events: none;';
        document.body.appendChild(toastContainer);
    }

    const toast = document.createElement('div');
    toast.className = `custom-toast toast-${type}`;

    let iconClass = 'fa-check-circle';
    let borderColor = '#10b981';
    let iconColor = '#34d399';
    if (type === 'error') {
        iconClass = 'fa-exclamation-circle';
        borderColor = '#ef4444';
        iconColor = '#f87171';
    } else if (type === 'info') {
        iconClass = 'fa-info-circle';
        borderColor = '#3b82f6';
        iconColor = '#60a5fa';
    }

    toast.style.cssText = `
        background: #000000;
        border: 1px solid ${borderColor};
        color: #f4f4f5;
        padding: 12px 18px;
        border-radius: 8px;
        font-size: 0.85rem;
        font-weight: 500;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.9);
        display: flex;
        align-items: center;
        gap: 10px;
        pointer-events: auto;
        opacity: 0;
        transform: translateY(12px);
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    `;

    toast.innerHTML = `<i class="fas ${iconClass}" style="color: ${iconColor}; font-size: 1rem;"></i> <span>${message}</span>`;
    toastContainer.appendChild(toast);

    requestAnimationFrame(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateY(0)';
    });

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(12px)';
        setTimeout(() => toast.remove(), 300);
    }, duration);
};

/**
 * Global Search Bar Handler (Navbar)
 */
function setupGlobalSearch() {
    const searchInput = document.getElementById('search-input');
    if (!searchInput) return;

    // If currently on manage-tasks page, populate current search query
    const urlParams = new URLSearchParams(window.location.search);
    const existingSearch = urlParams.get('search');
    if (existingSearch) {
        searchInput.value = existingSearch;
    }

    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            const query = searchInput.value.trim();
            if (query) {
                window.location.href = `/manage-tasks/?search=${encodeURIComponent(query)}`;
            } else {
                if (window.location.pathname.includes('manage-tasks') || window.location.pathname.includes('my-tasks')) {
                    window.location.href = '/manage-tasks/';
                }
            }
        }
    });

    const searchIcon = searchInput.parentElement?.querySelector('.fa-search');
    if (searchIcon) {
        searchIcon.style.cursor = 'pointer';
        searchIcon.addEventListener('click', () => {
            const query = searchInput.value.trim();
            if (query) {
                window.location.href = `/manage-tasks/?search=${encodeURIComponent(query)}`;
            }
        });
    }
}

function setupAlertAutoDismiss() {
    document.querySelectorAll('.auto-dismiss').forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transition = 'opacity 0.5s ease';
            setTimeout(() => alert.remove(), 500);
        }, 4000);
    });
}


/**
 * Custom Dropdown UI Transformer
 * Transforms standard <select> controls into modern floating dropdown panels
 * with exact gap spacing (top: calc(100% + 6px)) and rounded item options.
 */
function setupCustomDropdowns() {
    const selectElements = document.querySelectorAll('select:not([data-custom-dropdown="true"])');

    selectElements.forEach(select => {
        // Mark as processed
        select.setAttribute('data-custom-dropdown', 'true');
        select.style.display = 'none'; // Hide native select

        // Create custom dropdown wrapper container
        const wrapper = document.createElement('div');
        wrapper.className = 'custom-select-wrapper';

        // Trigger button displaying current selection
        const trigger = document.createElement('div');
        trigger.className = 'custom-select-trigger';
        
        const selectedOption = select.options[select.selectedIndex] || select.options[0];
        const triggerText = document.createElement('span');
        triggerText.textContent = selectedOption ? selectedOption.text : 'Select...';
        
        const chevronIcon = document.createElement('i');
        chevronIcon.className = 'fas fa-chevron-down';

        trigger.appendChild(triggerText);
        trigger.appendChild(chevronIcon);
        wrapper.appendChild(trigger);

        // Options panel floating with gap
        const optionsPanel = document.createElement('div');
        optionsPanel.className = 'custom-select-options';

        Array.from(select.options).forEach((opt, idx) => {
            const optionItem = document.createElement('div');
            optionItem.className = 'custom-option' + (idx === select.selectedIndex ? ' selected' : '');
            optionItem.textContent = opt.text;
            optionItem.dataset.value = opt.value;

            optionItem.addEventListener('click', (e) => {
                e.stopPropagation();
                // Update native select
                select.value = opt.value;
                // Update trigger label
                triggerText.textContent = opt.text;

                // Update active highlight
                optionsPanel.querySelectorAll('.custom-option').forEach(el => el.classList.remove('selected'));
                optionItem.classList.add('selected');

                // Close dropdown
                wrapper.classList.remove('open');

                // Dispatch native change event for forms & listeners
                select.dispatchEvent(new Event('change', { bubbles: true }));
            });

            optionsPanel.appendChild(optionItem);
        });

        wrapper.appendChild(optionsPanel);

        // Toggle dropdown open state
        trigger.addEventListener('click', (e) => {
            e.stopPropagation();
            const isCurrentlyOpen = wrapper.classList.contains('open');

            // Close other open dropdowns
            document.querySelectorAll('.custom-select-wrapper.open').forEach(other => {
                other.classList.remove('open');
            });

            if (!isCurrentlyOpen) {
                wrapper.classList.add('open');
            }
        });

        // Insert wrapper next to original select
        select.parentNode.insertBefore(wrapper, select);
    });

    // Close dropdowns when clicking anywhere outside
    document.addEventListener('click', () => {
        document.querySelectorAll('.custom-select-wrapper.open').forEach(wrapper => {
            wrapper.classList.remove('open');
        });
    });

    // Close dropdowns on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            document.querySelectorAll('.custom-select-wrapper.open').forEach(wrapper => {
                wrapper.classList.remove('open');
            });
        }
    });
}

/**
 * Sets up the event listeners for the responsive mobile navigation menu (hamburger).
 */
function setupMobileMenu() {
    const navbar = document.querySelector('.navbar-left');
    if (!navbar || document.querySelector('.mobile-menu-toggle')) return;

    const mobileMenuToggle = document.createElement('div');
    mobileMenuToggle.className = 'mobile-menu-toggle';
    mobileMenuToggle.innerHTML = '<i class="fas fa-bars"></i>';
    navbar.appendChild(mobileMenuToggle);

    const sidebar = document.querySelector('.sidebar');
    const overlay = document.createElement('div');
    overlay.className = 'mobile-overlay';
    document.body.appendChild(overlay);

    const closeMenu = () => {
        if (sidebar) sidebar.classList.remove('mobile-open');
        overlay.classList.remove('active');
    };

    mobileMenuToggle.addEventListener('click', () => {
        if (sidebar) sidebar.classList.toggle('mobile-open');
        overlay.classList.toggle('active');
    });

    overlay.addEventListener('click', closeMenu);
}

/**
 * Updates the date and day display in the main navbar.
 */
function updateDateTime() {
    const now = new Date();
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const dayName = days[now.getDay()];
    const dateString = now.toLocaleDateString('en-GB');
    
    const dateElement = document.querySelector('.date-day');
    if (dateElement) {
        dateElement.innerHTML = `<span>${dayName}</span> <span>${dateString}</span>`;
    }
}

/**
 * Sets up all event listeners for the global "Add Task" modal.
 */
function setupAddTaskModal() {
    const taskModal = document.getElementById('add-task-modal');
    const addTaskForm = document.getElementById('add-task-form');
    const openModalButtons = document.querySelectorAll('.invite-btn:not(#add-category-btn)');

    if (!taskModal || !addTaskForm) return;

    const closeModal = () => {
        taskModal.style.display = 'none';
    };

    const openModal = () => {
        taskModal.style.display = 'flex';
        const titleInput = taskModal.querySelector('input[name="title"]');
        if (titleInput) titleInput.focus();
    };
    
    openModalButtons.forEach(btn => {
        btn.addEventListener('click', (event) => {
            event.preventDefault();
            openModal();
        });
    });

    taskModal.addEventListener('click', (event) => {
        if (event.target.classList.contains('close-modal') || 
            event.target.classList.contains('btn-cancel') ||
            event.target.classList.contains('modal-backdrop')) {
            closeModal();
        }
    });

    addTaskForm.addEventListener('submit', (event) => {
        event.preventDefault();
        const formData = new FormData(addTaskForm);
        const url = addTaskForm.action;

        fetch(url, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.location.reload(); 
            } else {
                let errorMessages = 'Please correct the following errors:\n\n';
                for (const field in data.errors) {
                    const fieldName = field.charAt(0).toUpperCase() + field.slice(1);
                    errorMessages += `- ${fieldName}: ${data.errors[field][0]}\n`;
                }
                alert(errorMessages);
            }
        })
        .catch(error => {
            console.error('Error submitting form:', error);
            alert('An unexpected error occurred. Please check the console and try again.');
        });
    });
}

/**
 * Sets up the edit task modal functionality.
 */
function setupEditTaskModal() {
    const editModal = document.getElementById('edit-task-modal');
    const editForm = document.getElementById('edit-task-form');
    const deleteBtn = document.getElementById('edit-delete-btn');
    if (!editModal || !editForm) return;

    const closeModal = () => { editModal.style.display = 'none'; };

    editModal.addEventListener('click', (event) => {
        if (event.target.classList.contains('close-modal') || event.target.classList.contains('btn-cancel') || event.target.classList.contains('modal-backdrop')) {
            closeModal();
        }
    });

    // Delete button in edit modal
    if (deleteBtn) {
        deleteBtn.addEventListener('click', () => {
            const taskId = document.getElementById('edit-task-id').value;
            if (!taskId) return;
            if (!confirm('Are you sure you want to delete this task?')) return;

            const csrfToken = getCsrfToken() || document.querySelector('[name=csrfmiddlewaretoken]')?.value;
            const formData = new FormData();
            formData.append('csrfmiddlewaretoken', csrfToken);

            fetch(`/task/${taskId}/delete/`, {
                method: 'POST',
                headers: { 'X-CSRFToken': csrfToken, 'X-Requested-With': 'XMLHttpRequest' },
                body: formData
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    closeModal();
                    window.location.reload();
                }
            })
            .catch(() => {
                // Fallback - reload page
                closeModal();
                window.location.reload();
            });
        });
    }

    window.openEditTaskModal = function(taskId) {
        fetch(`/task/${taskId}/update/`, { method: 'GET', headers: { 'X-Requested-With': 'XMLHttpRequest' } })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('edit-task-id').value = taskId;
                document.getElementById('edit-title').value = data.task.title;
                document.getElementById('edit-description').value = data.task.description || '';
                document.getElementById('edit-category').value = data.task.category || '';
                document.getElementById('edit-priority').value = data.task.priority;
                document.getElementById('edit-status').value = data.task.status;
                document.getElementById('edit-due_date').value = data.task.due_date || '';
                editModal.style.display = 'flex';
                document.getElementById('edit-title').focus();
            }
        }).catch(error => alert('Failed to load task data'));
    };

    editForm.addEventListener('submit', (event) => {
        event.preventDefault();
        const taskId = document.getElementById('edit-task-id').value;
        const formData = new FormData(editForm);
        const csrfToken = getCsrfToken() || document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        fetch(`/task/${taskId}/update/`, { 
            method: 'POST', 
            body: formData, 
            headers: { 
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest' 
            } 
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                closeModal();
                window.location.reload();
            } else {
                let errorMessages = 'Please correct the following errors:\n\n';
                for (const field in data.errors) {
                    errorMessages += `- ${field}: ${data.errors[field][0]}\n`;
                }
                alert(errorMessages);
            }
        }).catch(error => alert('An unexpected error occurred.'));
    });
}


/**
 * Sets up Progressive Web App (PWA) features.
 */
function setupPWA() {
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/static/todo/js/sw.js')
            .catch(() => {});
    }
}

/* ==============================================================================
 *  TASKMITRA AI SIDE DRAWER
 * ============================================================================== */

function openAiDrawer() {
    document.getElementById('ai-side-drawer')?.classList.add('open');
    document.getElementById('ai-drawer-overlay')?.classList.add('open');
    document.body.style.overflow = 'hidden';
    setTimeout(() => document.getElementById('ai-drawer-prompt')?.focus(), 350);
}

function closeAiDrawer() {
    document.getElementById('ai-side-drawer')?.classList.remove('open');
    document.getElementById('ai-drawer-overlay')?.classList.remove('open');
    document.body.style.overflow = '';
}

// Close drawer on Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeAiDrawer();
});

function setAiDrawerPrompt(text) {
    const input = document.getElementById('ai-drawer-prompt');
    if (input) { input.value = text; input.focus(); }
}

let drawerAiTitle = '', drawerAiDesc = '';

function generateAiDrawerResponse() {
    const input = document.getElementById('ai-drawer-prompt');
    const responseBox = document.getElementById('ai-drawer-response');
    const responseText = document.getElementById('ai-drawer-response-text');
    if (!input || !input.value.trim()) return;
    const query = input.value.trim();

    responseBox.style.display = 'flex';
    responseText.textContent = '⚡ Thinking...';

    fetch('/api/ai/suggest/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken(), 'X-Requested-With': 'XMLHttpRequest' },
        body: JSON.stringify({ prompt: query })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            drawerAiTitle = data.title || 'AI Suggestion';
            drawerAiDesc = data.suggestion || data.description || '';
            responseText.textContent = `💡 ${drawerAiTitle}\n\n${drawerAiDesc}`;
        } else {
            simulateLocalAiFallback_drawer(query);
        }
    })
    .catch(() => simulateLocalAiFallback_drawer(query));
}

function simulateLocalAiFallback_drawer(query) {
    const responseText = document.getElementById('ai-drawer-response-text');
    const q = query.toLowerCase();
    let title, desc;
    if (q.includes('website') || q.includes('launch')) {
        title = 'Website Launch Plan';
        desc = '1. Finalize DNS & SSL setup\n2. Cross-browser QA audit\n3. Performance & Lighthouse check\n4. Deploy migrations & go live\n5. Monitor uptime & errors';
    } else if (q.includes('marketing') || q.includes('campaign')) {
        title = 'Marketing Campaign Plan';
        desc = '1. Define audience & objectives\n2. Create content calendar\n3. Set up ad creatives & A/B tests\n4. Launch & monitor metrics\n5. Analyse & optimise';
    } else {
        title = 'AI Workflow Plan';
        desc = `Action plan for "${query}":\n- Priority: High\n- Estimate: 3-5 hours\n- Steps: Research, plan, execute, review`;
    }
    drawerAiTitle = title;
    drawerAiDesc = desc;
    if (responseText) responseText.textContent = `💡 ${title}\n\n${desc}`;
}

function applyAiDrawerToTask() {
    closeAiDrawer();
    window.openAddTaskModal && window.openAddTaskModal();
    setTimeout(() => {
        const titleInput = document.querySelector('#add-task-form input[name="title"]');
        const descInput = document.querySelector('#add-task-form textarea[name="description"]');
        if (titleInput && drawerAiTitle) titleInput.value = drawerAiTitle;
        if (descInput && drawerAiDesc) descInput.value = drawerAiDesc;
    }, 250);
}

// Keep backward compatibility
function openAiModal() { openAiDrawer(); }
function closeAiModal() { closeAiDrawer(); }
function setAiPrompt(text) { setAiDrawerPrompt(text); openAiDrawer(); }



let lastGeneratedAiTitle = "";
let lastGeneratedAiDesc = "";

function generateAiResponse() {
    const input = document.getElementById('ai-prompt-input');
    const responseBox = document.getElementById('ai-response-box');
    const responseText = document.getElementById('ai-response-text');
    
    if (!input || !input.value.trim()) {
        alert('Please enter an AI prompt or select a quick action.');
        return;
    }

    const query = input.value.trim();
    if (responseBox) responseBox.style.display = 'block';
    if (responseText) responseText.innerHTML = '<i class="fas fa-spinner fa-spin" style="color:#60a5fa;"></i> Analyzing request with TaskFlix AI Engine...';

    // Call AI Backend endpoint or simulate intelligent AI response
    fetch('/api/ai/suggest/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({ prompt: query })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            lastGeneratedAiTitle = data.title || "AI Suggested Task";
            lastGeneratedAiDesc = data.suggestion || data.description;
            responseText.innerText = `💡 Title: ${lastGeneratedAiTitle}\n\n${lastGeneratedAiDesc}`;
        } else {
            simulateLocalAiFallback(query);
        }
    })
    .catch(() => {
        simulateLocalAiFallback(query);
    });
}

function simulateLocalAiFallback(query) {
    const responseText = document.getElementById('ai-response-text');
    let title = "AI Generated Plan";
    let desc = "";

    if (query.toLowerCase().includes('website') || query.toLowerCase().includes('launch')) {
        title = "Execute Website Launch Strategy";
        desc = "1. Finalize DNS and SSL setup.\n2. Complete cross-browser visual QA.\n3. Run performance & lighthouse audit.\n4. Deploy database migrations and launch.";
    } else if (query.toLowerCase().includes('subtask') || query.toLowerCase().includes('breakdown')) {
        title = "Deconstruct Module Tasks";
        desc = "Subtasks:\n- Setup API endpoints & payload validation\n- Write unit tests for business logic\n- Integrate frontend state management\n- Verify error boundaries & fallback state";
    } else {
        title = "Optimize Workflow & Prioritize";
        desc = `AI Analysis for "${query}":\n- Priority: High\n- Estimated Time: 3.5 Hours\n- Recommended Action: Create backlog item, assign owner, and schedule review before release.`;
    }

    lastGeneratedAiTitle = title;
    lastGeneratedAiDesc = desc;

    if (responseText) {
        responseText.innerText = `💡 Suggested Title: ${title}\n\n${desc}`;
    }
}

function applyAiSuggestionToTask() {
    closeAiModal();
    const addTaskBtn = document.getElementById('add-task-btn');
    if (addTaskBtn) addTaskBtn.click();

    setTimeout(() => {
        const titleInput = document.querySelector('#add-task-form input[name="title"]');
        const descInput = document.querySelector('#add-task-form textarea[name="description"]');
        if (titleInput && lastGeneratedAiTitle) titleInput.value = lastGeneratedAiTitle;
        if (descInput && lastGeneratedAiDesc) descInput.value = lastGeneratedAiDesc;
    }, 200);
}

function getCsrfToken() {
    const name = 'csrftoken';
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/**
 * Dynamic Ambient Dot Wave Canvas
 * Creates a fluid, shimmering wave ripple flowing across a fixed matrix of dots.
 * The dots stay in their grid positions while multi-harmonic wave physics dynamically
 * modulate their vertical elevation, radius, and luminous cyan/blue glow over time.
 */
function setupWaveBackground() {
    const canvas = document.getElementById('bg-wave-canvas');
    if (!canvas) return;

    const ctx = canvas.getContext('2d', { alpha: true });
    if (!ctx) return;

    let width = 0;
    let height = 0;
    let dpr = 1;
    let animationFrameId = null;
    let startTime = performance.now();

    // Mouse interaction tracking
    let mouse = {
        x: -9999,
        y: -9999,
        targetX: -9999,
        targetY: -9999,
        radius: 200,
        active: false
    };

    function resize() {
        dpr = Math.min(window.devicePixelRatio || 1, 2);
        width = window.innerWidth;
        height = window.innerHeight;
        canvas.width = Math.floor(width * dpr);
        canvas.height = Math.floor(height * dpr);
        canvas.style.width = width + 'px';
        canvas.style.height = height + 'px';
        ctx.scale(dpr, dpr);
    }

    window.addEventListener('resize', resize, { passive: true });

    window.addEventListener('mousemove', (e) => {
        mouse.targetX = e.clientX;
        mouse.targetY = e.clientY;
        mouse.active = true;
    }, { passive: true });

    window.addEventListener('mouseleave', () => {
        mouse.active = false;
    }, { passive: true });

    resize();

    const dotSpacing = 28; // Grid step in px

    function render(now) {
        // Stop rendering if page/tab is hidden to save CPU/battery
        if (document.hidden) {
            animationFrameId = requestAnimationFrame(render);
            return;
        }

        const t = (now - startTime) * 0.001; // Time in seconds

        // Smooth mouse position lerping
        if (mouse.active) {
            mouse.x += (mouse.targetX - mouse.x) * 0.08;
            mouse.y += (mouse.targetY - mouse.y) * 0.08;
        } else {
            mouse.x += (-9999 - mouse.x) * 0.08;
            mouse.y += (-9999 - mouse.y) * 0.08;
        }

        ctx.clearRect(0, 0, width, height);

        const cols = Math.ceil(width / dotSpacing) + 2;
        const rows = Math.ceil(height / dotSpacing) + 2;

        // Draw dots with travelling fluid waves across the grid
        for (let j = 0; j < rows; j++) {
            const y0 = j * dotSpacing;

            for (let i = 0; i < cols; i++) {
                const x0 = i * dotSpacing;

                // Multi-harmonic traveling wave formulas
                const wave1 = Math.sin(x0 * 0.0045 + y0 * 0.003 - t * 1.4);
                const wave2 = Math.cos(x0 * 0.0035 - y0 * 0.0045 + t * 1.0);
                const wave3 = Math.sin((x0 + y0) * 0.0025 - t * 0.7);

                // Combined wave elevation normalized (-1.0 to 1.0)
                let elevation = (wave1 * 0.45 + wave2 * 0.35 + wave3 * 0.20);

                // Interactive mouse wave disturbance
                if (mouse.active) {
                    const dx = x0 - mouse.x;
                    const dy = y0 - mouse.y;
                    const dist = Math.sqrt(dx * dx + dy * dy);
                    if (dist < mouse.radius) {
                        const factor = (1 - dist / mouse.radius);
                        elevation += Math.sin(dist * 0.04 - t * 4.5) * factor * 0.5;
                    }
                }

                // Vertical undulating wave displacement (dots remain anchored, wave passes through)
                const y = y0 + elevation * 5.5;
                const x = x0 + Math.cos(y0 * 0.003 + t * 0.6) * 1.5;

                // Radius expands on wave crests, contracts in troughs
                const normElev = Math.max(0, Math.min(1, (elevation + 1) * 0.5)); // 0.0 to 1.0
                const radius = 1.0 + normElev * 1.3;

                // Alpha glow: dimmer in troughs, vibrant luminous glow on wave crests
                const alpha = 0.12 + normElev * 0.38;

                // Color shifts from deep royal blue at troughs to radiant cyan-blue at crests
                const r = Math.round(59 + normElev * 37);    // 59 -> 96
                const g = Math.round(130 + normElev * 35);   // 130 -> 165
                const b = Math.round(246 + normElev * 9);    // 246 -> 255

                ctx.beginPath();
                ctx.arc(x, y, radius, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${alpha.toFixed(3)})`;
                ctx.fill();
            }
        }

        animationFrameId = requestAnimationFrame(render);
    }

    animationFrameId = requestAnimationFrame(render);
}

