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

// Cart Management
const cartIcon = document.getElementById('cart-icon');
const cartPopup = document.getElementById('cart-popup');
const closeCart = document.getElementById('close-cart');
const overlay = document.getElementById('overlay');

function showCart() {
    cartPopup.classList.add('active');
    overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function hideCart() {
    cartPopup.classList.remove('active');
    overlay.classList.remove('active');
    document.body.style.overflow = 'auto';
}

cartIcon.addEventListener('click', showCart);
closeCart.addEventListener('click', hideCart);
overlay.addEventListener('click', hideCart);

// Quantity buttons in cart
document.querySelectorAll('.quantity-btn.minus').forEach(btn => {
    btn.addEventListener('click', function() {
        const input = this.nextElementSibling;
        if (parseInt(input.value) > 1) {
            input.value = parseInt(input.value) - 1;
            input.dispatchEvent(new Event('change'));
        }
    });
});

document.querySelectorAll('.quantity-btn.plus').forEach(btn => {
    btn.addEventListener('click', function() {
        const input = this.previousElementSibling;
        input.value = parseInt(input.value) + 1;
        input.dispatchEvent(new Event('change'));
    });
});

// Close flash messages
document.querySelectorAll('.close-flash').forEach(btn => {
    btn.addEventListener('click', function() {
        this.parentElement.style.opacity = '0';
        setTimeout(() => {
            this.parentElement.remove();
        }, 300);
    });
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
    
    if (lowerMessage.includes('bonjour') || lowerMessage.includes('salut')) {
        return 'Bonjour ! Comment puis-je vous aider aujourd\'hui ?';
    } else if (lowerMessage.includes('produit') || lowerMessage.includes('article')) {
        return 'Nous proposons une sélection de produits alimentaires de qualité à prix réduits. Vous pouvez consulter notre catalogue dans la section "Produits".';
    } else if (lowerMessage.includes('livraison') || lowerMessage.includes('expédition')) {
        return 'Nous livrons en 24-48h partout en France. Les frais de livraison sont calculés lors de la validation du panier.';
    } else if (lowerMessage.includes('paiement') || lowerMessage.includes('payer')) {
        return 'Nous acceptons les paiements par carte bancaire, virement et en plusieurs fois via notre partenaire sécurisé.';
    } else if (lowerMessage.includes('merci')) {
        return 'Je vous en prie ! N\'hésitez pas si vous avez d\'autres questions.';
    } else {
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

function updateCartPopup() {
    fetch('/api/cart/items')
    .then(response => response.json())
    .then(items => {
        const cartItemsContainer = document.getElementById('cart-items');
        const cartTotalsContainer = document.getElementById('cart-totals');
        const viewCartBtn = document.getElementById('view-cart-btn');
        
        if (items.length === 0) {
            cartItemsContainer.innerHTML = `
                <div class="empty-cart">
                    <p>Votre panier est vide</p>
                </div>
            `;
            cartTotalsContainer.style.display = 'none';
            viewCartBtn.style.display = 'none';
        } else {
            let itemsHTML = '';
            let subtotal = 0;
            
            items.forEach(item => {
                subtotal += item.total;
                itemsHTML += `
                    <div class="cart-item">
                        <div class="cart-item-image">
                            <img src="/static/images/products/${item.image}" alt="${item.name}">
                        </div>
                        <div class="cart-item-details">
                            <h4 class="cart-item-title">${item.name}</h4>
                            <div class="cart-item-price">${item.price.toFixed(2)}€</div>
                            <div class="cart-item-actions">
                                <div class="quantity-control">
                                    <button class="quantity-btn minus" data-id="${item.id}">-</button>
                                    <input type="number" class="quantity-input" value="${item.quantity}" min="1" data-id="${item.id}">
                                    <button class="quantity-btn plus" data-id="${item.id}">+</button>
                                </div>
                                <span class="remove-item" data-id="${item.id}">Supprimer</span>
                            </div>
                        </div>
                    </div>
                `;
            });
            
            cartItemsContainer.innerHTML = itemsHTML;
            document.getElementById('cart-subtotal').textContent = subtotal.toFixed(2) + '€';
            document.getElementById('cart-total').textContent = subtotal.toFixed(2) + '€';
            cartTotalsContainer.style.display = 'block';
            viewCartBtn.style.display = 'block';
        }
    });
}

function updateCartCount(count) {
    document.getElementById('cart-count').textContent = count;
}
// Gestion de la suppression d'article
document.addEventListener('click', function(e) {
    if (e.target.closest('.remove-item')) {
        e.preventDefault();
        const productId = e.target.closest('.remove-item').getAttribute('data-id');
        removeCartItem(productId);
    }
});

function removeCartItem(productId) {
    fetch(`/supprimer-du-panier/${productId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Supprimer visuellement l'élément
            document.getElementById(`cart-item-${productId}`).remove();
            
            // Mettre à jour le compteur
            document.getElementById('cart-count').textContent = data.cart_count;
            
            // Mettre à jour les totaux
            updateCartTotals();
            
            // Afficher un message
            showFlashMessage('Produit supprimé du panier', 'success');
            
            // Si panier vide, afficher le message approprié
            if (data.cart_count === 0) {
                showEmptyCart();
            }
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showFlashMessage('Erreur lors de la suppression', 'error');
    });
}

function updateCartTotals() {
    let subtotal = 0;
    
    document.querySelectorAll('.cart-item').forEach(item => {
        const priceText = item.querySelector('.cart-item-price').textContent;
        const price = parseFloat(priceText.replace(/[^\d.,]/g, '').replace(',', '.'));
        const quantity = parseInt(item.querySelector('.quantity-input').value);
        const itemTotal = price * quantity;
        
        // Mise à jour du total par ligne
        const itemTotalElement = item.querySelector('.cart-item-total');
        if (itemTotalElement) {
            itemTotalElement.textContent = itemTotal.toFixed(2) + '€';
        }
        
        subtotal += itemTotal;
    });

    // Mise à jour du résumé de commande
    const subtotalElement = document.getElementById('cart-subtotal');
    const totalElement = document.getElementById('cart-total');
    
    if (subtotalElement) subtotalElement.textContent = subtotal.toFixed(2) + '€';
    if (totalElement) totalElement.textContent = subtotal.toFixed(2) + '€';
}

function showEmptyCart() {
    document.getElementById('cart-items').innerHTML = `
        <div class="empty-cart">
            <p>Votre panier est vide</p>
            <a href="{{ url_for('product_list') }}" class="btn">Voir nos produits</a>
        </div>
    `;
    document.getElementById('cart-totals').style.display = 'none';
    document.getElementById('view-cart-btn').style.display = 'none';
}
// Fonction pour supprimer un article du panier
function removeItem(productId) {
    if (!productId || productId === 'undefined') {
        console.error('ID de produit invalide');
        return;
    }

    fetch(`/supprimer-du-panier/${productId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Mettre à jour l'interface utilisateur
            const itemElement = document.getElementById(`item-${productId}`);
            if (itemElement) {
                itemElement.remove();
            }
            
            // Mettre à jour le compteur du panier
            document.getElementById('cart-count').textContent = data.cart_count;
            
            // Mettre à jour les totaux
            updateCartTotals();
            
            // Afficher un message
            flashMessage(data.message, 'success');
        } else {
            flashMessage(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        flashMessage('Une erreur est survenue', 'error');
    });
}

function updateCartItem(productId, quantity) {
    fetch('/modifier-panier', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ product_id: productId, quantity: quantity })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateCartPopup(); // pour le popup
            updateCartTotals(); // pour mettre à jour le total global
            updateCartCount(data.cart_count);
        }
    });
}
function recalculateFrontendCartTotals() {
    let subtotal = 0;
    document.querySelectorAll('.cart-item').forEach(item => {
        const price = parseFloat(item.querySelector('.cart-item-price').textContent.replace('€', ''));
        const quantity = parseInt(item.querySelector('.quantity-input').value);
        subtotal += price * quantity;
    });

    document.getElementById('cart-subtotal').textContent = subtotal.toFixed(2) + '€';
    document.getElementById('cart-total').textContent = subtotal.toFixed(2) + '€';
}

// Fonction pour afficher les messages flash
function flashMessage(message, type) {
    const flashContainer = document.createElement('div');
    flashContainer.className = `flash flash-${type}`;
    flashContainer.innerHTML = `
        ${message}
        <button class="close-flash">&times;</button>
    `;
    
    document.body.appendChild(flashContainer);
    
    setTimeout(() => {
        flashContainer.remove();
    }, 5000);
}

// Gestion des clics sur les boutons de suppression
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.remove-item').forEach(button => {
        button.addEventListener('click', function() {
            const productId = this.getAttribute('data-id');
            removeItem(productId);
        });
    });
});
// Modifiez la fonction removeFromCart pour bien utiliser POST et gérer les IDs invalides
function removeFromCart(productId) {
    // Validation de l'ID
    if (!productId || isNaN(productId)) {
        console.error('ID de produit invalide');
        return;
    }

    fetch(`/supprimer-du-panier/${productId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Erreur réseau');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Mise à jour de l'UI
            updateCartUI(data);
            
            // Suppression visuelle de l'élément
            const itemElement = document.querySelector(`[data-id="${productId}"]`);
            if (itemElement) {
                itemElement.closest('.cart-item').remove();
            }
            
            showFlashMessage(data.message, 'success');
        } else {
            showFlashMessage(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showFlashMessage('Erreur lors de la suppression', 'error');
    });
}

function updateCartUI(data) {
    // Mise à jour du compteur
    document.getElementById('cart-count').textContent = data.cart_count;
    
    // Mise à jour du total
    document.getElementById('cart-total').textContent = data.cart_total.toFixed(2) + ' €';
    
    // Si panier vide
    if (data.cart_count === 0) {
        document.getElementById('cart-items').innerHTML = `
            <div class="empty-cart">
                <p>Votre panier est vide</p>
                <a href="/produits" class="btn">Voir nos produits</a>
            </div>
        `;
    }
}

function showFlashMessage(message, type) {
    const flash = document.createElement('div');
    flash.className = `flash flash-${type}`;
    flash.innerHTML = `
        ${message}
        <button class="close-flash">&times;</button>
    `;
    document.body.appendChild(flash);
    setTimeout(() => flash.remove(), 3000);
}
document.addEventListener('DOMContentLoaded', function() {
    // Animation pour les cartes de mission
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

    // Gestion du formulaire de contact
    const contactForm = document.querySelector('.contact-form-section form');
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Ici vous pourriez ajouter une validation et un envoi AJAX
            alert('Merci pour votre message! Nous vous contacterons bientôt.');
            contactForm.reset();
        });
    }

    // Animation pour les témoignages
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
// Fonction pour calculer et mettre à jour les totaux
function updateCartTotals() {
    let subtotal = 0;
    
    // Calculer le sous-total à partir des articles visibles
    document.querySelectorAll('.cart-item').forEach(item => {
        const price = parseFloat(item.querySelector('.cart-item-price').textContent.replace('€', ''));
        const quantity = parseInt(item.querySelector('.quantity-input').value);
        const itemTotal = price * quantity;
        
        // Mettre à jour le total de l'article
        item.querySelector('.cart-item-total').textContent = itemTotal.toFixed(2) + '€';
        
        subtotal += itemTotal;
    });
    
    // Mettre à jour les totaux dans le résumé
    document.getElementById('cart-subtotal').textContent = subtotal.toFixed(2) + '€';
    document.getElementById('cart-total').textContent = subtotal.toFixed(2) + '€';
}

// Mettre à jour un article du panier
function updateCartItem(productId, quantity) {
    fetch('/modifier-panier', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
            product_id: productId,
            quantity: quantity
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateCartTotals(); // Mise à jour immédiate des totaux
            updateCartCount(data.cart_count);
            
            // Si dans la page panier, rafraîchir les totaux principaux
            if (window.location.pathname.includes('/panier')) {
                updateMainCartTotals();
            }
        }
    });
}

// Fonction spécifique pour la page panier
function updateMainCartTotals() {
    let subtotal = 0;
    
    document.querySelectorAll('.cart-content .cart-item').forEach(item => {
        const price = parseFloat(item.querySelector('.cart-item-price').textContent.replace('€', ''));
        const quantity = parseInt(item.querySelector('.quantity-input').value);
        subtotal += price * quantity;
    });
    
    document.querySelector('.cart-summary #cart-subtotal').textContent = subtotal.toFixed(2) + '€';
    document.querySelector('.cart-summary #cart-total').textContent = subtotal.toFixed(2) + '€';
}

// Modifiez l'écouteur d'événements pour les changements de quantité
document.addEventListener('change', function(e) {
    if (e.target.classList.contains('quantity-input')) {
        const productId = e.target.dataset.id;
        let quantity = parseInt(e.target.value);
        
        if (isNaN(quantity) || quantity < 1) {
            quantity = 1;
            e.target.value = quantity;
        }
        
        updateCartItem(productId, quantity);
    }
});

// Modifiez l'écouteur pour les boutons +/-
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('quantity-btn')) {
        const input = e.target.parentElement.querySelector('.quantity-input');
        const productId = input.dataset.id;
        let quantity = parseInt(input.value);
        
        if (e.target.classList.contains('minus')) {
            if (quantity > 1) {
                quantity--;
                input.value = quantity;
                updateCartItem(productId, quantity);
            }
        } else {
            quantity++;
            input.value = quantity;
            updateCartItem(productId, quantity);
        }
    }
});