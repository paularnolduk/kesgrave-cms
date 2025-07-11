/**
 * Event Modal Fix Script
 * Enhances event modal with images, tags, content sections, and keyboard support
 */

(function() {
    'use strict';
    
    console.log('🔧 Event modal fix script loaded (final safe version)');
    
    let currentEventData = null;
    let escapeHandler = null;
    
    // Wait for modal to appear - updated to detect event-modal-* classes
    function waitForModal() {
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === 1) {
                        // Check for event modal specific classes
                        if (node.classList?.contains('event-modal-backdrop') || 
                            node.classList?.contains('event-modal-container') ||
                            node.querySelector?.('.event-modal-backdrop, .event-modal-container')) {
                            console.log('✅ Event modal detected, enhancing...');
                            const modal = node.classList?.contains('event-modal-backdrop') ? node : 
                                         node.querySelector('.event-modal-backdrop, .event-modal-container');
                            enhanceModal(modal);
                        }
                    }
                });
            });
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
        
        // Also check for existing modals
        const existingModal = document.querySelector('.event-modal-backdrop, .event-modal-container');
        if (existingModal) {
            console.log('✅ Existing event modal found, enhancing...');
            enhanceModal(existingModal);
        }
    }
    
    // Get event data from homepage API
    async function getEventFromHomepage(eventTitle) {
        try {
            const response = await fetch('/api/homepage/events');
            if (response.ok) {
                const events = await response.json();
                const event = events.find(e => 
                    e.title.toLowerCase().includes(eventTitle.toLowerCase()) || 
                    eventTitle.toLowerCase().includes(e.title.toLowerCase())
                );
                console.log('✅ Event found in homepage data:', event);
                return event;
            }
        } catch (error) {
            console.warn('⚠️ Failed to fetch homepage events:', error);
        }
        return null;
    }
    
    // Extract event title from modal content
    function extractEventTitle(modal) {
        // Look for the title in various possible locations
        const selectors = [
            '.event-modal-title', 
            'h1', 'h2', 'h3', 
            '[class*="title"]',
            '[class*="heading"]'
        ];
        
        for (const selector of selectors) {
            const titleElement = modal.querySelector(selector);
            if (titleElement && titleElement.textContent.trim()) {
                const title = titleElement.textContent.trim();
                console.log('🔍 Found event title:', title);
                return title;
            }
        }
        
        return null;
    }
    
    // Enhance modal with images and content
    async function enhanceModal(modal) {
        if (!modal || modal.hasAttribute('data-enhanced')) {
            return;
        }
        
        modal.setAttribute('data-enhanced', 'true');
        console.log('🎨 Enhancing event modal...');
        
        // Add escape key handler (safe version)
        escapeHandler = (e) => {
            if (e.key === 'Escape') {
                console.log('🔑 Escape key pressed - using safe close');
                safeCloseModal(modal);
            }
        };
        
        document.addEventListener('keydown', escapeHandler);
        
        // Try to get event title and data
        const eventTitle = extractEventTitle(modal);
        if (eventTitle) {
            const eventData = await getEventFromHomepage(eventTitle);
            
            if (eventData) {
                currentEventData = eventData;
                addEventImage(modal, eventData);
                addEventTags(modal, eventData);
                addContentSections(modal, eventData);
            } else {
                console.warn('⚠️ Could not find event data for:', eventTitle);
            }
        } else {
            console.warn('⚠️ Could not extract event title from modal');
        }
        
        // Enhance close functionality (safe version)
        enhanceCloseButtons(modal);
    }
    
    // Add event image to modal header (safe version)
    function addEventImage(modal, eventData) {
        if (!eventData.image) {
            console.log('ℹ️ No image available for event');
            return;
        }
        
        // Find the modal header - try multiple selectors
        const headerSelectors = [
            '.event-modal-header',
            '[class*="modal-header"]',
            '[class*="header"]'
        ];
        
        let modalHeader = null;
        for (const selector of headerSelectors) {
            modalHeader = modal.querySelector(selector);
            if (modalHeader) break;
        }
        
        if (!modalHeader) {
            console.warn('⚠️ Could not find modal header element');
            return;
        }
        
        // Check if image already exists
        if (modal.querySelector('.event-modal-image-enhancement')) {
            console.log('ℹ️ Image enhancement already applied');
            return;
        }
        
        console.log('🖼️ Adding event image to modal header');
        
        // Create image overlay instead of modifying existing styles
        const imageOverlay = document.createElement('div');
        imageOverlay.className = 'event-modal-image-enhancement';
        imageOverlay.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-image: linear-gradient(rgba(0, 0, 0, 0.4), rgba(0, 0, 0, 0.4)), url('${eventData.image}');
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            z-index: -1;
            border-radius: inherit;
        `;
        
        // Make header relative if it isn't already
        const currentPosition = window.getComputedStyle(modalHeader).position;
        if (currentPosition === 'static') {
            modalHeader.style.position = 'relative';
        }
        
        modalHeader.appendChild(imageOverlay);
        
        // Add featured badge if applicable
        if (eventData.featured) {
            const featuredBadge = document.createElement('div');
            featuredBadge.className = 'event-modal-featured-badge-enhancement';
            featuredBadge.textContent = 'FEATURED';
            featuredBadge.style.cssText = `
                position: absolute;
                top: 16px;
                left: 16px;
                padding: 8px 16px;
                border-radius: 20px;
                font-size: 0.75rem;
                font-weight: 700;
                text-transform: uppercase;
                color: white;
                background-color: #f39c12;
                z-index: 10;
                box-shadow: 0 2px 8px rgba(0,0,0,0.3);
                border: 2px solid #e67e22;
            `;
            modalHeader.appendChild(featuredBadge);
        }
        
        console.log('✅ Added event image and featured badge to modal');
    }
    
    // Add event tags/categories (safe version)
    function addEventTags(modal, eventData) {
        // Find a good place to add tags
        const headerSelectors = [
            '.event-modal-header',
            '[class*="modal-header"]',
            '[class*="header"]'
        ];
        
        let modalHeader = null;
        for (const selector of headerSelectors) {
            modalHeader = modal.querySelector(selector);
            if (modalHeader) break;
        }
        
        if (!modalHeader) {
            console.warn('⚠️ Could not find modal header for tags');
            return;
        }
        
        // Check if tags already exist
        if (modal.querySelector('.event-modal-tags-enhancement')) {
            console.log('ℹ️ Tags enhancement already applied');
            return;
        }
        
        console.log('🏷️ Adding event category tags');
        
        const tagsContainer = document.createElement('div');
        tagsContainer.className = 'event-modal-tags-enhancement';
        tagsContainer.style.cssText = `
            position: absolute;
            top: 16px;
            right: 16px;
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            z-index: 10;
        `;
        
        // Determine categories based on title
        const categories = [];
        const title = eventData.title.toLowerCase();
        
        if (title.includes('meeting') || title.includes('council')) {
            categories.push({ name: 'COUNCIL', color: '#3498db', icon: '🏛️' });
        } else if (title.includes('market') || title.includes('fair')) {
            categories.push({ name: 'COMMUNITY', color: '#e74c3c', icon: '👥' });
        } else {
            categories.push({ name: 'EVENT', color: '#2ecc71', icon: '⭐' });
        }
        
        categories.forEach(category => {
            const tag = document.createElement('span');
            tag.className = 'event-modal-tag-enhancement';
            tag.innerHTML = `${category.icon} ${category.name}`;
            tag.style.cssText = `
                padding: 6px 12px;
                border-radius: 16px;
                font-size: 0.7rem;
                font-weight: 600;
                text-transform: uppercase;
                color: white;
                background-color: ${category.color};
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                border: 1px solid rgba(255,255,255,0.3);
            `;
            tagsContainer.appendChild(tag);
        });
        
        modalHeader.appendChild(tagsContainer);
        console.log('✅ Added category tags to modal');
    }
    
    // Add additional content sections (safe version)
    function addContentSections(modal, eventData) {
        // Find the modal body
        const bodySelectors = [
            '.event-modal-body',
            '[class*="modal-body"]',
            '[class*="body"]',
            '[class*="content"]'
        ];
        
        let modalBody = null;
        for (const selector of bodySelectors) {
            modalBody = modal.querySelector(selector);
            if (modalBody) break;
        }
        
        if (!modalBody) {
            console.warn('⚠️ Could not find modal body for content sections');
            return;
        }
        
        // Check if sections already exist
        if (modal.querySelector('.event-modal-enhancements')) {
            console.log('ℹ️ Content enhancements already applied');
            return;
        }
        
        console.log('📋 Adding additional content sections');
        
        // Create enhancement container
        const enhancementContainer = document.createElement('div');
        enhancementContainer.className = 'event-modal-enhancements';
        
        // Quick Actions Section
        const quickActionsSection = document.createElement('div');
        quickActionsSection.className = 'event-modal-quick-actions-enhancement';
        quickActionsSection.innerHTML = `
            <h3 style="color: #2c5f2d; margin: 24px 0 16px 0; font-size: 1.1rem; font-weight: 600;">Quick Actions</h3>
            <div style="display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 20px;">
                <a href="https://maps.google.com/?q=${encodeURIComponent(eventData.location || 'Kesgrave Community Centre')}" 
                   target="_blank" 
                   style="display: inline-flex; align-items: center; gap: 8px; padding: 10px 16px; background-color: #3498db; color: white; text-decoration: none; border-radius: 8px; font-size: 0.9rem; font-weight: 500; transition: background-color 0.2s;">
                    📍 View on Map
                </a>
                <a href="https://calendar.google.com/calendar/render?action=TEMPLATE&text=${encodeURIComponent(eventData.title)}&dates=${eventData.date ? eventData.date.replace(/-/g, '') : ''}T100000/${eventData.date ? eventData.date.replace(/-/g, '') : ''}T160000&details=${encodeURIComponent(eventData.description || '')}&location=${encodeURIComponent(eventData.location || '')}" 
                   target="_blank"
                   style="display: inline-flex; align-items: center; gap: 8px; padding: 10px 16px; background-color: #2ecc71; color: white; text-decoration: none; border-radius: 8px; font-size: 0.9rem; font-weight: 500; transition: background-color 0.2s;">
                    📅 Add to Calendar
                </a>
                <button onclick="if(navigator.share){navigator.share({title: '${eventData.title}', text: '${eventData.description || ''}', url: window.location.href})}else{navigator.clipboard.writeText(window.location.href).then(() => alert('Link copied to clipboard!'))}" 
                        style="display: inline-flex; align-items: center; gap: 8px; padding: 10px 16px; background-color: #9b59b6; color: white; border: none; border-radius: 8px; font-size: 0.9rem; font-weight: 500; cursor: pointer; transition: background-color 0.2s;">
                    🔗 Share Event
                </button>
            </div>
        `;
        
        // Event Details Enhancement
        const eventDetailsSection = document.createElement('div');
        eventDetailsSection.className = 'event-modal-enhanced-details';
        eventDetailsSection.innerHTML = `
            <h3 style="color: #2c5f2d; margin: 24px 0 16px 0; font-size: 1.1rem; font-weight: 600;">Event Information</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 20px;">
                <div style="padding: 12px; background-color: #f8f9fa; border-radius: 6px; border: 1px solid #e9ecef;">
                    <strong style="color: #495057; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.5px;">Date & Time</strong>
                    <p style="margin: 4px 0 0 0; color: #2c5f2d; font-weight: 500;">${eventData.date ? new Date(eventData.date).toLocaleDateString('en-GB', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }) : 'Date TBA'}</p>
                </div>
                <div style="padding: 12px; background-color: #f8f9fa; border-radius: 6px; border: 1px solid #e9ecef;">
                    <strong style="color: #495057; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.5px;">Location</strong>
                    <p style="margin: 4px 0 0 0; color: #2c5f2d; font-weight: 500;">${eventData.location || 'Location TBA'}</p>
                </div>
            </div>
        `;
        
        // Add sections to container
        enhancementContainer.appendChild(eventDetailsSection);
        enhancementContainer.appendChild(quickActionsSection);
        
        // Insert at the end of modal body
        modalBody.appendChild(enhancementContainer);
        
        console.log('✅ Added quick actions and enhanced details sections');
    }
    
    // Safe close modal function - doesn't interfere with React
    function safeCloseModal(modal) {
        console.log('🚪 Safely closing modal');
        
        // Cleanup escape listener
        if (escapeHandler) {
            document.removeEventListener('keydown', escapeHandler);
            escapeHandler = null;
        }
        
        // Try to find and click the existing close button instead of removing DOM elements
        const closeButton = modal.querySelector('.event-modal-close, [aria-label*="Close"], [aria-label*="close"], button[class*="close"]');
        if (closeButton) {
            console.log('✅ Found close button, clicking it');
            closeButton.click();
        } else {
            console.warn('⚠️ Could not find close button, modal may remain open');
        }
    }
    
    // Enhance close buttons (safe version)
    function enhanceCloseButtons(modal) {
        const closeButtons = modal.querySelectorAll('.event-modal-close, [aria-label*="Close"], [aria-label*="close"], button[class*="close"]');
        
        closeButtons.forEach(button => {
            // Add cleanup when the original close button is clicked
            button.addEventListener('click', () => {
                console.log('🧹 Cleaning up on modal close');
                if (escapeHandler) {
                    document.removeEventListener('keydown', escapeHandler);
                    escapeHandler = null;
                }
            });
        });
        
        // Add backdrop click to close (safe version)
        const backdrop = modal.querySelector('.event-modal-backdrop');
        if (backdrop) {
            backdrop.addEventListener('click', (e) => {
                if (e.target === backdrop) {
                    safeCloseModal(modal);
                }
            });
        }
        
        console.log('✅ Enhanced close functionality (safe version)');
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', waitForModal);
    } else {
        waitForModal();
    }
    
})();