import { createStore } from "/js/AlpineStore.js";

const model = {
    // Configuration
    scrollMargin: 60,
    prevTolerance: 35,
    nextTolerance: 5,

    init() {
        // Any initialization if needed
    },

    scrollToTop() {
        const scroller = this._getChatHistoryEl();
        if (scroller) scroller.scrollTo({ top: 0, behavior: "instant" });
    },

    scrollToBottom() {
        if (globalThis.forceScrollChatToBottom) {
            globalThis.forceScrollChatToBottom();
        } else {
             const scroller = this._getChatHistoryEl();
             if (scroller) scroller.scrollTop = scroller.scrollHeight;
        }
    },

    scrollToPrevUserMessage() {
        const scroller = this._getChatHistoryEl();
        if (!scroller) return;

        const positions = this._getUserMessagePositions(scroller);
        const scrollerRect = scroller.getBoundingClientRect();
        
        const prevThreshold = this.scrollMargin - this.prevTolerance; // 25px

        const currentIndex = positions.findIndex((p) => {
            const relativeTop = p.el.getBoundingClientRect().top - scrollerRect.top;
            return relativeTop >= prevThreshold;
        });

        if (currentIndex > 0) {
            // Go to previous message
            positions[currentIndex - 1].el.scrollIntoView({ block: "start" });
        } else if (currentIndex === 0) {
            // At the first message, scroll to top
            scroller.scrollTo({ top: 0, behavior: "instant" });
        } else if (currentIndex === -1 && positions.length > 0) {
            // All messages are above the threshold (scrolled past), scroll to bottom
            positions[positions.length - 1].el.scrollIntoView({ block: "start" });
        }
    },

    scrollToNextUserMessage() {
        const scroller = this._getChatHistoryEl();
        if (!scroller) return;

        const positions = this._getUserMessagePositions(scroller);
        const scrollerRect = scroller.getBoundingClientRect();
        
        const nextThreshold = this.scrollMargin + this.nextTolerance; // 65px

        // Find first message below the threshold
        const targetIndex = positions.findIndex((p) => {
            const relativeTop = p.el.getBoundingClientRect().top - scrollerRect.top;
            return relativeTop > nextThreshold;
        });

        if (targetIndex !== -1) {
            // Go to that message
            positions[targetIndex].el.scrollIntoView({ block: "start" });
        } else {
            // No message found below threshold => scroll to bottom
            this.scrollToBottom();
        }
    },

    // Helpers
    _getChatHistoryEl() {
        return document.getElementById("chat-history");
    },
    
    _getUserMessagePositions(scroller) {
         const userMessageEls = Array.from(
            scroller.querySelectorAll(".message-container.user-container")
          );
          // Helper for getElementTopInScroller
          const getTop = (el) => {
              const elRect = el.getBoundingClientRect();
              const scrollerRect = scroller.getBoundingClientRect();
              return elRect.top - scrollerRect.top + scroller.scrollTop;
          };

          return userMessageEls
            .map((el) => ({ el, top: getTop(el) }))
            .sort((a, b) => a.top - b.top);
    }
};

const store = createStore("chatNavigation", model);
export { store };
