// Mobile Menu
const mobileMenuBtn = document.getElementById('mobile-menu-btn');
const mobileMenu = document.getElementById('mobile-menu');
const closeMobileMenu = document.getElementById('close-mobile-menu');

mobileMenuBtn.addEventListener('click', () => {
    mobileMenu.classList.add('active');
    overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
});

closeMobileMenu.addEventListener('click', () => {
    mobileMenu.classList.remove('active');
    overlay.classList.remove('active');
    document.body.style.overflow = 'auto';
});
// Chatbot
const chatbotBtn = document.getElementById('chatbot-btn');
const chatbotContainer = document.getElementById('chatbot-container');
const closeChatbot = document.getElementById('close-chatbot');
const chatbotMessages = document.getElementById('chatbot-messages');
const chatbotInput = document.getElementById('chatbot-input');
const sendMessageBtn = document.getElementById('send-message');

function toggleChatbot() {
    chatbotContainer.classList.toggle('active');
}

function sendMessage() {
    const message = chatbotInput.value.trim();
    if (message) {
        // Add user message
        const userMessage = document.createElement('div');
        userMessage.className = 'message user-message';
        userMessage.textContent = message;
        chatbotMessages.appendChild(userMessage);

        // Bot response
        setTimeout(() => {
            const botMessage = document.createElement('div');
            botMessage.className = 'message bot-message';
            botMessage.textContent = getBotResponse(message);
            chatbotMessages.appendChild(botMessage);
            chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
        }, 500);

        chatbotInput.value = '';
        chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
    }
}

function getBotResponse(message) {
    const lowerMessage = message.toLowerCase();
    
    // Salutations
    if (lowerMessage.includes('bonjour') || lowerMessage.includes('salut')) {
        return 'Bonjour ! Comment puis-je vous aider aujourd\'hui ?';
    } 

    // Produits
    else if (lowerMessage.includes('produit') || lowerMessage.includes('article') || lowerMessage.includes('qu\'avez-vous')) {
        return 'Nous proposons une large sélection de produits alimentaires à prix réduits : des produits frais, des surgelés, des boissons, des produits d\'épicerie, et plus encore ! Vous pouvez consulter notre catalogue dans la section "Produits".';
    }

    // Livraison
    else if (lowerMessage.includes('livraison') || lowerMessage.includes('expédition') || lowerMessage.includes('délais')) {
        return 'Nous livrons en 24-48h partout en France. Les frais de livraison sont calculés lors de la validation du panier, selon votre localisation.';
    }

    // Paiement
    else if (lowerMessage.includes('paiement') || lowerMessage.includes('payer') || lowerMessage.includes('carte bancaire')) {
        return 'Nous acceptons plusieurs modes de paiement : carte bancaire (Visa, MasterCard), virement bancaire, et paiement en plusieurs fois via notre partenaire sécurisé.';
    }

    // Produits populaires
    else if (lowerMessage.includes('produit populaire') || lowerMessage.includes('produits tendance') || lowerMessage.includes('quels sont vos bestsellers')) {
        return 'Nos produits les plus populaires incluent des fromages frais, du beurre, des yaourts, ainsi que des légumes surgelés et des boissons gazeuses à prix réduits !';
    }

    // Offres et promotions
    else if (lowerMessage.includes('promotions') || lowerMessage.includes('offres') || lowerMessage.includes('réduction')) {
        return 'Nous avons des promotions exceptionnelles chaque semaine ! N\'hésitez pas à consulter notre page "Promotions" pour découvrir les offres actuelles.';
    }

    // FAQ
    else if (lowerMessage.includes('faq') || lowerMessage.includes('questions fréquentes')) {
        return 'Pour plus d\'informations, consultez notre section "FAQ" où nous répondons aux questions courantes sur les produits, la livraison et les retours.';
    }

    // Retour et remboursement
    else if (lowerMessage.includes('retour') || lowerMessage.includes('remboursement') || lowerMessage.includes('garantie')) {
        return 'Si vous souhaitez retourner un produit ou demander un remboursement, vous pouvez consulter notre politique de retour dans la section "Retour et Remboursement". Nous offrons une garantie de satisfaction à 100%.';
    }

    // Contact
    else if (lowerMessage.includes('contact') || lowerMessage.includes('joindre') || lowerMessage.includes('aide')) {
        return 'Si vous avez besoin de nous contacter, vous pouvez nous envoyer un email à contact@destockage-alimentaire.com ou appeler le 01 23 45 67 89. Nous sommes là pour vous aider !';
    }

    // À propos
    else if (lowerMessage.includes('à propos') || lowerMessage.includes('information sur l\'entreprise')) {
        return 'Destockage Alimentaire est une entreprise spécialisée dans la vente de produits alimentaires de qualité à prix réduits. Nous avons plusieurs magasins en France et un service de livraison rapide. Notre mission est de rendre les produits de marque accessibles à tous.';
    }

    // Demander des informations sur les horaires
    else if (lowerMessage.includes('horaires') || lowerMessage.includes('ouvert')) {
        return 'Nos magasins sont ouverts du lundi au samedi de 9h à 18h. Vous pouvez également passer commande en ligne à tout moment.';
    }

    // Autres
    else if (lowerMessage.includes('merci') || lowerMessage.includes('merci beaucoup')) {
        return 'Je vous en prie ! N\'hésitez pas si vous avez d\'autres questions.';
    }

    // Message par défaut si la question est trop vague
    else {
        return 'Je ne suis pas sûr de comprendre. Pouvez-vous reformuler votre question ? Sinon, vous pouvez nous contacter directement via la page "Contact".';
    }
}

