// ImageVault Frontend Controller
let currentImages = [];
let currentTags = [];
let selectedFile = null;
let currentModalImage = null;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initUploader();
    initFilters();
    initModal();
    loadStats();
    loadTags();
    loadImages();
});

// Tab Navigation
function initNavigation() {
    const navButtons = document.querySelectorAll('.nav-item');
    navButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.getAttribute('data-tab');
            switchTab(tabId);
        });
    });

    document.getElementById('btnOpenUploadModal')?.addEventListener('click', () => {
        switchTab('upload');
    });
}

function switchTab(tabId) {
    document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

    const targetNav = document.querySelector(`.nav-item[data-tab="${tabId}"]`);
    const targetPane = document.getElementById(`tab-${tabId}`);

    if (targetNav) targetNav.classList.add('active');
    if (targetPane) targetPane.classList.add('active');

    if (tabId === 'gallery') loadImages();
    if (tabId === 'analytics') loadStats();
}

// Uploader & Drag-Drop Handling
function initUploader() {
    const dropzone = document.getElementById('dropzoneCard');
    const fileInput = document.getElementById('fileInput');
    const btnBrowse = document.getElementById('btnBrowseFiles');
    const previewBox = document.getElementById('uploadPreviewBox');
    const previewImg = document.getElementById('previewImage');
    const promptBox = document.getElementById('dropzonePrompt');
    const btnRemove = document.getElementById('btnRemovePreview');
    const qualitySlider = document.getElementById('inputQuality');
    const qualityVal = document.getElementById('qualityVal');
    const uploadForm = document.getElementById('uploadForm');
    const btnSubmit = document.getElementById('btnSubmitUpload');

    btnBrowse.addEventListener('click', (e) => {
        e.stopPropagation();
        fileInput.click();
    });

    dropzone.addEventListener('click', () => {
        if (!selectedFile) fileInput.click();
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) handleFileSelect(e.target.files[0]);
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropzone.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropzone.classList.remove('dragover');
        });
    });

    dropzone.addEventListener('drop', (e) => {
        if (e.dataTransfer.files.length > 0) handleFileSelect(e.dataTransfer.files[0]);
    });

    btnRemove.addEventListener('click', (e) => {
        e.stopPropagation();
        clearSelectedFile();
    });

    qualitySlider.addEventListener('input', (e) => {
        qualityVal.textContent = e.target.value;
    });

    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (!selectedFile) return;

        btnSubmit.disabled = true;
        btnSubmit.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Compressing &amp; Storing...`;

        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('title', document.getElementById('inputTitle').value);
        formData.append('description', document.getElementById('inputDescription').value);
        formData.append('tags', document.getElementById('inputTags').value);
        formData.append('quality', qualitySlider.value);

        try {
            const res = await fetch('/api/images/upload', {
                method: 'POST',
                body: formData
            });

            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || 'Upload failed');

            showToast(data.message, 'success');
            renderUploadResult(data);
            clearSelectedFile();
            loadStats();
            loadTags();
        } catch (err) {
            showToast(err.message, 'error');
        } finally {
            btnSubmit.disabled = false;
            btnSubmit.innerHTML = `<i class="fa-solid fa-bolt"></i> Process, Compress &amp; Save`;
        }
    });

    function handleFileSelect(file) {
        if (!file.type.startsWith('image/')) {
            showToast('Please select a valid image file (JPEG, PNG, WebP, TIFF).', 'error');
            return;
        }

        selectedFile = file;
        const reader = new FileReader();
        reader.onload = (e) => {
            previewImg.src = e.target.result;
            promptBox.style.display = 'none';
            previewBox.style.display = 'block';
            btnSubmit.disabled = false;
        };
        reader.readAsDataURL(file);
    }

    function clearSelectedFile() {
        selectedFile = null;
        fileInput.value = '';
        previewImg.src = '';
        promptBox.style.display = 'block';
        previewBox.style.display = 'none';
        btnSubmit.disabled = true;
        document.getElementById('inputTitle').value = '';
        document.getElementById('inputTags').value = '';
        document.getElementById('inputDescription').value = '';
    }
}

function renderUploadResult(data) {
    const container = document.getElementById('uploadResultContainer');
    const img = data.image;
    
    let duplicateNotice = '';
    if (data.is_duplicate) {
        duplicateNotice = `
            <div style="background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.3); padding: 0.75rem; border-radius: 8px; margin-bottom: 1rem; font-size: 0.8rem; color: #fde68a;">
                <i class="fa-solid fa-triangle-exclamation"></i> <strong>Duplicate Alert:</strong> ${data.message}
            </div>
        `;
    }

    container.innerHTML = `
        <div class="result-header">
            <div class="result-icon ${data.is_duplicate ? 'duplicate' : 'success'}">
                <i class="fa-solid ${data.is_duplicate ? 'fa-clone' : 'fa-check'}"></i>
            </div>
            <div>
                <h4>${data.message}</h4>
                <p style="font-size: 0.8rem; color: var(--text-muted);">${img.original_filename} &rarr; JPEG (${img.width}x${img.height})</p>
            </div>
        </div>
        ${duplicateNotice}
        <div class="metric-highlight-banner" style="margin-bottom: 1rem;">
            <div class="banner-stat">
                <span class="label">Original</span>
                <span class="val">${formatBytes(img.original_size_bytes)}</span>
            </div>
            <div class="banner-arrow"><i class="fa-solid fa-arrow-right"></i></div>
            <div class="banner-stat">
                <span class="label">Optimized JPEG</span>
                <span class="val highlight-green">${formatBytes(img.compressed_size_bytes)}</span>
            </div>
            <div class="banner-stat">
                <span class="label">Saved</span>
                <span class="val highlight-blue">${img.savings_percent}%</span>
            </div>
        </div>
        <div style="display: flex; gap: 0.75rem;">
            <button class="btn btn-secondary" onclick="openModal(${img.id})">
                <i class="fa-solid fa-eye"></i> Inspect EXIF &amp; Hashes
            </button>
            <button class="btn btn-primary" onclick="switchTab('gallery')">
                <i class="fa-solid fa-images"></i> View in Gallery
            </button>
        </div>
    `;
    container.style.display = 'block';
}

// Gallery & Filtering
function initFilters() {
    const searchInput = document.getElementById('searchInput');
    const tagFilter = document.getElementById('tagFilter');
    const sortByFilter = document.getElementById('sortByFilter');
    const btnRefresh = document.getElementById('btnRefreshGallery');

    let debounceTimer;
    searchInput.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => loadImages(), 300);
    });

    tagFilter.addEventListener('change', () => loadImages());
    sortByFilter.addEventListener('change', () => loadImages());
    btnRefresh.addEventListener('click', () => {
        loadImages();
        loadStats();
    });
}

async function loadImages() {
    const q = document.getElementById('searchInput').value;
    const tag = document.getElementById('tagFilter').value;
    const sortBy = document.getElementById('sortByFilter').value;

    const params = new URLSearchParams();
    if (q) params.append('q', q);
    if (tag) params.append('tag', tag);
    if (sortBy) params.append('sort_by', sortBy);

    try {
        const res = await fetch(`/api/images?${params.toString()}`);
        if (!res.ok) throw new Error('Failed to load images');
        const images = await res.json();
        currentImages = images;
        renderGallery(images);
    } catch (err) {
        showToast(err.message, 'error');
    }
}

function renderGallery(images) {
    const grid = document.getElementById('galleryGrid');
    const emptyState = document.getElementById('galleryEmptyState');

    if (!images || images.length === 0) {
        grid.innerHTML = '';
        emptyState.style.display = 'block';
        return;
    }

    emptyState.style.display = 'none';
    grid.innerHTML = images.map(img => {
        const tagsHtml = (img.tags || []).map(t => `<span class="tag-chip">${escapeHtml(t.name)}</span>`).join('');
        return `
            <div class="image-card" onclick="openModal(${img.id})">
                <div class="card-thumb-wrapper">
                    <img src="${img.thumbnail_url}" alt="${escapeHtml(img.title || img.original_filename)}" loading="lazy">
                    <span class="savings-badge">-${img.savings_percent}%</span>
                </div>
                <div class="card-body">
                    <div class="card-title" title="${escapeHtml(img.title || img.original_filename)}">
                        ${escapeHtml(img.title || img.original_filename)}
                    </div>
                    <div class="card-meta-row">
                        <span>${img.width} &times; ${img.height} &bull; JPEG</span>
                        <span>${formatBytes(img.compressed_size_bytes)}</span>
                    </div>
                    <div class="card-tags">
                        ${tagsHtml || '<span style="font-size: 0.7rem; color: var(--text-dim);">No tags</span>'}
                    </div>
                    <div class="card-footer-actions" onclick="event.stopPropagation();">
                        <button class="btn btn-secondary btn-icon" title="Inspect details" onclick="openModal(${img.id})">
                            <i class="fa-solid fa-eye"></i>
                        </button>
                        <a href="/api/images/${img.id}/download" class="btn btn-secondary btn-icon" title="Download JPEG" download>
                            <i class="fa-solid fa-download"></i>
                        </a>
                        <button class="btn btn-danger btn-icon" title="Delete" onclick="deleteImage(${img.id})">
                            <i class="fa-solid fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// Modal & Inspector
