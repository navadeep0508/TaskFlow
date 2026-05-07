document.addEventListener('DOMContentLoaded', function() {
    const revealItems = Array.from(document.querySelectorAll('.tf-reveal'));
    if (!revealItems.length) return;

    const markVisible = (el) => el.classList.add('is-visible');

    if (!('IntersectionObserver' in window)) {
        revealItems.forEach(markVisible);
        return;
    }

    const observer = new IntersectionObserver(
        (entries, obs) => {
            entries.forEach((entry) => {
                if (!entry.isIntersecting) return;
                markVisible(entry.target);
                obs.unobserve(entry.target);
            });
        },
        { root: null, rootMargin: '0px 0px -12% 0px', threshold: 0.15 }
    );

    revealItems.forEach((item) => observer.observe(item));
});
