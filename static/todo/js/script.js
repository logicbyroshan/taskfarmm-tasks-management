// ==============================================================================
//  CORE APPLICATION JAVASCRIPT
//  Handles global layout, custom UI components, modals, and AJAX interactions.
// ==============================================================================

document.addEventListener('DOMContentLoaded', () => {
    setupMobileMenu();
    updateDateTime();
    setupAddTaskModal();
    setupEditTaskModal();
    setupCustomDropdowns();
    setupPWA();
    setupAlertAutoDismiss();

    // Update the date/time display every minute
    setInterval(updateDateTime, 60000);
});

// Global expose so onclick="openAddTaskModal()" works from HTML
window.openAddTaskModal = function() {
    const taskModal = document.getElementById('add-task-modal');
    if (taskModal) {
        taskModal.style.display = 'flex';
        const titleInput = taskModal.querySelector('input[name="title"]');
        if (titleInput) titleInput.focus();
    }
};

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
            // Close other open dropdowns
            document.querySelectorAll('.custom-select-wrapper.open').forEach(other => {
                if (other !== wrapper) other.classList.remove('open');
            });
            wrapper.classList.toggle('open');
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
 *  TASKFLIX AI ASSISTANT INTERACTIVE CONTROLLER
 * ============================================================================== */

function openAiModal() {
    const modal = document.getElementById('ai-assistant-modal');
    if (modal) {
        modal.style.display = 'flex';
        const promptInput = document.getElementById('ai-prompt-input');
        if (promptInput) promptInput.focus();
    }
}

function closeAiModal() {
    const modal = document.getElementById('ai-assistant-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function setAiPrompt(text) {
    const input = document.getElementById('ai-prompt-input');
    if (input) {
        input.value = text;
        generateAiResponse();
    }
}

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