function initModal() {
    const modal = document.getElementById('imageModal');
    const btnClose = document.getElementById('btnCloseModal');
    const btnDelete = document.getElementById('btnModalDelete');

    btnClose.addEventListener('click', closeModal);
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
    });

    btnDelete.addEventListener('click', () => {
        if (currentModalImage) deleteImage(currentModalImage.id);
    });
}

function openModal(imageId) {
    const img = currentImages.find(i => i.id === imageId);
    if (!img) return;

    currentModalImage = img;
    document.getElementById('modalImageTitle').textContent = img.title || img.original_filename;
    document.getElementById('modalImagePreview').src = img.image_url;
    document.getElementById('modalOrigSize').textContent = formatBytes(img.original_size_bytes);
    document.getElementById('modalCompSize').textContent = formatBytes(img.compressed_size_bytes);
    document.getElementById('modalSavingsPercent').textContent = `${img.savings_percent}% (${img.compression_ratio}x)`;
    document.getElementById('modalDimensions').textContent = `${img.width} x ${img.height} px`;
    document.getElementById('modalAspectRatio').textContent = `${img.aspect_ratio}`;
    document.getElementById('modalQuality').textContent = `${img.jpeg_quality}% (Progressive)`;
    document.getElementById('modalOriginalName').textContent = img.original_filename;
    document.getElementById('modalSha256').textContent = img.sha256_hash;
    document.getElementById('modalPhash').textContent = img.phash;
    document.getElementById('btnModalDownload').href = `/api/images/${img.id}/download`;

    // Render EXIF tags
    const exifContainer = document.getElementById('modalExifContainer');
    const meta = img.metadata_json || {};
    const sanitizedAttrs = meta.sanitized_attributes || [];

    let exifHtml = `
        <div class="exif-pill">
            <span><i class="fa-solid fa-shield-check"></i> Privacy Scrubbing:</span>
            <strong>${img.exif_stripped ? 'Active (GPS & Serials Removed)' : 'Clean'}</strong>
        </div>
    `;

    if (meta.camera_make || meta.camera_model) {
        exifHtml += `
            <div class="exif-pill" style="background: rgba(99, 102, 241, 0.1); border-color: rgba(99, 102, 241, 0.3); color: #c7d2fe;">
                <span><i class="fa-solid fa-camera"></i> Camera Device:</span>
                <strong>${meta.camera_make || ''} ${meta.camera_model || ''}</strong>
            </div>
        `;
    }

    if (meta.date_time_original) {
        exifHtml += `
            <div class="exif-pill" style="background: rgba(56, 189, 248, 0.1); border-color: rgba(56, 189, 248, 0.3); color: #bae6fd;">
                <span><i class="fa-regular fa-calendar"></i> Captured At:</span>
                <strong>${meta.date_time_original}</strong>
            </div>
        `;
    }

    if (sanitizedAttrs.length > 0) {
        exifHtml += `
            <div style="font-size: 0.7rem; color: var(--text-muted); margin-top: 0.3rem;">
                Sanitized elements: ${sanitizedAttrs.join(', ')}
            </div>
        `;
    }

    exifContainer.innerHTML = exifHtml;

    // Render tags
    const tagsContainer = document.getElementById('modalTagsContainer');
    tagsContainer.innerHTML = (img.tags || []).map(t => `<span class="tag-chip">${escapeHtml(t.name)}</span>`).join('') || '<span style="font-size: 0.8rem; color: var(--text-dim);">No tags</span>';

    document.getElementById('imageModal').style.display = 'flex';
}

