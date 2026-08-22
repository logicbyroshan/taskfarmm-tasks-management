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
// Global expose so onclick="openAddTaskModal()" and "openAddProjectModal()" work from HTML
window.openAddTaskModal = function(initialStatus = 'not-started', initialCategory = '') {
    const trelloModal = document.getElementById('trello-task-modal');
    if (!trelloModal) return;

    currentTrelloTask = null;
    const titleInput = document.getElementById('trello-task-title-input');
    const projText = document.getElementById('trello-project-text');
    const statusSelect = document.getElementById('trello-status-select');
    const prioSelect = document.getElementById('trello-priority-select');
    const projSelect = document.getElementById('trello-project-select');
    const dueInput = document.getElementById('trello-due-date-input');
    const descDisplay = document.getElementById('trello-desc-display');
    const descInput = document.getElementById('trello-description-input');
    const checklistSec = document.getElementById('trello-checklist-section');
    const metadataRow = document.getElementById('trello-metadata-badges-row');

    const statusNames = {
        'not-started': 'To Do',
        'in-progress': 'In Progress',
        'backlog': 'Backlog',
        'on-hold': 'On Hold',
        'completed': 'Done',
        'canceled': 'Canceled'
    };

    const activeProjSelect = document.getElementById('kanban-project-select');
    const currentProjId = initialCategory || (activeProjSelect ? activeProjSelect.value : '');
    const currentProjName = activeProjSelect && activeProjSelect.selectedIndex >= 0 
        ? activeProjSelect.options[activeProjSelect.selectedIndex].text.replace(/^[📁\s]+|\s*\(\d+\)$/g, '').trim()
        : 'General';

    if (titleInput) {
        titleInput.value = '';
        titleInput.placeholder = 'Enter card title...';
    }
    if (projText) projText.textContent = currentProjName || 'General';
    
    const statusPillText = document.getElementById('trello-status-pill-text');
    if (statusPillText) statusPillText.textContent = statusNames[initialStatus] || 'To Do';

    const prioPillText = document.getElementById('trello-priority-pill-text');
    const prioDot = document.getElementById('trello-priority-dot');
    if (prioPillText) prioPillText.textContent = 'Moderate';
    if (prioDot) prioDot.textContent = '🟡';

    if (statusSelect) statusSelect.value = initialStatus || 'not-started';
    if (prioSelect) prioSelect.value = 'moderate';
    if (projSelect) projSelect.value = currentProjId || '';
    if (dueInput) dueInput.value = '';
    if (descDisplay) {
        descDisplay.textContent = 'Add a more detailed description...';
        descDisplay.style.color = '#8c9bab';
    }
    if (descInput) descInput.value = '';
    if (checklistSec) checklistSec.style.display = 'none';
    if (metadataRow) metadataRow.style.display = 'none';

    updateTrelloStatusBadge(initialStatus || 'not-started');
    updateTrelloCompleteIcon(false);

    const stream = document.getElementById('trello-comments-stream');
    if (stream) {
        stream.innerHTML = `
            <div class="activity-log-item" style="display: flex; gap: 10px; align-items: flex-start;">
                <div style="width: 30px; height: 30px; border-radius: 50%; background: #0c66e4; color: #ffffff; display: flex; align-items: center; justify-content: center; font-size: 0.75rem; font-weight: 700; flex-shrink: 0;">
                    PA
                </div>
                <div style="flex: 1; font-size: 0.85rem; line-height: 1.4;">
                    <div>
                        <strong style="color: #dee4ea;">You</strong> 
                        <span style="color: #9fadbc;">are creating this card in</span> 
                        <strong style="color: #dee4ea;">${statusNames[initialStatus] || 'To Do'}</strong>
                    </div>
                    <div style="color: #579dff; font-size: 0.75rem; text-decoration: underline; margin-top: 2px;">
                        just now
                    </div>
                </div>
            </div>
        `;
    }

    trelloModal.style.display = 'flex';
    setTimeout(() => { if (titleInput) titleInput.focus(); }, 80);
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

                if (data.task.checklist && data.task.checklist.length > 0) {
                    if (checklistSec) checklistSec.style.display = 'block';
                    renderTrelloChecklist(data.task.checklist);
                } else {
                    if (checklistSec) checklistSec.style.display = 'none';
                }

                renderTrelloComments(data.task.comments || [], data.task);
                renderTrelloMembers(data.task.assignees || [], data.task);

                modal.style.display = 'flex';
            }
        })
        .catch(err => console.error('Error opening trello modal:', err));
};

