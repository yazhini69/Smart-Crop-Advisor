// script.js
console.log("script.js loaded successfully!"); // Add this line at the top

document.getElementById("cropForm").addEventListener("submit", async function (e) {
  // ... rest of your code
});
document.getElementById("cropForm").addEventListener("submit", async function (e) {
  e.preventDefault(); // Prevent the default form submission (page reload)

  const form = e.target;
  const data = {
    area: parseFloat(form.area.value),
    soil_type: form.soil_type.value,
    duration: form.duration.value,
    month: parseInt(form.month.value), // Get month value as an integer
    N: form.N.value !== '' ? parseFloat(form.N.value) : null, // Handle empty optional inputs by converting to null
    P: form.P.value !== '' ? parseFloat(form.P.value) : null,
    K: form.K.value !== '' ? parseFloat(form.K.value) : null,
    pH: form.pH.value !== '' ? parseFloat(form.pH.value) : null,
    moisture: form.moisture.value !== '' ? parseFloat(form.moisture.value) : null,
    symptoms: form.symptoms.value !== '' ? form.symptoms.value : null,
  };

  console.log("Sending data to server:", data);

  const resultDiv = document.getElementById("result");
  const suggestionsDiv = document.getElementById("suggestions");

  // Clear previous results and suggestions and show a loading indicator
  resultDiv.innerHTML = 'Calculating... Please wait...'; // More descriptive loading
  resultDiv.style.color = '#1b5e20'; // Keep loading text green
  suggestionsDiv.innerHTML = ''; // Clear previous suggestions

  // Disable the submit button to prevent multiple submissions
  const submitButton = form.querySelector('button[type="submit"]');
  submitButton.disabled = true;
  submitButton.textContent = 'Calculating...'; // Change button text to indicate loading

  try {
    const response = await fetch("http://127.0.0.1:5000/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });

    // Log the raw response status for better debugging
    console.log("Server response status:", response.status);

    const resData = await response.json(); // Attempt to parse JSON even if response.ok is false
    console.log("✅ Server response data:", resData);

    if (response.ok) {
      // If the response status is 200-299 (success)
      resultDiv.innerHTML = "<strong>🌾 Recommended Crop: </strong>" + resData.recommendation;
      resultDiv.style.color = '#1b5e20'; // Ensure success message is green

      // Display suggestions if available
      if (resData.suggestions && resData.suggestions.length > 0) {
        let suggestionsHtml = "<h3>💡 Suggestions for your soil conditions:</h3><ul>";
        resData.suggestions.forEach(suggestion => {
          suggestionsHtml += `<li>${suggestion}</li>`;
        });
        suggestionsHtml += "</ul>";
        suggestionsDiv.innerHTML = suggestionsHtml;
      } else {
        suggestionsDiv.innerHTML = "<p>No specific soil suggestions for current conditions (all optimal or values not provided).</p>";
      }
      if (resData.disease_suggestions && resData.disease_suggestions.length > 0) {
  let diseaseHtml = "<h3>🦠 Disease Symptom Suggestions:</h3><ul>";
  resData.disease_suggestions.forEach(tip => {
    diseaseHtml += `<li>${tip}</li>`;
  });
  diseaseHtml += "</ul>";
  suggestionsDiv.innerHTML += diseaseHtml;
}

    } else {
      // If the response status indicates an error (e.g., 400, 500)
      resultDiv.innerHTML = `<p style="color: red;">Error: ${resData.error || 'Something went wrong on the server.'}</p>`;
      suggestionsDiv.innerHTML = ''; // Clear suggestions on error
    }
  } catch (err) {
    // This block catches network errors (e.g., server not running, connection refused)
    console.error("❌ Fetch Error:", err);
    resultDiv.innerHTML = "<p style='color: red;'>Something went wrong. Please check if the server is running and try again!</p>";
    suggestionsDiv.innerHTML = ''; // Clear suggestions on error
  } finally {
    // Re-enable the submit button regardless of success or failure
    submitButton.disabled = false;
    submitButton.textContent = '🌾 Get Recommended Crop'; // Restore original button text
  }
});