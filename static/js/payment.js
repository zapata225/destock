// Formatage du numéro de carte
document.getElementById('card_number')?.addEventListener('input', function(e) {
    let value = this.value.replace(/\s+/g, '');
    if (value.length > 16) value = value.substr(0, 16);
    
    let formatted = '';
    for (let i = 0; i < value.length; i++) {
        if (i > 0 && i % 4 === 0) formatted += ' ';
        formatted += value[i];
    }
    
    this.value = formatted;
});

// Formatage de la date d'expiration
document.getElementById('expiry_date')?.addEventListener('input', function(e) {
    let value = this.value.replace(/\D/g, '');
    if (value.length > 4) value = value.substr(0, 4);
    
    if (value.length > 2) {
        value = value.substr(0, 2) + '/' + value.substr(2);
    }
    
    this.value = value;
});

// Formatage de l'IBAN
document.getElementById('iban')?.addEventListener('input', function(e) {
    let value = this.value.replace(/\s+/g, '').toUpperCase();
    if (value.length > 27) value = value.substr(0, 27);
    
    let formatted = '';
    for (let i = 0; i < value.length; i++) {
        if (i > 0 && i % 4 === 0) formatted += ' ';
        formatted += value[i];
    }
    
    this.value = formatted;
});

// Clavier virtuel
document.querySelector('.virtual-keyboard-btn')?.addEventListener('click', function() {
    const keyboard = document.querySelector('.virtual-keyboard-container');
    keyboard.style.display = keyboard.style.display === 'none' ? 'block' : 'none';
});

document.querySelectorAll('.keyboard-key')?.forEach(key => {
    key.addEventListener('click', function() {
        const passwordInput = document.getElementById('password');
        
        if (this.classList.contains('special')) {
            if (this.querySelector('i')?.classList.contains('fa-backspace')) {
                // Effacer
                passwordInput.value = passwordInput.value.slice(0, -1);
            } else {
                // Effacer tout
                passwordInput.value = '';
            }
        } else {
            // Ajouter le chiffre
            passwordInput.value += this.textContent;
        }
    });
});

// Détection du type de carte
document.getElementById('card_number')?.addEventListener('input', function() {
    const cardNumber = this.value.replace(/\s+/g, '');
    const cardIcon = document.querySelector('.card-type-icon');
    
    if (!cardIcon) return;
    
    // Visa
    if (/^4/.test(cardNumber)) {
        cardIcon.className = 'fab fa-cc-visa';
    } 
    // Mastercard
    else if (/^5[1-5]/.test(cardNumber)) {
        cardIcon.className = 'fab fa-cc-mastercard';
    } 
    // American Express
    else if (/^3[47]/.test(cardNumber)) {
        cardIcon.className = 'fab fa-cc-amex';
    } 
    // Discover
    else if (/^6(?:011|5)/.test(cardNumber)) {
        cardIcon.className = 'fab fa-cc-discover';
    } 
    // Default
    else {
        cardIcon.className = 'far fa-credit-card';
    }
});