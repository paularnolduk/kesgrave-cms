// This script fixes the date formatting and summary button text issues

(function() {
    'use strict';
    
    console.log('Meeting page fixes loading...');
    
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
    
    // Fix summary button text
    function fixSummaryButtons() {
        // Find all buttons with "AVAILABLE SOON" text that are summary buttons
        const buttons = document.querySelectorAll('button');
        
        buttons.forEach(button => {
            const text = button.textContent.trim();
            
            // Check if this is a summary button (usually the last button in a meeting card)
            if (text === 'AVAILABLE SOON') {
                const buttonParent = button.closest('.meeting-card, [class*="meeting"], [class*="card"]');
                if (buttonParent) {
                    // Check if this is likely a summary button (last button or has summary-related class)
                    const allButtons = buttonParent.querySelectorAll('button');
                    const isLastButton = button === allButtons[allButtons.length - 1];
                    
                    if (isLastButton || button.textContent.toLowerCase().includes('summary')) {
                        button.textContent = 'Summary Page Unavailable';
                        button.style.cursor = 'not-allowed';
                        button.style.opacity = '0.6';
                        console.log('Fixed summary button text');
                    }
                }
            }
        });
    }
    
    // Apply fixes when page loads
    function applyFixes() {
        fixDateFormatting();
        fixSummaryButtons();
    }
    
    // Run fixes on page load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', applyFixes);
    } else {
        applyFixes();
    }
    
    // Also run fixes after a short delay to catch dynamically loaded content
    setTimeout(applyFixes, 1000);
    setTimeout(applyFixes, 3000);
    
    // Set up a mutation observer to catch dynamic content changes
    const observer = new MutationObserver(function(mutations) {
        let shouldApplyFixes = false;
        
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                shouldApplyFixes = true;
            }
        });
        
        if (shouldApplyFixes) {
            setTimeout(applyFixes, 100);
        }
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    
    console.log('Meeting page fixes initialized');
})();