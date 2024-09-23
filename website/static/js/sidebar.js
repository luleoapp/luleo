document.addEventListener('DOMContentLoaded', () => {
    const sidebar = document.getElementById('sidebar');
    const toggleButton = document.querySelector('.toggle');

    // Function to set the sidebar state
    const setSidebarState = (isInactive) => {
        if (isInactive) {
            sidebar.classList.add('inactive');
        } else {
            sidebar.classList.remove('inactive');
        }
        try {
            localStorage.setItem('sidebarState', isInactive ? 'inactive' : 'active');
        } catch (e) {
            console.error('Could not save sidebar state to localStorage:', e);
        }
    };

    // Initialize sidebar state from localStorage
    let savedState = 'inactive'; // Default state
    try {
        savedState = localStorage.getItem('sidebarState') || 'inactive';
    } catch (e) {
        console.error('Could not read sidebar state from localStorage:', e);
    }
    setSidebarState(savedState === 'inactive');

    // Toggle sidebar state on button click
    toggleButton.addEventListener('click', () => {
        const isCurrentlyInactive = sidebar.classList.contains('inactive');
        setSidebarState(!isCurrentlyInactive);
    });

    // Optional: Prevent sidebar from closing on link clicks
    const sidebarLinks = sidebar.querySelectorAll('a');
    sidebarLinks.forEach(link => {
        link.addEventListener('click', (event) => {
            // No action needed unless sidebar should close on certain link clicks
            // Ensure sidebar state is preserved via localStorage
        });
    });
});
