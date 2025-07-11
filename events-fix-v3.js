/**
 * Events Fix Script v3
 * Targeted fix using correct event-content selector
 */

(function() {
    'use strict';
    
    console.log('🔧 Events fix v3 script loaded');
    
    // Wait for events to be rendered
    function waitForEvents() {
        return new Promise((resolve) => {
            const checkEvents = () => {
                const events = document.querySelectorAll('.event-content');
                if (events.length > 0) {
                    console.log('✅ Found', events.length, 'event-content elements');
                    resolve(events);
                } else {
                    console.log('⏳ Waiting for events...');
                    setTimeout(checkEvents, 100);
                }
            };
            checkEvents();
        });
    }
    
    // Fetch events data
    async function fetchEventsData() {
        try {
            const response = await fetch('/api/homepage/events');
            const data = await response.json();
            console.log('✅ Events data loaded:', data.length, 'events');
            return data;
        } catch (error) {
            console.error('❌ Failed to fetch events data:', error);
            return [];
        }
    }
    
    // Apply images to event cards
    function applyEventImages(eventElements, eventsData) {
        console.log('🎨 Applying event images to', eventElements.length, 'elements...');
        
        eventElements.forEach((eventElement, index) => {
            const eventData = eventsData[index];
            if (!eventData) {
                console.warn(`⚠️ No data for event ${index}`);
                return;
            }
            
            console.log(`🖼️ Processing event ${index + 1}:`, eventData.title);
            
            // Find the parent card container
            let cardContainer = eventElement.closest('.event-card') || eventElement.parentElement;
            
            // Apply background image with light overlay for readability
            if (eventData.image) {
                cardContainer.style.backgroundImage = `linear-gradient(rgba(255, 255, 255, 0.85), rgba(255, 255, 255, 0.85)), url('${eventData.image}')`;
                cardContainer.style.backgroundSize = 'cover';
                cardContainer.style.backgroundPosition = 'center';
                cardContainer.style.backgroundRepeat = 'no-repeat';
                cardContainer.style.position = 'relative';
                
                console.log(`✅ Applied background image to event ${index + 1}`);
                
                // Add a subtle border to make the image more visible
                cardContainer.style.border = '1px solid rgba(0,0,0,0.1)';
                cardContainer.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
            }
            
            // Update or add category tag
            let existingTag = cardContainer.querySelector('.event-category-tag');
            if (!existingTag) {
                const categoryTag = document.createElement('div');
                categoryTag.className = 'event-category-tag';
                categoryTag.style.cssText = `
                    position: absolute;
                    top: 12px;
                    right: 12px;
                    padding: 4px 10px;
                    border-radius: 12px;
                    font-size: 0.7rem;
                    font-weight: 600;
                    text-transform: uppercase;
                    color: white;
                    z-index: 10;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                `;
                
                // Determine category and color based on title
                const title = eventData.title.toLowerCase();
                if (title.includes('meeting') || title.includes('council')) {
                    categoryTag.textContent = 'Council';
                    categoryTag.style.backgroundColor = '#3498db';
                } else if (title.includes('market') || title.includes('fair')) {
                    categoryTag.textContent = 'Community';
                    categoryTag.style.backgroundColor = '#e74c3c';
                } else {
                    categoryTag.textContent = 'Event';
                    categoryTag.style.backgroundColor = '#2ecc71';
                }
                
                cardContainer.appendChild(categoryTag);
                console.log(`✅ Added category tag to event ${index + 1}`);
            }
        });
        
        console.log('🎉 Events images applied successfully!');
    }
    
    // Main function
    async function fixEvents() {
        try {
            console.log('🚀 Starting events fix v3...');
            
            const eventElements = await waitForEvents();
            const eventsData = await fetchEventsData();
            
            if (eventsData.length === 0) {
                console.error('❌ No events data available');
                return;
            }
            
            applyEventImages(eventElements, eventsData);
            
        } catch (error) {
            console.error('❌ Events fix v3 failed:', error);
        }
    }
    
    // Run the fix when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', fixEvents);
    } else {
        fixEvents();
    }
    
    // Also run when page becomes visible
    document.addEventListener('visibilitychange', () => {
        if (!document.hidden) {
            setTimeout(fixEvents, 500);
        }
    });
    
})();
