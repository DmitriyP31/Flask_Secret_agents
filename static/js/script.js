document.addEventListener('DOMContentLoaded', () => {
    const toggleBtn = document.getElementById('theme-toggle');
    const body = document.body;

    if (localStorage.getItem('theme') === 'dark') {
        body.classList.add('dark-theme');
    }

    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            body.classList.toggle('dark-theme');

            if (body.classList.contains('dark-theme')) {
                localStorage.setItem('theme', 'dark');
            } else {
                localStorage.setItem('theme', 'light');
            }
        });
    }
});


document.addEventListener('DOMContentLoaded', () => {
    const diceBtn = document.getElementById('generate-name');
    const nameInput = document.getElementById('codename-input');

    if (diceBtn && nameInput) {
        const adjectives = [
            'Shadow', 'Silent', 'Dark', 'Golden', 'Iron',
            'Ghost', 'Neon', 'Swift', 'Crimson', 'Cold'
        ];
        const nouns = [
            'Fox', 'Wolf', 'Falcon', 'Specter', 'Blade',
            'Hunter', 'Raven', 'Viper', 'Knight', 'Storm'
        ];

        diceBtn.addEventListener('click', () => {
            const randomAdj = adjectives[Math.floor(Math.random() * adjectives.length)];
            const randomNoun = nouns[Math.floor(Math.random() * nouns.length)];

            const generatedName = `${randomAdj} ${randomNoun}`;
            nameInput.value = generatedName;
        });
    }
});

