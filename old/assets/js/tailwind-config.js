/**
 * Nexus Framework | Global Tailwind Configuration
 * This file maps ALL CSS Design Tokens to Tailwind Utility Classes.
 */

tailwind.config = {
    darkMode: 'class',
    theme: {
        extend: {
            colors: {
                // Main Palette
                primary: 'rgb(var(--color-primary))',
                secondary: 'rgb(var(--color-secondary))',
                accent: 'rgb(var(--color-accent))',
                'accent-sky': 'rgb(var(--color-accent-sky))',
                'accent-violet': 'rgb(var(--color-accent-violet))',
                'peach': 'rgb(var(--color-accent-peach))',
                'violet': 'rgb(var(--color-accent-violet))',
                'sky': 'rgb(var(--color-accent-sky))',
                
                // Surfaces & Backgrounds
                'body-bg': 'var(--color-body-bg)',
                'body-text': 'var(--color-body-text)',
                'header': 'var(--color-header-bg)',
                'header-text': 'var(--color-header-text)',
                'panel-fill': 'rgb(var(--color-panel-fill))',
                'panel-border': 'rgb(var(--color-panel-border))',
                'panel-header': 'rgb(var(--color-panel-header-bg))',
                'audit-body': 'rgb(var(--color-audit-body))',
                'surface-container': 'rgb(var(--color-surface-container-bg))',
                'surface-container-border': 'rgb(var(--color-surface-container-border))',
                
                // Buttons & Interaction
                'button-bg': 'rgb(var(--color-button-bg))',
                'button-text': 'rgb(var(--color-button-text))',
                'button-disabled': 'rgb(var(--color-button-disabled-bg))',
                'button-disabled-text': 'rgb(var(--color-button-disabled-text))',
                
                // Inputs
                'input': 'var(--color-input-text)',
                'input-bg': 'rgb(var(--color-input-bg))',
                'input-border': 'rgb(var(--color-input-border))',
                'input-focus': 'rgb(var(--color-input-focus))',
                'label': 'rgb(var(--color-label-text))',
                
                // Navigation & Tabs
                'tab-bar': 'rgb(var(--color-tab-bar-bg))',
                'tab-active': 'rgb(var(--color-tab-active-bg))',
                'tab-active-text': 'rgb(var(--color-tab-active-text))',
                'tab-inactive': 'rgb(var(--color-tab-inactive-bg))',
                'tab-inactive-text': 'rgb(var(--color-tab-inactive-text))',
                
                // Business Intelligence (BI) & Status
                'bi-logistics': 'rgb(var(--color-bi-card-logistics))',
                'bi-ring': 'rgb(var(--color-bi-ring-bg))',
                'bi-main': 'rgb(var(--color-bi-text-main))',
                'bi-muted': 'rgb(var(--color-bi-text-muted))',
                'kpi-highlight': 'rgb(var(--color-kpi-highlight))',
                
                success: 'rgb(var(--color-success))',  /* unified: Emerald-600 #059669 */
                warning: '#f59e0b',
                error: '#ef4444',
                info: '#3b82f6'
            },
            borderRadius: {
                'base': 'var(--radius-base)',
                'panel': 'var(--radius-panel)'
            },
            spacing: {
                'unit': 'var(--space-1)'
            }
        }
    }
}
