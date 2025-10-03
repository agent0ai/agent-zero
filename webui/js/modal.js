// Full-Screen Input Modal logic moved to /components/modals/full-screen-store.js
// Keep only other modals here.

const genericModalProxy = {
    isOpen: false,
    isLoading: false,
    title: '',
    description: '',
    html: '',

    async openModal(title, description, html, contentClasses = []) {
        const modalEl = document.getElementById('genericModal');
        const modalContent = document.getElementById('viewer');
        const modalAD = Alpine.$data(modalEl);

        modalAD.isOpen = true;
        modalAD.title = title
        modalAD.description = description
        modalAD.html = html

        modalContent.className = 'modal-content';
        modalContent.classList.add(...contentClasses);
    },

    handleClose() {
        this.isOpen = false;
    }
}

// Wait for Alpine to be ready
document.addEventListener('alpine:init', () => {
    Alpine.data('genericModalProxy', () => ({
        init() {
            Object.assign(this, genericModalProxy);
            // Ensure immediate file fetch when modal opens
            this.$watch('isOpen', async (value) => {
               // what now?
            });
        }
    }));
});

// Keep the global assignment for backward compatibility
window.genericModalProxy = genericModalProxy;