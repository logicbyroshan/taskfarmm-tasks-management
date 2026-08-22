// ==============================================================================
//  CORE APPLICATION JAVASCRIPT
//  Handles global layout, custom UI components, modals, and AJAX interactions.
// ==============================================================================

document.addEventListener('DOMContentLoaded', () => {
    setupSidebarCollapse();
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

function setupSidebarCollapse() {
    const isCollapsed = localStorage.getItem('taskflixx_sidebar_collapsed') === '1';
    const sidebar = document.querySelector('.sidebar');
    if (sidebar && isCollapsed) {
        sidebar.classList.add('collapsed');
    }
}

window.toggleSidebarCollapse = function() {
    const sidebar = document.querySelector('.sidebar');
    if (!sidebar) return;
    const isCollapsed = sidebar.classList.toggle('collapsed');
    localStorage.setItem('taskflixx_sidebar_collapsed', isCollapsed ? '1' : '0');
};

// Global expose so onclick="openAddTaskModal()" and "openAddProjectModal()" work from HTML
// Global Quick Add Task Modal Handlers
window.openAddTaskModal = function(initialStatus = 'not-started', initialCategory = '') {
    const modal = document.getElementById('add-task-modal');
    if (!modal) return;

    const titleInput = document.getElementById('add-task-title-input');
    const statusSelect = document.getElementById('add-task-status-input');
    const catSelect = document.getElementById('add-task-category-input');
    const prioSelect = document.getElementById('add-task-priority-input');
    const dueInput = document.getElementById('add-task-due-date-input');

    if (titleInput) titleInput.value = '';
    if (statusSelect) statusSelect.value = initialStatus || 'not-started';
    if (prioSelect) prioSelect.value = 'moderate';
    if (dueInput) dueInput.value = '';

    // If on Kanban, get currently selected project from hidden input or URL
    const activeProjInput = document.getElementById('current-active-project-id');
    const urlParams = new URLSearchParams(window.location.search);
    const activeProjFromUrl = urlParams.get('project');
    const kanbanProjSelect = document.getElementById('kanban-project-select');
    const selectedProj = initialCategory || (activeProjInput ? activeProjInput.value : '') || activeProjFromUrl || (kanbanProjSelect ? kanbanProjSelect.value : '');

    if (catSelect && selectedProj) {
        catSelect.value = selectedProj;
    }

    modal.style.display = 'flex';
    setTimeout(() => {
        if (titleInput) titleInput.focus();
    }, 60);
};

window.closeAddTaskModal = function() {
    const modal = document.getElementById('add-task-modal');
    if (modal) modal.style.display = 'none';
};

window.handleAddTaskFormSubmit = function(e) {
    e.preventDefault();
    const form = e.target;
    const submitBtn = document.getElementById('add-task-submit-btn');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating...';
    }

    const formData = new FormData(form);
    const csrfToken = getCsrfToken() || form.querySelector('[name=csrfmiddlewaretoken]')?.value;

    fetch(form.action || '/task/create/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: formData
    })
    .then(r => r.json())
    .then(data => {
        if (data.success && data.task) {
            closeAddTaskModal();
            if (window.showToast) {
                window.showToast(`Task "${data.task.title}" created!`, 'success', 1200);
            }
            // Instant DOM insertion without page reload
            const inserted = insertTaskCardToKanban(data.task);
            if (!inserted) {
                const taskList = document.getElementById('dashboard-tasks-container');
                if (taskList) {
                    insertTaskCardToDashboard(data.task);
                } else {
                    setTimeout(() => window.location.reload(), 300);
                }
            }
        } else {
            alert(data.message || (data.errors ? JSON.stringify(data.errors) : 'Error creating task.'));
        }
    })
    .catch(err => {
        console.error('Error creating task:', err);
        alert('Network error while creating task.');
    })
    .finally(() => {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-plus"></i> Create Task';
        }
    });
};

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function insertTaskCardToKanban(task) {
    const status = task.status || 'not-started';
    const container = document.querySelector(`.kanban-cards-container[data-status="${status}"]`);
    if (!container) return false;

    // Hide empty state if present
    const emptyEl = document.getElementById(`empty-${status}`);
    if (emptyEl) emptyEl.style.display = 'none';

    const prio = task.priority || 'moderate';
    const prioLabel = prio.charAt(0).toUpperCase() + prio.slice(1);
    const userInitials = (task.user || 'DE').slice(0, 2).toUpperCase();

    const cardDiv = document.createElement('div');
    cardDiv.className = `kanban-card ${status === 'completed' ? 'is-completed' : ''}`;
    cardDiv.id = `kanban-card-${task.id}`;
    cardDiv.setAttribute('data-task-id', task.id);
    cardDiv.setAttribute('data-assignees', task.user || '');
    cardDiv.setAttribute('draggable', 'true');
    cardDiv.setAttribute('ondragstart', 'handleDragStart(event)');
    cardDiv.setAttribute('onclick', `openTrelloModal(${task.id})`);
    cardDiv.style.opacity = '0';
    cardDiv.style.transform = 'translateY(-6px)';
    cardDiv.style.transition = 'opacity 0.25s ease, transform 0.25s ease';

    cardDiv.innerHTML = `
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
            <span class="priority-tag prio-${prio}">${prioLabel}</span>
        </div>
        <div class="kanban-card-title" style="font-size: 0.9rem; font-weight: 600; color: #dee4ea; margin-bottom: 4px; line-height: 1.4;">${escapeHtml(task.title)}</div>
        ${task.description ? `<div style="font-size: 0.775rem; color: #8c9bab; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; margin-bottom: 8px;">${escapeHtml(task.description)}</div>` : ''}
        <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 8px; padding-top: 6px; border-top: 1px solid #282e33; font-size: 0.725rem;">
            <div class="card-assignees" style="display: flex; align-items: center; gap: 4px; margin-left: auto;">
                <span title="Created by ${escapeHtml(task.user || 'You')}" style="width: 22px; height: 22px; min-width: 22px; border-radius: 5px; background: linear-gradient(135deg, #1e293b, #0f172a); color: #94a3b8; font-size: 0.65rem; font-weight: 700; display: inline-flex; align-items: center; justify-content: center; border: 1px solid #334155; box-shadow: 0 1px 3px rgba(0,0,0,0.4);">
                    ${userInitials}
                </span>
            </div>
        </div>
    `;

    container.insertBefore(cardDiv, container.firstChild);
    requestAnimationFrame(() => {
        cardDiv.style.opacity = '1';
        cardDiv.style.transform = 'translateY(0)';
    });

    if (window.updateKanbanColumnCounts) updateKanbanColumnCounts();
    return true;
}

function insertTaskCardToDashboard(task) {
    const container = document.getElementById('dashboard-tasks-container');
    if (!container) return false;
    // Hide empty state if present
    const emptyState = document.getElementById('dashboard-empty-state');
    if (emptyState) emptyState.style.display = 'none';

    const prio = task.priority || 'moderate';
    const prioLabel = prio.charAt(0).toUpperCase() + prio.slice(1);
    const userInitials = (task.user || 'DE').slice(0, 2).toUpperCase();

    const art = document.createElement('article');
    art.className = 'task-card';
    art.id = `task-card-${task.id}`;
    art.setAttribute('role', 'listitem');
    art.setAttribute('onclick', `openTrelloModal(${task.id})`);
    art.style.cursor = 'pointer';

    art.innerHTML = `
        <div class="task-card-header">
            <div class="task-card-title-group" style="display: flex; align-items: center; gap: 10px; width: 100%;">
                <input type="checkbox" id="task${task.id}" class="task-checkbox" onchange="event.stopPropagation(); toggleTaskCompletion(${task.id}, this.checked);">
                <label for="task${task.id}" onclick="event.stopPropagation(); openTrelloModal(${task.id});" style="cursor: pointer; flex: 1;">
                    <h3 class="task-title" style="margin: 0; font-size: 0.925rem;">${escapeHtml(task.title)}</h3>
                </label>
                <button type="button" class="task-menu-btn" aria-label="Task options" onclick="event.stopPropagation(); openTrelloModal(${task.id});">
                    <i class="fas fa-ellipsis-v"></i>
                </button>
            </div>
        </div>
    `;

    container.insertBefore(art, container.firstChild);
    return true;
}

window.openAddProjectModal = function() {
    const projModal = document.getElementById('category-modal');
    if (projModal) {
        projModal.style.display = 'flex';
        const nameInput = document.getElementById('new_project_name') || projModal.querySelector('input[name="name"]');
        if (nameInput) setTimeout(() => nameInput.focus(), 50);
    } else {
        window.location.href = '/manage-projects/';
    }
};

window.closeAddProjectModal = function() {
    const projModal = document.getElementById('category-modal');
    if (projModal) projModal.style.display = 'none';
};

window.openEditProjectModal = function(id, name, color, template, description) {
    const editModal = document.getElementById('edit-category-modal');
    const editForm = document.getElementById('edit-category-form');
    const editName = document.getElementById('edit_project_name');
    const editColor = document.getElementById('edit_project_color');
    const editId = document.getElementById('edit_project_id');
    const editDesc = document.getElementById('edit_project_description');

    if (editForm) editForm.action = '/category/' + id + '/update/';
    if (editId) editId.value = id;
    if (editName) editName.value = name || '';
    if (editColor) editColor.value = color || '#3b82f6';
    if (editDesc) editDesc.value = description || '';

    selectEditTemplate(template || 'smart');
    selectEditProjectColor(color || '#3b82f6');

    if (editModal) {
        editModal.style.display = 'flex';
        if (editName) setTimeout(() => editName.focus(), 50);
    }
};

