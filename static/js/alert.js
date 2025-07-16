setTimeout(function() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        const bootstrapAlert = new bootstrap.Alert(alert);
        bootstrapAlert.close();
    });
}, 5000);
