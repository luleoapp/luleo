document.addEventListener('DOMContentLoaded', function() {
    const imageContainers = document.querySelectorAll('.image-container');
    
    imageContainers.forEach(container => {
      // Show overlay on page load
      setTimeout(() => {
        container.classList.add('show-overlay');
      }, 500); // Delay of 500ms for a smoother effect after page load

      // Toggle overlay on click
      container.addEventListener('click', function() {
        this.classList.toggle('show-overlay');
      });
    });
  });
