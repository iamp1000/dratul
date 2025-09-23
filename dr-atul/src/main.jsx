// src/main.jsx
import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './app';
import './styles/globals.css';

// Tailwind CSS configuration
const tailwindConfig = {
    theme: {
        extend: {
            colors: {
                primary: '#272343',
                secondary: '#e3f6f5',
                accent: '#bae8e8',
                light: '#ffffff',
                'text-dark': '#2d334a',
                'text-light': '#5a5e74',
            },
            fontFamily: {
                sans: ['Inter', 'sans-serif'],
            },
        },
    },
};

// Apply Tailwind configuration
if (window.tailwind && window.tailwind.config) {
    window.tailwind.config = tailwindConfig;
}

const container = document.getElementById('root');
const root = createRoot(container);

root.render(<App />);