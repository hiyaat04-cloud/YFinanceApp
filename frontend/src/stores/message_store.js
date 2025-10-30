import { ref } from 'vue'; // Import computed only if needed, ref is sufficient here
import { defineStore } from 'pinia';

export const useMessageStore = defineStore('message_store', () => {
    // --- State ---
    const flash_message = ref(''); // Reactive variable to hold the message

    // --- Actions ---
    function setFlashMessage(message) {
        flash_message.value = message; // Set the message
        // Automatically clear the message after 5000 milliseconds (5 seconds)
        setTimeout(() => {
            // Only clear if the current message is still the one we set
            if (flash_message.value === message) {
                flash_message.value = '';
            }
        }, 5000);
    }

    function clearFlashMessage() {
        // Manually clear the message (e.g., when the user clicks the close button)
        flash_message.value = '';
    }

    // --- Getters ---
    // Simple getter function (can also use computed if more complex logic is needed)
    function getFlashMessage() {
        return flash_message.value;
    }

    // --- Return public API ---
    return {
        // State (not usually returned directly, accessed via getters)
        // flash_message, // Can expose if needed, but getters are safer

        // Getters
        getFlashMessage, // Call as: messageStore.getFlashMessage()

        // Actions
        setFlashMessage, // Call as: messageStore.setFlashMessage("Your message")
        clearFlashMessage // Call as: messageStore.clearFlashMessage()
    };
});
