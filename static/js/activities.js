// Function to get random activities from the schedule
function getRandomActivities(schedule, count) {
    const activities = Object.entries(schedule).map(([time, activity]) => ({
        time,
        activity,
        icon: getActivityIcon(activity.toLowerCase())
    }));
    
    // Shuffle array and get first 'count' items
    return activities
        .sort(() => Math.random() - 0.5)
        .slice(0, count);
}

// Function to get appropriate icon for activity type
function getActivityIcon(activity) {
    const icons = {
        walk: 'fa-walking',
        play: 'fa-gamepad',
        training: 'fa-dumbbell',
        feeding: 'fa-utensils',
        grooming: 'fa-brush',
        exercise: 'fa-running',
        rest: 'fa-bed',
        default: 'fa-paw'
    };

    return icons[Object.keys(icons).find(key => activity.includes(key))] || icons.default;
}

// Function to update upcoming activities display
function updateUpcomingActivities(breedData) {
    const container = document.getElementById('upcomingActivities');
    if (!container) return;

    // Get two random activities from the schedule
    const activities = getRandomActivities(breedData.schedule, 2);

    if (activities.length === 0) {
        container.innerHTML = `
            <div class="no-activities">
                <i class="fas fa-calendar-times"></i>
                <p>No upcoming activities found</p>
            </div>
        `;
        return;
    }

    container.innerHTML = activities.map(({ time, activity, icon }) => `
        <div class="upcoming-activity-card">
            <div class="activity-time">
                <i class="far fa-clock"></i>
                <span>${time}</span>
            </div>
            <div class="activity-name">${activity}</div>
            <div class="activity-icon">
                <i class="fas ${icon}"></i>
            </div>
            <div class="activity-status">Upcoming</div>
        </div>
    `).join('');
}

// Function to load and display upcoming activities
function loadUpcomingActivities() {
    const container = document.getElementById('upcomingActivities');
    if (!container) return;

    // Show loading state
    container.innerHTML = `
        <div class="activity-loading">
            <i class="fas fa-spinner fa-spin"></i>
            <p>Loading upcoming activities...</p>
        </div>
    `;

    // Fetch breed activities from the server
    fetch('/api/breed-activities')
        .then(response => response.json())
        .then(data => {
            // Get the first pet's breed (you can modify this to handle multiple pets)
            const pets = document.querySelectorAll('.activity-card');
            if (pets.length > 0) {
                const breed = pets[0].querySelector('.breed-tag').textContent;
                if (data[breed]) {
                    updateUpcomingActivities(data[breed]);
                } else {
                    throw new Error('No activities found for this breed');
                }
            } else {
                throw new Error('No pets found');
            }
        })
        .catch(error => {
            console.error('Error loading upcoming activities:', error);
            container.innerHTML = `
                <div class="error-message">
                    <i class="fas fa-exclamation-circle"></i>
                    <p>Failed to load upcoming activities</p>
                </div>
            `;
        });
}

// Initialize upcoming activities when the page loads
document.addEventListener('DOMContentLoaded', loadUpcomingActivities);

// Refresh activities every 30 minutes
setInterval(loadUpcomingActivities, 30 * 60 * 1000); 