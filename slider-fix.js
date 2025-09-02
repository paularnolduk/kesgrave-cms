/**
 * Slider Fix Script - Frontend Version
 * This script patches the slider to properly display images, introduction text, and buttons
 * from the API data. ONLY runs on homepage to prevent admin interface conflicts.
 */

(function() {
    'use strict';
    
    console.log('🔧 Slider fix script loaded (frontend version)');
    
    // CRITICAL: Only run on homepage - prevent interference with admin pages
    if (window.location.pathname !== '/' && 
        !window.location.pathname.includes('/index') && 
        window.location.pathname !== '') {
        console.log('ℹ️ Not on homepage, skipping slider fix');
        return;
    }
    
    // Additional check: Don't run on admin pages
    if (window.location.pathname.includes('/admin') || 
        window.location.pathname.includes('/cms') ||
        window.location.pathname.includes('/login')) {
        console.log('ℹ️ On admin page, skipping slider fix');
        return;
    }
    
    console.log('✅ On homepage, initializing slider fix');
    
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
    
    // Wait for slides to be rendered with timeout to prevent infinite loops
    function waitForSlides() {
        return new Promise((resolve) => {
            let attempts = 0;
            const maxAttempts = 50; // Maximum 5 seconds (50 * 100ms)
            
            const checkSlides = () => {
                attempts++;
                
                if (attempts > maxAttempts) {
                    console.warn('⚠️ Slider fix timeout - slides not found after 5 seconds');
                    resolve([]);
                    return;
                }
                
                const slides = document.querySelectorAll('.slide');
                if (slides.length > 0) {
                    console.log('✅ Found', slides.length, 'slides after', attempts, 'attempts');
                    resolve(slides);
                } else {
                    console.log('⏳ Waiting for slides... (attempt', attempts + '/' + maxAttempts + ')');
                    setTimeout(checkSlides, 100);
                }
            };
            checkSlides();
        });
    }
    
    // Fetch slides data from API
    async function fetchSlidesData() {
        try {
            console.log('📡 Fetching slides data...');
            const response = await fetch('/api/homepage/slides');
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log('✅ Slides data loaded:', data.length, 'slides');
            return data;
        } catch (error) {
            console.error('❌ Failed to fetch slides data:', error);
            return [];
        }
    }
    
    // Apply slide data to DOM elements
    function applySlideData(slides, slidesData) {
        console.log('🎨 Applying slide data to DOM...');
        
        slides.forEach((slide, index) => {
            const slideData = slidesData[index];
            if (!slideData) {
                console.warn('⚠️ No data for slide', index);
                return;
            }
            
            console.log(`🖼️ Processing slide ${index + 1}:`, slideData.title);
            
            // Set background image
            if (slideData.image) {
                const imageUrl = slideData.image;
                slide.style.backgroundImage = `linear-gradient(rgba(0, 0, 0, 0.4), rgba(0, 0, 0, 0.4)), url('${imageUrl}')`;
                slide.style.backgroundSize = 'cover';
                slide.style.backgroundPosition = 'center';
                slide.style.backgroundRepeat = 'no-repeat';
                console.log(`✅ Set background image for slide ${index + 1}:`, imageUrl);
            }
            
            // Find slide content container
            const slideContent = slide.querySelector('.slide-content');
            if (!slideContent) {
                console.warn('⚠️ No slide-content found for slide', index);
                return;
            }
            
            // Add introduction text if it doesn't exist
            if (slideData.introduction && !slideContent.querySelector('.slide-introduction')) {
                const introElement = document.createElement('p');
                introElement.className = 'slide-introduction';
                introElement.textContent = slideData.introduction;
                introElement.style.cssText = `
                    color: white;
                    font-size: 1.1rem;
                    line-height: 1.5;
                    margin: 1rem 0;
                    max-width: 600px;
                    text-shadow: 0 2px 4px rgba(0,0,0,0.5);
                `;
                slideContent.appendChild(introElement);
                console.log(`✅ Added introduction for slide ${index + 1}`);
            }
            
            // Add or update button if it doesn't exist
            if (slideData.button_text && slideData.button_url && !slideContent.querySelector('.slide-button')) {
                const buttonElement = document.createElement('a');
                buttonElement.className = 'slide-button';
                buttonElement.textContent = slideData.button_text;
                buttonElement.href = slideData.button_url;
                
                // Set target based on open_method
                if (slideData.open_method === 'new_tab') {
                    buttonElement.target = '_blank';
                    buttonElement.rel = 'noopener noreferrer';
                }
                
                buttonElement.style.cssText = `
                    display: inline-block;
                    background-color: #28a745;
                    color: white;
                    padding: 12px 24px;
                    text-decoration: none;
                    border-radius: 5px;
                    font-weight: bold;
                    margin-top: 1rem;
                    transition: background-color 0.3s ease;
                    text-shadow: none;
                `;
                
                // Add hover effect
                buttonElement.addEventListener('mouseenter', () => {
                    buttonElement.style.backgroundColor = '#218838';
                });
                buttonElement.addEventListener('mouseleave', () => {
                    buttonElement.style.backgroundColor = '#28a745';
                });
                
                slideContent.appendChild(buttonElement);
                console.log(`✅ Added button for slide ${index + 1}:`, slideData.button_text);
            }
        });
    }
    
    // Main initialization function
    async function initSliderFix() {
        try {
            console.log('🚀 Starting slider fix initialization...');
            
            // Wait for DOM to be ready
            await waitForDOM();
            console.log('✅ DOM ready');
            
            // Wait for slides to be rendered
            const slides = await waitForSlides();
            if (slides.length === 0) {
                console.warn('⚠️ No slides found, skipping slider fix');
                return;
            }
            
            // Fetch slides data
            const slidesData = await fetchSlidesData();
            if (slidesData.length === 0) {
                console.warn('⚠️ No slides data available, skipping slider fix');
                return;
            }
            
            // Apply slide data to DOM
            applySlideData(slides, slidesData);
            
            console.log('🎉 Slider fix complete!');
            
        } catch (error) {
            console.error('❌ Slider fix failed:', error);
        }
    }
    
    // Start the slider fix
    initSliderFix();
    
})();