document.addEventListener('DOMContentLoaded', function() {
    // Gestion des onglets
    const tabLinks = document.querySelectorAll('[data-tab]');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Retirer la classe active de tous les liens et contenus
            tabLinks.forEach(l => l.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            // Ajouter la classe active au lien cliqué
            this.classList.add('active');
            
            // Afficher le contenu correspondant
            const tabId = this.getAttribute('data-tab');
            document.getElementById(tabId).classList.add('active');
        });
    });
    
    // Gestion de l'édition d'adresse
    const editAddressBtn = document.querySelector('.edit-address');
    const cancelEditBtn = document.querySelector('.cancel-edit');
    const editAddressForm = document.querySelector('.edit-address-form');
    
    if (editAddressBtn && editAddressForm) {
        editAddressBtn.addEventListener('click', function() {
            editAddressForm.style.display = 'block';
        });
        
        cancelEditBtn.addEventListener('click', function() {
            editAddressForm.style.display = 'none';
        });
    }
    
    // Gestion de l'ajout de carte de crédit
    const addPaymentToggle = document.querySelector('.add-payment-toggle');
    const cancelAddPayment = document.querySelector('.cancel-add-payment');
    const addPaymentForm = document.querySelector('.add-payment-form');
    
    if (addPaymentToggle && addPaymentForm) {
        addPaymentToggle.addEventListener('click', function() {
            addPaymentForm.style.display = addPaymentForm.style.display === 'none' ? 'block' : 'none';
        });
        
        cancelAddPayment.addEventListener('click', function() {
            addPaymentForm.style.display = 'none';
        });
    }
    
    // Formatage du numéro de carte
    const cardNumberInput = document.getElementById('card_number');
    if (cardNumberInput) {
        cardNumberInput.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\s+/g, '');
            if (value.length > 16) value = value.substr(0, 16);
            
            let formatted = '';
            for (let i = 0; i < value.length; i++) {
                if (i > 0 && i % 4 === 0) formatted += ' ';
                formatted += value[i];
            }
            
            e.target.value = formatted;
        });
    }
    
    // Formatage de la date d'expiration
    const expiryInput = document.getElementById('card_expiry');
    if (expiryInput) {
        expiryInput.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 4) value = value.substr(0, 4);
            
            if (value.length > 2) {
                value = value.substr(0, 2) + '/' + value.substr(2);
            }
            
            e.target.value = value;
        });
    }
    
    // Validation du formulaire de changement de mot de passe
    const passwordForm = document.getElementById('change-password-form');
    if (passwordForm) {
        passwordForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const newPassword = document.getElementById('new_password').value;
            const confirmPassword = document.getElementById('confirm_password').value;
            
            if (newPassword !== confirmPassword) {
                alert('Les mots de passe ne correspondent pas');
                return;
            }
            
            // Ici, vous pourriez ajouter un appel AJAX pour changer le mot de passe
            alert('Mot de passe changé avec succès');
            this.reset();
        });
    }
    
    // Activation du premier onglet par défaut
    if (tabLinks.length > 0) {
        tabLinks[0].click();
    }
    
    // Gestion de l'URL hash au chargement
    if (window.location.hash) {
        const tabLink = document.querySelector(`[data-tab="${window.location.hash.substring(1)}"]`);
        if (tabLink) {
            tabLink.click();
        }
    }
});
document.addEventListener('DOMContentLoaded', function() {
    // Gestion des onglets
    const tabs = document.querySelectorAll('.account-menu a');
    tabs.forEach(tab => {
        tab.addEventListener('click', function(e) {
            e.preventDefault();
            const tabId = this.getAttribute('data-tab');
            
            // Masquer tous les contenus d'onglets
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            
            // Désactiver tous les onglets
            tabs.forEach(t => {
                t.classList.remove('active');
            });
            
            // Activer l'onglet courant
            this.classList.add('active');
            document.getElementById(tabId).classList.add('active');
        });
    });

    // Gestion des adresses
    const editAddressBtn = document.querySelector('.edit-address');
    const editAddressForm = document.querySelector('.edit-address-form');
    const cancelEditBtn = document.querySelector('.cancel-edit');
    
    if (editAddressBtn) {
        editAddressBtn.addEventListener('click', function() {
            this.style.display = 'none';
            editAddressForm.style.display = 'block';
        });
    }
    
    if (cancelEditBtn) {
        cancelEditBtn.addEventListener('click', function() {
            editAddressForm.style.display = 'none';
            editAddressBtn.style.display = 'block';
        });
    }

    // Gestion des cartes de paiement
    const addPaymentToggle = document.querySelector('.add-payment-toggle');
    const addPaymentForm = document.querySelector('.add-payment-form');
    const cancelAddPayment = document.querySelector('.cancel-add-payment');
    
    if (addPaymentToggle) {
        addPaymentToggle.addEventListener('click', function() {
            this.style.display = 'none';
            addPaymentForm.style.display = 'block';
        });
    }
    
    if (cancelAddPayment) {
        cancelAddPayment.addEventListener('click', function() {
            addPaymentForm.style.display = 'none';
            addPaymentToggle.style.display = 'block';
        });
    }

    // Gestion des actions sur les commandes
    document.querySelectorAll('.btn-danger').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const orderId = this.closest('tr').querySelector('td:first-child').textContent;
            if (confirm(`Voulez-vous vraiment annuler la commande ${orderId} ?`)) {
                cancelOrder(orderId);
            }
        });
    });

    // Gestion des cartes par défaut
    document.querySelectorAll('.card-actions .btn-outline').forEach(btn => {
        btn.addEventListener('click', function() {
            const cardId = this.closest('.payment-card').dataset.cardId;
            setDefaultCard(cardId);
        });
    });

    // Gestion de la suppression de cartes
    document.querySelectorAll('.card-actions .btn-danger').forEach(btn => {
        btn.addEventListener('click', function() {
            const cardId = this.closest('.payment-card').dataset.cardId;
            if (confirm('Voulez-vous vraiment supprimer cette carte ?')) {
                deleteCard(cardId);
            }
        });
    });
});

