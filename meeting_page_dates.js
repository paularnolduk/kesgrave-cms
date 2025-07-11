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
    
    // Apply fixes when page loads
    function applyFixes() {
        console.log('Applying meeting page fixes...');
        fixDateFormatting();
        fixSummaryButtons();
        console.log('Meeting page fixes applied');
    }
    
    // Run fixes on page load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', applyFixes);
    } else {
        applyFixes();
    }
    
    // Also run fixes after delays to catch dynamically loaded content
    setTimeout(() => {
        console.log('Running delayed fixes (1s)...');
        applyFixes();
    }, 1000);
    
    setTimeout(() => {
        console.log('Running delayed fixes (3s)...');
        applyFixes();
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
            setTimeout(applyFixes, 100);
        }
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    
    console.log('Meeting page fixes initialized with mutation observer');
})();