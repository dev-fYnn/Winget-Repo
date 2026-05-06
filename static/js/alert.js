setTimeout(function() {
    const alerts = document.querySelectorAll('.alert:not(.alert-static)');
    alerts.forEach(alert => {
        const bootstrapAlert = new bootstrap.Alert(alert);
        bootstrapAlert.close();
    });
}, 5000);