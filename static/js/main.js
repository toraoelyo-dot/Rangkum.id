// ==========================
// SMARTDOC AI
// main.js
// ==========================

document.addEventListener("DOMContentLoaded", () => {

    const uploadForm = document.getElementById("upload-form");
    const textForm = document.getElementById("text-form");
    const loading = document.getElementById("loading");
    const fileInput = document.querySelector("input[type='file']");
    const uploadCard = document.querySelector(".upload-card");

    // ==========================
    // FORM SUBMITS (Specific)
    // ==========================

    if (uploadForm && fileInput) {
        uploadForm.addEventListener("submit", function(e) {
            if (!fileInput.files.length) {
                e.preventDefault();
                alert("Harap pilih berkas dokumen terlebih dahulu.");
                return;
            }
            if (loading) {
                loading.style.display = "flex";
            }
        });
    }

    if (textForm) {
        textForm.addEventListener("submit", function(e) {
            const textInput = document.getElementById("text-input");
            const text = textInput ? textInput.value.trim() : "";
            if (text.length < 50) {
                e.preventDefault();
                alert("Teks terlalu pendek. Minimal 50 karakter diperlukan.");
                return;
            }
            if (loading) {
                loading.style.display = "flex";
            }
        });
    }

    // ==========================
    // THEME TOGGLE (Mode Gelap/Terang)
    // ==========================

    const themeToggleBtn = document.getElementById("theme-toggle-btn");
    const themeToggleIcon = document.getElementById("theme-toggle-icon");

    function initTheme() {
        const savedTheme = localStorage.getItem("theme") || "dark";
        if (savedTheme === "light") {
            document.body.classList.add("light-mode");
            if (themeToggleIcon) {
                themeToggleIcon.className = "fa-solid fa-moon";
            }
        } else {
            document.body.classList.remove("light-mode");
            if (themeToggleIcon) {
                themeToggleIcon.className = "fa-solid fa-sun";
            }
        }
    }

    function toggleTheme() {
        if (document.body.classList.contains("light-mode")) {
            document.body.classList.remove("light-mode");
            localStorage.setItem("theme", "dark");
            if (themeToggleIcon) {
                themeToggleIcon.className = "fa-solid fa-sun";
            }
        } else {
            document.body.classList.add("light-mode");
            localStorage.setItem("theme", "light");
            if (themeToggleIcon) {
                themeToggleIcon.className = "fa-solid fa-moon";
            }
        }
    }

    // Jalankan inisialisasi tema
    initTheme();

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener("click", toggleTheme);
    }

    // ==========================
    // DRAG & DROP
    // ==========================

    if (uploadCard && fileInput) {

        uploadCard.addEventListener(
            "dragover",
            (e) => {
                e.preventDefault();
                uploadCard.style.border = "2px dashed #818cf8";
                uploadCard.style.transform = "scale(1.02)";
            }
        );

        uploadCard.addEventListener(
            "dragleave",
            () => {
                uploadCard.style.border = "1px solid var(--card-border)";
                uploadCard.style.transform = "scale(1)";
            }
        );

        uploadCard.addEventListener(
            "drop",
            (e) => {
                e.preventDefault();
                uploadCard.style.border = "1px solid var(--card-border)";
                uploadCard.style.transform = "scale(1)";
                fileInput.files = e.dataTransfer.files;
                updateFileName();
            }
        );

    }

    // ==========================
    // FILE NAME PREVIEW
    // ==========================

    const preview = document.createElement("div");
    preview.classList.add("mt-3", "text-center");

    if (fileInput) {
        fileInput.parentNode.appendChild(preview);
        fileInput.addEventListener("change", updateFileName);
    }

    function updateFileName() {
        if (fileInput && fileInput.files.length) {
            preview.innerHTML = `
                <div class="alert alert-success d-inline-block py-2 px-4" style="border-radius: 12px; margin-bottom: 0;">
                    <strong>Terpilih:</strong> ${fileInput.files[0].name}
                </div>
            `;
        }
    }

    // ==========================
    // SMOOTH CARD ANIMATION
    // ==========================

    const cards = document.querySelectorAll(
        ".feature-card, .stat-card, .card-glass"
    );

    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach(
                entry => {
                    if (entry.isIntersecting) {
                        entry.target.style.opacity = "1";
                        entry.target.style.transform = "translateY(0)";
                    }
                }
            );
        },
        {
            threshold: 0.1
        }
    );

    cards.forEach(card => {
        card.style.opacity = "0";
        card.style.transform = "translateY(30px)";
        card.style.transition = "all .7s ease";
        observer.observe(card);
    });

});