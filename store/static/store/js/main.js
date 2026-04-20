/* SRI LAKSHMI GANAPATI KIRANA - MAIN JS */

document.addEventListener('DOMContentLoaded', function () {

    // CSRF token helper
    function csrfToken() {
        const el = document.querySelector('[name=csrfmiddlewaretoken]');
        if (el) return el.value;
        const m = document.cookie.match(/csrftoken=([^;]+)/);
        return m ? m[1] : '';
    }

    // Toast notification
    function showToast(msg) {
        const t = document.getElementById('toast');
        if (!t) return;
        t.textContent = msg;
        t.classList.add('show');
        setTimeout(() => t.classList.remove('show'), 2200);
    }

    // ========================================
    // CAROUSEL (home page)
    // ========================================
    const carousel = document.getElementById('carousel');
    const dotsWrap = document.getElementById('carousel-dots');
    
    if (carousel && dotsWrap) {
        let carIdx = 0;
        const TOTAL_SLIDES = 5;

        for (let i = 0; i < TOTAL_SLIDES; i++) {
            const d = document.createElement('span');
            if (i === 0) d.classList.add('active');
            d.addEventListener('click', () => goSlide(i));
            dotsWrap.appendChild(d);
        }

        function goSlide(n) {
            carIdx = n;
            carousel.style.transform = 'translateX(-' + (n * 100) + '%)';
            dotsWrap.querySelectorAll('span').forEach((d, i) => {
                d.classList.toggle('active', i === n);
            });
        }

        function nextSlide() {
            goSlide((carIdx + 1) % TOTAL_SLIDES);
        }

        let carInterval = setInterval(nextSlide, 4000);
        carousel.parentElement.addEventListener('mouseenter', () => clearInterval(carInterval));
        carousel.parentElement.addEventListener('mouseleave', () => {
            carInterval = setInterval(nextSlide, 4000);
        });
    }

    // ========================================
    // PRODUCT CARDS
    // ========================================
    const cardState = {};

    document.querySelectorAll('.product-card').forEach(card => {
        const pid = card.dataset.id;
        if (!pid) return;

        // Find first active unit button
        const firstUnit = card.querySelector('.unit-btn.active');
        if (!firstUnit) return;

        // Initialize state
        cardState[pid] = {
            unit: firstUnit.dataset.unit,
            price: parseFloat(firstUnit.dataset.price),
            qty: 0
        };

        const priceEl = card.querySelector('.p-price');
        const qtyEl = card.querySelector('.qty-val');

        // Update price display
        function updatePrice() {
            const state = cardState[pid];
            if (!state) return;
            
            if (state.qty <= 1) {
                priceEl.textContent = '₹' + Math.round(state.price);
            } else {
                const total = Math.round(state.price * state.qty);
                priceEl.textContent = '₹' + Math.round(state.price) + ' × ' + state.qty + ' = ₹' + total;
            }
        }

        // Unit button clicks
        card.querySelectorAll('.unit-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                card.querySelectorAll('.unit-btn').forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                
                cardState[pid].unit = this.dataset.unit;
                cardState[pid].price = parseFloat(this.dataset.price);
                updatePrice();
            });
        });

        // Minus button
        const minusBtn = card.querySelector('.qty-btn.minus');
        if (minusBtn) {
            minusBtn.addEventListener('click', function() {
                cardState[pid].qty = Math.max(0, cardState[pid].qty - 1);
                qtyEl.textContent = cardState[pid].qty;
                updatePrice();
            });
        }

        // Plus button
        const plusBtn = card.querySelector('.qty-btn.plus');
        if (plusBtn) {
            plusBtn.addEventListener('click', function() {
                cardState[pid].qty += 1;
                qtyEl.textContent = cardState[pid].qty;
                updatePrice();
            });
        }

        // Add to cart button
        const addBtn = card.querySelector('.add-cart-btn');
        if (addBtn) {
            addBtn.addEventListener('click', function() {
                const state = cardState[pid];
                if (!state || state.qty === 0) {
                    showToast('Please set quantity first (+)');
                    return;
                }

                fetch('/cart/add/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken()
                    },
                    body: JSON.stringify({
                        product_id: pid,
                        unit: state.unit,
                        qty: state.qty
                    })
                })
                .then(r => r.json())
                .then(data => {
                    if (data.status === 'ok') {
                        showToast(data.message);
                        cardState[pid].qty = 0;
                        qtyEl.textContent = '0';
                        updatePrice();
                        refreshCartDrawer();
                    } else {
                        showToast(data.message);
                    }
                })
                .catch(() => showToast('Error adding to cart'));
            });
        }
    });

    // ========================================
    // CART DRAWER
    // ========================================
    const cartOverlay = document.getElementById('cart-overlay');
    const cartDrawer = document.getElementById('cart-drawer');

    function toggleCart() {
        if (!cartOverlay || !cartDrawer) return;
        cartOverlay.classList.toggle('open');
        cartDrawer.classList.toggle('open');
        if (cartDrawer.classList.contains('open')) {
            refreshCartDrawer();
        }
    }

    // Open cart triggers
    document.querySelectorAll('.cart-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            toggleCart();
        });
    });

    if (cartOverlay) {
        cartOverlay.addEventListener('click', toggleCart);
    }

    const closeBtn = document.querySelector('.cart-close');
    if (closeBtn) {
        closeBtn.addEventListener('click', toggleCart);
    }

    // Refresh cart drawer
    function refreshCartDrawer() {
        fetch('/cart/get/')
            .then(r => r.json())
            .then(data => {
                renderCartItems(data);
                updateBadges(data.item_count);
            })
            .catch(() => {});
    }

    // Render cart items
    function renderCartItems(data) {
        const container = document.getElementById('cart-items');
        const subtotalEl = document.getElementById('cart-subtotal');
        const deliveryEl = document.getElementById('cart-delivery');
        const noteEl = document.getElementById('delivery-note');
        const totalEl = document.getElementById('cart-total');
        const checkoutEl = document.getElementById('checkout-btn');

        if (!container) return;

        if (data.items.length === 0) {
            container.innerHTML = 
                '<div class="empty-cart">' +
                '<div class="empty-icon">🛒</div>' +
                '<p>Your cart is empty.<br/>Add some products!</p>' +
                '</div>';
        } else {
            container.innerHTML = data.items.map((item, idx) =>
                '<div class="cart-item">' +
                '<span class="cart-item-emoji">' + item.emoji + '</span>' +
                '<div class="cart-item-info">' +
                '<h5>' + item.name + '</h5>' +
                '<span>' + item.qty + ' × ' + item.unit + ' @ ₹' + item.unit_price + '</span>' +
                '</div>' +
                '<span class="cart-item-price">₹' + item.total + '</span>' +
                '<button class="cart-item-remove" data-index="' + idx + '">🗑</button>' +
                '</div>'
            ).join('');

            // Bind remove buttons
            container.querySelectorAll('.cart-item-remove').forEach(btn => {
                btn.addEventListener('click', function() {
                    const idx = parseInt(this.dataset.index);
                    fetch('/cart/remove/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': csrfToken()
                        },
                        body: JSON.stringify({ index: idx })
                    })
                    .then(() => refreshCartDrawer())
                    .catch(() => {});
                });
            });
        }

        if (subtotalEl) subtotalEl.textContent = '₹' + data.subtotal;
        if (deliveryEl) deliveryEl.textContent = data.delivery > 0 ? '₹' + data.delivery : 'Free';
        if (totalEl) totalEl.textContent = '₹' + data.total;

        if (noteEl) {
            if (data.items.length === 0) {
                noteEl.innerHTML = '';
            } else if (data.delivery > 0) {
                noteEl.innerHTML = 'Subtotal is below ₹500. <span class="charge">₹50 delivery charge</span> applies. Add more to get <span class="free">free delivery!</span>';
            } else {
                noteEl.innerHTML = '🎉 Great news! You qualify for <span class="free">free delivery!</span>';
            }
        }

        if (checkoutEl) {
            checkoutEl.disabled = (data.items.length === 0);
        }
    }

    // Update cart badges
    function updateBadges(count) {
        document.querySelectorAll('.cart-badge').forEach(b => {
            b.textContent = count;
        });
    }

    // ========================================
    // CHECKOUT
    // ========================================
    const checkoutBtn = document.getElementById('checkout-btn');
    if (checkoutBtn) {
        checkoutBtn.addEventListener('click', function() {
            this.disabled = true;
            this.textContent = 'Placing…';

            fetch('/order/place/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken()
                },
                body: JSON.stringify({})
            })
            .then(r => r.json())
            .then(data => {
                if (data.status === 'ok') {
                    window.location.href = '/order/confirm/';
                } else {
                    showToast(data.message);
                    checkoutBtn.disabled = false;
                    checkoutBtn.textContent = 'Place Order';
                }
            })
            .catch(() => {
                showToast('Error placing order');
                checkoutBtn.disabled = false;
                checkoutBtn.textContent = 'Place Order';
            });
        });
    }

    // Initial badge sync
    fetch('/cart/get/')
        .then(r => r.json())
        .then(data => updateBadges(data.item_count))
        .catch(() => {});

});

document.addEventListener("click", function (e) {

  if (e.target.closest(".order-status-btn")) {
    const panel = document.querySelector(".order-status-panel");
    if (!panel) return;
    panel.classList.toggle("show");
  }

});
