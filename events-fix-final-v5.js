(function() {
    'use strict';
    
    console.log('🚀 Events Fix v5 - Final Version Loading...');
    
    // Only run on events page
    if (!window.location.pathname.includes('/ktc-events')) {
        console.log('ℹ️ Not on events page, skipping events fix');
        return;
    }
    
    console.log('✅ On events page, initializing events fix v5');
    
    // Configuration
    const CONFIG = {
        API_BASE: '/api/events',
        RETRY_DELAY: 300,
        MAX_RETRIES: 20,
        IMAGE_HEIGHT: '200px'
    };
    
    // State management
    let isProcessing = false;
    let currentMonth = null;
    let currentYear = null;
    
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
    
    // Wait for events to be rendered with better detection
    function waitForEvents() {
        return new Promise((resolve, reject) => {
            let attempts = 0;
            
            const checkEvents = () => {
                attempts++;
                
                if (attempts > CONFIG.MAX_RETRIES) {
                    console.warn('⚠️ Max retries reached, proceeding anyway');
                    resolve([]);
                    return;
                }
                
                // Look for article elements that contain event content
                const articles = document.querySelectorAll('article');
                const eventArticles = Array.from(articles).filter(el => {
                    const text = el.textContent || '';
                    // Check for event-specific content patterns
                    return (text.includes('View Details') && 
                           (text.includes('2025') || text.includes('2024') || text.includes('2026'))) ||
                           text.includes('Annual Summer Fair') || 
                           text.includes('Kesgrave Market') ||
                           text.includes('Fireworks Night');
                });
                
                if (eventArticles.length > 0) {
                    console.log(`✅ Found ${eventArticles.length} event elements after ${attempts} attempts`);
                    resolve(eventArticles);
                } else {
                    console.log(`⏳ Attempt ${attempts}/${CONFIG.MAX_RETRIES}: Waiting for events...`);
                    setTimeout(checkEvents, CONFIG.RETRY_DELAY);
                }
            };
            
            checkEvents();
        });
    }
    
    // Get current month and year from the page
    function getCurrentMonthYear() {
        // Try multiple selectors to find month/year
        const selectors = [
            'h2:contains("2025")',
            'h2:contains("2024")', 
            '[class*="month"]',
            '[class*="title"]',
            'h1, h2, h3'
        ];
        
        for (const selector of selectors) {
            const elements = document.querySelectorAll(selector.replace(':contains', ''));
            for (const element of elements) {
                const text = element.textContent;
                const match = text.match(/(\w+)\s+(\d{4})/);
                if (match) {
                    const [, month, year] = match;
                    console.log(`📅 Detected month/year: ${month} ${year}`);
                    return { month, year };
                }
            }
        }
        
        // Fallback to current date
        const now = new Date();
        const months = ['January', 'February', 'March', 'April', 'May', 'June',
                       'July', 'August', 'September', 'October', 'November', 'December'];
        return { 
            month: months[now.getMonth()], 
            year: now.getFullYear().toString() 
        };
    }
    
    // Fetch events data from API with proper parameters
    async function fetchEventsData() {
        try {
            const { month, year } = getCurrentMonthYear();
            currentMonth = month;
            currentYear = year;
            
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
            
            let url = CONFIG.API_BASE;
            const params = new URLSearchParams();
            
            if (monthNum) params.append('month', monthNum);
            if (year) params.append('year', year);
            if (isPastMonth) {
                params.append('include_past', 'true');
                console.log('📜 Including past events for historic month');
            }
            
            if (params.toString()) {
                url += '?' + params.toString();
            }
            
            console.log(`📡 API URL: ${url}`);
            const response = await fetch(url);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log(`✅ Events data loaded: ${data.events?.length || 0} events`);
            
            if (data.events && data.events.length > 0) {
                console.log('📊 Sample event data:', data.events[0]);
            }
            
            return data.events || [];
        } catch (error) {
            console.error('❌ Failed to fetch events data:', error);
            return [];
        }
    }
    
    // Apply event data to DOM elements
    function applyEventData(eventElements, eventsData) {
        if (isProcessing) {
            console.log('⏸️ Already processing, skipping...');
            return;
        }
        
        isProcessing = true;
        console.log('🎨 Applying event data to DOM...');
        
        try {
            eventElements.forEach((eventElement, index) => {
                const eventData = eventsData[index];
                if (!eventData) {
                    console.warn(`⚠️ No data for event element ${index}`);
                    return;
                }
                
                console.log(`🖼️ Processing event ${index + 1}: ${eventData.title}`);
                
                // Remove any existing image containers to prevent duplicates
                const existingContainers = eventElement.querySelectorAll('.event-image-container-v5');
                existingContainers.forEach(container => container.remove());
                
                // Create image container with unique class
                const imageContainer = document.createElement('div');
                imageContainer.className = 'event-image-container-v5';
                imageContainer.style.cssText = `
                    position: relative;
                    width: 100%;
                    height: ${CONFIG.IMAGE_HEIGHT};
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
                    console.log(`✅ Set background image for event ${index + 1}: ${imageUrl}`);
                    
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
                } else {
                    console.warn(`⚠️ No image for event: ${eventData.title}`);
                }
                
                // Insert at the beginning of the event element
                eventElement.insertBefore(imageContainer, eventElement.firstChild);
            });
            
            console.log('🎉 Events fix v5 complete!');
        } finally {
            isProcessing = false;
        }
    }
    
    // Add category tag to image container
    function addCategoryTag(container, category) {
        const tag = document.createElement('div');
        tag.className = 'event-category-tag-v5';
        tag.textContent = category.name.toUpperCase();
        tag.style.cssText = `
            position: absolute;
            top: 12px;
            left: 12px;
            background-color: ${category.color || '#3498db'};
            color: white;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            z-index: 2;
        `;
        container.appendChild(tag);
        console.log(`🏷️ Added category tag: ${category.name}`);
    }
    
    // Add featured tag to image container
    function addFeaturedTag(container) {
        const tag = document.createElement('div');
        tag.className = 'event-featured-tag-v5';
        tag.textContent = 'FEATURED';
        tag.style.cssText = `
            position: absolute;
            top: 12px;
            right: 12px;
            background-color: #f39c12;
            color: white;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            z-index: 2;
        `;
        container.appendChild(tag);
        console.log('⭐ Added featured tag');
    }
    
    // Add past event badge to image container
    function addPastEventBadge(container) {
        const badge = document.createElement('div');
        badge.className = 'event-past-badge-v5';
        badge.textContent = 'PAST EVENT';
        badge.style.cssText = `
            position: absolute;
            bottom: 12px;
            left: 12px;
            background-color: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 6px 12px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            z-index: 2;
        `;
        container.appendChild(badge);
        console.log('🕰️ Added past event badge');
    }
    
    // Main initialization function
    async function initializeEventsFix() {
        try {
            console.log('🔄 Initializing events fix v5...');
            
            // Wait for DOM
            await waitForDOM();
            console.log('✅ DOM ready');
            
            // Wait for events to be rendered
            const eventElements = await waitForEvents();
            
            if (eventElements.length === 0) {
                console.log('ℹ️ No event elements found, nothing to fix');
                return;
            }
            
            // Fetch events data
            const eventsData = await fetchEventsData();
            
            if (eventsData.length === 0) {
                console.log('ℹ️ No events data received from API');
                return;
            }
            
            // Apply the fixes
            applyEventData(eventElements, eventsData);
            
        } catch (error) {
            console.error('❌ Events fix v5 failed:', error);
        }
    }
    
    // Set up mutation observer for dynamic content changes
    function setupMutationObserver() {
        const observer = new MutationObserver((mutations) => {
            let shouldRerun = false;
            
            mutations.forEach((mutation) => {
                // Check if new event content was added
                if (mutation.type === 'childList') {
                    const addedNodes = Array.from(mutation.addedNodes);
                    const hasEventContent = addedNodes.some(node => {
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            const text = node.textContent || '';
                            return text.includes('View Details') || 
                                   text.includes('events found') ||
                                   text.includes('2025') ||
                                   text.includes('2024');
                        }
                        return false;
                    });
                    
                    if (hasEventContent) {
                        shouldRerun = true;
                    }
                }
            });
            
            if (shouldRerun) {
                console.log('🔄 Content change detected, re-running events fix...');
                setTimeout(initializeEventsFix, 500);
            }
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
        
        console.log('👁️ Mutation observer set up for dynamic content');
    }
    
    // Initialize everything
    console.log('🚀 Starting events fix v5 initialization...');
    initializeEventsFix();
    setupMutationObserver();
    
    // Also run on hash changes (for navigation)
    window.addEventListener('hashchange', () => {
        console.log('🔄 Hash change detected, re-running events fix...');
        setTimeout(initializeEventsFix, 500);
    });
    
    console.log('✅ Events fix v5 setup complete!');
    
})();
