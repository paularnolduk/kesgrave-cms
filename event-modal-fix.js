/**
 * Event Modal Fix Script
 * Enhances event modal with images, tags, content sections, and keyboard support
 */

(function() {
    'use strict';
    
    console.log('🔧 Event modal fix script loaded');
    
    let currentEventData = null;
    
    // Wait for modal to appear
    function waitForModal() {
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === 1 && (node.classList?.contains('modal') || node.querySelector?.('.modal'))) {
                        console.log('✅ Modal detected, enhancing...');
                        enhanceModal(node.classList?.contains('modal') ? node : node.querySelector('.modal'));
                    }
                });
            });
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
        
        // Also check for existing modals
        const existingModal = document.querySelector('.modal');
        if (existingModal) {
            enhanceModal(existingModal);
        }
    }
    
    // Fetch event details
    async function fetchEventDetails(eventId) {
        try {
            const response = await fetch(`/api/events/${eventId}`);
            if (response.ok) {
                const eventData = await response.json();
                console.log('✅ Event details loaded:', eventData);
                return eventData;
            } else {
                console.warn('⚠️ Event details API not available, using basic data');
                return null;
            }
        } catch (error) {
            console.warn('⚠️ Failed to fetch event details:', error);
            return null;
        }
    }
    
    // Get event data from homepage API
    async function getEventFromHomepage(eventId) {
        try {
            const response = await fetch('/api/homepage/events');
            if (response.ok) {
                const events = await response.json();
                const event = events.find(e => e.id === parseInt(eventId));
                console.log('✅ Event found in homepage data:', event);
                return event;
            }
        } catch (error) {
            console.warn('⚠️ Failed to fetch homepage events:', error);
        }
        return null;
    }
    
    // Extract event ID from modal content
    function extractEventId(modal) {
        // Try to find event ID in modal content or data attributes
        const eventIdElement = modal.querySelector('[data-event-id]');
        if (eventIdElement) {
            return eventIdElement.getAttribute('data-event-id');
        }
        
        // Try to extract from URL or other sources
        const titleElement = modal.querySelector('h2, h3, .modal-title');
        if (titleElement) {
            const title = titleElement.textContent.trim();
            console.log('🔍 Looking for event with title:', title);
            // We'll need to match this with our events data
            return title;
        }
        
        return null;
    }
    
    // Enhance modal with images and content
    async function enhanceModal(modal) {
        if (!modal || modal.hasAttribute('data-enhanced')) {
            return;
        }
        
        modal.setAttribute('data-enhanced', 'true');
        console.log('🎨 Enhancing modal...');
        
        // Add escape key handler
        const handleEscape = (e) => {
            if (e.key === 'Escape') {
                closeModal(modal);
            }
        };
        
        document.addEventListener('keydown', handleEscape);
        
        // Store cleanup function
        modal._cleanupEscape = () => {
            document.removeEventListener('keydown', handleEscape);
        };
        
        // Try to get event ID and data
        const eventId = extractEventId(modal);
        if (eventId) {
            let eventData = await fetchEventDetails(eventId);
            if (!eventData) {
                eventData = await getEventFromHomepage(eventId);
            }
            
            if (eventData) {
                currentEventData = eventData;
                addEventImage(modal, eventData);
                addEventTags(modal, eventData);
                addContentSections(modal, eventData);
            }
        }
        
        // Enhance close functionality
        enhanceCloseButtons(modal);
    }
    
    // Add event image to modal
    function addEventImage(modal, eventData) {
        if (!eventData.image) return;
        
        const modalContent = modal.querySelector('.modal-content, .modal-body');
        if (!modalContent) return;
        
        // Check if image already exists
        if (modal.querySelector('.event-modal-image')) return;
        
        const imageContainer = document.createElement('div');
        imageContainer.className = 'event-modal-image';
        imageContainer.style.cssText = `
            width: 100%;
            height: 200px;
            background-image: url('${eventData.image}');
            background-size: cover;
            background-position: center;
            border-radius: 8px;
            margin-bottom: 20px;
            position: relative;
            overflow: hidden;
        `;
        
        // Add featured badge if applicable
        if (eventData.featured) {
            const featuredBadge = document.createElement('div');
            featuredBadge.className = 'event-modal-featured-badge';
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
            imageContainer.appendChild(featuredBadge);
        }
        
        // Insert at the beginning of modal content
        modalContent.insertBefore(imageContainer, modalContent.firstChild);
        console.log('✅ Added event image to modal');
    }
    
    // Add event tags/categories
    function addEventTags(modal, eventData) {
        const modalContent = modal.querySelector('.modal-content, .modal-body');
        if (!modalContent) return;
        
        // Check if tags already exist
        if (modal.querySelector('.event-modal-tags')) return;
        
        const tagsContainer = document.createElement('div');
        tagsContainer.className = 'event-modal-tags';
        tagsContainer.style.cssText = `
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 16px;
        `;
        
        // Determine categories based on title
        const categories = [];
        const title = eventData.title.toLowerCase();
        
        if (title.includes('meeting') || title.includes('council')) {
            categories.push({ name: 'COUNCIL', color: '#3498db' });
        } else if (title.includes('market') || title.includes('fair')) {
            categories.push({ name: 'COMMUNITY', color: '#e74c3c' });
        } else {
            categories.push({ name: 'EVENT', color: '#2ecc71' });
        }
        
        categories.forEach(category => {
            const tag = document.createElement('span');
            tag.className = 'event-modal-tag';
            tag.textContent = category.name;
            tag.style.cssText = `
                padding: 4px 12px;
                border-radius: 12px;
                font-size: 0.7rem;
                font-weight: 600;
                text-transform: uppercase;
                color: white;
                background-color: ${category.color};
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            `;
            tagsContainer.appendChild(tag);
        });
        
        // Insert after image or at beginning
        const imageContainer = modal.querySelector('.event-modal-image');
        if (imageContainer) {
            imageContainer.parentNode.insertBefore(tagsContainer, imageContainer.nextSibling);
        } else {
            modalContent.insertBefore(tagsContainer, modalContent.firstChild);
        }
        
        console.log('✅ Added event tags to modal');
    }
    
    // Add content sections
    function addContentSections(modal, eventData) {
        const modalContent = modal.querySelector('.modal-content, .modal-body');
        if (!modalContent) return;
        
        // Check if sections already exist
        if (modal.querySelector('.event-modal-sections')) return;
        
        const sectionsContainer = document.createElement('div');
        sectionsContainer.className = 'event-modal-sections';
        sectionsContainer.style.cssText = `
            margin-top: 24px;
            border-top: 1px solid #e5e7eb;
            padding-top: 20px;
        `;
        
        // Event Details Section
        const detailsSection = createSection('Event Details', [
            { label: 'Date', value: formatDate(eventData.date) },
            { label: 'Location', value: eventData.location },
            { label: 'Description', value: eventData.description }
        ]);
        sectionsContainer.appendChild(detailsSection);
        
        // Quick Actions Section
        const actionsSection = createActionsSection(eventData);
        sectionsContainer.appendChild(actionsSection);
        
        // Related Links Section (if available)
        if (eventData.website_url || eventData.booking_url) {
            const linksSection = createLinksSection(eventData);
            sectionsContainer.appendChild(linksSection);
        }
        
        modalContent.appendChild(sectionsContainer);
        console.log('✅ Added content sections to modal');
    }
    
    // Create a content section
    function createSection(title, items) {
        const section = document.createElement('div');
        section.className = 'event-modal-section';
        section.style.cssText = `
            margin-bottom: 20px;
        `;
        
        const sectionTitle = document.createElement('h4');
        sectionTitle.textContent = title;
        sectionTitle.style.cssText = `
            font-size: 1.1rem;
            font-weight: 600;
            color: #374151;
            margin-bottom: 12px;
            border-bottom: 2px solid #10b981;
            padding-bottom: 4px;
        `;
        section.appendChild(sectionTitle);
        
        items.forEach(item => {
            if (item.value) {
                const itemElement = document.createElement('div');
                itemElement.style.cssText = `
                    margin-bottom: 8px;
                    display: flex;
                    flex-wrap: wrap;
                `;
                
                const label = document.createElement('span');
                label.textContent = item.label + ': ';
                label.style.cssText = `
                    font-weight: 600;
                    color: #6b7280;
                    margin-right: 8px;
                `;
                
                const value = document.createElement('span');
                value.textContent = item.value;
                value.style.cssText = `
                    color: #374151;
                `;
                
                itemElement.appendChild(label);
                itemElement.appendChild(value);
                section.appendChild(itemElement);
            }
        });
        
        return section;
    }
    
    // Create actions section
    function createActionsSection(eventData) {
        const section = document.createElement('div');
        section.className = 'event-modal-actions';
        section.style.cssText = `
            margin-bottom: 20px;
        `;
        
        const sectionTitle = document.createElement('h4');
        sectionTitle.textContent = 'Quick Actions';
        sectionTitle.style.cssText = `
            font-size: 1.1rem;
            font-weight: 600;
            color: #374151;
            margin-bottom: 12px;
            border-bottom: 2px solid #10b981;
            padding-bottom: 4px;
        `;
        section.appendChild(sectionTitle);
        
        const actionsGrid = document.createElement('div');
        actionsGrid.style.cssText = `
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 12px;
        `;
        
        // View on Map action
        if (eventData.location) {
            const mapButton = createActionButton(
                '📍 View on Map',
                `https://www.google.com/maps/search/${encodeURIComponent(eventData.location)}`,
                '#3b82f6'
            );
            actionsGrid.appendChild(mapButton);
        }
        
        // Add to Calendar action
        const calendarButton = createActionButton(
            '📅 Add to Calendar',
            createCalendarLink(eventData),
            '#10b981'
        );
        actionsGrid.appendChild(calendarButton);
        
        // Share Event action
        const shareButton = createActionButton(
            '🔗 Share Event',
            '#',
            '#8b5cf6'
        );
        shareButton.addEventListener('click', (e) => {
            e.preventDefault();
            shareEvent(eventData);
        });
        actionsGrid.appendChild(shareButton);
        
        section.appendChild(actionsGrid);
        return section;
    }
    
    // Create links section
    function createLinksSection(eventData) {
        const section = document.createElement('div');
        section.className = 'event-modal-links';
        section.style.cssText = `
            margin-bottom: 20px;
        `;
        
        const sectionTitle = document.createElement('h4');
        sectionTitle.textContent = 'Related Links';
        sectionTitle.style.cssText = `
            font-size: 1.1rem;
            font-weight: 600;
            color: #374151;
            margin-bottom: 12px;
            border-bottom: 2px solid #10b981;
            padding-bottom: 4px;
        `;
        section.appendChild(sectionTitle);
        
        const linksGrid = document.createElement('div');
        linksGrid.style.cssText = `
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 12px;
        `;
        
        if (eventData.website_url) {
            const websiteButton = createActionButton(
                '🌐 Event Website',
                eventData.website_url,
                '#6366f1'
            );
            linksGrid.appendChild(websiteButton);
        }
        
        if (eventData.booking_url) {
            const bookingButton = createActionButton(
                '🎫 Book Now',
                eventData.booking_url,
                '#ef4444'
            );
            linksGrid.appendChild(bookingButton);
        }
        
        section.appendChild(linksGrid);
        return section;
    }
    
    // Create action button
    function createActionButton(text, href, color) {
        const button = document.createElement('a');
        button.href = href;
        button.target = '_blank';
        button.rel = 'noopener noreferrer';
        button.textContent = text;
        button.style.cssText = `
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 10px 16px;
            background-color: ${color};
            color: white;
            text-decoration: none;
            border-radius: 8px;
            font-size: 0.9rem;
            font-weight: 500;
            transition: all 0.2s ease;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        `;
        
        button.addEventListener('mouseenter', () => {
            button.style.transform = 'translateY(-1px)';
            button.style.boxShadow = '0 4px 8px rgba(0,0,0,0.15)';
        });
        
        button.addEventListener('mouseleave', () => {
            button.style.transform = 'translateY(0)';
            button.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
        });
        
        return button;
    }
    
    // Utility functions
    function formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-GB', {
            weekday: 'long',
            day: 'numeric',
            month: 'long',
            year: 'numeric'
        });
    }
    
    function createCalendarLink(eventData) {
        const startDate = new Date(eventData.date);
        const endDate = new Date(startDate.getTime() + 2 * 60 * 60 * 1000); // 2 hours later
        
        const formatDateForCalendar = (date) => {
            return date.toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';
        };
        
        const params = new URLSearchParams({
            action: 'TEMPLATE',
            text: eventData.title,
            dates: `${formatDateForCalendar(startDate)}/${formatDateForCalendar(endDate)}`,
            details: eventData.description || '',
            location: eventData.location || ''
        });
        
        return `https://calendar.google.com/calendar/render?${params.toString()}`;
    }
    
    function shareEvent(eventData) {
        if (navigator.share) {
            navigator.share({
                title: eventData.title,
                text: eventData.description,
                url: window.location.href
            });
        } else {
            // Fallback: copy to clipboard
            const shareText = `${eventData.title}\n${eventData.description}\n${window.location.href}`;
            navigator.clipboard.writeText(shareText).then(() => {
                alert('Event details copied to clipboard!');
            });
        }
    }
    
    // Enhance close buttons
    function enhanceCloseButtons(modal) {
        const closeButtons = modal.querySelectorAll('[data-dismiss="modal"], .close, .modal-close, .btn-close');
        closeButtons.forEach(button => {
            button.addEventListener('click', () => closeModal(modal));
        });
        
        // Close on backdrop click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal(modal);
            }
        });
    }
    
    // Close modal function
    function closeModal(modal) {
        console.log('🔒 Closing modal...');
        
        // Cleanup escape handler
        if (modal._cleanupEscape) {
            modal._cleanupEscape();
        }
        
        // Hide modal
        modal.style.display = 'none';
        modal.classList.remove('show');
        
        // Remove modal from DOM if needed
        setTimeout(() => {
            if (modal.parentNode) {
                modal.parentNode.removeChild(modal);
            }
        }, 300);
        
        // Remove backdrop
        const backdrop = document.querySelector('.modal-backdrop');
        if (backdrop) {
            backdrop.remove();
        }
        
        // Restore body scroll
        document.body.style.overflow = '';
        document.body.classList.remove('modal-open');
    }
    
    // Initialize
    function init() {
        console.log('🚀 Initializing event modal fix...');
        waitForModal();
    }
    
    // Run when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
})();