window.closeEditProjectModal = function() {
    const editModal = document.getElementById('edit-category-modal');
    if (editModal) editModal.style.display = 'none';
};

window.selectAddProjectColor = function(color) {
    const colorInput = document.getElementById('new_project_color');
    if (colorInput) colorInput.value = color;
    document.querySelectorAll('#add-color-swatches .color-swatch-btn').forEach(btn => {
        btn.style.borderColor = (btn.style.backgroundColor === color || btn.getAttribute('onclick')?.includes(color)) ? '#ffffff' : 'transparent';
    });
};

window.syncAddProjectCustomColor = function(color) {
    document.querySelectorAll('#add-color-swatches .color-swatch-btn').forEach(btn => {
        btn.style.borderColor = 'transparent';
    });
};

window.selectEditProjectColor = function(color) {
    const colorInput = document.getElementById('edit_project_color');
    if (colorInput) colorInput.value = color;
    document.querySelectorAll('#edit-color-swatches .color-swatch-btn').forEach(btn => {
        btn.style.borderColor = (btn.style.backgroundColor === color || btn.getAttribute('onclick')?.includes(color)) ? '#ffffff' : 'transparent';
    });
};

window.syncEditProjectCustomColor = function(color) {
    document.querySelectorAll('#edit-color-swatches .color-swatch-btn').forEach(btn => {
        btn.style.borderColor = 'transparent';
    });
};

window.selectAddTemplate = function(template) {
    const smartRadio = document.getElementById('add_tpl_smart');
    const superRadio = document.getElementById('add_tpl_super');
    const smartLabel = document.getElementById('add-tpl-smart-label');
    const superLabel = document.getElementById('add-tpl-super-label');

    if (template === 'super') {
        if (superRadio) superRadio.checked = true;
        if (superLabel) {
            superLabel.style.borderColor = '#3b82f6';
            superLabel.style.background = 'rgba(59, 130, 246, 0.08)';
        }
        if (smartLabel) {
            smartLabel.style.borderColor = '#27272a';
            smartLabel.style.background = '#121316';
        }
    } else {
        if (smartRadio) smartRadio.checked = true;
        if (smartLabel) {
            smartLabel.style.borderColor = '#3b82f6';
            smartLabel.style.background = 'rgba(59, 130, 246, 0.08)';
        }
        if (superLabel) {
            superLabel.style.borderColor = '#27272a';
            superLabel.style.background = '#121316';
        }
    }
};

window.selectEditTemplate = function(template) {
    const smartRadio = document.getElementById('edit_tpl_smart');
    const superRadio = document.getElementById('edit_tpl_super');
    const smartLabel = document.getElementById('edit-tpl-smart-label');
    const superLabel = document.getElementById('edit-tpl-super-label');

    if (template === 'super') {
        if (superRadio) superRadio.checked = true;
        if (superLabel) {
            superLabel.style.borderColor = '#3b82f6';
            superLabel.style.background = 'rgba(59, 130, 246, 0.08)';
        }
        if (smartLabel) {
            smartLabel.style.borderColor = '#27272a';
            smartLabel.style.background = '#121316';
        }
    } else {
        if (smartRadio) smartRadio.checked = true;
        if (smartLabel) {
            smartLabel.style.borderColor = '#3b82f6';
            smartLabel.style.background = 'rgba(59, 130, 246, 0.08)';
        }
        if (superLabel) {
            superLabel.style.borderColor = '#27272a';
            superLabel.style.background = '#121316';
        }
    }
};

/**
 * Global Intelligent Auto-Correct & Spell-Check helper (Powered by OpenHinglish)
 * Corrects spelling in English, Hindi & Hinglish with subtle animation & toast.
 */
window.autoCorrectInput = function(inputElementOrId, silent = false) {
    if (localStorage.getItem('taskflixx_autocorrect_enabled') === 'false') return;
    const el = typeof inputElementOrId === 'string' ? document.getElementById(inputElementOrId) : inputElementOrId;
    if (!el) return;
    const originalText = el.value;
    if (!originalText || !originalText.trim()) return;

    fetch('/api/autocorrect/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken(),
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ text: originalText })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success && data.corrected && data.corrected !== originalText) {
            el.value = data.corrected;
            el.dispatchEvent(new Event('input', { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));

            // Visual feedback flash
            const prevTransition = el.style.transition;
            el.style.transition = 'background 0.3s ease, border-color 0.3s ease';
            el.style.background = 'rgba(59, 130, 246, 0.15)';
            el.style.borderColor = '#579dff';
            setTimeout(() => {
                el.style.background = '';
                el.style.borderColor = '';
                el.style.transition = prevTransition;
            }, 500);

            if (data.changed && !silent && window.showToast) {
                window.showToast('✨ Auto-corrected (OpenHinglish)', 'info', 1500);
            }
        }
    })
    .catch(err => console.error('Auto-correct notice:', err));
};

// Automatic listener for task & project input blur
document.addEventListener('DOMContentLoaded', function() {
    const autoCorrectIds = [
        'add-task-title-input',
        'add-task-description-input',
        'new_project_name',
        'new_project_description',
        'edit_project_name',
        'edit_project_description',
        'trello-task-title-input',
        'trello-description-input',
        'trello-comment-input'
    ];

    document.addEventListener('focusout', function(e) {
        if (e.target && autoCorrectIds.includes(e.target.id)) {
            window.autoCorrectInput(e.target, true);
        }
    });
});

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
    const openModalButtons = document.querySelectorAll('.open-add-task-btn, [data-action="add-task"], #open-task-modal-btn');

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
}

// ==============================================================================
//  TRELLO-STYLE RICH CARD MODAL MANAGER
// ==============================================================================
let currentTrelloTask = null;

window.openTrelloModal = function(taskId) {
    const modal = document.getElementById('trello-task-modal');
    if (!modal) {
        if (window.openEditTaskModalLegacy) return window.openEditTaskModalLegacy(taskId);
        return;
    }

    fetch(`/task/${taskId}/update/`, { method: 'GET', headers: { 'X-Requested-With': 'XMLHttpRequest' } })
        .then(r => r.json())
        .then(data => {
            if (data.success && data.task) {
                currentTrelloTask = data.task;
                
                const titleInput = document.getElementById('trello-task-title-input');
                const projText = document.getElementById('trello-project-text');
                const statusSelect = document.getElementById('trello-status-select');
                const prioSelect = document.getElementById('trello-priority-select');
                const projSelect = document.getElementById('trello-project-select');
                const dueInput = document.getElementById('trello-due-date-input');
                const descDisplay = document.getElementById('trello-desc-display');
                const descInput = document.getElementById('trello-description-input');
                const checklistSec = document.getElementById('trello-checklist-section');

                if (titleInput) titleInput.value = data.task.title;
                if (projText) projText.textContent = data.task.category_name || 'General';
                
                const statusNames = {
                    'not-started': 'To Do',
                    'in-progress': 'In Progress',
                    'backlog': 'Backlog',
                    'on-hold': 'On Hold',
                    'completed': 'Done',
                    'canceled': 'Canceled'
                };
                const prioInfo = {
                    'high': { text: 'High', dot: '🔴' },
                    'moderate': { text: 'Moderate', dot: '🟡' },
                    'low': { text: 'Low', dot: '🟢' }
                };

                const statusPillText = document.getElementById('trello-status-pill-text');
                if (statusPillText) statusPillText.textContent = statusNames[data.task.status] || data.task.status_display || 'To Do';

                const prioPillText = document.getElementById('trello-priority-pill-text');
                const prioDot = document.getElementById('trello-priority-dot');
                const pInfo = prioInfo[data.task.priority] || { text: 'Moderate', dot: '🟡' };
                if (prioPillText) prioPillText.textContent = pInfo.text;
                if (prioDot) prioDot.textContent = pInfo.dot;

                if (statusSelect) statusSelect.value = data.task.status;
                if (prioSelect) prioSelect.value = data.task.priority;
                if (projSelect) projSelect.value = data.task.category || '';
                if (dueInput) dueInput.value = data.task.due_date || '';
                if (descInput) descInput.value = data.task.description || '';

                if (descDisplay) {
                    if (data.task.description && data.task.description.trim()) {
                        descDisplay.textContent = data.task.description;
                        descDisplay.style.color = '#dee4ea';
                    } else {
                        descDisplay.textContent = 'Add a more detailed description...';
                        descDisplay.style.color = '#8c9bab';
                    }
                }

                updateTrelloStatusBadge(data.task.status);
                updateTrelloCompleteIcon(data.task.status === 'completed');
                updateTrelloDueDateText(data.task.due_date || '');

                const labelsContainer = document.getElementById('trello-labels-container');
                const labelBadge = document.getElementById('trello-label-badge');
                if (labelsContainer) labelsContainer.style.display = 'block';
                if (labelBadge) {
                    labelBadge.textContent = pInfo.text;
                    const colorMap = { 'high': '#ef4444', 'moderate': '#f59e0b', 'low': '#22c55e' };
                    labelBadge.style.background = colorMap[data.task.priority] || '#216e4e';
                }

                const checklistTitleInput = document.getElementById('trello-checklist-title-input');
                if (checklistTitleInput) {
                    checklistTitleInput.value = data.task.checklist_title || 'Checklist';
                }

                if (data.task.checklist && data.task.checklist.length > 0) {
                    if (checklistSec) checklistSec.style.display = 'block';
                    renderTrelloChecklist(data.task.checklist);
                } else {
                    if (checklistSec) checklistSec.style.display = 'none';
                }

                renderTrelloComments(data.task.comments || [], data.task);
                renderTrelloMembers(data.task.assignees || [], data.task);
                renderTrelloAttachments(data.task.attachments || []);

                modal.style.display = 'flex';
            }
        })
        .catch(err => console.error('Error opening trello modal', err));
};

