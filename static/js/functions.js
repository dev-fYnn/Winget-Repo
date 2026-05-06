document.querySelectorAll(".checkbox-cell").forEach(cell => {
    cell.addEventListener("click", function (e) {
        if (e.target.tagName.toLowerCase() !== "input") {
            const checkbox = this.querySelector('input[type="checkbox"]');
            if (checkbox) {
                checkbox.checked = !checkbox.checked;
                checkbox.dispatchEvent(new Event('change', { bubbles: true }));
            }
        }
    });
});

function showAlert(message, type) {
    const alertContainer = document.getElementById('alertContainer');
    const div = document.createElement('div');
    div.className = `alert ${type} alert-dismissible fade show`;
    div.setAttribute('role', 'alert');
    div.textContent = message;
    alertContainer.appendChild(div);

    setTimeout(function () {
        const bootstrapAlert = new bootstrap.Alert(div);
        bootstrapAlert.close();
    }, 5000);
}
