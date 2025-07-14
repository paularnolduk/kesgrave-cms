/**
 * Events Fix Script
 * This script patches the events section to properly display images and category tags
 * from the API data.
 */

(function() {
    'use strict';
    
    console.log('🔧 Final Events fix script loaded');
    
    // Only run on events page
    if (!window.location.pathname.includes('/ktc-events')) {
        console.log('ℹ️ Not on events page, skipping events fix');
        return;
    }
    
    console.log('✅ On events page, initializing events fix');
    
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
    
    // Wait for events to be rendered - improved detection
    function waitForEvents() {
        return new Promise((resolve) => {
            const checkEvents = () => {
                // Look for article elements that contain event content
                const articles = document.querySelectorAll('article');
                const eventArticles = Array.from(articles).filter(el => {
                    const text = el.textContent || '';
                    // Check for event-specific content
                    return text.includes('View Details') || 
                           text.includes('July 2025') || 
                           text.includes('November 2025') ||
                           text.includes('Annual Summer Fair') || 
                           text.includes('Kesgrave Market') ||
                           text.includes('Fireworks Night') ||
                           text.includes('Fun Day') ||
                           text.includes('Council Meeting');
                });
                
                if (eventArticles.length > 0) {
                    console.log('✅ Found', eventArticles.length, 'event elements');
                    resolve(eventArticles);
                } else {
                    console.log('⏳ Waiting for events...');
                    setTimeout(checkEvents, 200);
                }
            };
            checkEvents();
        });
    }
    
    // Get current month and year from the page
    function getCurrentMonthYear() {
        const monthElement = document.querySelector('h2, [class*="month"], [class*="title"]');
        if (monthElement) {
            const text = monthElement.textContent;
            const match = text.match(/(\w+)\s+(\d{4})/);
            if (match) {
                const [, month, year] = match;
                return { month, year };
            }
        }
        return { month: 'July', year: '2025' }; // Default
    }
    
    // Fetch events data from API with proper parameters
    async function fetchEventsData() {
        try {
            const { month, year } = getCurrentMonthYear();
            console.log(`📡 Fetching events data for ${month} ${year}...`);
            
            // Convert month name to number
            const monthMap = {
                'January': 1, 'February': 2, 'March': 3, 'April': 4,
                'May': 5, 'June': 6, 'July': 7, 'August': 8,
                'September': 9, 'October': 10, 'November': 11, 'December': 12
            };
            
            const monthNum = monthMap[month];
            const currentDate = new Date();
            const currentMonth = currentDate.getMonth() + 1;
            const currentYear = currentDate.getFullYear();
            
            // Check if this is a past month
            const isPastMonth = (parseInt(year) < currentYear) || 
                               (parseInt(year) === currentYear && monthNum < currentMonth);
            
            let url = '/api/events';
            const params = new URLSearchParams();
            
            if (monthNum) params.append('month', monthNum);
            if (year) params.append('year', year);
            if (isPastMonth) params.append('include_past', 'true');
            
            if (params.toString()) {
                url += '?' + params.toString();
            }
            
            console.log(`📡 API URL: ${url}`);
            const response = await fetch(url);
            const data = await response.json();
            console.log('✅ Events data loaded:', data.events.length, 'events');
            console.log('📊 Events data:', data.events);
            return data.events;
        } catch (error) {
            console.error('❌ Failed to fetch events data:', error);
            return [];
        }
    }
    
    // Apply event data to DOM elements
    function applyEventData(eventElements, eventsData) {
        console.log('🎨 Applying event data to DOM...');
        
        eventElements.forEach((eventElement, index) => {
            const eventData = eventsData[index];
            if (!eventData) {
                console.warn('⚠️ No data for event element', index);
                return;
            }
            
            console.log(`🖼️ Processing event ${index + 1}:`, eventData.title);
            
            // Remove any existing image containers added by previous runs
            const existingContainers = eventElement.querySelectorAll('.event-image-container');
            existingContainers.forEach(container => container.remove());
            
            // Create image container
            const imageContainer = document.createElement('div');
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
            
            // Set background image
            if (eventData.image) {
                const imageUrl = eventData.image;
                imageContainer.style.backgroundImage = `linear-gradient(rgba(0, 0, 0, 0.3), rgba(0, 0, 0, 0.3)), url('${imageUrl}')`;
                imageContainer.style.backgroundSize = 'cover';
                imageContainer.style.backgroundPosition = 'center';
                imageContainer.style.backgroundRepeat = 'no-repeat';
                console.log(`✅ Set background image for event ${index + 1}:`, imageUrl);
                
                // Add grayscale filter and past event badge for past events
                if (eventData.is_past) {
                    imageContainer.style.filter = 'grayscale(100%)';
                    addPastEventBadge(imageContainer);
                    console.log(`🕰️ Applied past event styling to: ${eventData.title}`);
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
            
            // Insert at the beginning of the event element
            eventElement.insertBefore(imageContainer, eventElement.firstChild);
        });
        
        console.log('🎉 Events fix complete!');
    }
    
    // Add category tag to image container
    function addCategoryTag(container, category) {
        const tag = document.createElement('div');
        tag.className = 'event-category-tag';
        tag.textContent = category.name.toUpperCase();
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
            console.log('🚀 Starting events fix...');
            
            // Wait for DOM and events
            await waitForDOM();
            const eventElements = await waitForEvents();
            
            // Fetch events data from API
            const eventsData = await fetchEventsData();
            
            if (eventsData.length === 0) {
                console.log('ℹ️ No events data available for this month');
                return;
            }
            
            // Apply the fix
            applyEventData(eventElements, eventsData);
            
        } catch (error) {
            console.error('❌ Events fix failed:', error);
        }
    }
    
    // Run the fix initially
    fixEvents();
    
    // Enhanced mutation observer for month navigation
    const observer = new MutationObserver((mutations) => {
        let shouldRerun = false;
        
        mutations.forEach((mutation) => {
            if (mutation.type === 'childList') {
                // Check for new article elements (new events loaded)
                const hasNewEvents = Array.from(mutation.addedNodes).some(node => {
                    return node.nodeType === 1 && (
                        node.tagName === 'ARTICLE' || 
                        node.querySelector && node.querySelector('article') ||
                        (node.textContent && node.textContent.includes('View Details'))
                    );
                });
                
                // Check for month/year changes
                const hasMonthChange = Array.from(mutation.addedNodes).some(node => {
                    return node.nodeType === 1 && (
                        (node.textContent && /\w+\s+\d{4}/.test(node.textContent)) ||
                        (node.querySelector && node.querySelector('h2, [class*="month"]'))
                    );
                });
                
                if (hasNewEvents || hasMonthChange) {
                    shouldRerun = true;
                }
            }
            
            // Check for text changes (month navigation)
            if (mutation.type === 'characterData' || mutation.type === 'childList') {
                const target = mutation.target;
                if (target.textContent && /\w+\s+\d{4}/.test(target.textContent)) {
                    shouldRerun = true;
                }
            }
        });
        
        if (shouldRerun) {
            console.log('🔄 Content change detected, re-running events fix...');
            setTimeout(fixEvents, 1000); // Give time for content to fully load
        }
    });
    
    // Observe the entire document for changes
    observer.observe(document.body, {
        childList: true,
        subtree: true,
        characterData: true
    });
    
    // Also listen for popstate events (browser navigation)
    window.addEventListener('popstate', () => {
        console.log('🔄 Navigation detected, re-running events fix...');
        setTimeout(fixEvents, 1000);
    });
    
    console.log('👀 Events fix observer initialized');
    
})();