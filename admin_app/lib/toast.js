const toast = (msg) => {
    const el = document.createElement('div');
    el.className = 'fixed bottom-4 left-1/2 -translate-x-1/2 bg-medical-dark text-white px-4 py-2 rounded shadow z-[9999]';
    el.textContent = msg;
    document.body.appendChild(el);
    setTimeout(() => { el.remove(); }, 2500);
};

window.toast = toast;

