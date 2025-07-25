// Appliance toggle handler with confirmation
document.addEventListener("DOMContentLoaded", function () {
  const toggleAppliances = document.querySelectorAll('.appliance-toggle');

  toggleAppliances.forEach((checkbox) => {
    checkbox.addEventListener('change', function () {
      const appliance = this.dataset.appliance;
      const isChecked = this.checked;

      const confirmed = confirm(Are you sure you want to turn ${isChecked ? 'ON' : 'OFF'} ${appliance}?);
      if (confirmed) {
        toggleAppliance(appliance, isChecked);
      } else {
        this.checked = !isChecked;
      }
    });
  });
});

// Function to call backend with appliance toggle update
function toggleAppliance(appliance, isChecked) {
  fetch('/update_toggle', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      appliance: appliance,
      state: isChecked ? 'on' : 'off'
    })
  })
  .then(response => {
    if (!response.ok) {
      alert("Failed to update appliance state.");
    }
  })
  .catch(error => {
    console.error("Error:", error);
    alert("An error occurred while updating.");
  });
}