window.renderTrelloMembers = function(assignees, task) {
    const chips = document.getElementById('trello-members-chips');
    if (!chips) return;

    const membersList = assignees || [];
    if (membersList.length === 0) {
        const creatorName = (task && task.user) || (currentTrelloTask && currentTrelloTask.user) || 'You';
        const creatorInitials = creatorName.slice(0, 2).toUpperCase();
        chips.innerHTML = `
            <div title="Created by ${creatorName} (Click to manage)" style="width: 32px; height: 32px; min-width: 32px; min-height: 32px; max-width: 32px; max-height: 32px; border-radius: 4px !important; background: #0c66e4; color: #ffffff; display: flex; align-items: center; justify-content: center; font-size: 0.775rem; font-weight: 700; border: 1px solid #1c2024; cursor: pointer; flex-shrink: 0; box-sizing: border-box; transition: transform 0.15s ease;" onclick="toggleTrelloMembersPopup(event)" onmouseenter="this.style.transform='scale(1.05)'" onmouseleave="this.style.transform='scale(1)'">
                ${creatorInitials}
            </div>
            <button type="button" onclick="toggleTrelloMembersPopup(event)" title="Assign members" style="width: 32px; height: 32px; min-width: 32px; min-height: 32px; max-width: 32px; max-height: 32px; border-radius: 4px !important; background: #22272b; color: #579dff; border: 1px solid #3b444c; font-size: 0.85rem; cursor: pointer; display: flex; align-items: center; justify-content: center; padding: 0; flex-shrink: 0; box-sizing: border-box; transition: all 0.15s ease;" onmouseenter="this.style.background='#282e33'; this.style.borderColor='#579dff';" onmouseleave="this.style.background='#22272b'; this.style.borderColor='#3b444c';">
                <i class="fas fa-plus"></i>
            </button>
        `;
        return;
    }

    const colors = ['#0c66e4', '#d97706', '#216e4e', '#7c3aed'];
    chips.innerHTML = `
        <div style="display: flex; align-items: center; gap: 4px;">
            ${membersList.map((a, idx) => `
                <div title="Assigned to ${a.username} (Click to manage)" style="width: 32px; height: 32px; min-width: 32px; min-height: 32px; max-width: 32px; max-height: 32px; border-radius: 4px !important; background: ${colors[idx % colors.length]}; color: #ffffff; display: flex; align-items: center; justify-content: center; font-size: 0.775rem; font-weight: 700; border: 1px solid #1c2024; cursor: pointer; flex-shrink: 0; box-sizing: border-box; transition: transform 0.15s ease;" onclick="toggleTrelloMembersPopup(event)" onmouseenter="this.style.transform='scale(1.05)'" onmouseleave="this.style.transform='scale(1)'">
                    ${a.initials}
                </div>
            `).join('')}
        </div>
        <button type="button" onclick="toggleTrelloMembersPopup(event)" title="Assign members" style="width: 32px; height: 32px; min-width: 32px; min-height: 32px; max-width: 32px; max-height: 32px; border-radius: 4px !important; background: #22272b; color: #579dff; border: 1px solid #3b444c; font-size: 0.85rem; cursor: pointer; display: flex; align-items: center; justify-content: center; padding: 0; flex-shrink: 0; box-sizing: border-box; transition: all 0.15s ease; margin-left: 2px;" onmouseenter="this.style.background='#282e33'; this.style.borderColor='#579dff';" onmouseleave="this.style.background='#22272b'; this.style.borderColor='#3b444c';">
            <i class="fas fa-plus"></i>
        </button>
    `;
};

window.toggleTrelloMembersPopup = function(e) {
    if (e) e.stopPropagation();
    const popup = document.getElementById('trello-members-popup');
    if (!popup) return;

    if (popup.style.display === 'block') {
        popup.style.display = 'none';
        return;
    }

    if (!currentTrelloTask) return;

    const pid = currentTrelloTask.category;
    if (!pid) {
        populateTrelloMembersChecklist([{ id: 1, username: currentTrelloTask.user || 'demo_user', initials: (currentTrelloTask.user || 'DE').slice(0, 2).toUpperCase() }]);
        popup.style.display = 'block';
        return;
    }

    fetch(`/project/${pid}/share/`, {
        method: 'GET',
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            const allMembers = [data.owner, ...(data.members || [])];
            populateTrelloMembersChecklist(allMembers);
            popup.style.display = 'block';
        }
    })
    .catch(err => console.error('Error fetching project members:', err));
};

function populateTrelloMembersChecklist(members) {
    const list = document.getElementById('trello-members-checkbox-list');
    if (!list || !currentTrelloTask) return;

    const assignedIds = new Set((currentTrelloTask.assignees || []).map(a => a.id));

    list.innerHTML = members.map(m => `
        <label style="display: flex; align-items: center; gap: 8px; padding: 6px 8px; border-radius: 4px; cursor: pointer; background: #1d2125; color: #dee4ea; font-size: 0.825rem; transition: background 0.15s ease;" onmouseenter="this.style.background='#282e33';" onmouseleave="this.style.background='#1d2125';">
            <input type="checkbox" ${assignedIds.has(m.id) ? 'checked' : ''} onchange="toggleTrelloAssignee(${m.id}, this.checked)" style="accent-color: #579dff; cursor: pointer;">
            <div style="width: 22px; height: 22px; border-radius: 50%; background: #0c66e4; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 0.65rem; font-weight: 700;">
                ${m.initials}
            </div>
            <span>${m.username}</span>
        </label>
    `).join('');
}

window.closeTrelloMembersPopup = function() {
    const popup = document.getElementById('trello-members-popup');
    if (popup) popup.style.display = 'none';
};

