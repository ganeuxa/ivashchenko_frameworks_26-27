const yearElement = document.getElementById("current-year");

if (yearElement) {
    yearElement.textContent = new Date().getFullYear();
}

const hideCancelled = document.getElementById("hide-cancelled");

if (hideCancelled) {
    hideCancelled.addEventListener("change", () => {
        document.querySelectorAll(".operation-cancelled").forEach((row) => {
            row.hidden = hideCancelled.checked;
        });
    });
}
