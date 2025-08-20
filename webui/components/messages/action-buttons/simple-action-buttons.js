// Simplified Message Action Buttons - Keeping the Great Look & Feel
import { store as speechStore } from "/components/chat/speech/speech-store.js";

// Extract text content from different message types
function getTextContent(element) {
  // Get all children except action buttons
  const textParts = [];
  // Loop through all child elements
  for (const child of element.children) {
    // Skip action buttons
    if (child.classList.contains("action-buttons")) continue;
    // If the child is an image, copy its src URL
    if (child.tagName && child.tagName.toLowerCase() === "img") {
      if (child.src) textParts.push(child.src);
      continue;
    }
    // Get text content from the child
    const text = child.innerText || "";
    if (text.trim()) {
      textParts.push(text.trim());
    }
  }
  // Join all text parts with double newlines
  return textParts.join("\n\n");
}


// Create and add action buttons to element
export function addActionButtonsToElement(element, options = {}) {
  // Skip if buttons already exist
  if (element.querySelector(".action-buttons")) return;

  // Create container with same styling as original
  const container = document.createElement("div");
  container.className = "action-buttons";

  // Copy button - matches original design
  const copyBtn = document.createElement("button");
  copyBtn.className = "action-button copy-action";
  copyBtn.setAttribute("aria-label", "Copy text");
  copyBtn.innerHTML =
    '<span class="material-symbols-outlined">content_copy</span>';

  copyBtn.onclick = async (e) => {
    e.stopPropagation();

    // Check if the button container is still fading in (opacity < 0.5)
    if (parseFloat(window.getComputedStyle(container).opacity) < 0.5) return; // Don't proceed if still fading in

    const text = getTextContent(element);
    const icon = copyBtn.querySelector(".material-symbols-outlined");

    try {
      // Try modern clipboard API
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text);
      } else {
        // Fallback for local dev
        const textarea = document.createElement("textarea");
        textarea.value = text;
        textarea.style.position = "fixed";
        textarea.style.left = "-999999px";
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand("copy");
        document.body.removeChild(textarea);
      }

      // Visual feedback
      icon.textContent = "check";
      copyBtn.classList.add("success");
      setTimeout(() => {
        icon.textContent = "content_copy";
        copyBtn.classList.remove("success");
      }, 2000);
    } catch (err) {
      console.error("Copy failed:", err);
      icon.textContent = "error";
      copyBtn.classList.add("error");
      setTimeout(() => {
        icon.textContent = "content_copy";
        copyBtn.classList.remove("error");
      }, 2000);
    }
  };

  // Speak button - matches original design
  const speakBtn = document.createElement("button");
  speakBtn.className = "action-button speak-action";
  speakBtn.setAttribute("aria-label", "Speak text");
  speakBtn.innerHTML =
    '<span class="material-symbols-outlined">volume_up</span>';

  speakBtn.onclick = async (e) => {
    e.stopPropagation();

    // Check if the button container is still fading in (opacity < 0.5)
    if (parseFloat(window.getComputedStyle(container).opacity) < 0.5) return; // Don't proceed if still fading in

    const text = getTextContent(element);
    const icon = speakBtn.querySelector(".material-symbols-outlined");

    if (!text || text.trim().length === 0) return;

    try {
      // Visual feedback
      icon.textContent = "check";
      speakBtn.classList.add("success");
      setTimeout(() => {
        icon.textContent = "volume_up";
        speakBtn.classList.remove("success");
      }, 2000);

      // Use speech store
      await speechStore.speak(text);
    } catch (err) {
      console.error("Speech failed:", err);
      icon.textContent = "error";
      speakBtn.classList.add("error");
      setTimeout(() => {
        icon.textContent = "volume_up";
        speakBtn.classList.remove("error");
      }, 2000);
    }
  };

  container.append(copyBtn, speakBtn);
  
  // Add Manual Control button for browser messages
  if (options.isBrowserMessage) {
    const controlBtn = document.createElement("button");
    controlBtn.className = "action-button browser-control-action";
    controlBtn.setAttribute("aria-label", "Manual browser control");
    controlBtn.innerHTML =
      '<span class="material-symbols-outlined">touch_app</span>';
    
    controlBtn.onclick = async (e) => {
      e.stopPropagation();
      
      // Check if the button container is still fading in (opacity < 0.5)
      if (parseFloat(window.getComputedStyle(container).opacity) < 0.5) return;
      
      const icon = controlBtn.querySelector(".material-symbols-outlined");
      
      console.log("Manual Control button clicked!");
      console.log("browserControlModalProxy available:", !!window.browserControlModalProxy);
      
      try {
        // Open browser control modal or fallback to direct API
        if (window.browserControlModalProxy) {
          console.log("Opening browser control modal...");
          await window.browserControlModalProxy.openModal();
        } else {
          console.log("Modal not available, using direct API fallback...");
          
          // Import the API function dynamically
          const { callJsonApi } = await import('/js/api.js');
          
          // Fallback: Direct API call to start browser and open DevTools URL
          const data = await callJsonApi('/browser_control_start', {
            mode: 'devtools',
            headless: false
          });
          
          if (data && data.browser && data.browser.devtools_url) {
            // Open DevTools in new tab
            window.open(data.browser.devtools_url, '_blank');
          } else {
            throw new Error('Failed to start browser session');
          }
        }
        
        // Visual feedback
        icon.textContent = "check";
        controlBtn.classList.add("success");
        setTimeout(() => {
          icon.textContent = "touch_app";
          controlBtn.classList.remove("success");
        }, 2000);
        
      } catch (err) {
        console.error("Browser control failed:", err);
        icon.textContent = "error";
        controlBtn.classList.add("error");
        setTimeout(() => {
          icon.textContent = "touch_app";
          controlBtn.classList.remove("error");
        }, 2000);
      }
    };
    
    container.appendChild(controlBtn);
  }
  
  // Add container as the first child instead of appending it
  if (element.firstChild) {
    element.insertBefore(container, element.firstChild);
  } else {
    element.appendChild(container);
  }
}
