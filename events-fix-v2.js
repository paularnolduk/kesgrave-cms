/**
 * Events Fix Script v2
 * This script adds images to events without distorting the card layout
 */

(function() {
    'use strict';
    
    console.log('🔧 Events fix v2 script loaded');
    
    // Wait for DOM and events
    function waitForEvents() {
        return new Promise((resolve) => {
            const checkEvents = () => {
                const events = document.querySelectorAll('.event-card, .event-item, [class*="event"]');
                if (events.length > 0) {
                    console.log('✅ Found', events.length, 'event elements');
                    resolve(events);
                } else {
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
    
    // Apply images without distorting layout
    function applyEventImages(eventElements, eventsData) {
        console.log('🎨 Applying event images...');
        
        eventElements.forEach((eventElement, index) => {
            const eventData = eventsData[index];
            if (!eventData || !eventData.image) return;
            
            console.log(`🖼️ Adding image to event ${index + 1}:`, eventData.title);
            
            // Add image as background to the entire card with subtle overlay
            eventElement.style.backgroundImage = `linear-gradient(rgba(255, 255, 255, 0.9), rgba(255, 255, 255, 0.9)), url('${eventData.image}')`;
            eventElement.style.backgroundSize = 'cover';
            eventElement.style.backgroundPosition = 'center';
            eventElement.style.backgroundRepeat = 'no-repeat';
            
            // Add category tag in top-right corner
            const categoryTag = document.createElement('div');
            categoryTag.style.cssText = `
                position: absolute;
                top: 8px;
                right: 8px;
                background-color: #e74c3c;
                color: white;
                padding: 2px 8px;
                border-radius: 12px;
                font-size: 0.7rem;
                font-weight: 600;
                text-transform: uppercase;
                z-index: 10;
            `;
            
            // Determine category based on title
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
            
            // Make parent relative for positioning
            eventElement.style.position = 'relative';
            eventElement.appendChild(categoryTag);
            
            console.log(`✅ Applied image to event ${index + 1}`);
        });
        
        console.log('🎉 Events images applied!');
    }
    
    // Main function
    async function fixEvents() {
        try {
            console.log('🚀 Starting events fix v2...');
            
            const eventElements = await waitForEvents();
            const eventsData = await fetchEventsData();
            
            if (eventsData.length === 0) {
                console.error('❌ No events data available');
                return;
            }
            
            applyEventImages(eventElements, eventsData);
            
        } catch (error) {
            console.error('❌ Events fix failed:', error);
        }
    }
    
    // Run the fix
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', fixEvents);
    } else {
        fixEvents();
    }
    
})();