window.toggleTrelloAssignee = function(memberId, isChecked) {
    if (!currentTrelloTask) return;
    const currentAssigneeIds = (currentTrelloTask.assignees || []).map(a => a.id);
    let newAssigneeIds;
    if (isChecked) {
        newAssigneeIds = Array.from(new Set([...currentAssigneeIds, memberId]));
    } else {
        newAssigneeIds = currentAssigneeIds.filter(id => id !== memberId);
    }

    const csrfToken = getCsrfToken() || document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    fetch(`/task/${currentTrelloTask.id}/update/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ assignees: newAssigneeIds })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success && data.task) {
            currentTrelloTask.assignees = data.task.assignees;
            renderTrelloMembers(data.task.assignees, currentTrelloTask);
            updateBoardCardAssignees(currentTrelloTask.id, data.task.assignees);
            if (window.showToast) window.showToast('Card members updated', 'success', 1000);
        }
    })
    .catch(err => console.error('Error updating assignees:', err));
};

function updateBoardCardAssignees(taskId, assignees) {
    const card = document.querySelector(`.kanban-card[data-task-id="${taskId}"]`);
    if (!card) return;

    const usernames = (assignees || []).map(a => a.username).join(',');
    card.setAttribute('data-assignees', usernames);

    const assigneesContainer = card.querySelector('.card-assignees');
    if (assigneesContainer) {
        if (assignees && assignees.length > 0) {
            assigneesContainer.innerHTML = assignees.map(a => `
                <span title="Assigned to ${a.username}" style="width: 22px; height: 22px; border-radius: 50%; background: #0c66e4; color: #ffffff; font-size: 0.65rem; font-weight: 700; display: inline-flex; align-items: center; justify-content: center; border: 1px solid #18181b;">
                    ${a.initials}
                </span>
            `).join('');
        } else if (currentTrelloTask && currentTrelloTask.user) {
            const initials = currentTrelloTask.user.slice(0, 2).toUpperCase();
            assigneesContainer.innerHTML = `
                <span title="Created by ${currentTrelloTask.user}" style="width: 22px; height: 22px; border-radius: 50%; background: #282e33; color: #8c9bab; font-size: 0.65rem; font-weight: 600; display: inline-flex; align-items: center; justify-content: center; border: 1px solid #333c43;">
                    ${initials}
                </span>
            `;
        }
    }
}

document.addEventListener('click', function(e) {
    if (!e.target.closest('#trello-members-popup') && !e.target.closest('.trello-pill-action')) {
        closeTrelloMembersPopup();
    }
});

window.toggleTrelloProjectDropdown = function(e) {
    if (e) e.stopPropagation();
    closeAllTrelloDropdowns();
    const menu = document.getElementById('trello-project-dropdown-menu');
    if (menu) menu.style.display = menu.style.display === 'block' ? 'none' : 'block';
};

window.selectTrelloProject = function(id, name) {
    const projText = document.getElementById('trello-project-text');
    if (projText) projText.textContent = name;
    saveTrelloTaskField('category', id);
    closeAllTrelloDropdowns();
};

window.toggleTrelloStatusDropdown = function(e) {
    if (e) e.stopPropagation();
    closeAllTrelloDropdowns();
    const menu = document.getElementById('trello-status-dropdown-menu');
    if (menu) menu.style.display = menu.style.display === 'block' ? 'none' : 'block';
};

window.selectTrelloStatus = function(status, name) {
    const statusText = document.getElementById('trello-status-pill-text');
    if (statusText) statusText.textContent = name;
    const select = document.getElementById('trello-status-select');
    if (select) select.value = status;
    saveTrelloTaskField('status', status);
    updateTrelloCompleteIcon(status === 'completed');
    closeAllTrelloDropdowns();
};

window.toggleTrelloPriorityDropdown = function(e) {
    if (e) e.stopPropagation();
    closeAllTrelloDropdowns();
    const menu = document.getElementById('trello-priority-dropdown-menu');
    if (menu) menu.style.display = menu.style.display === 'block' ? 'none' : 'block';
};

window.selectTrelloPriority = function(priority, label) {
    const prioText = document.getElementById('trello-priority-pill-text');
    const prioDot = document.getElementById('trello-priority-dot');
    const prioInfo = {
        'high': { text: 'High', dot: '🔴' },
        'moderate': { text: 'Moderate', dot: '🟡' },
        'low': { text: 'Low', dot: '🟢' }
    };
    const p = prioInfo[priority] || { text: 'Moderate', dot: '🟡' };
    if (prioText) prioText.textContent = p.text;
    if (prioDot) prioDot.textContent = p.dot;

    const select = document.getElementById('trello-priority-select');
    if (select) select.value = priority;
    saveTrelloTaskField('priority', priority);

    // Sync active Label / Priority badge
    const labelsContainer = document.getElementById('trello-labels-container');
    const labelBadge = document.getElementById('trello-label-badge');
    if (labelsContainer) labelsContainer.style.display = 'block';
    if (labelBadge) {
        labelBadge.textContent = p.text;
        const colorMap = { 'high': '#ef4444', 'moderate': '#f59e0b', 'low': '#22c55e' };
        labelBadge.style.background = colorMap[priority] || '#216e4e';
    }

    closeTrelloMenus();
};

function closeAllTrelloDropdowns() {
    const menus = [
        'trello-project-dropdown-menu',
        'trello-status-dropdown-menu',
        'trello-priority-dropdown-menu',
        'trello-add-dropdown-menu',
        'trello-labels-popup'
    ];
    menus.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.style.display = 'none';
    });
}

window.toggleTrelloAddMenu = function(e) {
    if (e) e.stopPropagation();
    const menu = document.getElementById('trello-add-dropdown-menu');
    const isShown = menu && menu.style.display === 'block';
    closeTrelloMenus();
    if (menu && !isShown) menu.style.display = 'block';
};

window.toggleTrelloLabelsPopup = function(e) {
    if (e) e.stopPropagation();
    const menu = document.getElementById('trello-labels-popup');
    const isShown = menu && menu.style.display === 'block';
    closeTrelloMenus();
    if (menu && !isShown) menu.style.display = 'block';
};

window.closeTrelloMenus = function() {
    closeAllTrelloDropdowns();
    closeTrelloMembersPopup();
};

document.addEventListener('click', function(e) {
    if (!e.target.closest('#trello-project-pill-btn') &&
        !e.target.closest('#trello-status-pill-btn') &&
        !e.target.closest('#trello-priority-pill-btn') &&
        !e.target.closest('#trello-add-dropdown-menu') &&
        !e.target.closest('#trello-labels-popup') &&
        !e.target.closest('#trello-members-popup') &&
        !e.target.closest('.trello-pill-action')) {
        closeTrelloMenus();
    }
});

let currentShareProjectId = null;

window.openShareProjectModal = function(projectId) {
    const modal = document.getElementById('share-project-modal');
    if (!modal) return;

    const pid = projectId || (currentTrelloTask ? currentTrelloTask.category : null) || document.getElementById('kanban-project-select')?.value;
    if (!pid) {
        if (window.showToast) window.showToast('Please select a project first', 'info');
        return;
    }
    currentShareProjectId = pid;

    fetch(`/project/${pid}/share/`, {
        method: 'GET',
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            const input = document.getElementById('share-project-link-input');
            if (input) input.value = data.share_url;

            const list = document.getElementById('share-project-members-list');
            if (list) {
                let html = `
                    <div style="display:flex;align-items:center;justify-content:space-between;padding:8px 12px;background:#22272b;border-radius:4px;">
                        <div style="display:flex;align-items:center;gap:10px;">
                            <div style="width:28px;height:28px;border-radius:50%;background:#0c66e4;color:#fff;display:flex;align-items:center;justify-content:center;font-size:0.75rem;font-weight:700;">
                                ${data.owner.initials}
                            </div>
                            <div>
                                <strong style="font-size:0.85rem;color:#dee4ea;">${data.owner.username}</strong>
                                <span style="font-size:0.75rem;color:#8c9bab;margin-left:6px;">(Owner)</span>
                            </div>
                        </div>
                    </div>
                `;
                if (data.members && data.members.length > 0) {
                    html += data.members.map(m => `
                        <div style="display:flex;align-items:center;justify-content:space-between;padding:8px 12px;background:#22272b;border-radius:4px;">
                            <div style="display:flex;align-items:center;gap:10px;">
                                <div style="width:28px;height:28px;border-radius:50%;background:#d97706;color:#fff;display:flex;align-items:center;justify-content:center;font-size:0.75rem;font-weight:700;">
                                    ${m.initials}
                                </div>
                                <div>
                                    <strong style="font-size:0.85rem;color:#dee4ea;">${m.username}</strong>
                                    <span style="font-size:0.75rem;color:#579dff;margin-left:6px;">(Collaborator)</span>
                                </div>
                            </div>
                            ${data.is_owner ? `
                                <button type="button" onclick="removeProjectMember(${m.id})" style="background:transparent;border:none;color:#f87171;font-size:0.8rem;cursor:pointer;">
                                    <i class="fas fa-user-minus"></i>
                                </button>
                            ` : ''}
                        </div>
                    `).join('');
                }
                list.innerHTML = html;
            }

            modal.style.display = 'flex';
        }
    })
    .catch(err => console.error('Error fetching project share info:', err));
};

window.closeShareProjectModal = function() {
    const modal = document.getElementById('share-project-modal');
    if (modal) modal.style.display = 'none';
};

window.copyShareProjectLink = function() {
    const input = document.getElementById('share-project-link-input');
    if (input) {
        navigator.clipboard.writeText(input.value).then(() => {
            if (window.showToast) window.showToast('📋 Project invite link copied to clipboard!', 'success');
        });
    }
};

window.addProjectMember = function() {
    const input = document.getElementById('share-project-username-input');
    if (!input || !input.value.trim() || !currentShareProjectId) return;
    const username = input.value.trim();
    const csrfToken = getCsrfToken() || document.querySelector('[name=csrfmiddlewaretoken]')?.value;

    fetch(`/project/${currentShareProjectId}/share/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ action: 'add_member', username: username })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            input.value = '';
            if (window.showToast) window.showToast(data.message, 'success');
            openShareProjectModal(currentShareProjectId);
        } else {
            if (window.showToast) window.showToast(data.message || 'Could not add member', 'error');
        }
    })
    .catch(err => console.error('Error adding member:', err));
};

window.removeProjectMember = function(memberId) {
    if (!memberId || !currentShareProjectId) return;
    if (!confirm('Remove this collaborator from the board?')) return;
    const csrfToken = getCsrfToken() || document.querySelector('[name=csrfmiddlewaretoken]')?.value;

    fetch(`/project/${currentShareProjectId}/share/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ action: 'remove_member', member_id: memberId })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            if (window.showToast) window.showToast(data.message, 'info');
            openShareProjectModal(currentShareProjectId);
        }
    })
    .catch(err => console.error('Error removing member:', err));
};

function updateTrelloStatusBadge(status) {
    const badge = document.getElementById('trello-label-badge');
    if (!badge) return;
    const map = {
        'completed': { text: 'done', bg: '#216e4e' },
        'in-progress': { text: 'in progress', bg: '#0c66e4' },
        'backlog': { text: 'backlog', bg: '#596773' },
        'not-started': { text: 'to do', bg: '#ae2e24' },
        'on-hold': { text: 'on hold', bg: '#974f0c' },
        'canceled': { text: 'canceled', bg: '#454f59' }
    };
    const item = map[status] || { text: status, bg: '#216e4e' };
    badge.textContent = item.text;
    badge.style.background = item.bg;
}

function updateTrelloCompleteIcon(isComplete) {
    const icon = document.getElementById('trello-circle-icon');
    const titleInput = document.getElementById('trello-task-title-input');
    if (icon) {
        if (isComplete) {
            icon.className = 'fas fa-check-circle';
            icon.style.color = '#216e4e';
        } else {
            icon.className = 'far fa-circle';
            icon.style.color = '#8c9bab';
        }
    }
    if (titleInput) {
        titleInput.style.textDecoration = isComplete ? 'line-through' : 'none';
        titleInput.style.color = isComplete ? '#8c9bab' : '#dee4ea';
    }
}

window.openEditTaskModal = window.openTrelloModal;

window.closeTrelloModal = function() {
    const modal = document.getElementById('trello-task-modal');
    if (modal) modal.style.display = 'none';
};

window.toggleTrelloComplete = function() {
    if (!currentTrelloTask) return;
    const newStatus = (currentTrelloTask.status === 'completed') ? 'not-started' : 'completed';
    saveTrelloTaskField('status', newStatus);
    const statusSelect = document.getElementById('trello-status-select');
    if (statusSelect) statusSelect.value = newStatus;
    updateTrelloCompleteIcon(newStatus === 'completed');
    updateTrelloStatusBadge(newStatus);
};

window.focusTrelloChecklist = function() {
    const checklistSec = document.getElementById('trello-checklist-section');
    if (checklistSec) checklistSec.style.display = 'block';
    const input = document.getElementById('trello-new-item-input');
    if (input) {
        input.scrollIntoView({ behavior: 'smooth', block: 'center' });
        input.focus();
    }
};

window.triggerTrelloAttachment = function() {
    const input = document.getElementById('trello-file-input');
    if (input) input.click();
};

window.uploadTrelloFiles = function(files) {
    if (!files || files.length === 0 || !currentTrelloTask) return;
    const csrfToken = getCsrfToken() || document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
    }

    if (window.showToast) window.showToast('Uploading attachment...', 'info', 1000);

    fetch(`/task/${currentTrelloTask.id}/attachment/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: formData
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            currentTrelloTask.attachments = data.attachments;
            renderTrelloAttachments(data.attachments);
            if (window.showToast) window.showToast(data.message || 'Uploaded!', 'success', 1500);
            const fileInput = document.getElementById('trello-file-input');
            if (fileInput) fileInput.value = '';
        } else {
            if (window.showToast) window.showToast(data.error || 'Upload failed', 'error');
        }
    })
    .catch(err => {
        console.error('Error uploading attachment:', err);
        if (window.showToast) window.showToast('Upload failed', 'error');
    });
};

