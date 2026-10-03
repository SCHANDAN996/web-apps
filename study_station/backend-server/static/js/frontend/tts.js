function speakNotes() {
    if (!window.speechSynthesis) {
        alert("Text-to-speech is not supported in your browser.");
        return;
    }
    
    // Stop any current speech
    window.speechSynthesis.cancel();
    
    // Extract plain text from AI Notes HTML
    const htmlContent = document.getElementById('aiNotesContent').innerHTML;
    const tempDiv = document.createElement("div");
    tempDiv.innerHTML = htmlContent;
    const plainText = tempDiv.textContent || tempDiv.innerText || "";
    
    if (!plainText.trim()) {
        alert("No notes available to read.");
        return;
    }
    
    const utterance = new SpeechSynthesisUtterance(plainText);
    utterance.lang = 'en-IN'; // Indian English Accent
    utterance.rate = 0.9; // Slightly slower for clear understanding
    
    window.speechSynthesis.speak(utterance);
}

// Stop speaking if user leaves page
window.addEventListener('beforeunload', () => {
    if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
    }
});
