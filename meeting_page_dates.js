(function() {
    'use strict';
    
    console.log('Meeting page fixes + enhanced breadcrumb navigation loading...');
    
    // Fix date formatting to add comma
    function fixDateFormatting() {
        const dateElements = document.querySelectorAll('h3, h2, td, .meeting-date, [class*="date"]');
        
        dateElements.forEach(element => {
            const text = element.textContent;
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
        console.log('Looking for summary buttons...');
        
        const buttons = document.querySelectorAll('button');
        let summaryButtonsFound = 0;
        
        buttons.forEach((button, index) => {
            const text = button.textContent.trim();
            
            if (text === 'AVAILABLE SOON') {
                const parent = button.parentElement;
                const hasIcon = button.querySelector('svg, i, [class*="icon"]') || 
                               button.innerHTML.includes('📄') || 
                               button.innerHTML.includes('📋');
                
                const siblingButtons = parent ? parent.querySelectorAll('button') : [];
                const availableSoonButtons = Array.from(siblingButtons).filter(btn => 
                    btn.textContent.trim() === 'AVAILABLE SOON'
                );
                
                if (availableSoonButtons.length === 1 || hasIcon) {
                    button.textContent = 'Summary Page Unavailable';
                    button.style.cursor = 'not-allowed';
                    button.style.opacity = '0.6';
                    button.disabled = true;
                    summaryButtonsFound++;
                    console.log('Fixed summary button #' + summaryButtonsFound);
                }
            }
        });
        
        console.log('Total summary buttons fixed:', summaryButtonsFound);
    }
    
    // Enhanced category mapping with human-readable anchors
    const categoryMapping = {
        'Financial Information': {
            id: 'category-5',
            anchor: 'financial-information'
        },
        'Policies and Important Documents': {
            id: 'category-1',
            anchor: 'policies-and-documents'
        },
        'Business Plan': {
            id: 'category-7',
            anchor: 'business-plan'
        },
        'Council Information': {
            id: 'category-2',
            anchor: 'council-information'
        },
        'Reporting Problems': {
            id: 'category-4',
            anchor: 'reporting-problems'
        }
    };
    
    // Add human-readable anchor IDs to sections
    function addHumanReadableAnchors() {
        console.log('Adding human-readable anchors...');
        
        Object.values(categoryMapping).forEach(category => {
            const section = document.getElementById(category.id);
            if (section && !document.getElementById(category.anchor)) {
                // Create an invisible anchor element for the human-readable name
                const anchor = document.createElement('div');
                anchor.id = category.anchor;
                anchor.style.position = 'absolute';
                anchor.style.top = '-100px'; // Offset for fixed header
                anchor.style.visibility = 'hidden';
                
                // Insert the anchor just before the section
                section.parentNode.insertBefore(anchor, section);
                console.log(`Added anchor: ${category.anchor} for ${category.id}`);
            }
        });
    }
    
    // Enhanced smooth scrolling function
    function smoothScrollToElement(targetId, offset = 100) {
        const element = document.getElementById(targetId);
        if (element) {
            const elementPosition = element.getBoundingClientRect().top + window.pageYOffset;
            const offsetPosition = elementPosition - offset;
            
            window.scrollTo({
                top: offsetPosition,
                behavior: 'smooth'
            });
            
            console.log(`Smooth scrolled to ${targetId} with ${offset}px offset`);
            return true;
        }
        return false;
    }
    
    // Handle anchor navigation on page load
    function handleAnchorNavigation() {
        const hash = window.location.hash.substring(1); // Remove the #
        
        if (hash) {
            console.log('Handling anchor navigation for:', hash);
            
            // Try to scroll to the element with a delay to ensure content is loaded
            setTimeout(() => {
                if (!smoothScrollToElement(hash)) {
                    // If the direct ID doesn't work, try the original category ID
                    const categoryEntry = Object.values(categoryMapping).find(cat => cat.anchor === hash);
                    if (categoryEntry) {
                        smoothScrollToElement(categoryEntry.id);
                    }
                }
            }, 500);
        }
    }
    
    // Fix breadcrumb links to use human-readable anchors
    function fixBreadcrumbLinks() {
        console.log('Fixing breadcrumb links with human-readable anchors...');
        
        const breadcrumbLinks = document.querySelectorAll('nav a[href^="/content/"]');
        let breadcrumbsFixed = 0;
        
        breadcrumbLinks.forEach(link => {
            const href = link.getAttribute('href');
            
            // Skip the main /content link, only fix category-specific ones
            if (href !== '/content' && href.includes('/content/')) {
                const categoryName = link.textContent.trim();
                
                if (categoryMapping[categoryName]) {
                    const newHref = `/content#${categoryMapping[categoryName].anchor}`;
                    link.setAttribute('href', newHref);
                    breadcrumbsFixed++;
                    console.log(`Fixed breadcrumb: "${categoryName}" -> ${newHref}`);
                } else {
                    // For unknown categories, redirect to main content page
                    link.setAttribute('href', '/content');
                    console.log(`Fixed unknown category breadcrumb: "${categoryName}" -> /content`);
                    breadcrumbsFixed++;
                }
            }
        });
        
        console.log('Total breadcrumb links fixed:', breadcrumbsFixed);
    }
    
    // Enhanced click handler for breadcrumb links
    function addBreadcrumbClickHandlers() {
        const breadcrumbLinks = document.querySelectorAll('nav a[href*="#"]');
        
        breadcrumbLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                const href = this.getAttribute('href');
                const hash = href.split('#')[1];
                
                if (hash && window.location.pathname === '/content') {
                    // If we're already on the content page, just scroll
                    e.preventDefault();
                    smoothScrollToElement(hash);
                    
                    // Update the URL without triggering navigation
                    history.pushState(null, null, href);
                }
            });
        });
    }
    
    // Apply all fixes
    function applyAllFixes() {
        console.log('Applying all page fixes...');
        fixDateFormatting();
        fixSummaryButtons();
        addHumanReadableAnchors();
        fixBreadcrumbLinks();
        addBreadcrumbClickHandlers();
        handleAnchorNavigation();
        console.log('All page fixes applied');
    }
    
    // Initialize when page loads
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', applyAllFixes);
    } else {
        applyAllFixes();
    }
    
    // Handle hash changes (back/forward navigation)
    window.addEventListener('hashchange', handleAnchorNavigation);
    
    // Apply fixes after delays for dynamic content
    setTimeout(applyAllFixes, 1000);
    setTimeout(applyAllFixes, 3000);
    
    // Set up mutation observer for dynamic content
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
    
    console.log('Meeting page fixes + enhanced breadcrumb navigation initialized');
})();