chatbotBtn.addEventListener('click', toggleChatbot);
closeChatbot.addEventListener('click', toggleChatbot);
sendMessageBtn.addEventListener('click', sendMessage);
chatbotInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendMessage();
    }
});


// Payment method selection
document.querySelectorAll('input[name="payment_method"]').forEach(radio => {
    radio.addEventListener('change', function() {
        document.querySelectorAll('.payment-form').forEach(form => {
            form.classList.remove('active');
        });
        
        const selectedForm = document.getElementById(`${this.id}-form`);
        if (selectedForm) {
            selectedForm.classList.add('active');
        }
    });
});

// Credit card formatting
const cardNumberInput = document.getElementById('card-number');
if (cardNumberInput) {
    cardNumberInput.addEventListener('input', function() {
        let value = this.value.replace(/\s+/g, '');
        if (value.length > 16) value = value.substr(0, 16);
        
        let formatted = '';
        for (let i = 0; i < value.length; i++) {
            if (i > 0 && i % 4 === 0) formatted += ' ';
            formatted += value[i];
        }
        
        this.value = formatted;
    });
}

// Expiry date formatting
const expiryDateInput = document.getElementById('expiry-date');
if (expiryDateInput) {
    expiryDateInput.addEventListener('input', function() {
        let value = this.value.replace(/\D/g, '');
        if (value.length > 4) value = value.substr(0, 4);
        
        if (value.length > 2) {
            value = value.substr(0, 2) + '/' + value.substr(2);
        }
        
        this.value = value;
    });
}

// Virtual keyboard for IBAN input
const showKeyboardBtn = document.getElementById('show-keyboard');
const virtualKeyboard = document.getElementById('virtual-keyboard');
const ibanInput = document.getElementById('iban');

if (showKeyboardBtn && virtualKeyboard && ibanInput) {
    showKeyboardBtn.addEventListener('click', () => {
        virtualKeyboard.classList.toggle('active');
    });
    
    document.querySelectorAll('.keyboard-key').forEach(key => {
        key.addEventListener('click', () => {
            const keyValue = key.getAttribute('data-key');
            
            if (keyValue === 'backspace') {
                ibanInput.value = ibanInput.value.slice(0, -1);
            } else {
                ibanInput.value += keyValue;
            }
        });
    });
}

// Close flash messages
document.querySelectorAll('.close-flash').forEach(btn => {
    btn.addEventListener('click', function() {
        this.parentElement.style.opacity = '0';
        setTimeout(() => {
            this.parentElement.remove();
        }, 300);
    });
});

// Animation for mission cards
document.addEventListener('DOMContentLoaded', function() {
    const missionCards = document.querySelectorAll('.mission-card');
    missionCards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = `opacity 0.5s ease ${index * 0.1}s, transform 0.5s ease ${index * 0.1}s`;
        
        setTimeout(() => {
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, 100);
    });

    // Animation for testimonials
    const testimonialCards = document.querySelectorAll('.testimonial-card');
    testimonialCards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'scale(0.95)';
        card.style.transition = `opacity 0.5s ease ${index * 0.2}s, transform 0.5s ease ${index * 0.2}s`;
        
        setTimeout(() => {
            card.style.opacity = '1';
            card.style.transform = 'scale(1)';
        }, 100);
    });
});