// Fonctions API
async function cancelOrder(orderId) {
    try {
        const response = await fetch('/api/orders/cancel', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ order_id: orderId })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('Commande annulée avec succès');
            location.reload();
        } else {
            alert('Erreur: ' + data.message);
        }
    } catch (error) {
        console.error('Erreur:', error);
        alert('Une erreur est survenue');
    }
}

async function setDefaultCard(cardId) {
    try {
        const response = await fetch('/api/cards/default', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ card_id: cardId })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('Carte définie par défaut avec succès');
            location.reload();
        } else {
            alert('Erreur: ' + data.message);
        }
    } catch (error) {
        console.error('Erreur:', error);
        alert('Une erreur est survenue');
    }
}

async function deleteCard(cardId) {
    try {
        const response = await fetch('/api/cards/delete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ card_id: cardId })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('Carte supprimée avec succès');
            location.reload();
        } else {
            alert('Erreur: ' + data.message);
        }
    } catch (error) {
        console.error('Erreur:', error);
        alert('Une erreur est survenue');
    }
}
document.addEventListener('DOMContentLoaded', function() {
    // Gestion des onglets
    const tabs = document.querySelectorAll('.account-menu a');
    tabs.forEach(tab => {
        tab.addEventListener('click', function(e) {
            e.preventDefault();
            const tabId = this.getAttribute('data-tab');
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            document.querySelectorAll('.account-menu a').forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            document.getElementById(tabId).classList.add('active');
        });
    });

    // Gestion des adresses
    const addAddressBtn = document.getElementById('add-address-btn');
    const addressFormContainer = document.getElementById('address-form-container');
    const addressForm = document.getElementById('address-form');
    const cancelAddressBtn = document.getElementById('cancel-address-btn');
    const editAddressBtns = document.querySelectorAll('.edit-address-btn');
    const deleteAddressForms = document.querySelectorAll('.delete-address-form');

    if (addAddressBtn) {
        addAddressBtn.addEventListener('click', function() {
            document.getElementById('address-form-title').textContent = 'Ajouter une adresse';
            document.getElementById('address-id').value = '';
            addressForm.reset();
            addressFormContainer.style.display = 'block';
            window.scrollTo({ top: addressFormContainer.offsetTop, behavior: 'smooth' });
        });
    }

    if (cancelAddressBtn) {
        cancelAddressBtn.addEventListener('click', function() {
            addressFormContainer.style.display = 'none';
        });
    }

    editAddressBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const addressId = this.getAttribute('data-address-id');
            const addressCard = document.querySelector(`.address-card[data-address-id="${addressId}"]`);
            
            // Remplir le formulaire avec les données existantes
            document.getElementById('address-form-title').textContent = 'Modifier l\'adresse';
            document.getElementById('address-id').value = addressId;
            document.getElementById('address-label').value = addressCard.querySelector('h3').textContent;
            // ... Remplir les autres champs ...
            
            addressFormContainer.style.display = 'block';
            window.scrollTo({ top: addressFormContainer.offsetTop, behavior: 'smooth' });
        });
    });

    deleteAddressForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!confirm('Voulez-vous vraiment supprimer cette adresse ?')) {
                e.preventDefault();
            }
        });
    });

    // Gestion des cartes de paiement
    const addPaymentToggle = document.getElementById('add-payment-toggle');
    const addPaymentForm = document.getElementById('add-payment-form');
    const cancelPaymentBtn = document.getElementById('cancel-payment-btn');
    const setDefaultForms = document.querySelectorAll('.set-default-form');
    const deleteCardForms = document.querySelectorAll('.delete-card-form');

    if (addPaymentToggle && addPaymentForm) {
        addPaymentToggle.addEventListener('click', function() {
            addPaymentForm.style.display = 'block';
            window.scrollTo({ top: addPaymentForm.offsetTop, behavior: 'smooth' });
        });
    }

    if (cancelPaymentBtn) {
        cancelPaymentBtn.addEventListener('click', function() {
            addPaymentForm.style.display = 'none';
        });
    }

    setDefaultForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!confirm('Définir cette carte comme moyen de paiement par défaut ?')) {
                e.preventDefault();
            }
        });
    });

    deleteCardForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!confirm('Voulez-vous vraiment supprimer cette carte ?')) {
                e.preventDefault();
            }
        });
    });

    // Gestion des commandes
    const cancelOrderForms = document.querySelectorAll('.cancel-order-form');
    
    cancelOrderForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!confirm('Voulez-vous vraiment annuler cette commande ?')) {
                e.preventDefault();
            }
        });
    });

    // Formatage des inputs
    document.getElementById('card-number')?.addEventListener('input', function(e) {
        this.value = this.value.replace(/\D/g, '').replace(/(\d{4})(?=\d)/g, '$1 ');
    });

    document.getElementById('card-expiry')?.addEventListener('input', function(e) {
        this.value = this.value.replace(/\D/g, '').replace(/(\d{2})(?=\d)/g, '$1/');
    });
});
// Gestion des onglets
document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', function(e) {
        e.preventDefault();
        
        // Active l'onglet cliqué
        document.querySelectorAll('.nav-link').forEach(item => {
            item.classList.remove('active');
        });
        this.classList.add('active');
        
        // Affiche la section correspondante
        const tab = this.getAttribute('data-tab');
        document.querySelectorAll('.account-section').forEach(section => {
            section.style.display = 'none';
        });
        document.getElementById(`${tab}-section`).style.display = 'block';
    });
});
// Formulaire de profil
const editProfileBtn = document.getElementById('edit-profile-btn');
const profileForm = document.getElementById('profile-form');