window.renderTrelloMembers = function(assignees, task) {
    const chips = document.getElementById('trello-members-chips');
    if (!chips) return;

    const membersList = assignees || [];
    if (membersList.length === 0) {
        const creatorName = (task && task.user) || (currentTrelloTask && currentTrelloTask.user) || 'You';
        const creatorInitials = creatorName.slice(0, 2).toUpperCase();
        chips.innerHTML = `
            <div title="Created by ${creatorName} (Click to assign)" style="width: 28px; height: 28px; border-radius: 50%; background: #282e33; color: #dee4ea; display: inline-flex; align-items: center; justify-content: center; font-size: 0.725rem; font-weight: 700; border: 2px solid #1d2125; cursor: pointer; transition: transform 0.15s ease;" onclick="toggleTrelloMembersPopup(event)">
                ${creatorInitials}
            </div>
            <button type="button" onclick="toggleTrelloMembersPopup(event)" title="Assign members" style="width: 28px; height: 28px; border-radius: 50%; background: #22272b; color: #579dff; border: 1px dashed #579dff; font-size: 0.8rem; cursor: pointer; display: inline-flex; align-items: center; justify-content: center; transition: all 0.15s ease;">
                <i class="fas fa-plus"></i>
            </button>
        `;
        return;
    }

    const colors = ['#0c66e4', '#d97706', '#216e4e', '#7c3aed'];
    chips.innerHTML = `
        <div style="display: flex; align-items: center;">
            ${membersList.map((a, idx) => `
                <div title="Assigned to ${a.username} (Click to manage)" style="width: 28px; height: 28px; border-radius: 50%; background: ${colors[idx % colors.length]}; color: #ffffff; display: inline-flex; align-items: center; justify-content: center; font-size: 0.725rem; font-weight: 700; border: 2px solid #1d2125; ${idx > 0 ? 'margin-left: -6px;' : ''} box-shadow: 0 2px 5px rgba(0,0,0,0.3); cursor: pointer; transition: transform 0.15s ease;" onclick="toggleTrelloMembersPopup(event)">
                    ${a.initials}
                </div>
            `).join('')}
        </div>
        <button type="button" onclick="toggleTrelloMembersPopup(event)" title="Assign members" style="width: 28px; height: 28px; border-radius: 50%; background: #22272b; color: #579dff; border: 1px dashed #579dff; font-size: 0.8rem; cursor: pointer; display: inline-flex; align-items: center; justify-content: center; transition: all 0.15s ease; margin-left: 3px;">
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
    closeAllTrelloDropdowns();
};

function closeAllTrelloDropdowns() {
    const menus = [
        'trello-project-dropdown-menu',
        'trello-status-dropdown-menu',
        'trello-priority-dropdown-menu'
    ];
    menus.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.style.display = 'none';
    });
}

document.addEventListener('click', function(e) {
    if (!e.target.closest('#trello-project-pill-btn') &&
        !e.target.closest('#trello-status-pill-btn') &&
        !e.target.closest('#trello-priority-pill-btn')) {
        closeAllTrelloDropdowns();
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

window.handleTrelloFileUpload = function(fileInput) {
    if (!fileInput.files || !fileInput.files[0]) return;
    const file = fileInput.files[0];
    if (window.showToast) window.showToast('Attachment attached!', 'success');
};

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
    if (!textEl) return;
    if (!dateStr) {
        textEl.textContent = 'Aug 24';
        return;
    }
    const d = new Date(dateStr);
    const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
    textEl.textContent = `${months[d.getMonth()]} ${d.getDate()}`;
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
                if (window.showToast) window.showToast('Card created!', 'success', 1200);
            }
        })
        .catch(err => console.error('Error creating card:', err));
        return;
    }

    const payload = { [field]: value };

    fetch(`/task/${currentTrelloTask.id}/update/`, {
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
            if (field === 'status') {
                updateTrelloStatusBadge(value);
                updateTrelloCompleteIcon(value === 'completed');
            }
            if (window.showToast) window.showToast('Saved', 'info', 1200);
        }
    })
    .catch(err => console.error('Error saving task field:', err));
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
        <div class="checklist-item-row" style="display:flex;align-items:center;justify-content:space-between;gap:10px;padding:6px 10px;background:#22272b;border:1px solid #282e33;border-radius:4px;">
            <label style="display:flex;align-items:center;gap:10px;flex:1;cursor:pointer;margin:0;">
                <input type="checkbox" ${item.completed ? 'checked' : ''} onchange="toggleTrelloChecklistItem('${item.id || idx}', this.checked)" style="width:15px;height:15px;cursor:pointer;accent-color:#579dff;">
                <span style="font-size:0.825rem;color:${item.completed ? '#8c9bab' : '#dee4ea'};text-decoration:${item.completed ? 'line-through' : 'none'};">${item.text}</span>
            </label>
            <button type="button" onclick="deleteTrelloChecklistItem('${item.id || idx}')" style="background:transparent;border:none;color:#8c9bab;cursor:pointer;padding:2px 6px;">
                <i class="fas fa-times"></i>
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

function renderTrelloComments(comments = [], task = null) {
    const container = document.getElementById('trello-comments-stream');
    if (!container) return;

    const t = task || currentTrelloTask;
    const author = (t && t.user) ? t.user : 'prakash ahuja';
    const initials = author.slice(0, 2).toUpperCase();
    const avatarBg = initials === 'AC' ? '#d97706' : '#0c66e4';
    const listName = (t && (t.category_name || t.status_display)) ? (t.category_name || t.status_display) : 'Tasks for Roshan (D-G)';
    const timeText = (t && t.created_at) ? t.created_at : 'Jul 22, 2026, 12:52 PM';

    let html = '';

    // Render Comments first
    if (comments && comments.length > 0) {
        html += comments.map(c => {
            const cUser = c.user || 'adarsh computer';
            const cInitials = cUser.slice(0, 2).toUpperCase();
            const cBg = cInitials === 'AC' ? '#d97706' : '#0c66e4';
            const cTime = c.time_ago || c.created_at || 'just now';

            return `
                <div class="comment-item-row" style="display: flex; gap: 10px; align-items: flex-start;">
                    <div style="width: 30px; height: 30px; border-radius: 50%; background: ${cBg}; color: #ffffff; display: flex; align-items: center; justify-content: center; font-size: 0.75rem; font-weight: 700; flex-shrink: 0;">
                        ${cInitials}
                    </div>
                    <div style="flex: 1; min-width: 0;">
                        <div style="font-size: 0.825rem; margin-bottom: 3px;">
                            <strong style="color: #dee4ea;">${cUser}</strong>
                            <span style="color: #579dff; font-size: 0.775rem; text-decoration: underline; margin-left: 6px; cursor: pointer;">${cTime}</span>
                            ${c.is_edited ? '<span style="color: #8c9bab; font-size: 0.725rem; margin-left: 4px;">(edited)</span>' : ''}
                        </div>
                        <div style="background: #22272b; border-radius: 4px; padding: 10px 14px; color: #dee4ea; font-size: 0.85rem; line-height: 1.5; word-break: break-word; white-space: pre-wrap;">${c.content}</div>
                        <div style="display: flex; align-items: center; gap: 10px; margin-top: 4px; font-size: 0.75rem; color: #8c9bab;">
                            <span style="cursor: pointer; text-decoration: underline;" onclick="replyToTrelloComment('${cUser}')">• Reply</span>
                            <span style="cursor: pointer; text-decoration: underline;" onclick="editTrelloCommentInline(${c.id})">• Edit</span>
                            ${c.id ? `<span style="cursor: pointer; text-decoration: underline;" onclick="deleteTrelloComment(${c.id})">• Delete</span>` : ''}
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    // Activity Log Entry at bottom of feed (e.g. prakash ahuja added this card to Tasks for Roshan)
    html += `
        <div class="activity-log-item" style="display: flex; gap: 10px; align-items: flex-start; margin-top: 6px;">
            <div style="width: 30px; height: 30px; border-radius: 50%; background: ${avatarBg}; color: #ffffff; display: flex; align-items: center; justify-content: center; font-size: 0.75rem; font-weight: 700; flex-shrink: 0;">
                ${initials}
            </div>
            <div style="flex: 1; font-size: 0.85rem; line-height: 1.4;">
                <div>
                    <strong style="color: #dee4ea;">${author}</strong> 
                    <span style="color: #9fadbc;">added this card to</span> 
                    <strong style="color: #dee4ea;">${listName}</strong>
                </div>
                <div style="color: #579dff; font-size: 0.75rem; text-decoration: underline; cursor: pointer; margin-top: 2px;">
                    ${timeText}
                </div>
            </div>
        </div>
    `;

    container.innerHTML = html;
}

