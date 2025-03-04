document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('fileInput');
    const browseBtn = document.getElementById('browseBtn');
    const uploadPreview = document.getElementById('uploadPreview');
    const uploadInfo = document.getElementById('uploadInfo');
    const uploadCount = document.getElementById('uploadCount');
    const resetUpload = document.getElementById('resetUpload');
    const uploadError = document.getElementById('uploadError');
    const errorMessage = document.getElementById('errorMessage');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const uploaderStep = document.getElementById('uploaderStep');
    const analyzingStep = document.getElementById('analyzingStep');
    const editingStep = document.getElementById('editingStep');
    const listingForm = document.getElementById('listingForm');
    
    // State variables
    let uploadedFiles = [];
    
    // Only initialize if we're on the upload page
    if (dropzone && fileInput) {
        // Initialize drag and drop functionality
        initDragAndDrop();
        
        // Initialize file input
        browseBtn.addEventListener('click', function(e) {
            e.preventDefault();
            fileInput.click();
        });
        
        fileInput.addEventListener('change', function() {
            handleFiles(this.files);
        });
        
        // Reset upload button
        if (resetUpload) {
            resetUpload.addEventListener('click', function(e) {
                e.preventDefault();
                resetUploadState();
            });
        }
        
        // Analyze button
        if (analyzeBtn) {
            analyzeBtn.addEventListener('click', function() {
                analyzeImages();
            });
        }
    }
    
    // Thumbnail gallery in preview page
    const thumbnails = document.querySelectorAll('.listing-thumbnail');
    if (thumbnails.length > 0) {
        thumbnails.forEach(thumb => {
            thumb.addEventListener('click', function() {
                const slideIndex = this.getAttribute('data-bs-slide-to');
                const carousel = document.querySelector(this.getAttribute('data-bs-target'));
                if (carousel) {
                    bootstrap.Carousel.getInstance(carousel).to(parseInt(slideIndex));
                }
            });
        });
    }
    
    // Functions
    function initDragAndDrop() {
        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropzone.addEventListener(eventName, preventDefaults, false);
            document.body.addEventListener(eventName, preventDefaults, false);
        });
        
        // Highlight drop zone when item is dragged over it
        ['dragenter', 'dragover'].forEach(eventName => {
            dropzone.addEventListener(eventName, highlight, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            dropzone.addEventListener(eventName, unhighlight, false);
        });
        
        // Handle dropped files
        dropzone.addEventListener('drop', handleDrop, false);
    }
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    function highlight() {
        dropzone.classList.add('dragover');
    }
    
    function unhighlight() {
        dropzone.classList.remove('dragover');
    }
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    }
    
    function handleFiles(files) {
        if (files.length === 0) return;
        
        // Convert FileList to Array
        const filesArray = Array.from(files);
        
        // Check for non-image files
        const invalidFiles = filesArray.filter(file => !file.type.match('image.*'));
        if (invalidFiles.length > 0) {
            showError('Only image files are allowed');
            return;
        }
        
        // Upload files to server
        uploadFiles(filesArray);
    }
    
    function uploadFiles(files) {
        const formData = new FormData();
        
        // Append all files to form data
        files.forEach(file => {
            formData.append('files[]', file);
        });
        
        // If this is a new upload set reset flag
        if (uploadedFiles.length === 0) {
            formData.append('reset', 'true');
        }
        
        // Show loading state
        dropzone.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div><p class="mt-3">Uploading images...</p>';
        
        // Send AJAX request
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update UI with uploaded files
                updateUploadUI(data.files, data.count);
            } else {
                showError(data.error || 'Upload failed. Please try again.');
                // Reset dropzone
                resetDropzone();
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showError('An error occurred during upload');
            resetDropzone();
        });
    }
    
    function updateUploadUI(files, count) {
        // Update state
        uploadedFiles = files;
        
        // Enable analyze button if files were uploaded
        if (count > 0) {
            analyzeBtn.disabled = false;
        }
        
        // Update count display
        uploadCount.textContent = count;
        uploadInfo.style.display = 'block';
        
        // Reset dropzone
        resetDropzone();
        
        // Display thumbnails
        displayThumbnails(files);
    }
    
    function displayThumbnails(files) {
        // Clear existing previews
        uploadPreview.innerHTML = '';
        
        // Create thumbnail for each file
        files.forEach((file, index) => {
            const col = document.createElement('div');
            col.className = 'col-6 col-sm-4 col-md-3 col-lg-2';
            
            col.innerHTML = `
                <div class="image-preview-container">
                    <img src="${file}" class="image-preview" alt="Preview">
                    <div class="image-preview-overlay">
                        <button class="remove-image-btn" data-index="${index}">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </div>
            `;
            
            uploadPreview.appendChild(col);
        });
        
        // Show preview container
        uploadPreview.style.display = 'flex';
        
        // Add event listeners to remove buttons
        document.querySelectorAll('.remove-image-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const index = parseInt(this.getAttribute('data-index'));
                removeFile(index);
            });
        });
    }
    
    function removeFile(index) {
        // For simplicity, we'll just reset everything for now
        // In a production app, you'd want to remove just the single file
        resetUploadState();
    }
    
    function resetUploadState() {
        // Reset UI
        uploadPreview.innerHTML = '';
        uploadPreview.style.display = 'none';
        uploadInfo.style.display = 'none';
        uploadError.style.display = 'none';
        analyzeBtn.disabled = true;
        
        // Reset state
        uploadedFiles = [];
        
        // Reset dropzone
        resetDropzone();
        
        // Reset file input
        if (fileInput) {
            fileInput.value = '';
        }
        
        // Reset on server
        const formData = new FormData();
        formData.append('reset', 'true');
        
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .catch(error => {
            console.error('Error resetting:', error);
        });
    }
    
    function resetDropzone() {
        dropzone.innerHTML = `
            <i class="fas fa-cloud-upload-alt fa-3x mb-3 text-primary"></i>
            <h4>Drag & Drop Photos Here</h4>
            <p>or</p>
            <button id="browseBtn" class="btn btn-primary">
                <i class="fas fa-folder-open me-2"></i>Browse Files
            </button>
            <input type="file" id="fileInput" multiple accept="image/*" class="d-none">
            <p class="mt-3 text-muted small">Upload up to 12 photos (Max 16MB each)</p>
        `;
        
        // Re-attach event listener to new browse button
        const newBrowseBtn = document.getElementById('browseBtn');
        const newFileInput = document.getElementById('fileInput');
        
        if (newBrowseBtn && newFileInput) {
            newBrowseBtn.addEventListener('click', function(e) {
                e.preventDefault();
                newFileInput.click();
            });
            
            newFileInput.addEventListener('change', function() {
                handleFiles(this.files);
            });
        }
    }
    
    function showError(message) {
        errorMessage.textContent = message;
        uploadError.style.display = 'block';
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            uploadError.style.display = 'none';
        }, 5000);
    }
    
    function analyzeImages() {
        // Show analyzing step
        uploaderStep.style.display = 'none';
        analyzingStep.style.display = 'block';
        
        // Call API to analyze images
        fetch('/analyze', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Populate form with AI-generated data
                populateForm(data.data);
                
                // Show editing step
                analyzingStep.style.display = 'none';
                editingStep.style.display = 'block';
            } else {
                // Show error and go back to uploader
                showError(data.error || 'Analysis failed. Please try again.');
                analyzingStep.style.display = 'none';
                uploaderStep.style.display = 'block';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showError('An error occurred during analysis');
            analyzingStep.style.display = 'none';
            uploaderStep.style.display = 'block';
        });
    }
    
    function populateForm(data) {
        // Log the data received from the server
        console.log("Data received from server:", data);
        
        // Populate form fields with AI-generated data
        for (const key in data) {
            const element = document.getElementById(key);
            if (element) {
                console.log(`Setting field ${key} to:`, data[key]);
                
                if (Array.isArray(data[key])) {
                    // Handle arrays (like keywords)
                    if (key === 'keywords') {
                        element.value = data[key].join(', ');
                    } else {
                        element.value = data[key].join('\n');
                    }
                } else if (typeof data[key] === 'object' && data[key] !== null) {
                    // Handle nested objects
                    console.log(`Skipping object field: ${key}`);
                } else {
                    // Handle regular string/number values
                    element.value = data[key];
                    
                    // Special handling for select elements
                    if (element.tagName === 'SELECT') {
                        console.log(`Select element ${key} with value ${data[key]}`);
                        
                        // Try to find a matching option
                        const options = Array.from(element.options);
                        const matchingOption = options.find(option => 
                            option.value.toLowerCase() === String(data[key]).toLowerCase());
                        
                        if (matchingOption) {
                            console.log(`Found matching option: ${matchingOption.value}`);
                            element.value = matchingOption.value;
                        } else if (data[key] && element.id === 'condition') {
                            // For condition field, try to map to our predefined values
                            const conditionMap = {
                                'new': 'New',
                                'new other': 'New other',
                                'like new': 'New other',
                                'open box': 'New other',
                                'used': 'Used',
                                'pre-owned': 'Used',
                                'for parts': 'For parts/not working',
                                'not working': 'For parts/not working',
                                'for parts/not working': 'For parts/not working'
                            };
                            
                            const lowerCondition = String(data[key]).toLowerCase();
                            console.log(`Trying to map condition: ${lowerCondition}`);
                            
                            for (const [key, value] of Object.entries(conditionMap)) {
                                if (lowerCondition.includes(key)) {
                                    console.log(`Mapped condition to: ${value}`);
                                    element.value = value;
                                    break;
                                }
                            }
                        }
                    }
                }
            } else {
                console.log(`No element found for field: ${key}`);
            }
        }
        
        // Handle special cases and nested fields
        if (data.price && typeof data.price === 'object') {
            if (data.price.starting_bid) {
                const startingPriceElement = document.getElementById('starting_price');
                if (startingPriceElement) {
                    startingPriceElement.value = data.price.starting_bid.toString().replace('$', '');
                }
            }
            
            if (data.price.buy_it_now) {
                const buyItNowElement = document.getElementById('buy_it_now_price');
                if (buyItNowElement) {
                    buyItNowElement.value = data.price.buy_it_now.toString().replace('$', '');
                }
            }
        }
        
        // Handle item specifics if they're in a nested object
        if (data.item_specifics && typeof data.item_specifics === 'object') {
            const specificMappings = {
                'brand': 'brand',
                'model': 'model',
                'mpn': 'model',
                'type': 'type_style',
                'style': 'type_style',
                'color': 'color',
                'size': 'size_dimensions',
                'dimensions': 'size_dimensions',
                'material': 'material'
            };
            
            for (const [apiKey, formKey] of Object.entries(specificMappings)) {
                if (data.item_specifics[apiKey]) {
                    const element = document.getElementById(formKey);
                    if (element && !element.value) { // Only set if not already set
                        element.value = data.item_specifics[apiKey];
                    }
                }
            }
        }
    }
    
    // Handle eBay draft listing creation
    var createEbayDraftBtn = document.getElementById('create_ebay_draft');
    if (createEbayDraftBtn) {
        createEbayDraftBtn.addEventListener('click', function() {
            // Check if we're in production mode
            const isProductionMode = document.querySelector('.alert-danger') !== null;
            
            let confirmMessage = 'Create a draft listing on eBay?';
            if (isProductionMode) {
                confirmMessage = 'WARNING: You are in PRODUCTION MODE. This will create a REAL draft listing on your eBay account. Continue?';
            }
            
            // Ask for confirmation
            if (!confirm(confirmMessage)) {
                return; // User cancelled
            }
            
            // Change button state to loading
            createEbayDraftBtn.disabled = true;
            createEbayDraftBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Creating Draft...';
            
            // Send request to create draft listing
            fetch('/api/ebay/create_draft', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    let successMessage = 'Draft listing created successfully! Listing ID: ' + data.listing_id;
                    
                    // Add environment info if available
                    if (data.environment === 'production') {
                        successMessage = 'PRODUCTION: ' + successMessage + '\n\nThis listing has been created on your REAL eBay account.';
                    }
                    
                    // Show success message
                    alert(successMessage);
                    
                    // Change button to success state
                    createEbayDraftBtn.innerHTML = '<i class="fas fa-check me-2"></i>Draft Created';
                    createEbayDraftBtn.classList.remove('btn-warning');
                    createEbayDraftBtn.classList.add('btn-success');
                } else {
                    // Show error message
                    alert('Error creating draft listing: ' + data.error);
                    
                    // Reset button
                    createEbayDraftBtn.disabled = false;
                    createEbayDraftBtn.innerHTML = '<i class="fas fa-tag me-2"></i>Create eBay Draft';
                }
            })
            .catch(error => {
                // Show error message
                alert('Error creating draft listing: ' + error);
                
                // Reset button
                createEbayDraftBtn.disabled = false;
                createEbayDraftBtn.innerHTML = '<i class="fas fa-tag me-2"></i>Create eBay Draft';
            });
        });
    }
}); 