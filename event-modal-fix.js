/**
 * Event Modal Fix Script
 * Enhances event modal with images, tags, content sections, and keyboard support
 */

(function() {
    'use strict';
    
    console.log('🔧 Event modal fix script loaded (final timing fix version)');
    
    let currentEventData = null;
    let escapeHandler = null;
    
    // Wait for modal to appear
    function waitForModal() {
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === 1) {
                        // Look specifically for the container element that has content
                        let targetModal = null;
                        
                        if (node.classList?.contains('event-modal-container')) {
                            targetModal = node;
                        } else if (node.classList?.contains('event-modal-backdrop')) {
                            // If backdrop is added, find the container inside it
                            targetModal = node.querySelector('.event-modal-container');
                        } else {
                            // Check if a container was added inside this node
                            targetModal = node.querySelector?.('.event-modal-container');
                        }
                        
                        if (targetModal) {
                            console.log('✅ Event modal container detected, enhancing...');
                            // Increased delay to ensure modal content is fully rendered
                            setTimeout(() => {
                                enhanceModal(targetModal);
                            }, 400);
                        }
                    }
                });
            });
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
        
        // Also check for existing modal containers
        const existingContainer = document.querySelector('.event-modal-container');
        if (existingContainer) {
            console.log('✅ Existing event modal container found, enhancing...');
            setTimeout(() => {
                enhanceModal(existingContainer);
            }, 400);
        }
    }
    
    // Get combined event data from both APIs
    async function getCombinedEventData(eventTitle) {
        try {
            console.log('🔍 Fetching data for event:', eventTitle);
            
            // First get homepage events data (has images)
            const homepageResponse = await fetch('/api/homepage/events');
            let homepageEvent = null;
            
            if (homepageResponse.ok) {
                const events = await homepageResponse.json();
                homepageEvent = events.find(e => 
                    e.title.toLowerCase().includes(eventTitle.toLowerCase()) || 
                    eventTitle.toLowerCase().includes(e.title.toLowerCase())
                );
                console.log('✅ Homepage event data:', homepageEvent);
            }
            
            // Then get detailed event data from individual API
            let detailedEvent = null;
            if (homepageEvent && homepageEvent.id) {
                try {
                    const detailResponse = await fetch(`/api/events/${homepageEvent.id}`);
                    if (detailResponse.ok) {
                        detailedEvent = await detailResponse.json();
                        console.log('✅ Detailed event data:', detailedEvent);
                    }
                } catch (error) {
                    console.warn('⚠️ Could not fetch detailed event data:', error);
                }
            }
            
            // Combine the data, prioritizing homepage data for images and detailed data for additional fields
            const combinedData = {
                ...homepageEvent,
                ...detailedEvent,
                // Ensure image comes from homepage data
                image: homepageEvent?.image || detailedEvent?.image || '',
                // Ensure featured status comes from homepage data
                featured: homepageEvent?.featured || detailedEvent?.is_featured || false
            };
            
            console.log('✅ Combined event data:', combinedData);
            return combinedData;
            
        } catch (error) {
            console.warn('⚠️ Failed to fetch event data:', error);
            return null;
        }
    }
    
    // Extract event title from modal content with better debugging
    function extractEventTitle(modal) {
        console.log('🔍 Attempting to extract event title from modal container...');
        
        const selectors = [
            '.event-modal-title', 
            'h1', 'h2', 'h3', 
            '[class*="title"]',
            '[class*="heading"]'
        ];
        
        for (const selector of selectors) {
            console.log(`🔍 Trying selector: ${selector}`);
            const titleElement = modal.querySelector(selector);
            if (titleElement) {
                const title = titleElement.textContent.trim();
                console.log(`🔍 Found element with selector "${selector}":`, title);
                if (title) {
                    console.log('✅ Successfully extracted title:', title);
                    return title;
                }
            } else {
                console.log(`❌ No element found for selector: ${selector}`);
            }
        }
        
        console.warn('⚠️ Could not extract event title from modal container');
        return null;
    }
    
    // Enhance modal with all improvements
    async function enhanceModal(modal) {
        if (!modal || modal.hasAttribute('data-enhanced')) {
            console.log('ℹ️ Modal already enhanced or not found');
            return;
        }
        
        modal.setAttribute('data-enhanced', 'true');
        console.log('🎨 Enhancing event modal container...');
        
        // Add escape key handler
        escapeHandler = (e) => {
            if (e.key === 'Escape') {
                console.log('🔑 Escape key pressed - using safe close');
                safeCloseModal(modal);
            }
        };
        
        document.addEventListener('keydown', escapeHandler);
        
        // Get event data with better error handling
        try {
            const eventTitle = extractEventTitle(modal);
            if (eventTitle) {
                console.log('🎯 Extracted title, fetching event data...');
                const eventData = await getCombinedEventData(eventTitle);
                
                if (eventData) {
                    currentEventData = eventData;
                    console.log('🖼️ Adding image to modal...');
                    addEventImage(modal, eventData);
                    console.log('📋 Adding related sections...');
                    addRelatedSections(modal, eventData);
                } else {
                    console.warn('⚠️ Could not find event data for:', eventTitle);
                }
            } else {
                console.warn('⚠️ Could not extract event title from modal container');
            }
        } catch (error) {
            console.error('❌ Error enhancing modal:', error);
        }
        
        // Enhance close functionality
        enhanceCloseButtons(modal);
    }
    
    // Add event image to modal header with better debugging
    function addEventImage(modal, eventData) {
        console.log('🖼️ addEventImage called with:', eventData);
        
        if (!eventData.image) {
            console.log('ℹ️ No image available for event, image field:', eventData.image);
            return;
        }
        
        console.log('✅ Image available:', eventData.image);
        
        // Find the modal header - look in the container and its children
        const headerSelectors = [
            '.event-modal-header',
            '[class*="modal-header"]',
            '[class*="header"]'
        ];
        
        let modalHeader = null;
        for (const selector of headerSelectors) {
            modalHeader = modal.querySelector(selector);
            if (modalHeader) {
                console.log(`✅ Found modal header with selector: ${selector}`);
                break;
            }
        }
        
        if (!modalHeader) {
            console.warn('⚠️ Could not find modal header element in container');
            return;
        }
        
        // Check if image already exists
        if (modal.querySelector('.event-modal-image-enhancement')) {
            console.log('ℹ️ Image enhancement already applied');
            return;
        }
        
        console.log('🖼️ Adding event image to modal header');
        
        // Create image overlay
        const imageOverlay = document.createElement('div');
        imageOverlay.className = 'event-modal-image-enhancement';
        
        // Construct full image URL
        const imageUrl = eventData.image.startsWith('http') ? eventData.image : `https://kesgrave-cms.onrender.com${eventData.image}`;
        console.log('🔗 Full image URL:', imageUrl);
        
        imageOverlay.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-image: linear-gradient(rgba(0, 0, 0, 0.4), rgba(0, 0, 0, 0.4)), url('${imageUrl}');
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            z-index: 0;
            border-radius: inherit;
        `;
        
        // Make header relative if it isn't already
        const currentPosition = window.getComputedStyle(modalHeader).position;
        if (currentPosition === 'static') {
            modalHeader.style.position = 'relative';
        }
        
        modalHeader.appendChild(imageOverlay);
        
        // Add featured badge if applicable (positioned to not cover close button)
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
            console.log('✅ Added featured badge');
        }
        
        console.log('✅ Successfully added event image and featured badge to modal');
    }
    
    // Add related sections (simplified for debugging)
    function addRelatedSections(modal, eventData) {
        console.log('📋 addRelatedSections called');
        
        // Find the modal body - look in the container
        const bodySelectors = [
            '.event-modal-body',
            '.event-modal-content',
            '[class*="modal-body"]',
            '[class*="body"]',
            '[class*="content"]'
        ];
        
        let modalBody = null;
        for (const selector of bodySelectors) {
            modalBody = modal.querySelector(selector);
            if (modalBody) {
                console.log(`✅ Found modal body with selector: ${selector}`);
                break;
            }
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
        
        console.log('📋 Adding related sections');
        
        // Create enhancement container
        const enhancementContainer = document.createElement('div');
        enhancementContainer.className = 'event-modal-enhancements';
        
        // Quick Actions Section
        const quickActionsSection = createQuickActionsSection(eventData);
        
        // Related Links Section (if available)
        const relatedLinksSection = createRelatedLinksSection(eventData);
        
        // Add sections to container
        if (quickActionsSection) {
            enhancementContainer.appendChild(quickActionsSection);
            console.log('✅ Added quick actions section');
        }
        if (relatedLinksSection) {
            enhancementContainer.appendChild(relatedLinksSection);
            console.log('✅ Added related links section');
        }
        
        // Insert at the end of modal body
        modalBody.appendChild(enhancementContainer);
        
        console.log('✅ Successfully added related sections to modal');
    }
    
    // Create Quick Actions section
    function createQuickActionsSection(eventData) {
        const section = document.createElement('div');
        section.className = 'event-modal-quick-actions-enhancement';
        
        const locationQuery = eventData.location_name || eventData.location || 'Kesgrave Community Centre';
        const fullLocation = eventData.location_address ? 
            `${eventData.location_name || eventData.location}, ${eventData.location_address}` : 
            locationQuery;
        
        // Format date for calendar
        let calendarDate = '';
        if (eventData.start_date) {
            const startDate = new Date(eventData.start_date);
            const endDate = eventData.end_date ? new Date(eventData.end_date) : new Date(startDate.getTime() + 2 * 60 * 60 * 1000);
            calendarDate = `${startDate.toISOString().replace(/[-:]/g, '').split('.')[0]}Z/${endDate.toISOString().replace(/[-:]/g, '').split('.')[0]}Z`;
        } else if (eventData.date) {
            const eventDate = new Date(eventData.date);
            const endDate = new Date(eventDate.getTime() + 2 * 60 * 60 * 1000);
            calendarDate = `${eventDate.toISOString().replace(/[-:]/g, '').split('.')[0]}Z/${endDate.toISOString().replace(/[-:]/g, '').split('.')[0]}Z`;
        }
        
        section.innerHTML = `
            <h3 style="color: #2c5f2d; margin: 24px 0 16px 0; font-size: 1.1rem; font-weight: 600;">Quick Actions</h3>
            <div style="display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 20px;">
                <a href="https://maps.google.com/?q=${encodeURIComponent(fullLocation)}" 
                   target="_blank" 
                   style="display: inline-flex; align-items: center; gap: 8px; padding: 10px 16px; background-color: #3498db; color: white; text-decoration: none; border-radius: 8px; font-size: 0.9rem; font-weight: 500; transition: background-color 0.2s;">
                    📍 View on Map
                </a>
                <a href="https://calendar.google.com/calendar/render?action=TEMPLATE&text=${encodeURIComponent(eventData.title)}&dates=${calendarDate}&details=${encodeURIComponent(eventData.description || eventData.long_description || '')}&location=${encodeURIComponent(fullLocation)}" 
                   target="_blank"
                   style="display: inline-flex; align-items: center; gap: 8px; padding: 10px 16px; background-color: #2ecc71; color: white; text-decoration: none; border-radius: 8px; font-size: 0.9rem; font-weight: 500; transition: background-color 0.2s;">
                    📅 Add to Calendar
                </a>
                <button onclick="if(navigator.share){navigator.share({title: '${eventData.title}', text: '${(eventData.description || '').replace(/'/g, "\\'")}', url: window.location.href})}else{navigator.clipboard.writeText(window.location.href).then(() => alert('Link copied to clipboard!'))}" 
                        style="display: inline-flex; align-items: center; gap: 8px; padding: 10px 16px; background-color: #9b59b6; color: white; border: none; border-radius: 8px; font-size: 0.9rem; font-weight: 500; cursor: pointer; transition: background-color 0.2s;">
                    🔗 Share Event
                </button>
            </div>
        `;
        
        return section;
    }
    
    // Create Related Links section
    function createRelatedLinksSection(eventData) {
        const links = [];
        
        // Add website URL if available
        if (eventData.website_url && eventData.website_url.trim()) {
            links.push({
                title: 'Event Website',
                url: eventData.website_url,
                icon: '🌐'
            });
        }
        
        // Add booking URL if available
        if (eventData.booking_url && eventData.booking_url.trim()) {
            links.push({
                title: 'Book Tickets',
                url: eventData.booking_url,
                icon: '🎫'
            });
        }
        
        // If no links, don't create the section
        if (links.length === 0) {
            return null;
        }
        
        const section = document.createElement('div');
        section.className = 'event-modal-related-links-enhancement';
        
        const linksHtml = links.map(link => `
            <a href="${link.url}" 
               target="_blank" 
               rel="noopener noreferrer"
               style="display: flex; align-items: center; gap: 12px; padding: 12px 16px; background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px; text-decoration: none; color: #2c5f2d; font-weight: 500; transition: all 0.2s;">
                <span style="font-size: 1.2rem;">${link.icon}</span>
                <span>${link.title}</span>
                <span style="margin-left: auto; color: #6c757d;">↗</span>
            </a>
        `).join('');
        
        section.innerHTML = `
            <h3 style="color: #2c5f2d; margin: 24px 0 16px 0; font-size: 1.1rem; font-weight: 600;">Related Links</h3>
            <div style="display: flex; flex-direction: column; gap: 8px; margin-bottom: 20px;">
                ${linksHtml}
            </div>
        `;
        
        return section;
    }
    
    // Safe close modal function
    function safeCloseModal(modal) {
        console.log('🚪 Safely closing modal');
        
        // Cleanup escape listener
        if (escapeHandler) {
            document.removeEventListener('keydown', escapeHandler);
            escapeHandler = null;
        }
        
        // Try to find and click the existing close button (look in backdrop or container)
        const backdrop = modal.closest('.event-modal-backdrop') || document.querySelector('.event-modal-backdrop');
        const searchArea = backdrop || modal;
        
        const closeButton = searchArea.querySelector('.event-modal-close, [aria-label*="Close"], [aria-label*="close"], button[class*="close"]');
        if (closeButton) {
            console.log('✅ Found close button, clicking it');
            closeButton.click();
        } else {
            console.warn('⚠️ Could not find close button, modal may remain open');
        }
    }
    
    // Enhance close buttons
    function enhanceCloseButtons(modal) {
        // Look for close buttons in the backdrop or container
        const backdrop = modal.closest('.event-modal-backdrop') || document.querySelector('.event-modal-backdrop');
        const searchArea = backdrop || modal;
        
        const closeButtons = searchArea.querySelectorAll('.event-modal-close, [aria-label*="Close"], [aria-label*="close"], button[class*="close"]');
        
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
        
        // Add backdrop click to close
        if (backdrop) {
            backdrop.addEventListener('click', (e) => {
                if (e.target === backdrop) {
                    safeCloseModal(modal);
                }
            });
        }
        
        console.log('✅ Enhanced close functionality');
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', waitForModal);
    } else {
        waitForModal();
    }
    
})();