window.replyToTrelloComment = function(username) {
    const input = document.getElementById('trello-comment-input');
    if (input) {
        input.value = `@${username} `;
        input.focus();
        document.getElementById('trello-comment-save-btn').style.display = 'inline-block';
    }
};

window.editTrelloCommentInline = function(commentId) {
    if (!commentId || !currentTrelloTask || !currentTrelloTask.comments) return;
    const comment = currentTrelloTask.comments.find(c => c.id === commentId);
    if (!comment) return;
    const newContent = prompt('Edit comment:', comment.content);
    if (newContent === null || newContent.trim() === '' || newContent.trim() === comment.content) return;

    comment.content = newContent.trim();
    comment.is_edited = true;
    renderTrelloComments(currentTrelloTask.comments);
    if (window.showToast) window.showToast('Comment updated', 'info', 1200);
};

window.deleteTrelloComment = function(commentId) {
    if (!commentId || !currentTrelloTask) return;
    if (!confirm('Are you sure you want to delete this comment?')) return;

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
            if (window.showToast) window.showToast('Comment deleted', 'info');
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

        const csrfToken = getCsrfToken() || document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        const formData = new FormData();
        formData.append('csrfmiddlewaretoken', csrfToken);

        fetch(`/task/${currentTrelloTask.id}/delete/`, {
            method: 'POST',
            headers: { 'X-CSRFToken': csrfToken, 'X-Requested-With': 'XMLHttpRequest' },
            body: formData
        })
        .then(r => r.json())
        .then(data => {
            closeTrelloModal();
            if (window.showToast) window.showToast('Task deleted', 'success');
            setTimeout(() => window.location.reload(), 300);
        })
        .catch(() => {
            closeTrelloModal();
            window.location.reload();
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

