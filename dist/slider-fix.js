/**
 * Slider Fix Script
 * This script patches the slider to properly display images, introduction text, and buttons
 * from the API data.
 */

(function() {
    'use strict';
    
    console.log('🔧 Slider fix script loaded');
    
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
    
    // Wait for slides to be rendered
    function waitForSlides() {
        return new Promise((resolve) => {
            const checkSlides = () => {
                const slides = document.querySelectorAll('.slide');
                if (slides.length > 0) {
                    console.log('✅ Found', slides.length, 'slides');
                    resolve(slides);
                } else {
                    console.log('⏳ Waiting for slides...');
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
                slide.style.backgroundImage = `url('${imageUrl}'), linear-gradient(135deg, rgba(44, 95, 45, 0.8) 0%, rgba(151, 188, 98, 0.8) 100%)`;
                slide.style.backgroundSize = 'cover';
                slide.style.backgroundPosition = 'center';
                slide.style.backgroundBlendMode = 'overlay';
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
            
            // Add button if it doesn't exist
            if (slideData.button_text && slideData.button_url && !slideContent.querySelector('.slide-button')) {
                const buttonElement = document.createElement('a');
                buttonElement.className = 'slide-button';
                buttonElement.href = slideData.button_url;
                buttonElement.textContent = slideData.button_text;
                buttonElement.target = slideData.open_method === 'new_tab' ? '_blank' : '_self';
                if (buttonElement.target === '_blank') {
                    buttonElement.rel = 'noopener noreferrer';
                }
                buttonElement.style.cssText = `
                    display: inline-block;
                    background-color: #97bc62;
                    color: white;
                    padding: 12px 24px;
                    border-radius: 6px;
                    text-decoration: none;
                    font-weight: 600;
                    margin-top: 1.5rem;
                    transition: background-color 0.3s ease;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
                `;
                
                // Add hover effect
                buttonElement.addEventListener('mouseenter', () => {
                    buttonElement.style.backgroundColor = '#7da050';
                });
                buttonElement.addEventListener('mouseleave', () => {
                    buttonElement.style.backgroundColor = '#97bc62';
                });
                
                slideContent.appendChild(buttonElement);
                console.log(`✅ Added button for slide ${index + 1}:`, slideData.button_text);
            }
        });
        
        console.log('🎉 Slider fix complete!');
    }
    
    // Main function
    async function fixSlider() {
        try {
            console.log('🚀 Starting slider fix...');
            
            // Wait for DOM and slides
            await waitForDOM();
            const slides = await waitForSlides();
            
            // Fetch slides data
            const slidesData = await fetchSlidesData();
            
            if (slidesData.length === 0) {
                console.error('❌ No slides data available');
                return;
            }
            
            // Apply the fix
            applySlideData(slides, slidesData);
            
        } catch (error) {
            console.error('❌ Slider fix failed:', error);
        }
    }
    
    // Run the fix
    fixSlider();
    
    // Also run the fix when the page becomes visible (in case of navigation)
    document.addEventListener('visibilitychange', () => {
        if (!document.hidden) {
            setTimeout(fixSlider, 500);
        }
    });
    
})();