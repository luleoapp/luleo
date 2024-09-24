document.getElementById('file-upload').addEventListener('change', function(e) {
  const file = this.files[0];
  const fileSize = file.size;
  const fileType = file.type;
  const preview = document.getElementById('file-preview');
  const previewImage = preview.querySelector('.file-upload__preview-image');
  const previewDocument = preview.querySelector('.file-upload__preview-document');
  const previewDocumentName = preview.querySelector('.file-upload__preview-document-name');

  if (fileSize > 10485760) {
    alert('File is too big! Maximum size is 10MB.');
    this.value = '';
    preview.style.display = 'none';
    return;
  }

  if (fileType.startsWith('image/')) {
    const reader = new FileReader();
    reader.onload = function(e) {
      previewImage.src = e.target.result;
      previewImage.style.display = 'block';
      previewDocument.style.display = 'none';
    }
    reader.readAsDataURL(file);
  } else if (fileType === 'application/pdf') {
    previewDocumentName.textContent = file.name;
    previewImage.style.display = 'none';
    previewDocument.style.display = 'flex';
  } else {
    preview.style.display = 'none';
    return;
  }

  preview.style.display = 'block';
});

// Function to handle file selection and preview
function handleFileSelection(event) {
    const file = event.target.files[0];
    const preview = document.getElementById('file-preview');
    const previewImage = preview.querySelector('.file-upload__preview-image');
    const previewDocument = preview.querySelector('.file-upload__preview-document');
    const previewDocumentName = preview.querySelector('.file-upload__preview-document-name');

    if (file) {
        // Check file size (10MB = 10485760 bytes)
        if (file.size > 10485760) {
            alert('File is too big! Maximum size is 10MB.');
            event.target.value = '';
            preview.style.display = 'none';
            return;
        }

        // Check file type
        if (file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = function(e) {
                previewImage.src = e.target.result;
                previewImage.style.display = 'block';
                previewDocument.style.display = 'none';
            }
            reader.readAsDataURL(file);
        } else if (file.type === 'application/pdf') {
            previewDocumentName.textContent = file.name;
            previewImage.style.display = 'none';
            previewDocument.style.display = 'flex';
        } else {
            alert('Unsupported file type. Please select an image or PDF.');
            event.target.value = '';
            preview.style.display = 'none';
            return;
        }

        // Show the preview container
        preview.style.display = 'block';
    } else {
        preview.style.display = 'none';
    }
}

// Function to reset the file upload
function resetFileUpload() {
    const fileInput = document.getElementById('file-upload');
    const preview = document.getElementById('file-preview');
    const previewImage = preview.querySelector('.file-upload__preview-image');
    const previewDocument = preview.querySelector('.file-upload__preview-document');
    const previewDocumentName = preview.querySelector('.file-upload__preview-document-name');

    // Clear the file input
    fileInput.value = '';

    // Hide the preview container
    preview.style.display = 'none';

    // Reset the preview image and document elements
    if (previewImage) {
        previewImage.src = '';
        previewImage.style.display = 'none';
    }

    if (previewDocument) {
        previewDocumentName.textContent = '';
        previewDocument.style.display = 'none';
    }
}

// Function to initialize event listeners
function initializeFileUpload() {
    const fileInput = document.getElementById('file-upload');
    const resetButton = document.getElementById('reset-button');

    fileInput.addEventListener('change', handleFileSelection);

    if (resetButton) {
        resetButton.addEventListener('click', resetFileUpload);
    }
}

// Initialize when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', initializeFileUpload);
