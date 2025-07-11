(function() {
    'use strict';
    
    console.log('Meeting page fixes + breadcrumb fixes loading...');
    
    // Fix date formatting to add comma
    function fixDateFormatting() {
        // Find all elements that might contain dates
        const dateElements = document.querySelectorAll('h3, h2, td, .meeting-date, [class*="date"]');
        
        dateElements.forEach(element => {
            const text = element.textContent;
            
            // Pattern to match "Monday 30 June 2025" and add comma
            const datePattern = /^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s+(\d{1,2}\s+\w+\s+\d{4})$/;
            
            if (datePattern.test(text.trim())) {
                const newText = text.replace(datePattern, '$1, $2');
                element.textContent = newText;
                console.log('Fixed date:', text, '->', newText);
            }
        });
    }
    
    // Fix summary button text - improved targeting
    function fixSummaryButtons() {
        console.log('Looking for summary buttons...');
        
        // Find all buttons with "AVAILABLE SOON" text
        const buttons = document.querySelectorAll('button');
        let summaryButtonsFound = 0;
        
        buttons.forEach((button, index) => {
            const text = button.textContent.trim();
            
            // Check if this is a summary button
            if (text === 'AVAILABLE SOON') {
                // Get the parent container
                const parent = button.parentElement;
                
                // Check if this button has an icon (summary buttons typically have icons)
                const hasIcon = button.querySelector('svg, i, [class*="icon"]') || 
                               button.innerHTML.includes('📄') || 
                               button.innerHTML.includes('📋');
                
                // Check if this is the only "AVAILABLE SOON" button in its container
                // (summary buttons are typically standalone, not part of a group)
                const siblingButtons = parent ? parent.querySelectorAll('button') : [];
                const availableSoonButtons = Array.from(siblingButtons).filter(btn => 
                    btn.textContent.trim() === 'AVAILABLE SOON'
                );
                
                // If this is a standalone "AVAILABLE SOON" button, it's likely a summary button
                if (availableSoonButtons.length === 1 || hasIcon) {
                    button.textContent = 'Summary Page Unavailable';
                    button.style.cursor = 'not-allowed';
                    button.style.opacity = '0.6';
                    button.disabled = true;
                    summaryButtonsFound++;
                    console.log('Fixed summary button #' + summaryButtonsFound + ' (index: ' + index + ')');
                }
            }
        });
        
        console.log('Total summary buttons fixed:', summaryButtonsFound);
        
        // Alternative approach: target buttons that are likely summary buttons by position
        // Look for buttons that are the last in their meeting card section
        const meetingCards = document.querySelectorAll('[class*="meeting"], .card, section');
        meetingCards.forEach((card, cardIndex) => {
            const cardButtons = card.querySelectorAll('button');
            if (cardButtons.length > 0) {
                const lastButton = cardButtons[cardButtons.length - 1];
                if (lastButton.textContent.trim() === 'AVAILABLE SOON' && 
                    !lastButton.textContent.includes('Summary Page Unavailable')) {
                    lastButton.textContent = 'Summary Page Unavailable';
                    lastButton.style.cursor = 'not-allowed';
                    lastButton.style.opacity = '0.6';
                    lastButton.disabled = true;
                    console.log('Fixed last button in card #' + cardIndex + ' as summary button');
                }
            }
        });
    }
    
    // NEW: Fix breadcrumb category links
    function fixBreadcrumbLinks() {
        console.log('Looking for breadcrumb links to fix...');
        
        // Find all breadcrumb links that go to /content/category-name
        const breadcrumbLinks = document.querySelectorAll('nav a[href^="/content/"]');
        let breadcrumbsFixed = 0;
        
        breadcrumbLinks.forEach(link => {
            const href = link.getAttribute('href');
            
            // Skip the main /content link, only fix category-specific ones
            if (href !== '/content' && href.includes('/content/')) {
                // Extract category info from the link text and convert to anchor
                const categoryName = link.textContent.trim();
                
                // Map category names to their section IDs (based on content hub structure)
                const categoryMap = {
                    'Financial Information': 'category-5',
                    'Policies and Important Documents': 'category-1', 
                    'Business Plan': 'category-7',
                    'Council Information': 'category-2',
                    'Reporting Problems': 'category-4'
                    // Add more categories as they are discovered
                };
                
                if (categoryMap[categoryName]) {
                    const newHref = `/content#${categoryMap[categoryName]}`;
                    link.setAttribute('href', newHref);
                    breadcrumbsFixed++;
                    console.log(`Fixed breadcrumb: "${categoryName}" -> ${newHref}`);
                } else {
                    // For unknown categories, try to extract ID from current URL pattern
                    // Look for patterns like /content/financial-information and convert to anchor
                    const urlParts = href.split('/');
                    const categorySlug = urlParts[urlParts.length - 1];
                    
                    // Try to guess the category ID based on common patterns
                    if (categorySlug) {
                        // For now, just redirect to main content page
                        link.setAttribute('href', '/content');
                        console.log(`Fixed unknown category breadcrumb: "${categoryName}" -> /content`);
                        breadcrumbsFixed++;
                    }
                }
            }
        });
        
        console.log('Total breadcrumb links fixed:', breadcrumbsFixed);
    }
    
    // Apply all fixes when page loads
    function applyAllFixes() {
        console.log('Applying all page fixes...');
        fixDateFormatting();
        fixSummaryButtons();
        fixBreadcrumbLinks();
        console.log('All page fixes applied');
    }
    
    // Run fixes on page load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', applyAllFixes);
    } else {
        applyAllFixes();
    }
    
    // Also run fixes after delays to catch dynamically loaded content
    setTimeout(() => {
        console.log('Running delayed fixes (1s)...');
        applyAllFixes();
    }, 1000);
    
    setTimeout(() => {
        console.log('Running delayed fixes (3s)...');
        applyAllFixes();
    }, 3000);
    
    // Set up a mutation observer to catch dynamic content changes
    const observer = new MutationObserver(function(mutations) {
        let shouldApplyFixes = false;
        
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                shouldApplyFixes = true;
            }
        });
        
        if (shouldApplyFixes) {
            console.log('Content changed, applying fixes...');
            setTimeout(applyAllFixes, 100);
        }
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    
    console.log('Meeting page fixes + breadcrumb fixes initialized with mutation observer');
})();