window.uploadTrelloPastedImage = function(imageData, filename = 'pasted_image.png') {
    if (!imageData || !currentTrelloTask) return;
    const csrfToken = getCsrfToken() || document.querySelector('[name=csrfmiddlewaretoken]')?.value;

    if (window.showToast) window.showToast('Uploading pasted image...', 'info', 1000);

    fetch(`/task/${currentTrelloTask.id}/attachment/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ image_data: imageData, filename: filename })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            currentTrelloTask.attachments = data.attachments;
            renderTrelloAttachments(data.attachments);
            if (window.showToast) window.showToast('Image uploaded to attachments!', 'success', 1500);
        } else {
            if (window.showToast) window.showToast(data.error || 'Upload failed', 'error');
        }
    })
    .catch(err => {
        console.error('Error uploading pasted image:', err);
        if (window.showToast) window.showToast('Upload failed', 'error');
    });
};

window.deleteTrelloAttachment = function(attachmentId) {
    if (!attachmentId || !currentTrelloTask) return;
    const csrfToken = getCsrfToken() || document.querySelector('[name=csrfmiddlewaretoken]')?.value;

    fetch(`/task/attachment/${attachmentId}/delete/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            currentTrelloTask.attachments = data.attachments;
            renderTrelloAttachments(data.attachments);
            if (window.showToast) window.showToast('Attachment deleted', 'info', 1200);
        }
    })
    .catch(err => console.error('Error deleting attachment:', err));
};

window.renderTrelloAttachments = function(attachments = []) {
    const section = document.getElementById('trello-attachments-section');
    const list = document.getElementById('trello-attachments-list');
    if (!section || !list) return;

    if (!attachments || attachments.length === 0) {
        section.style.display = 'none';
        list.innerHTML = '';
        return;
    }

    section.style.display = 'flex';
    list.innerHTML = attachments.map(att => {
        const isImg = att.is_image;
        const iconClass = att.filename.endsWith('.pdf') ? 'fas fa-file-pdf' :
                          (att.filename.match(/\.(doc|docx)$/i) ? 'fas fa-file-word' :
                          (att.filename.match(/\.(xls|xlsx|csv)$/i) ? 'fas fa-file-excel' : 'fas fa-file-alt'));
        const iconColor = att.filename.endsWith('.pdf') ? '#ef4444' :
                          (att.filename.match(/\.(doc|docx)$/i) ? '#3b82f6' :
                          (att.filename.match(/\.(xls|xlsx|csv)$/i) ? '#10b981' : '#579dff'));

        return `
            <div class="attachment-card-item" style="display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 8px 12px; background: #16181d; border: 1px solid #22272b; border-radius: 6px; transition: border-color 0.15s ease;">
                <div style="display: flex; align-items: center; gap: 10px; min-width: 0; flex: 1;">
                    ${isImg ? `
                        <a href="${att.file_url}" target="_blank" title="View full image" style="flex-shrink: 0; display: block;">
                            <img src="${att.file_url}" alt="${escapeHtml(att.filename)}" style="width: 42px; height: 42px; object-fit: cover; border-radius: 4px; border: 1px solid #2e353b;">
                        </a>
                    ` : `
                        <div style="width: 42px; height: 42px; border-radius: 4px; background: #22272b; border: 1px solid #2e353b; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                            <i class="${iconClass}" style="color: ${iconColor}; font-size: 1.25rem;"></i>
                        </div>
                    `}
                    <div style="min-width: 0; flex: 1; line-height: 1.3;">
                        <a href="${att.file_url}" target="_blank" download="${escapeHtml(att.filename)}" style="color: #dee4ea; font-size: 0.85rem; font-weight: 600; text-decoration: none; display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" onmouseenter="this.style.color='#579dff'" onmouseleave="this.style.color='#dee4ea'">
                            ${escapeHtml(att.filename)}
                        </a>
                        <div style="font-size: 0.725rem; color: #8c9bab; margin-top: 2px;">
                            <span>${att.file_size_display || ''}</span>
                            <span style="color: #3b444c; margin: 0 4px;">•</span>
                            <span>Added ${att.created_at || 'Just now'}</span>
                        </div>
                    </div>
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <a href="${att.file_url}" target="_blank" download="${escapeHtml(att.filename)}" title="Download" style="color: #8c9bab; font-size: 0.8rem; padding: 4px; transition: color 0.15s ease;" onmouseenter="this.style.color='#579dff'" onmouseleave="this.style.color='#8c9bab'">
                        <i class="fas fa-download"></i>
                    </a>
                    <button type="button" onclick="deleteTrelloAttachment(${att.id})" title="Delete attachment" style="background: transparent; border: none; color: #8c9bab; font-size: 0.8rem; cursor: pointer; padding: 4px; transition: color 0.15s ease;" onmouseenter="this.style.color='#ef4444'" onmouseleave="this.style.color='#8c9bab'">
                        <i class="fas fa-trash-alt"></i>
                    </button>
                </div>
            </div>
        `;
    }).join('');
};

function handlePasteAttachment(e) {
    if (!e.clipboardData || !currentTrelloTask) return;
    const items = e.clipboardData.items;
    if (!items) return;

    for (let i = 0; i < items.length; i++) {
        const item = items[i];
        if (item.kind === 'file') {
            const file = item.getAsFile();
            if (file) {
                e.preventDefault();
                if (file.type.startsWith('image/')) {
                    const reader = new FileReader();
                    reader.onload = function(evt) {
                        window.uploadTrelloPastedImage(evt.target.result, file.name || `pasted_image_${Date.now()}.png`);
                    };
                    reader.readAsDataURL(file);
                } else {
                    window.uploadTrelloFiles([file]);
                }
                return;
            }
        }
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const descInput = document.getElementById('trello-description-input');
    const commentInput = document.getElementById('trello-comment-input');
    if (descInput) descInput.addEventListener('paste', handlePasteAttachment);
    if (commentInput) commentInput.addEventListener('paste', handlePasteAttachment);
});

window.toggleTrelloExpand = function() {
    const modalContent = document.querySelector('.trello-modal-content');
    const icon = document.querySelector('[onclick="toggleTrelloExpand()"] i');
    if (modalContent) {
        modalContent.classList.toggle('trello-modal-fullscreen');
        const isFull = modalContent.classList.contains('trello-modal-fullscreen');
        if (icon) {
            icon.className = isFull ? 'fas fa-compress-alt' : 'fas fa-expand-alt';
        }
        if (window.showToast) window.showToast(isFull ? 'Expanded to full width' : 'Restored standard width', 'info', 1000);
    }
};

window.openTrelloDescEdit = function() {
    const display = document.getElementById('trello-desc-display');
    const editWrapper = document.getElementById('trello-desc-edit-wrapper');
    const textarea = document.getElementById('trello-description-input');

    if (display) display.style.display = 'none';
    if (editWrapper) editWrapper.style.display = 'flex';
    if (textarea) {
        const val = currentTrelloTask?.description || (display?.textContent !== 'Add a more detailed description...' ? display?.textContent.trim() : '') || '';
        textarea.value = val;
        textarea.focus();
    }
};

window.closeTrelloDescEdit = function() {
    const display = document.getElementById('trello-desc-display');
    const editWrapper = document.getElementById('trello-desc-edit-wrapper');

    if (editWrapper) editWrapper.style.display = 'none';
    if (display) display.style.display = 'block';
};

window.saveTrelloDesc = function() {
    const textarea = document.getElementById('trello-description-input');
    const display = document.getElementById('trello-desc-display');
    const text = textarea ? textarea.value.trim() : '';

    if (display) {
        if (text) {
            display.textContent = text;
            display.style.color = '#dee4ea';
        } else {
            display.textContent = 'Add a more detailed description...';
            display.style.color = '#8c9bab';
        }
    }
    saveTrelloTaskField('description', text);
    closeTrelloDescEdit();
};

window.cycleTrelloStatus = function() {
    const statuses = ['in-progress', 'completed', 'not-started', 'backlog', 'on-hold', 'canceled'];
    const current = currentTrelloTask?.status || 'not-started';
    const nextIdx = (statuses.indexOf(current) + 1) % statuses.length;
    const nextStatus = statuses[nextIdx];

    const select = document.getElementById('trello-status-select');
    if (select) select.value = nextStatus;
    saveTrelloTaskField('status', nextStatus);
    updateTrelloStatusBadge(nextStatus);
    updateTrelloCompleteIcon(nextStatus === 'completed');
};

window.openTrelloDatePicker = function() {
    const input = document.getElementById('trello-due-date-input');
    if (input) {
        if (input.showPicker) {
            input.showPicker();
        } else {
            input.focus();
        }
    }
};

window.updateTrelloDueDateText = function(dateStr) {
    const textEl = document.getElementById('trello-due-date-text');
    const datesContainer = document.getElementById('trello-dates-container');
    if (!dateStr) {
        if (datesContainer) datesContainer.style.display = 'none';
        return;
    }
    if (datesContainer) datesContainer.style.display = 'block';
    if (textEl) {
        const d = new Date(dateStr);
        const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
        textEl.textContent = `${months[d.getMonth()]} ${d.getDate()}`;
    }
};