function closeModal() {
    document.getElementById('imageModal').style.display = 'none';
    currentModalImage = null;
}

async function deleteImage(imageId) {
    if (!confirm('Are you sure you want to delete this image permanently from ImageVault?')) return;

    try {
        const res = await fetch(`/api/images/${imageId}`, { method: 'DELETE' });
        if (!res.ok) throw new Error('Delete failed');

        showToast('Image deleted successfully.', 'success');
        closeModal();
        loadImages();
        loadStats();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// Stats & Aggregates
async function loadStats() {
    try {
        const res = await fetch('/api/stats');
        if (!res.ok) return;
        const stats = await res.json();

        // Header pills
        document.getElementById('statTotalImages').textContent = stats.total_images;
        document.getElementById('statSavedBytes').textContent = formatBytes(stats.total_bytes_saved);
        document.getElementById('statAvgSavings').textContent = `${stats.average_savings_percent}%`;

        // Analytics tab
        document.getElementById('analyticsTotalCount').textContent = stats.total_images;
        document.getElementById('analyticsOrigSize').textContent = formatBytes(stats.total_original_bytes);
        document.getElementById('analyticsCompSize').textContent = formatBytes(stats.total_compressed_bytes);
        document.getElementById('analyticsAvgRatio').textContent = `${stats.average_savings_percent}%`;
    } catch (err) {
        console.error('Stats loading error:', err);
    }
}

async function loadTags() {
    try {
        const res = await fetch('/api/tags');
        if (!res.ok) return;
        const tags = await res.json();
        currentTags = tags;

        const tagFilter = document.getElementById('tagFilter');
        tagFilter.innerHTML = `<option value="">All Tags (${tags.length})</option>` +
            tags.map(t => `<option value="${escapeHtml(t.name)}">${escapeHtml(t.name)} (${t.image_count})</option>`).join('');
    } catch (err) {
        console.error('Tags loading error:', err);
    }
}

// Utility Helpers
function formatBytes(bytes, decimals = 1) {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = 'toast';
    
    let icon = '<i class="fa-solid fa-circle-info" style="color: var(--accent-blue);"></i>';
    if (type === 'success') icon = '<i class="fa-solid fa-circle-check" style="color: var(--accent-green);"></i>';
    if (type === 'error') icon = '<i class="fa-solid fa-triangle-exclamation" style="color: var(--accent-red);"></i>';

    toast.innerHTML = `${icon} <span>${escapeHtml(message)}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}