editProfileBtn.addEventListener('click', function() {
    profileForm.style.display = profileForm.style.display === 'none' ? 'block' : 'none';
});

profileForm.addEventListener('submit', function(e) {
    e.preventDefault();
    
    fetch("{{ url_for('save_profile') }}", {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams(new FormData(this))
    })
    .then(response => {
        if (response.ok) {
            window.location.reload();
        }
    });
});
// Formulaire d'adresse
const editAddressBtn = document.getElementById('edit-address-btn');
const addressForm = document.getElementById('address-form');

editAddressBtn.addEventListener('click', function() {
    addressForm.style.display = addressForm.style.display === 'none' ? 'block' : 'none';
});

// Suppression d'adresse
document.getElementById('delete-address-btn')?.addEventListener('click', function() {
    if (confirm('Supprimer cette adresse ?')) {
        fetch("{{ url_for('save_address') }}", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: 'action=delete'
        }).then(response => {
            if (response.ok) {
                window.location.reload();
            }
        });
    }
});
// Ajout de carte
document.getElementById('add-payment-btn').addEventListener('click', function() {
    document.getElementById('payment-form').style.display = 'block';
});

// Définir comme carte par défaut
document.querySelectorAll('.card-btn-default').forEach(btn => {
    btn.addEventListener('click', function() {
        const cardId = this.dataset.cardId;
        fetch("{{ url_for('set_default_card') }}", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `card_id=${cardId}`
        }).then(response => {
            if (response.ok) {
                window.location.reload();
            }
        });
    });
});
// Changement de mot de passe
document.getElementById('change-password-btn').addEventListener('click', function() {
    document.getElementById('password-form').style.display = 'block';
});

document.getElementById('password-form').addEventListener('submit', function(e) {
    e.preventDefault();
    
    fetch("{{ url_for('change_password') }}", {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams(new FormData(this))
    }).then(response => {
        if (response.ok) {
            window.location.reload();
        }
    });
});
document.querySelector('.nav-link[data-tab="profile"]').click();

document.getElementById('delete-address-btn')?.addEventListener('click', function() {
    if (confirm('Êtes-vous sûr de vouloir supprimer cette adresse ?')) {
        fetch("{{ url_for('save_address') }}", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: 'action=delete'
        }).then(response => {
            if (response.ok) {
                window.location.reload();
            }
        });
    }
});
