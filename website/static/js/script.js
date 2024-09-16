document.addEventListener('DOMContentLoaded', function() {
    const infoIcon = document.querySelector('.info-icon');
    const mobileDescription = document.querySelector('.mobile-description');
    const imageContainer = document.querySelector('.image-container');
    const hamburgerMenu = document.querySelector('.hamburger-menu');
    const mobileNav = document.querySelector('.mobile-nav');
    const navLinks = document.querySelectorAll('nav a');

    infoIcon.addEventListener('click', function(event) {
        event.stopPropagation();
        mobileDescription.classList.toggle('show');
    });

    imageContainer.addEventListener('click', function() {
        if (window.innerWidth <= 767) {
            mobileDescription.classList.remove('show');
        }
    });

    hamburgerMenu.addEventListener('click', function() {
        this.classList.toggle('active');
        mobileNav.classList.toggle('active');
    });

    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);

            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth'
                });
            }

            if (window.innerWidth <= 767) {
                mobileNav.classList.remove('active');
                hamburgerMenu.classList.remove('active');
            }
        });
    });

    let resizeTimer;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function() {
            if (window.innerWidth > 767) {
                mobileDescription.classList.remove('show');
                mobileNav.classList.remove('active');
                hamburgerMenu.classList.remove('active');
            }
        }, 250);
    });
});
