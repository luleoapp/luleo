document.addEventListener('DOMContentLoaded', () => {
    const commentButtons = document.querySelectorAll('.comment-button');
    const modal = document.getElementById('comment-modal');
    const closeButton = document.querySelector('.close-button');
    const modalIdeaTitle = document.getElementById('modal-idea-title');
    const commentsSection = document.getElementById('comments-section');
    const submitCommentButton = document.getElementById('submit-comment');
    const newCommentInput = document.getElementById('new-comment');

    let currentIdeaId = null;
    let currentIdeaTitle = '';

    // Sample comments storage (Replace with backend integration)
    const commentsData = {
        // Idea ID: [comments]
        1: [
            { user: 'Alice', comment: 'Great idea! Really aligns with our goals.' },
            { user: 'Bob', comment: 'How do you plan to implement this?' }
        ],
        // Add more ideas and their comments here
    };

    commentButtons.forEach(button => {
        button.addEventListener('click', () => {
            currentIdeaId = button.getAttribute('data-idea-id');
            const ideaLink = document.querySelector(`.idea-link[data-idea-id="${currentIdeaId}"]`);
            currentIdeaTitle = ideaLink.textContent;
            openModal(currentIdeaTitle, currentIdeaId);
        });
    });

    closeButton.addEventListener('click', closeModal);

    window.addEventListener('click', (event) => {
        if (event.target == modal) {
            closeModal();
        }
    });

    submitCommentButton.addEventListener('click', () => {
        const commentText = newCommentInput.value.trim();
        if (commentText === '') {
            alert('Please enter a comment.');
            return;
        }

        const userName = 'Anonymous'; // Replace with actual user data if available

        const newComment = { user: userName, comment: commentText };

        if (!commentsData[currentIdeaId]) {
            commentsData[currentIdeaId] = [];
        }
        commentsData[currentIdeaId].push(newComment);

        renderComments(currentIdeaId);
        newCommentInput.value = '';
    });

    function openModal(title, ideaId) {
        modalIdeaTitle.textContent = title;
        modal.style.display = 'block';
        renderComments(ideaId);
    }

    function closeModal() {
        modal.style.display = 'none';
        commentsSection.innerHTML = '';
        newCommentInput.value = '';
    }

    function renderComments(ideaId) {
        commentsSection.innerHTML = '';
        const comments = commentsData[ideaId] || [];
        if (comments.length === 0) {
            commentsSection.innerHTML = '<p>No comments yet. Be the first to comment!</p>';
            return;
        }
        comments.forEach(comment => {
            const commentDiv = document.createElement('div');
            commentDiv.classList.add('comment');
            commentDiv.innerHTML = `<strong>${comment.user}:</strong> ${comment.comment}`;
            commentsSection.appendChild(commentDiv);
        });
    }
});