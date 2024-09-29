function updateDate() {
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    const today = new Date().toLocaleDateString('en-US', options);
    document.getElementById('currentDate').textContent = today;
}
updateDate(); // Call the function immediately