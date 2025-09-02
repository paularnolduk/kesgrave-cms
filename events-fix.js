/**
 * Events Fix Script - Frontend Version
 * Enhances event cards with images, tags, and navigation functionality
 * ONLY runs on events pages to prevent admin interface conflicts.
 */

(function() {
    'use strict';
    
    console.log('🚀 Events Fix - Frontend Version Loading...');
    
    // CRITICAL: Only run on events page - prevent interference with admin pages
    if (!window.location.pathname.includes('/ktc-events') && 
        !window.location.pathname.includes('/events')) {
        console.log('ℹ️ Not on events page, skipping events fix');
        return;
    }
    
    // Additional check: Don't run on admin pages
    if (window.location.pathname.includes('/admin') || 
        window.location.pathname.includes('/cms') ||
        window.location.pathname.includes('/login')) {
        console.log('ℹ️ On admin page, skipping events fix');
        return;
    }
    
    console.log('✅ On events page, initializing events fix');
    
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
    
    // Wait for events to be rendered with better detection and timeout
    function waitForEvents() {
        return new Promise((resolve) => {
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
                const match = text.match(/(\\w+)\\s+(\\d{4})/);
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
                const existingContainers = eventElement.querySelectorAll('.event-image-container-frontend');
                existingContainers.forEach(container => container.remove());
                
                // Create image container with unique class
                const imageContainer = document.createElement('div');
                imageContainer.className = 'event-image-container-frontend';
                imageContainer.style.cssText = `
                    position: relative;
                    width: 100%;
                    height: ${CONFIG.IMAGE_HEIGHT};
                    border-radius: 8px;
                    overflow: hidden;
                    margin-bottom: 1rem;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                `;
                
                // Add background image if available
                if (eventData.image) {
                    imageContainer.style.backgroundImage = `url('${eventData.image}')`;
                    imageContainer.style.backgroundSize = 'cover';
                    imageContainer.style.backgroundPosition = 'center';
                    console.log(`✅ Set background image for event ${index + 1}: ${eventData.image}`);
                }
                
                // Add overlay for better text readability
                const overlay = document.createElement('div');
                overlay.style.cssText = `
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: linear-gradient(45deg, rgba(0,0,0,0.3), rgba(0,0,0,0.1));
                `;
                imageContainer.appendChild(overlay);
                
                // Add category tag if available
                if (eventData.category && eventData.category.name) {
                    const categoryTag = document.createElement('div');
                    categoryTag.textContent = eventData.category.name.toUpperCase();
                    categoryTag.style.cssText = `
                        position: absolute;
                        top: 10px;
                        left: 10px;
                        background: ${eventData.category.color || '#007bff'};
                        color: white;
                        padding: 4px 8px;
                        border-radius: 4px;
                        font-size: 0.75rem;
                        font-weight: bold;
                        z-index: 2;
                    `;
                    imageContainer.appendChild(categoryTag);
                }
                
                // Add featured badge if applicable
                if (eventData.featured) {
                    const featuredBadge = document.createElement('div');
                    featuredBadge.textContent = 'FEATURED';
                    featuredBadge.style.cssText = `
                        position: absolute;
                        top: 10px;
                        right: 10px;
                        background: #ff6b35;
                        color: white;
                        padding: 4px 8px;
                        border-radius: 4px;
                        font-size: 0.75rem;
                        font-weight: bold;
                        z-index: 2;
                    `;
                    imageContainer.appendChild(featuredBadge);
                }
                
                // Add past event badge if applicable
                if (eventData.is_past) {
                    const pastBadge = document.createElement('div');
                    pastBadge.textContent = 'PAST EVENT';
                    pastBadge.style.cssText = `
                        position: absolute;
                        bottom: 10px;
                        left: 10px;
                        background: rgba(108, 117, 125, 0.9);
                        color: white;
                        padding: 4px 8px;
                        border-radius: 4px;
                        font-size: 0.75rem;
                        font-weight: bold;
                        z-index: 2;
                    `;
                    imageContainer.appendChild(pastBadge);
                    
                    // Apply grayscale filter for past events
                    imageContainer.style.filter = 'grayscale(70%)';
                    imageContainer.style.opacity = '0.8';
                }
                
                // Insert image container at the beginning of the event element
                eventElement.insertBefore(imageContainer, eventElement.firstChild);
                
                console.log(`✅ Enhanced event ${index + 1} with image and styling`);
            });
            
        } catch (error) {
            console.error('❌ Error applying event data:', error);
        } finally {
            isProcessing = false;
        }
    }
    
    // Set up mutation observer for dynamic content changes
    function setupMutationObserver() {
        const observer = new MutationObserver((mutations) => {
            let shouldReprocess = false;
            
            mutations.forEach((mutation) => {
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    // Check if new event content was added
                    for (const node of mutation.addedNodes) {
                        if (node.nodeType === 1 && 
                            (node.tagName === 'ARTICLE' || node.querySelector('article'))) {
                            shouldReprocess = true;
                            break;
                        }
                    }
                }
            });
            
            if (shouldReprocess) {
                console.log('🔄 Content change detected, re-running events fix...');
                setTimeout(runEventsFix, 500); // Small delay to ensure content is fully loaded
            }
        });
        
        // Observe the main content area
        const contentArea = document.body;
        if (contentArea) {
            observer.observe(contentArea, {
                childList: true,
                subtree: true
            });
            console.log('👁️ Mutation observer set up for dynamic content');
        }
    }
    
    // Main events fix function
    async function runEventsFix() {
        try {
            console.log('🚀 Starting events fix...');
            
            // Wait for DOM to be ready
            await waitForDOM();
            
            // Wait for events to be rendered
            const eventElements = await waitForEvents();
            if (eventElements.length === 0) {
                console.warn('⚠️ No event elements found');
                return;
            }
            
            // Fetch events data
            const eventsData = await fetchEventsData();
            if (eventsData.length === 0) {
                console.warn('⚠️ No events data available');
                return;
            }
            
            // Apply event data to DOM
            applyEventData(eventElements, eventsData);
            
            console.log('🎉 Events fix complete!');
            
        } catch (error) {
            console.error('❌ Events fix failed:', error);
        }
    }
    
    // Initialize the events fix
    async function initEventsFix() {
        await runEventsFix();
        setupMutationObserver();
    }
    
    // Start the events fix
    initEventsFix();
    
})();