window.saveTrelloTaskField = function(field, value) {
    const csrfToken = getCsrfToken() || document.querySelector('[name=csrfmiddlewaretoken]')?.value;

    if (!currentTrelloTask) {
        const title = document.getElementById('trello-task-title-input')?.value.trim() || 'New Card';
        const payload = {
            title: title,
            status: document.getElementById('trello-status-select')?.value || 'not-started',
            priority: 'moderate',
            category: document.getElementById('trello-project-select')?.value || '',
            [field]: value
        };
        fetch('/task/create/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify(payload)
        })
        .then(r => r.json())
        .then(data => {
            if (data.success && data.task) {
                currentTrelloTask = data.task;
                insertTaskCardToKanban(data.task);
                if (window.showToast) window.showToast('Card created!', 'success', 1200);
            }
        })
        .catch(err => console.error('Error creating card:', err));
        return;
    }

    const payload = { [field]: value };
    const taskId = currentTrelloTask.id;

    fetch(`/task/${taskId}/update/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify(payload)
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            currentTrelloTask[field] = value;
            
            // Instant DOM updates for the Kanban card
            const card = document.querySelector(`.kanban-card[data-task-id="${taskId}"]`);
            if (card) {
                if (field === 'title') {
                    const titleEl = card.querySelector('.kanban-card-title');
                    if (titleEl) titleEl.textContent = value;
                } else if (field === 'priority') {
                    const prioTag = card.querySelector('.priority-tag');
                    if (prioTag) {
                        prioTag.className = `priority-tag prio-${value}`;
                        prioTag.textContent = value.charAt(0).toUpperCase() + value.slice(1);
                    }
                } else if (field === 'status') {
                    updateTrelloStatusBadge(value);
                    updateTrelloCompleteIcon(value === 'completed');
                    
                    // Move card dynamically to the new status column
                    const targetContainer = document.querySelector(`.kanban-cards-container[data-status="${value}"]`);
                    const oldContainer = card.closest('.kanban-cards-container');
                    if (targetContainer && oldContainer !== targetContainer) {
                        if (value === 'completed') {
                            card.classList.add('is-completed');
                        } else {
                            card.classList.remove('is-completed');
                        }
                        targetContainer.appendChild(card);

                        const oldStatus = oldContainer.getAttribute('data-status');
                        if (oldContainer.querySelectorAll('.kanban-card').length === 0) {
                            const oldEmpty = document.getElementById(`empty-${oldStatus}`);
                            if (oldEmpty) oldEmpty.style.display = 'flex';
                        }
                        const newEmpty = document.getElementById(`empty-${value}`);
                        if (newEmpty) newEmpty.style.display = 'none';

                        if (window.updateKanbanColumnCounts) updateKanbanColumnCounts();
                    }
                }
            }
            if (window.showToast) window.showToast('Saved', 'info', 1000);
        }
    })
    .catch(err => console.error('Error saving task field:', err));
};

window.saveTrelloChecklistTitle = function(title) {
    if (!currentTrelloTask) return;
    const cleanTitle = (title || '').trim() || 'Checklist';
    currentTrelloTask.checklist_title = cleanTitle;
    saveTrelloTaskField('checklist_title', cleanTitle);
};

window.deleteTrelloWholeChecklist = function() {
    if (!currentTrelloTask) return;
    currentTrelloTask.checklist = [];
    saveTrelloTaskField('checklist', []);
    const checklistSec = document.getElementById('trello-checklist-section');
    if (checklistSec) checklistSec.style.display = 'none';
    if (window.showToast) window.showToast('Checklist deleted', 'info', 1200);
};

function renderTrelloChecklist(items) {
    const container = document.getElementById('trello-checklist-items');
    if (!container) return;

    const total = items.length;
    const completed = items.filter(i => i.completed).length;
    const pct = total > 0 ? Math.round((completed / total) * 100) : 0;

    const pctBadge = document.getElementById('trello-checklist-pct-badge');
    const fillBar = document.getElementById('trello-checklist-progress-fill');
    if (pctBadge) pctBadge.textContent = `${pct}%`;
    if (fillBar) fillBar.style.width = `${pct}%`;

    container.innerHTML = items.map((item, idx) => `
        <div class="checklist-item-row" id="chk-item-${item.id || idx}" style="display: flex; align-items: center; justify-content: space-between; gap: 10px; padding: 7px 10px; background: #16181d; border: 1px solid #24292e; border-radius: 5px; transition: all 0.15s ease;">
            <label style="display: flex; align-items: center; gap: 10px; flex: 1; cursor: pointer; margin: 0; min-width: 0;">
                <input type="checkbox" ${item.completed ? 'checked' : ''} onchange="toggleTrelloChecklistItem('${item.id || idx}', this.checked)" style="width: 16px; height: 16px; min-width: 16px; cursor: pointer; accent-color: #579dff; margin: 0;">
                <span id="chk-text-${item.id || idx}" style="font-size: 0.85rem; color: ${item.completed ? '#8c9bab' : '#dee4ea'}; text-decoration: ${item.completed ? 'line-through' : 'none'}; word-break: break-word; line-height: 1.4;">${escapeHtml(item.text)}</span>
            </label>
            <button type="button" onclick="deleteTrelloChecklistItem('${item.id || idx}')" title="Delete item" style="background: transparent; border: none; color: #8c9bab; cursor: pointer; padding: 2px 5px; font-size: 0.775rem; border-radius: 3px; transition: color 0.15s ease;" onmouseenter="this.style.color='#ef4444'" onmouseleave="this.style.color='#8c9bab'">
                <i class="fas fa-trash-alt"></i>
            </button>
        </div>
    `).join('');
}

window.addTrelloChecklistItem = function() {
    const input = document.getElementById('trello-new-item-input');
    if (!input) return;
    const text = input.value.trim();
    if (!text || !currentTrelloTask) return;

    if (!currentTrelloTask.checklist) currentTrelloTask.checklist = [];
    currentTrelloTask.checklist.push({
        id: 'chk_' + Date.now(),
        text: text,
        completed: false
    });

    input.value = '';
    renderTrelloChecklist(currentTrelloTask.checklist);
    saveTrelloTaskField('checklist', currentTrelloTask.checklist);
};

window.toggleTrelloChecklistItem = function(itemId, isCompleted) {
    if (!currentTrelloTask || !currentTrelloTask.checklist) return;
    currentTrelloTask.checklist = currentTrelloTask.checklist.map((item, idx) => {
        if (item.id === itemId || String(idx) === String(itemId)) {
            return { ...item, completed: isCompleted };
        }
        return item;
    });
    renderTrelloChecklist(currentTrelloTask.checklist);
    saveTrelloTaskField('checklist', currentTrelloTask.checklist);
};

window.deleteTrelloChecklistItem = function(itemId) {
    if (!currentTrelloTask || !currentTrelloTask.checklist) return;
    currentTrelloTask.checklist = currentTrelloTask.checklist.filter((item, idx) => {
        return !(item.id === itemId || String(idx) === String(itemId));
    });
    renderTrelloChecklist(currentTrelloTask.checklist);
    saveTrelloTaskField('checklist', currentTrelloTask.checklist);
};

function escapeHtml(text) {
    if (!text) return '';
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return String(text).replace(/[&<>"']/g, m => map[m]);
}

function renderTrelloComments(comments = [], task = null) {
    const container = document.getElementById('trello-comments-stream');

    const t = task || currentTrelloTask;
    const author = (t && t.user) ? t.user : 'You';
    const initials = author.slice(0, 2).toUpperCase();
    const avatarBg = initials === 'AC' ? '#d97706' : (initials === 'PA' ? '#7c3aed' : '#0c66e4');
    const listName = (t && (t.category_name || t.status_display)) ? (t.category_name || t.status_display) : 'General';
    const timeText = (t && t.created_at) ? t.created_at : 'Just now';

    // Update Full-Width Fixed Bottom Footer Bar (never scrolls with chat/comments)
    const bAvatar = document.getElementById('trello-bottom-avatar');
    const bAuthor = document.getElementById('trello-bottom-author');
    const bList = document.getElementById('trello-bottom-list');
    const bTime = document.getElementById('trello-bottom-time');

    if (bAvatar) {
        bAvatar.textContent = initials;
        bAvatar.style.background = avatarBg;
    }
    if (bAuthor) bAuthor.textContent = author;
    if (bList) bList.textContent = listName;
    if (bTime) bTime.textContent = timeText;

    if (!container) return;

    let html = '';

    // Render Comments only in the scrollable stream
    if (comments && comments.length > 0) {
        html += '<div style="display: flex; flex-direction: column; gap: 6px; flex: 1; overflow-y: auto;">';
        html += comments.map(c => {
            const cUser = c.user || 'User';
            const cInitials = cUser.slice(0, 2).toUpperCase();
            const cBg = cInitials === 'AC' ? '#d97706' : (cInitials === 'PA' ? '#7c3aed' : '#0c66e4');
            const cTime = c.time_ago || c.created_at || 'Just now';

            return `
                <div class="comment-item-row" id="comment-row-${c.id}" style="display: flex; flex-direction: column; gap: 4px; background: #16181d; border: 1px solid #22272b; border-radius: 6px; padding: 8px 10px;">
                    <!-- Highlighted Comment Body -->
                    <div id="comment-bubble-${c.id}" style="color: #ffffff; font-size: 0.875rem; font-weight: 500; line-height: 1.4; word-break: break-word; white-space: pre-wrap;">${escapeHtml(c.content)}</div>
                    
                    <!-- Bottom Row: Actions on Left, Avatar + User + Time on Right -->
                    <div id="comment-footer-${c.id}" style="display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-top: 1px; padding-top: 4px; border-top: 1px solid #1f2328; font-size: 0.7rem;">
                        <!-- Left: Actions -->
                        <div id="comment-actions-${c.id}" style="display: flex; align-items: center; gap: 5px; color: #8c9bab;">
                            <span style="cursor: pointer; color: #8c9bab; font-size: 0.7rem; transition: color 0.15s ease;" onmouseenter="this.style.color='#579dff'" onmouseleave="this.style.color='#8c9bab'" onclick="replyToTrelloComment('${cUser}')">Reply</span>
                            <span style="color: #2e353b; font-size: 0.6rem;">•</span>
                            <span style="cursor: pointer; color: #8c9bab; font-size: 0.7rem; transition: color 0.15s ease;" onmouseenter="this.style.color='#579dff'" onmouseleave="this.style.color='#8c9bab'" onclick="editTrelloCommentInline(${c.id})">Edit</span>
                            ${c.id ? `
                            <span style="color: #2e353b; font-size: 0.6rem;">•</span>
                            <span style="cursor: pointer; color: #ef4444; font-size: 0.7rem; transition: opacity 0.15s ease;" onmouseenter="this.style.opacity='0.8'" onmouseleave="this.style.opacity='1'" onclick="deleteTrelloComment(${c.id})">Delete</span>` : ''}
                        </div>

                        <!-- Right: Profile Avatar BEFORE Username & Time -->
                        <div style="display: flex; align-items: center; gap: 5px;">
                            <div style="width: 18px; height: 18px; min-width: 18px; min-height: 18px; max-width: 18px; max-height: 18px; border-radius: 4px; background: ${cBg}; color: #ffffff; display: flex; align-items: center; justify-content: center; font-size: 0.6rem; font-weight: 700; flex-shrink: 0; box-sizing: border-box;">
                                ${cInitials}
                            </div>
                            <div style="display: flex; align-items: center; gap: 4px;">
                                <strong style="color: #9fadbc; font-size: 0.7rem; font-weight: 600;">${cUser}</strong>
                                <span style="color: #6b7785; font-size: 0.675rem;">${cTime}</span>
                                ${c.is_edited ? '<span style="color: #579dff; font-size: 0.625rem; font-style: italic; margin-left: 2px;">(edited)</span>' : ''}
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
        html += '</div>';
    }

    container.innerHTML = html;
}

