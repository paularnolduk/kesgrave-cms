/**
 * Events Fix Script
 * This script patches the events section to properly display images and category tags
 * from the API data.
 */

(function() {
    'use strict';
    
    console.log('🔧 Updated Events fix script loaded');
    
    // Wait for DOM to be ready
    function waitForDOM() {
        return new Promise((resolve) => {
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', resolve);
            } else {
                resolve();
            }
        });
    }
    
    // Wait for events to be rendered - updated selectors
    function waitForEvents() {
        return new Promise((resolve) => {
            const checkEvents = () => {
                // Look for article elements or any elements containing event content
                const events = document.querySelectorAll('article, .event-card, .event-item, [class*="event"]');
                const eventArticles = Array.from(events).filter(el => {
                    const text = el.textContent || '';
                    return text.includes('July 2025') || text.includes('View Details') || 
                           text.includes('Annual Summer Fair') || text.includes('Kesgrave Market');
                });
                
                if (eventArticles.length > 0) {
                    console.log('✅ Found', eventArticles.length, 'event elements');
                    resolve(eventArticles);
                } else {
                    console.log('⏳ Waiting for events...');
                    setTimeout(checkEvents, 100);
                }
            };
            checkEvents();
        });
    }
    
    // Fetch events data from the NEW API endpoint
    async function fetchEventsData() {
        try {
            console.log('📡 Fetching events data from /api/events...');
            const response = await fetch('/api/events');
            const data = await response.json();
            console.log('✅ Events data loaded:', data.events.length, 'events');
            return data.events; // Return the events array from the response
        } catch (error) {
            console.error('❌ Failed to fetch events data:', error);
            return [];
        }
    }
    
    // Apply event data to DOM elements
    function applyEventData(eventElements, eventsData) {
        console.log('🎨 Applying event data to DOM...');
        
        // Try to match events by title
        eventElements.forEach((eventElement, index) => {
            const eventData = eventsData[index];
            if (!eventData) {
                console.warn('⚠️ No data for event element', index);
                return;
            }
            
            console.log(`🖼️ Processing event ${index + 1}:`, eventData.title);
            
            // Find or create image container
            let imageContainer = eventElement.querySelector('.event-image, .event-img, [class*="image"]');
            if (!imageContainer) {
                // Create image container if it doesn't exist
                imageContainer = document.createElement('div');
                imageContainer.className = 'event-image-container';
                imageContainer.style.cssText = `
                    position: relative;
                    width: 100%;
                    height: 200px;
                    border-radius: 8px;
                    overflow: hidden;
                    margin-bottom: 1rem;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                `;
                eventElement.insertBefore(imageContainer, eventElement.firstChild);
            }
            
            // Set background image
            if (eventData.image) {
                const imageUrl = eventData.image;
                imageContainer.style.backgroundImage = `linear-gradient(rgba(0, 0, 0, 0.3), rgba(0, 0, 0, 0.3)), url('${imageUrl}')`;
                imageContainer.style.backgroundSize = 'cover';
                imageContainer.style.backgroundPosition = 'center';
                imageContainer.style.backgroundRepeat = 'no-repeat';
                console.log(`✅ Set background image for event ${index + 1}:`, imageUrl);
                
                // Add grayscale filter for past events
                if (eventData.is_past) {
                    imageContainer.style.filter = 'grayscale(100%)';
                    addPastEventBadge(imageContainer);
                }
                
                // Add category tags if available
                if (eventData.category) {
                    addCategoryTag(imageContainer, eventData.category);
                }
                
                // Add featured tag if featured
                if (eventData.featured) {
                    addFeaturedTag(imageContainer);
                }
            }
        });
        
        console.log('🎉 Events fix complete!');
    }
    
    // Add category tag to image container
    function addCategoryTag(container, category) {
        const tag = document.createElement('div');
        tag.className = 'event-category-tag';
        tag.textContent = category.name;
        tag.style.cssText = `
            position: absolute;
            top: 12px;
            left: 12px;
            background-color: ${category.color};
            color: white;
            padding: 4px 12px;
            border-radius: 16px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            z-index: 10;
        `;
        
        // Add icon if available
        if (category.icon) {
            const icon = document.createElement('i');
            icon.className = category.icon;
            icon.style.marginRight = '6px';
            tag.insertBefore(icon, tag.firstChild);
        }
        
        container.appendChild(tag);
        console.log(`✅ Added category tag: ${category.name}`);
    }
    
    // Add featured tag
    function addFeaturedTag(container) {
        const tag = document.createElement('div');
        tag.className = 'event-featured-tag';
        tag.textContent = 'FEATURED';
        tag.style.cssText = `
            position: absolute;
            top: 12px;
            right: 12px;
            background-color: #f39c12;
            color: white;
            padding: 4px 12px;
            border-radius: 16px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            z-index: 10;
        `;
        
        container.appendChild(tag);
        console.log('✅ Added featured tag');
    }
    
    // Add past event badge
    function addPastEventBadge(container) {
        const badge = document.createElement('div');
        badge.className = 'event-past-badge';
        badge.textContent = 'Past Event';
        badge.style.cssText = `
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background-color: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            z-index: 15;
        `;
        
        container.appendChild(badge);
        console.log('✅ Added past event badge');
    }
    
    // Main function
    async function fixEvents() {
        try {
            console.log('🚀 Starting updated events fix...');
            
            // Wait for DOM and events
            await waitForDOM();
            const eventElements = await waitForEvents();
            
            // Fetch events data from the new API
            const eventsData = await fetchEventsData();
            
            if (eventsData.length === 0) {
                console.error('❌ No events data available');
                return;
            }
            
            // Apply the fix
            applyEventData(eventElements, eventsData);
            
        } catch (error) {
            console.error('❌ Events fix failed:', error);
        }
    }
    
    // Run the fix
    fixEvents();
    
    // Also run the fix when the page becomes visible (in case of navigation)
    document.addEventListener('visibilitychange', () => {
        if (!document.hidden) {
            setTimeout(fixEvents, 500);
        }
    });
    
    // Run fix when navigating between months
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                // Check if new event elements were added
                const hasEventContent = Array.from(mutation.addedNodes).some(node => {
                    return node.nodeType === 1 && (
                        node.tagName === 'ARTICLE' || 
                        node.textContent?.includes('View Details')
                    );
                });
                
                if (hasEventContent) {
                    console.log('🔄 New events detected, re-running fix...');
                    setTimeout(fixEvents, 500);
                }
            }
        });
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    
})();
