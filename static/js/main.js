(function () {
    'use strict';

    function initNavToggle() {
        var toggle = document.getElementById('navToggle');
        var menu = document.getElementById('navMenu');

        if (!toggle || !menu) return;

        toggle.addEventListener('click', function () {
            var isOpen = menu.classList.toggle('navbar__menu--active');
            toggle.setAttribute('aria-expanded', isOpen);
        });

        menu.querySelectorAll('.navbar__link').forEach(function (link) {
            link.addEventListener('click', function () {
                menu.classList.remove('navbar__menu--active');
                toggle.setAttribute('aria-expanded', 'false');
            });
        });
    }

    function initAlerts() {
        document.querySelectorAll('.alert').forEach(function (alert) {
            var closeBtn = alert.querySelector('.alert__close');
            if (closeBtn) {
                closeBtn.addEventListener('click', function () {
                    dismissAlert(alert);
                });
            }

            setTimeout(function () {
                dismissAlert(alert);
            }, 5000);
        });
    }

    function dismissAlert(el) {
        el.style.opacity = '0';
        el.style.transform = 'translateY(-8px)';
        el.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        setTimeout(function () {
            el.remove();
        }, 300);
    }

    function initFormErrorModal() {
        var errorModal = document.getElementById('errorModal');
        if (!errorModal) return;

        var fieldErrors = document.querySelectorAll('.form-field-errors li, .form-errors__item');
        if (fieldErrors.length === 0) return;

        var errorList = errorModal.querySelector('.error-modal__list');
        if (!errorList) return;

        var groups = {};
        document.querySelectorAll('.form-group--error').forEach(function (group) {
            var label = group.querySelector('.form-label');
            var errors = group.querySelectorAll('.form-field-errors li');
            if (label && errors.length > 0) {
                var fieldName = label.textContent.replace('*', '').trim();
                groups[fieldName] = [];
                errors.forEach(function (err) {
                    groups[fieldName].push(err.textContent.trim());
                });
            }
        });

        var nonFieldErrors = document.querySelectorAll('.form-errors__item');
        if (nonFieldErrors.length > 0) {
            groups['General'] = [];
            nonFieldErrors.forEach(function (err) {
                groups['General'].push(err.textContent.trim());
            });
        }

        errorList.innerHTML = '';
        Object.keys(groups).forEach(function (field) {
            var li = document.createElement('li');
            li.className = 'error-modal__field';
            var strong = document.createElement('strong');
            strong.textContent = field + ': ';
            li.appendChild(strong);
            li.appendChild(document.createTextNode(groups[field].join(', ')));
            errorList.appendChild(li);
        });

        errorModal.classList.add('modal--active');
        document.body.style.overflow = 'hidden';

        var closeBtn = errorModal.querySelector('.modal__close');
        var okBtn = errorModal.querySelector('.error-modal__ok');
        var overlay = errorModal.querySelector('.modal__overlay');

        function closeErrorModal() {
            errorModal.classList.remove('modal--active');
            document.body.style.overflow = '';
        }

        if (closeBtn) closeBtn.addEventListener('click', closeErrorModal);
        if (okBtn) okBtn.addEventListener('click', closeErrorModal);
        if (overlay) overlay.addEventListener('click', closeErrorModal);

        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && errorModal.classList.contains('modal--active')) {
                closeErrorModal();
            }
        });
    }

    window.getCSRFToken = function () {
        var cookie = document.cookie.split(';').find(function (c) {
            return c.trim().startsWith('csrftoken=');
        });
        return cookie ? cookie.split('=')[1] : '';
    };

    document.addEventListener('DOMContentLoaded', function () {
        initNavToggle();
        initAlerts();
        initFormErrorModal();
    });
})();
