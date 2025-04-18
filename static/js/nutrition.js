// Function to load nutrition tips
async function loadNutritionTips() {
    const tipsContainer = document.getElementById('nutrition-tips');
    const loadingElement = tipsContainer.querySelector('.tips-loading');
    const tipsListElement = tipsContainer.querySelector('.tips-list');
    const noTipsElement = tipsContainer.querySelector('.no-tips');

    try {
        // Show loading state
        loadingElement.style.display = 'block';
        tipsListElement.style.display = 'none';
        noTipsElement.style.display = 'none';

        // Fetch tips from the server
        const response = await fetch('/api/nutrition-tips');
        const tips = await response.json();

        if (tips && tips.length > 0) {
            // Clear existing tips
            tipsListElement.innerHTML = '';

            // Add each tip to the list
            tips.forEach(tip => {
                const tipElement = createTipElement(tip);
                tipsListElement.appendChild(tipElement);
            });

            // Show tips list
            loadingElement.style.display = 'none';
            tipsListElement.style.display = 'block';
            noTipsElement.style.display = 'none';
        } else {
            // Show no tips message
            loadingElement.style.display = 'none';
            tipsListElement.style.display = 'none';
            noTipsElement.style.display = 'block';
        }
    } catch (error) {
        console.error('Error loading nutrition tips:', error);
        // Show no tips message with error
        loadingElement.style.display = 'none';
        tipsListElement.style.display = 'none';
        noTipsElement.style.display = 'block';
        noTipsElement.querySelector('p').textContent = 'Failed to load nutrition tips. Please try again.';
    }
}

// Function to create a tip element
function createTipElement(tip) {
    const tipElement = document.createElement('div');
    tipElement.className = 'tip-card';

    tipElement.innerHTML = `
        <div class="tip-icon-wrapper">
            <i class="fas ${tip.icon || 'fa-lightbulb'}"></i>
        </div>
        <div class="tip-content">
            <h4 class="tip-title">${tip.title}</h4>
            <p class="tip-description">${tip.description}</p>
            <div class="tip-meta">
                <span class="tip-tag">${tip.category}</span>
                <span class="tip-source">
                    <i class="fas fa-book"></i>
                    Source: ${tip.source || 'Pet Care Expert'}
                </span>
            </div>
        </div>
    `;

    return tipElement;
}

// Function to refresh tips
function refreshTips() {
    loadNutritionTips();
}

// Load tips when the page loads
document.addEventListener('DOMContentLoaded', loadNutritionTips); 