window.replyToTrelloComment = function(username) {
    const input = document.getElementById('trello-comment-input');
    if (input) {
        input.value = `@${username} `;
        input.focus();
    }
};

window.editTrelloCommentInline = function(commentId) {
    if (!commentId || !currentTrelloTask || !currentTrelloTask.comments) return;
    const comment = currentTrelloTask.comments.find(c => c.id === commentId);
    if (!comment) return;

    const bubble = document.getElementById(`comment-bubble-${commentId}`);
    const footer = document.getElementById(`comment-footer-${commentId}`);
    if (!bubble) return;

    if (footer) footer.style.display = 'none';

    bubble.innerHTML = `
        <div style="display: flex; flex-direction: column; gap: 6px; width: 100%;">
            <textarea id="edit-comment-input-${commentId}" 
                      rows="2"
                      style="width: 100%; background: #121417; border: 1px solid #579dff; border-radius: 4px; color: #dee4ea; font-size: 0.85rem; padding: 6px 8px; resize: vertical; min-height: 42px; box-sizing: border-box; outline: none; font-family: inherit; line-height: 1.4;"
                      onkeydown="if(event.key === 'Enter' && !event.shiftKey){ event.preventDefault(); saveEditedTrelloComment(${commentId}); }">${escapeHtml(comment.content)}</textarea>
            <div style="display: flex; align-items: center; gap: 6px;">
                <button type="button" onclick="saveEditedTrelloComment(${commentId})" style="background: #579dff; color: #000000; font-size: 0.725rem; font-weight: 700; border: none; border-radius: 4px; padding: 3px 10px; cursor: pointer; transition: opacity 0.15s ease;" onmouseenter="this.style.opacity='0.9'" onmouseleave="this.style.opacity='1'">Save</button>
                <button type="button" onclick="cancelEditTrelloComment(${commentId})" style="background: transparent; color: #8c9bab; font-size: 0.725rem; border: none; border-radius: 4px; padding: 3px 6px; cursor: pointer;" onmouseenter="this.style.color='#dee4ea'" onmouseleave="this.style.color='#8c9bab'">Cancel</button>
            </div>
        </div>
    `;
    const textarea = document.getElementById(`edit-comment-input-${commentId}`);
    if (textarea) {
        textarea.focus();
        textarea.setSelectionRange(textarea.value.length, textarea.value.length);
    }
};

window.saveEditedTrelloComment = function(commentId) {
    const textarea = document.getElementById(`edit-comment-input-${commentId}`);
    if (!textarea) return;
    const content = textarea.value.trim();
    if (!content) return;

    const csrfToken = getCsrfToken() || document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    fetch(`/task/comment/${commentId}/edit/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ content: content })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            const comment = currentTrelloTask.comments.find(c => c.id === commentId);
            if (comment) {
                comment.content = content;
                comment.is_edited = true;
            }
            renderTrelloComments(currentTrelloTask.comments);
            if (window.showToast) window.showToast('Comment updated', 'success', 1000);
        }
    })
    .catch(err => console.error('Error updating comment:', err));
};

window.cancelEditTrelloComment = function(commentId) {
    renderTrelloComments(currentTrelloTask.comments);
};

window.deleteTrelloComment = function(commentId) {
    if (!commentId || !currentTrelloTask) return;

    const csrfToken = getCsrfToken() || document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    fetch(`/task/comment/${commentId}/delete/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            if (currentTrelloTask.comments) {
                currentTrelloTask.comments = currentTrelloTask.comments.filter(c => c.id !== commentId);
                renderTrelloComments(currentTrelloTask.comments);
            }
            if (window.showToast) window.showToast('Comment deleted', 'info', 1000);
        }
    })
    .catch(err => console.error('Error deleting comment:', err));
};

