function switchChapterTab(tabId) {
    // Update tab buttons
    document.querySelectorAll('.ch-tab').forEach(btn => btn.classList.remove('active'));
    event.currentTarget.classList.add('active');
    
    // Update tab content
    document.querySelectorAll('.ch-tab-content').forEach(content => content.style.display = 'none');
    
    // Display appropriate tab
    const targetTab = document.getElementById('tab-' + tabId);
    if (targetTab) {
        targetTab.style.display = (tabId === 'chat' || tabId === 'pdf') ? 'flex' : 'block';
    }
}
