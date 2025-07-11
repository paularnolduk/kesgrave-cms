/**
 * Events Fix Script v4
 * Creates separate image sections within cards matching reference screenshot
 */

(function() {
    'use strict';
    
    console.log('🔧 Events fix v4 script loaded - separate image sections');
    
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
    
    // Create image section with overlays
    function createImageSection(eventData) {
        const imageSection = document.createElement('div');
        imageSection.className = 'event-image-section';
        imageSection.style.cssText = `
            position: relative;
            width: 100%;
            height: 200px;
            border-radius: 12px 12px 0 0;
            overflow: hidden;
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-color: #f8f9fa;
        `;
        
        // Set background image
        if (eventData.image) {
            imageSection.style.backgroundImage = `url('${eventData.image}')`;
        }
        
        // Add featured badge (top-left)
        if (eventData.featured) {
            const featuredBadge = document.createElement('div');
            featuredBadge.className = 'event-featured-badge';
            featuredBadge.textContent = 'FEATURED';
            featuredBadge.style.cssText = `
                position: absolute;
                top: 12px;
                left: 12px;
                padding: 6px 12px;
                border-radius: 16px;
                font-size: 0.7rem;
                font-weight: 700;
                text-transform: uppercase;
                color: white;
                background-color: #f39c12;
                z-index: 10;
                box-shadow: 0 2px 8px rgba(0,0,0,0.3);
                border: 2px solid #e67e22;
            `;
            imageSection.appendChild(featuredBadge);
        }
        
        // Add category tag (top-right)
        const categoryTag = document.createElement('div');
        categoryTag.className = 'event-category-tag';
        categoryTag.style.cssText = `
            position: absolute;
            top: 12px;
            right: 12px;
            padding: 6px 12px;
            border-radius: 16px;
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: uppercase;
            color: white;
            z-index: 10;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        `;
        
        // Determine category and color
        const title = eventData.title.toLowerCase();
        if (title.includes('meeting') || title.includes('council')) {
            categoryTag.textContent = 'COUNCIL';
            categoryTag.style.backgroundColor = '#3498db';
        } else if (title.includes('market') || title.includes('fair')) {
            categoryTag.textContent = 'COMMUNITY';
            categoryTag.style.backgroundColor = '#e74c3c';
        } else {
            categoryTag.textContent = 'EVENT';
            categoryTag.style.backgroundColor = '#2ecc71';
        }
        
        imageSection.appendChild(categoryTag);
        
        return imageSection;
    }
    
    // Apply new card structure to events
    function applyEventCardStructure(eventElements, eventsData) {
        console.log('🎨 Creating card structure for', eventElements.length, 'events...');
        
        eventElements.forEach((eventElement, index) => {
            const eventData = eventsData[index];
            if (!eventData) {
                console.warn(`⚠️ No data for event ${index}`);
                return;
            }
            
            console.log(`🖼️ Restructuring event ${index + 1}:`, eventData.title);
            
            // Find the parent card container
            let cardContainer = eventElement.closest('.event-card') || eventElement.parentElement;
            
            // Style the card container
            cardContainer.style.cssText = `
                position: relative;
                background: white;
                border-radius: 12px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                overflow: hidden;
                transition: transform 0.2s ease, box-shadow 0.2s ease;
                border: 1px solid rgba(0,0,0,0.08);
            `;
            
            // Add hover effect
            cardContainer.addEventListener('mouseenter', () => {
                cardContainer.style.transform = 'translateY(-2px)';
                cardContainer.style.boxShadow = '0 8px 24px rgba(0,0,0,0.15)';
            });
            
            cardContainer.addEventListener('mouseleave', () => {
                cardContainer.style.transform = 'translateY(0)';
                cardContainer.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)';
            });
            
            // Check if image section already exists
            let existingImageSection = cardContainer.querySelector('.event-image-section');
            if (!existingImageSection) {
                // Create and insert image section at the top
                const imageSection = createImageSection(eventData);
                cardContainer.insertBefore(imageSection, cardContainer.firstChild);
                
                // Style the content section
                eventElement.style.cssText = `
                    padding: 20px;
                    background: white;
                `;
                
                console.log(`✅ Added image section to event ${index + 1}`);
            }
        });
        
        console.log('🎉 Event card structure applied successfully!');
    }
    
    // Main function
    async function fixEvents() {
        try {
            console.log('🚀 Starting events fix v4 - separate image sections...');
            
            const eventElements = await waitForEvents();
            const eventsData = await fetchEventsData();
            
            if (eventsData.length === 0) {
                console.error('❌ No events data available');
                return;
            }
            
            applyEventCardStructure(eventElements, eventsData);
            
        } catch (error) {
            console.error('❌ Events fix v4 failed:', error);
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