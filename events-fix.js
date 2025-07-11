/**
 * Events Fix Script
 * This script patches the events section to properly display images and category tags
 * from the API data.
 */

(function() {
    'use strict';
    
    console.log('🔧 Events fix script loaded');
    
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
    
    // Wait for events to be rendered
    function waitForEvents() {
        return new Promise((resolve) => {
            const checkEvents = () => {
                const events = document.querySelectorAll('.event-card, .event-item, [class*="event"]');
                if (events.length > 0) {
                    console.log('✅ Found', events.length, 'event elements');
                    resolve(events);
                } else {
                    console.log('⏳ Waiting for events...');
                    setTimeout(checkEvents, 100);
                }
            };
            checkEvents();
        });
    }
    
    // Fetch events data from API
    async function fetchEventsData() {
        try {
            console.log('📡 Fetching events data...');
            const response = await fetch('/api/homepage/events');
            const data = await response.json();
            console.log('✅ Events data loaded:', data.length, 'events');
            return data;
        } catch (error) {
            console.error('❌ Failed to fetch events data:', error);
            return [];
        }
    }
    
    // Fetch event categories data
    async function fetchEventCategories() {
        try {
            console.log('📡 Fetching event categories...');
            const response = await fetch('/api/event-categories');
            const data = await response.json();
            console.log('✅ Event categories loaded:', data.length, 'categories');
            return data;
        } catch (error) {
            console.error('❌ Failed to fetch event categories:', error);
            return [];
        }
    }
    
    // Apply event data to DOM elements
    function applyEventData(eventElements, eventsData, categories) {
        console.log('🎨 Applying event data to DOM...');
        
        // Try to match events by title or content
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
                
                // Add category tags if available
                if (eventData.category_id && categories.length > 0) {
                    const category = categories.find(cat => cat.id === eventData.category_id);
                    if (category) {
                        addCategoryTag(imageContainer, category);
                    }
                }
                
                // If no specific category, add a default tag based on event type
                if (!eventData.category_id) {
                    // Determine category based on title or description
                    let defaultCategory = null;
                    const title = eventData.title.toLowerCase();
                    
                    if (title.includes('meeting') || title.includes('council')) {
                        defaultCategory = { name: 'Council Meeting', color: '#3498db', icon: 'fas fa-gavel' };
                    } else if (title.includes('market') || title.includes('fair')) {
                        defaultCategory = { name: 'Community Event', color: '#e74c3c', icon: 'fas fa-users' };
                    } else if (title.includes('sport') || title.includes('fun') || title.includes('fireworks')) {
                        defaultCategory = { name: 'Recreation', color: '#2ecc71', icon: 'fas fa-star' };
                    }
                    
                    if (defaultCategory) {
                        addCategoryTag(imageContainer, defaultCategory);
                    }
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
    
    // Main function
    async function fixEvents() {
        try {
            console.log('🚀 Starting events fix...');
            
            // Wait for DOM and events
            await waitForDOM();
            const eventElements = await waitForEvents();
            
            // Fetch events data and categories
            const [eventsData, categories] = await Promise.all([
                fetchEventsData(),
                fetchEventCategories()
            ]);
            
            if (eventsData.length === 0) {
                console.error('❌ No events data available');
                return;
            }
            
            // Apply the fix
            applyEventData(eventElements, eventsData, categories);
            
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
    
})();