lucide.createIcons();

const navToggle = document.querySelector('.nav__toggle');
const mobileMenu = document.querySelector('.nav__mobile');
const menuIcon = document.querySelector('.menu-icon');
const closeIcon = document.querySelector('.close-icon');

navToggle.addEventListener('click', () => {
  mobileMenu.classList.toggle('hidden');
  menuIcon.classList.toggle('hidden');
  closeIcon.classList.toggle('hidden');
});

// Hero image error handling
const heroImage = document.getElementById('heroImage');
const heroImg = heroImage.querySelector('img');

heroImg.addEventListener('error', () => {
  heroImage.style.display = 'none';
});

document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function (e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute('href'));
    if (target) {
      target.scrollIntoView({
        behavior: 'smooth'
      });

      mobileMenu.classList.add('hidden');
      menuIcon.classList.remove('hidden');
      closeIcon.classList.add('hidden');
    }
  });
});