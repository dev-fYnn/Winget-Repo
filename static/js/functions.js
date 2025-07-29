document.querySelectorAll(".checkbox-cell").forEach(cell => {
    cell.addEventListener("click", function (e) {
        if (e.target.tagName.toLowerCase() !== "input") {
            const checkbox = this.querySelector('input[type="checkbox"]');
            if (checkbox) {
                checkbox.checked = !checkbox.checked;
            }
        }
    });
});