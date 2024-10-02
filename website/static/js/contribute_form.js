document.querySelector('form').addEventListener('submit', function(e) {
    var message = document.getElementById('message').value.trim();
    var file = document.getElementById('file-upload').files[0];
    var name = document.getElementById('name').value.trim();
    var human = document.getElementById('human').checked;
    if (!message && !file) {
        e.preventDefault();
        alert('Please provide either a message or upload a file.');
    }
    if (!human) {
        e.preventDefault();
        alert('Please check the "I am a human" checkbox.');
    }
    if (!name) {
        e.preventDefault();
        alert('Please enter your name.');
    }
});