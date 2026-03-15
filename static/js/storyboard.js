// Handle broken images
document.querySelectorAll('img').forEach(img => {
    img.onerror = function() {
        this.style.display = 'none';
        var errorDiv = this.parentElement.querySelector('.img-error');
        if(errorDiv) errorDiv.style.display = 'flex';
    }
});

function copyAllPrompts() {
    const prompts = [...document.querySelectorAll('.prompt-text')]
        .map((el, i) => `PANEL ${i + 1}:\n${el.textContent.trim()}`)
        .join('\n\n---\n\n');

    navigator.clipboard.writeText(prompts).then(() => {
        const btnTop = document.getElementById('copy-btn-top');
        const btnBot = document.getElementById('copy-btn-bot');

        if (!btnTop && !btnBot) return;

        const origHTMLTop = btnTop ? btnTop.innerHTML : '';
        const origHTMLBot = btnBot ? btnBot.innerHTML : '';
        
        const successContent = '<span class="material-symbols-outlined text-[18px]">check_circle</span> COPIED!';
        if (btnTop) btnTop.innerHTML = successContent;
        if (btnBot) btnBot.innerHTML = successContent;
        
        if (btnTop) btnTop.style.color = '#e7390d';
        if (btnBot) btnBot.style.color = '#e7390d';
        
        setTimeout(() => {
            if (btnTop) {
                btnTop.innerHTML = origHTMLTop;
                btnTop.style.color = '';
            }
            if (btnBot) {
                btnBot.innerHTML = origHTMLBot;
                btnBot.style.color = '';
            }
        }, 2000);
    });
}
