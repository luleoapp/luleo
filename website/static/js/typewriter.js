function typeWriter(element, text, i, fnCallback) {
    if (i < text.length) {
        element.innerHTML = text.substring(0, i+1) + '<span aria-hidden="true"></span>';

        setTimeout(function() {
            typeWriter(element, text, i + 1, fnCallback)
        }, 30); // Faster typing speed
    } else if (typeof fnCallback == 'function') {
        setTimeout(fnCallback, 700);
    }
}

// Start the typewriter effect when the page loads
document.addEventListener('DOMContentLoaded', function() {
    var typewriterElement = document.getElementById("typewriter");
    if (typewriterElement) {
        // Set the font to be consistent with the rest of the site
        //typewriterElement.style.fontFamily = 'inherit';
        //typewriterElement.style.fontSize = 'inherit';
       // typewriterElement.style.fontWeight = 'inherit';
        //typewriterElement.style.lineHeight = 'inherit';

        var text = typewriterElement.getAttribute('data-description');
        typeWriter(typewriterElement, text, 0, function() {
            // Callback after typing is complete
            console.log("Typing complete");
            typewriterElement.style.borderRight = 'none'; // Remove the caret when done
        });
    }
});