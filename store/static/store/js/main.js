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

        const firstUnit = card.querySelector('.unit-btn.active');
        if (!firstUnit) return;

        cardState[pid] = {
            unit: firstUnit.dataset.unit,
            price: parseFloat(firstUnit.dataset.price),
            qty: 0
        };

        const priceEl = card.querySelector('.p-price');
        const qtyEl   = card.querySelector('.qty-val');

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

        card.querySelectorAll('.unit-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                card.querySelectorAll('.unit-btn').forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                cardState[pid].unit  = this.dataset.unit;
                cardState[pid].price = parseFloat(this.dataset.price);
                updatePrice();
            });
        });

        const minusBtn = card.querySelector('.qty-btn.minus');
        if (minusBtn) {
            minusBtn.addEventListener('click', function() {
                cardState[pid].qty = Math.max(0, cardState[pid].qty - 1);
                qtyEl.textContent  = cardState[pid].qty;
                updatePrice();
            });
        }

        const plusBtn = card.querySelector('.qty-btn.plus');
        if (plusBtn) {
            plusBtn.addEventListener('click', function() {
                cardState[pid].qty += 1;
                qtyEl.textContent   = cardState[pid].qty;
                updatePrice();
            });
        }

        // ── Add to cart ──
        const addBtn = card.querySelector('.add-cart-btn');
        if (addBtn) {
            addBtn.addEventListener('click', function() {

                // ✅ NOT logged in → redirect to login
                if (typeof IS_LOGGED_IN !== 'undefined' && !IS_LOGGED_IN) {
                    window.location.href = '/login/?next=/products/';
                    return;
                }

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
                        qtyEl.textContent  = '0';
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
    const cartDrawer  = document.getElementById('cart-drawer');

    function toggleCart() {
        if (!cartOverlay || !cartDrawer) return;
        cartOverlay.classList.toggle('open');
        cartDrawer.classList.toggle('open');
        const isOpen    = cartDrawer.classList.contains('open');
        const bottomNav = document.querySelector('.bottom-nav');
        const floatBtns = document.getElementById('float-btns');
        const askAiBtn = document.getElementById('ask-ai-btn');
        if (bottomNav) bottomNav.style.display  = isOpen ? 'none' : 'flex';
        if (floatBtns) floatBtns.classList.toggle('cart-open', isOpen);
        if (askAiBtn) askAiBtn.classList.toggle('cart-open', isOpen);
        if (cartDrawer.classList.contains('open')) {
            refreshCartDrawer();
        }
    }

    document.querySelectorAll('.cart-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();

            // ✅ NOT logged in → redirect to login
            if (typeof IS_LOGGED_IN !== 'undefined' && !IS_LOGGED_IN) {
                window.location.href = '/login/?next=/products/';
                return;
            }

            toggleCart();
        });
    });

    if (cartOverlay) cartOverlay.addEventListener('click', toggleCart);

    const closeBtn = document.querySelector('.cart-close');
    if (closeBtn) closeBtn.addEventListener('click', toggleCart);

    function refreshCartDrawer() {
        fetch('/cart/get/')
            .then(r => r.json())
            .then(data => {
                renderCartItems(data);
                updateBadges(data.item_count);
            })
            .catch(() => {});
    }

    function renderCartItems(data) {
        const container  = document.getElementById('cart-items');
        const subtotalEl = document.getElementById('cart-subtotal');
        const deliveryEl = document.getElementById('cart-delivery');
        const noteEl     = document.getElementById('delivery-note');
        const totalEl    = document.getElementById('cart-total');
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
                (item.image_url
                    ? '<img class="cart-item-image" src="' + item.image_url + '" alt="">'
                    : '<span class="cart-item-emoji" aria-hidden="true">📦</span>') +
                '<div class="cart-item-info">' +
                '<h5>' + item.name + '</h5>' +
                '<span>' + item.qty + ' × ' + item.unit + ' @ ₹' + item.unit_price + '</span>' +
                '</div>' +
                '<span class="cart-item-price">₹' + item.total + '</span>' +
                '<div class="cart-quantity-controls" aria-label="Quantity controls">' +
                '<button type="button" class="cart-qty-btn" data-index="' + idx + '" data-delta="-1" aria-label="Reduce quantity">−</button>' +
                '<span class="cart-qty-value">' + item.qty + '</span>' +
                '<button type="button" class="cart-qty-btn" data-index="' + idx + '" data-delta="1" aria-label="Increase quantity">+</button>' +
                '</div>' +
                '<button class="cart-item-remove" data-index="' + idx + '">🗑</button>' +
                '</div>'
            ).join('');

            container.querySelectorAll('.cart-qty-btn').forEach(btn => {
                btn.addEventListener('click', function() {
                    const index = parseInt(this.dataset.index, 10);
                    const delta = parseInt(this.dataset.delta, 10);
                    container.querySelectorAll('.cart-qty-btn').forEach(control => control.disabled = true);

                    fetch('/cart/update/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': csrfToken()
                        },
                        body: JSON.stringify({ index, delta })
                    })
                    .then(r => r.json())
                    .then(data => {
                        if (data.status !== 'ok') showToast(data.message || 'Unable to update quantity');
                        refreshCartDrawer();
                    })
                    .catch(() => {
                        showToast('Unable to update quantity');
                        refreshCartDrawer();
                    });
                });
            });

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
        if (deliveryEl) deliveryEl.textContent  = data.delivery > 0 ? '₹' + data.delivery : 'Free';
        if (totalEl)    totalEl.textContent      = '₹' + data.total;

        if (noteEl) {
            if (data.items.length === 0) {
                noteEl.innerHTML = '';
            } else if (data.delivery > 0) {
                noteEl.innerHTML = 'Subtotal is below ₹500. <span class="charge">₹50 delivery charge</span> applies. Add more to get <span class="free">free delivery!</span>';
            } else {
                noteEl.innerHTML = '🎉 Great news! You qualify for <span class="free">free delivery!</span>';
            }
        }

        if (checkoutEl) checkoutEl.disabled = (data.items.length === 0);
    }

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
            this.disabled    = true;
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
                    checkoutBtn.disabled    = false;
                    checkoutBtn.textContent = 'Place Order';
                }
            })
            .catch(() => {
                showToast('Error placing order');
                checkoutBtn.disabled    = false;
                checkoutBtn.textContent = 'Place Order';
            });
        });
    }

    // Initial badge sync — only if logged in
    if (typeof IS_LOGGED_IN !== 'undefined' && IS_LOGGED_IN) {
        fetch('/cart/get/')
            .then(r => r.json())
            .then(data => updateBadges(data.item_count))
            .catch(() => {});
    }

});

document.addEventListener("click", function (e) {
    if (e.target.closest(".order-status-btn")) {
        const panel = document.querySelector(".order-status-panel");
        if (!panel) return;
        panel.classList.toggle("show");
    }
});

const hamburger = document.getElementById('hamburger');
const mobileMenu = document.getElementById('mobile-menu');

if (hamburger && mobileMenu) {
    const closeMobileMenu = () => {
        mobileMenu.classList.remove('active');
        hamburger.setAttribute('aria-expanded', 'false');
    };

    hamburger.addEventListener('click', (event) => {
        event.stopPropagation();
        const isOpen = mobileMenu.classList.toggle('active');
        hamburger.setAttribute('aria-expanded', String(isOpen));
    });

    document.addEventListener('click', (event) => {
        if (mobileMenu.classList.contains('active') &&
            !mobileMenu.contains(event.target) &&
            !hamburger.contains(event.target)) {
            closeMobileMenu();
        }
    });
}
