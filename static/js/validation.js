// Driver ID validation
function validateDriverId() {
    const driverIdInput = document.getElementById("driver_id");
    const value = driverIdInput.value;

    if (value.length !== 4) {
        showError("Driver ID must be exactly 4 characters long.");
        return false;
    }
    return true;
}

// Password validation
function validatePassword() {
    const password = document.getElementById("password").value;
    const pattern = /^[a-zA-Z][a-zA-Z0-9_]{7,31}$/;

    if (!pattern.test(password)) {
        showError("Password must be 8-32 characters long, start with a letter, " +
                 "and contain only alphabets, numbers, and underscores.");
        return false;
    }
    return true;
}

// Stock validation
function validateStock() {
    const stockInput = document.getElementById("new_stock");
    const currentStock = parseInt(stockInput.getAttribute("data-current-stock"));
    const newStock = parseInt(stockInput.value);

    if (isNaN(newStock) || newStock <= 0) {
        showError("Please enter a valid positive number.");
        return false;
    }

    if (currentStock + newStock > 9) {
        showError("Total stock cannot exceed 9 items.");
        return false;
    }

    return true;
}

// Generic form validation
function validateForm(formType) {
    switch(formType) {
        case 'register':
            return validateDriverId() && validatePassword();
        case 'update_stock':
            return validateStock();
        default:
            return true;
    }
}

// Error display
function showError(message) {
    const errorDiv = document.getElementById("validation-error") || 
                    createErrorDiv();
    errorDiv.textContent = message;
    errorDiv.style.display = "block";

    // Hide error after 3 seconds
    setTimeout(() => {
        errorDiv.style.display = "none";
    }, 3000);
}

// Create error div if it doesn't exist
function createErrorDiv() {
    const errorDiv = document.createElement("div");
    errorDiv.id = "validation-error";
    errorDiv.className = "alert alert-error";
    document.querySelector("form").insertBefore(errorDiv, 
        document.querySelector("form").firstChild);
    return errorDiv;
}