window.submitTrelloComment = function() {
    const textarea = document.getElementById('trello-comment-input');
    if (!textarea) return;
    const content = textarea.value.trim();
    if (!content) return;

    const csrfToken = getCsrfToken() || document.querySelector('[name=csrfmiddlewaretoken]')?.value;

    const doSubmit = (taskId) => {
        fetch(`/task/${taskId}/comment/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ content: content })
        })
        .then(r => r.json())
        .then(data => {
            if (data.success && data.comment) {
                textarea.value = '';
                const saveBtn = document.getElementById('trello-comment-save-btn');
                if (saveBtn) saveBtn.style.display = 'none';
                if (!currentTrelloTask.comments) currentTrelloTask.comments = [];
                currentTrelloTask.comments.unshift(data.comment);
                renderTrelloComments(currentTrelloTask.comments);
                if (window.showToast) window.showToast('Comment posted!', 'success', 1200);
            }
        })
        .catch(err => console.error('Error posting comment:', err));
    };

    if (!currentTrelloTask) {
        const title = document.getElementById('trello-task-title-input')?.value.trim() || 'New Card';
        const payload = {
            title: title,
            status: document.getElementById('trello-status-select')?.value || 'not-started',
            priority: 'moderate',
            category: document.getElementById('trello-project-select')?.value || ''
        };
        fetch('/task/create/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify(payload)
        })
        .then(r => r.json())
        .then(data => {
            if (data.success && data.task) {
                currentTrelloTask = data.task;
                doSubmit(data.task.id);
            }
        })
        .catch(err => console.error('Error creating card for comment:', err));
        return;
    }

    doSubmit(currentTrelloTask.id);
};

    window.copyTrelloTitle = function() {
        const titleInput = document.getElementById('trello-task-title-input');
        const title = titleInput ? titleInput.value : '';
        if (navigator.clipboard && title) {
            navigator.clipboard.writeText(title).then(() => {
                if (window.showToast) window.showToast('Task title copied to clipboard!', 'info');
            });
        }
    };

    window.copyTrelloDescription = function() {
        const descInput = document.getElementById('trello-description-input');
        const desc = descInput ? descInput.value : '';
        if (navigator.clipboard && desc) {
            navigator.clipboard.writeText(desc).then(() => {
                if (window.showToast) window.showToast('Description copied to clipboard!', 'info');
            });
        }
    };

    window.copyTrelloFullSummary = function() {
        if (!currentTrelloTask) return;
        const title = document.getElementById('trello-task-title-input')?.value || '';
        const desc = document.getElementById('trello-description-input')?.value || '';
        const status = document.getElementById('trello-status-select')?.value || '';
        const priority = document.getElementById('trello-priority-select')?.value || '';
        const due = document.getElementById('trello-due-date-input')?.value || '';
        const summary = `📌 Task: ${title}\n📊 Status: ${status}\n🔺 Priority: ${priority}\n📅 Due Date: ${due || 'None'}\n\n📝 Description:\n${desc || 'None'}`;

        if (navigator.clipboard) {
            navigator.clipboard.writeText(summary).then(() => {
                if (window.showToast) window.showToast('Full task summary copied to clipboard!', 'success');
            });
        }
    };

    window.toggleTrelloComplete = function() {
        if (!currentTrelloTask) return;
        const newStatus = currentTrelloTask.status === 'completed' ? 'not-started' : 'completed';
        saveTrelloTaskField('status', newStatus);
        const sel = document.getElementById('trello-status-select');
        if (sel) sel.value = newStatus;
        if (window.showToast) window.showToast(`Task marked as ${newStatus === 'completed' ? 'Done' : 'To Do'}!`, 'success');
    };

    window.deleteTrelloTask = function() {
        if (!currentTrelloTask) return;
        if (!confirm(`Are you sure you want to delete "${currentTrelloTask.title}"?`)) return;

        const taskId = currentTrelloTask.id;
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
            closeTrelloModal();
            if (window.showToast) window.showToast('Task deleted', 'success', 1200);

            // Remove card instantly from Kanban board
            const kanbanCard = document.getElementById(`kanban-card-${taskId}`);
            if (kanbanCard) {
                kanbanCard.style.transition = 'all 0.25s ease';
                kanbanCard.style.opacity = '0';
                kanbanCard.style.transform = 'scale(0.9)';
                setTimeout(() => {
                    const parentCol = kanbanCard.closest('.kanban-cards-container');
                    kanbanCard.remove();
                    if (parentCol) {
                        const remainingCards = parentCol.querySelectorAll('.kanban-card');
                        if (remainingCards.length === 0) {
                            const statusKey = parentCol.getAttribute('data-status');
                            const emptyEl = document.getElementById(`empty-${statusKey}`);
                            if (emptyEl) emptyEl.style.display = 'flex';
                        }
                    }
                    if (window.updateKanbanColumnCounts) updateKanbanColumnCounts();
                }, 250);
            }

            // Remove card from Dashboard if present
            const taskCard = document.getElementById(`task-card-${taskId}`);
            if (taskCard) {
                taskCard.style.transition = 'all 0.25s ease';
                taskCard.style.opacity = '0';
                setTimeout(() => taskCard.remove(), 250);
            }
        })
        .catch(() => {
            closeTrelloModal();
        });
    };

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
 *  TASKFLIXX AI SIDE DRAWER
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
    let cookieValue = '';
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
    if (!cookieValue) {
        const input = document.querySelector('[name=csrfmiddlewaretoken]');
        if (input && input.value) cookieValue = input.value;
    }
    if (!cookieValue) {
        const meta = document.querySelector('meta[name="csrf-token"]');
        if (meta && meta.content) cookieValue = meta.content;
    }
    return cookieValue || '';
}
window.getCsrfToken = getCsrfToken;

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

    // Cool color palette spectrum (RGB stops):
    const coolPalette = [
        [20, 184, 166],   // Aquamarine Teal (#14b8a6)
        [6, 182, 212],    // Electric Cyan (#06b6d4)
        [56, 189, 248],   // Neon Sky Blue (#38bdf8)
        [37, 99, 235],    // Deep Sapphire (#2563eb)
        [99, 102, 241],   // Vivid Indigo (#6366f1)
        [139, 92, 246]    // Cool Violet (#8b5cf6)
    ];

    function getCoolGradientColor(phase, brightness) {
        const p = ((phase % 1) + 1) % 1;
        const idx = p * (coolPalette.length - 1);
        const i1 = Math.floor(idx);
        const i2 = Math.min(coolPalette.length - 1, i1 + 1);
        const frac = idx - i1;

        const c1 = coolPalette[i1];
        const c2 = coolPalette[i2];

        let r = Math.round(c1[0] + (c2[0] - c1[0]) * frac);
        let g = Math.round(c1[1] + (c2[1] - c1[1]) * frac);
        let b = Math.round(c1[2] + (c2[2] - c1[2]) * frac);

        if (brightness > 0.5) {
            const boost = (brightness - 0.5) * 50;
            r = Math.min(255, Math.round(r + boost * 0.7));
            g = Math.min(255, Math.round(g + boost * 0.9));
            b = Math.min(255, Math.round(b + boost));
        }
        return { r, g, b };
    }

    function render(now) {
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

        // Draw dots with flowing cool-gradient waves across the grid
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
                let mouseGlow = 0;

                // Interactive mouse wave disturbance
                if (mouse.active) {
                    const dx = x0 - mouse.x;
                    const dy = y0 - mouse.y;
                    const dist = Math.sqrt(dx * dx + dy * dy);
                    if (dist < mouse.radius) {
                        const factor = (1 - dist / mouse.radius);
                        elevation += Math.sin(dist * 0.04 - t * 4.5) * factor * 0.6;
                        mouseGlow = factor;
                    }
                }

                // Vertical undulating wave displacement
                const y = y0 + elevation * 6.5;
                const x = x0 + Math.cos(y0 * 0.003 + t * 0.6) * 1.5;

                // Radius & Elevation normalization
                const normElev = Math.max(0, Math.min(1, (elevation + 1) * 0.5)); // 0.0 to 1.0
                const radius = 1.0 + normElev * 1.5 + mouseGlow * 0.8;

                // Dynamic cool gradient color calculation based on spatial flow and phase
                const colorPhase = (x0 * 0.0006 + y0 * 0.0004 + t * 0.07 + normElev * 0.2);
                const rgb = getCoolGradientColor(colorPhase, normElev);

                // Alpha glow: dimmer in troughs, vibrant radiant cool glow on wave crests
                const alpha = Math.min(0.75, 0.14 + normElev * 0.48 + mouseGlow * 0.25);

                ctx.beginPath();
                ctx.arc(x, y, radius, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${alpha.toFixed(3)})`;
                ctx.fill();
            }
        }

        animationFrameId = requestAnimationFrame(render);
    }

    animationFrameId = requestAnimationFrame(render);
}

// ==============================================================================
//  MULTI-USER LIVE COLLABORATION & CARD SYNC ENGINE
// ==============================================================================

window.toggleUserSwitcherMenu = function(e) {
    if (e) e.stopPropagation();
    const menu = document.getElementById('user-switcher-menu');
    if (menu) menu.style.display = menu.style.display === 'block' ? 'none' : 'block';
};

window.switchCollaboratorUser = function(username) {
    const csrfToken = getCsrfToken() || document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    fetch('/api/auth/switch-user/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ username: username })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            if (window.showToast) window.showToast(`Switched account to ${username}!`, 'success', 1000);
            setTimeout(() => { window.location.reload(); }, 350);
        }
    })
    .catch(err => console.error('Error switching user:', err));
};

document.addEventListener('click', function(e) {
    if (!e.target.closest('#user-switcher-btn')) {
        const menu = document.getElementById('user-switcher-menu');
        if (menu) menu.style.display = 'none';
    }
});

// Periodic Multi-User Card Sync Poller (Live Real-Time updates when viewing cards)
let trelloLiveSyncTimer = null;

function startTrelloLiveSync() {
    if (trelloLiveSyncTimer) clearInterval(trelloLiveSyncTimer);
    trelloLiveSyncTimer = setInterval(() => {
        if (!currentTrelloTask) return;
        const modal = document.getElementById('trello-task-modal');
        if (!modal || modal.style.display === 'none') return;
        
        // Skip polling if the current user is actively typing in title, description, or comment
        const activeTag = document.activeElement ? document.activeElement.tagName : '';
        if (activeTag === 'INPUT' || activeTag === 'TEXTAREA') return;

        fetch(`/task/${currentTrelloTask.id}/update/`, {
            method: 'GET',
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(r => r.json())
        .then(data => {
            if (data.success && data.task && currentTrelloTask && data.task.id === currentTrelloTask.id) {
                const oldCommentCount = (currentTrelloTask.comments || []).length;
                const newCommentCount = (data.task.comments || []).length;
                
                // Status sync
                if (data.task.status !== currentTrelloTask.status) {
                    currentTrelloTask.status = data.task.status;
                    const statusSelect = document.getElementById('trello-status-select');
                    if (statusSelect) statusSelect.value = data.task.status;
                    const statusNames = {
                        'not-started': 'To Do', 'in-progress': 'In Progress', 'backlog': 'Backlog',
                        'on-hold': 'On Hold', 'completed': 'Done', 'canceled': 'Canceled'
                    };
                    const statusPillText = document.getElementById('trello-status-pill-text');
                    if (statusPillText) statusPillText.textContent = statusNames[data.task.status] || data.task.status;
                    updateTrelloStatusBadge(data.task.status);
                    updateTrelloCompleteIcon(data.task.status === 'completed');
                }

                // Checklist sync
                if (JSON.stringify(data.task.checklist) !== JSON.stringify(currentTrelloTask.checklist)) {
                    currentTrelloTask.checklist = data.task.checklist;
                    renderTrelloChecklist(data.task.checklist);
                }

                // Description sync
                if (data.task.description !== currentTrelloTask.description) {
                    currentTrelloTask.description = data.task.description;
                    const descDisplay = document.getElementById('trello-desc-display');
                    if (descDisplay && descDisplay.style.display !== 'none') {
                        if (data.task.description && data.task.description.trim()) {
                            descDisplay.textContent = data.task.description;
                            descDisplay.style.color = '#dee4ea';
                        } else {
                            descDisplay.textContent = 'Add a more detailed description...';
                            descDisplay.style.color = '#8c9bab';
                        }
                    }
                }

                // Comments & activity sync
                if (newCommentCount !== oldCommentCount || JSON.stringify(data.task.comments) !== JSON.stringify(currentTrelloTask.comments)) {
                    currentTrelloTask.comments = data.task.comments;
                    renderTrelloComments(data.task.comments, data.task);
                    if (newCommentCount > oldCommentCount && window.showToast) {
                        window.showToast('💬 New activity received from collaborator', 'info', 1500);
                    }
                }
            }
        })
        .catch(err => console.debug('Sync poll check:', err));
    }, 3500);
}

// Start live sync poller on page initialization
startTrelloLiveSync();

