// Dashboard Navigation
document.addEventListener('DOMContentLoaded', function() {
    // Get all sections and navigation items
    const sections = document.querySelectorAll('.dashboard-section');
    const navItems = document.querySelectorAll('.dashboard-nav .nav-item');

    // Function to show selected section and hide others
    function showSection(sectionId) {
        sections.forEach(section => {
            if (section.id === sectionId) {
                section.classList.add('active');
            } else {
                section.classList.remove('active');
            }
        });
    }

    // Handle navigation item clicks
    navItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remove active class from all items
            navItems.forEach(nav => nav.classList.remove('active'));
            // Add active class to clicked item
            this.classList.add('active');

            // Get the section id from the href
            const sectionId = this.getAttribute('href').substring(1);
            showSection(sectionId);
        });
    });

    // Show overview section by default
    showSection('overview');

    // Handle quick action buttons
    const actionButtons = document.querySelectorAll('.action-button');
    actionButtons.forEach(button => {
        button.addEventListener('click', function() {
            const action = this.textContent.trim();
            switch(action) {
                case 'Add Pet':
                    // Handle add pet action
                    console.log('Add Pet clicked');
                    break;
                case 'Schedule Checkup':
                    // Handle schedule checkup action
                    console.log('Schedule Checkup clicked');
                    break;
                case 'Add Record':
                    // Handle add record action
                    console.log('Add Record clicked');
                    break;
            }
        });
    });

    // Handle form submissions
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            // Handle form submission
            console.log('Form submitted:', this);
        });
    });

    // Handle record filtering
    const recordFilter = document.querySelector('.records-filter select');
    if (recordFilter) {
        recordFilter.addEventListener('change', function() {
            const filterValue = this.value;
            // Handle record filtering
            console.log('Filter changed to:', filterValue);
        });
    }

    // Animate metric values
    const metricValues = document.querySelectorAll('.metric-value');
    metricValues.forEach(value => {
        const finalValue = value.textContent;
        value.textContent = '0';
        let current = 0;
        const increment = parseFloat(finalValue) / 50;
        const interval = setInterval(() => {
            current += increment;
            if (current >= parseFloat(finalValue)) {
                value.textContent = finalValue;
                clearInterval(interval);
            } else {
                value.textContent = current.toFixed(1);
            }
        }, 20);
    });

    // Check if this is the first login
    const isFirstLogin = document.body.dataset.firstLogin === 'true';
    
    // Get modal elements
    const modal = document.getElementById('petDetailsModal');
    const petDetailsForm = document.getElementById('petDetailsForm');
    const breedSelect = document.getElementById('petBreed');

    // Fetch and populate breeds
    async function loadBreeds() {
        try {
            const response = await fetch('/api/breeds');
            const data = await response.json();
            
            // Sort breeds alphabetically
            const breeds = data.breeds.sort();
            
            // Add breeds to select
            breeds.forEach(breed => {
                const option = document.createElement('option');
                option.value = breed;
                option.textContent = breed;
                breedSelect.appendChild(option);
            });
        } catch (error) {
            console.error('Error loading breeds:', error);
            showNotification('Error loading breeds. Please try again.', 'error');
        }
    }

    // Load breeds when modal is shown
    if (isFirstLogin) {
        modal.classList.add('active');
        loadBreeds();
    }

    // Handle form submission
    petDetailsForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = {
            name: document.getElementById('petName').value,
            age: document.getElementById('petAge').value,
            weight: document.getElementById('petWeight').value,
            breed: document.getElementById('petBreed').value
        };

        try {
            const response = await fetch('/api/pets', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            if (response.ok) {
                // Hide modal
                modal.classList.remove('active');
                // Show success message
                showNotification('Pet details saved successfully!', 'success');
            } else {
                const data = await response.json();
                throw new Error(data.error || 'Failed to save pet details');
            }
        } catch (error) {
            showNotification(error.message, 'error');
        }
    });

    // Function to show notifications
    function showNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Remove notification after 3 seconds
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
}); 