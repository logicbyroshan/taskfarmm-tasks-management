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

    // Update the date/time display every minute
    setInterval(updateDateTime, 60000);
});

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
    if (!editModal || !editForm) return;

    const closeModal = () => { editModal.style.display = 'none'; };

    editModal.addEventListener('click', (event) => {
        if (event.target.classList.contains('close-modal') || event.target.classList.contains('btn-cancel') || event.target.classList.contains('modal-backdrop')) {
            closeModal();
        }
    });

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
        fetch(`/task/${taskId}/update/`, { method: 'POST', body: formData, headers: { 'X-Requested-With': 'XMLHttpRequest' } })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
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
