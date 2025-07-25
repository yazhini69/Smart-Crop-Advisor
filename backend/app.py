from flask import Flask, request, jsonify # Removed render_template as you won't serve HTML from here
from flask_cors import CORS
import pandas as pd
import joblib
import numpy as np
from pathlib import Path

app = Flask(__name__) # Revert to default Flask app initialization
CORS(app) # Keep CORS, it's essential for cross-origin communication now

# Define paths to saved model and encoders (relative to App.py)
MODEL_PATH = Path("model/crop_model.pkl")
IMPUTER_PATH = Path("model/imputer.pkl")
SOIL_ENCODER_PATH = Path("encoders/soil_encoder.pkl")
DURATION_ENCODER_PATH = Path("encoders/duration_encoder.pkl")
CROP_ENCODER_PATH = Path("encoders/crop_encoder.pkl")

# Load model and preprocessing tools at app startup
try:
    model = joblib.load(MODEL_PATH)
    imputer = joblib.load(IMPUTER_PATH)
    soil_encoder = joblib.load(SOIL_ENCODER_PATH)
    duration_encoder = joblib.load(DURATION_ENCODER_PATH)
    crop_encoder = joblib.load(CROP_ENCODER_PATH)
    print("✅ Model and encoders loaded successfully.")
except FileNotFoundError as e:
    print(f"Error: Missing model or encoder file. Please run train.py first. Details: {e}")
    exit()
except Exception as e:
    print(f"Error loading model or encoders: {e}")
    exit()

# --- Define general optimal ranges for pH and NPK (Adjust these values as needed) ---
OPTIMAL_PH_LOW = 6.0
OPTIMAL_PH_HIGH = 7.5
OPTIMAL_N_LOW = 60 # kg/ha
OPTIMAL_N_HIGH = 120 # kg/ha
OPTIMAL_P_LOW = 30 # kg/ha
OPTIMAL_P_HIGH = 80 # kg/ha
OPTIMAL_K_LOW = 30 # kg/ha
OPTIMAL_K_HIGH = 70 # kg/ha

def get_soil_suggestions(ph, N, P, K):
    """
    Generates soil management suggestions based on pH and NPK levels.
    """
    suggestions = []
    # ... (your existing get_soil_suggestions function code) ...
    # No changes needed here, as this is purely logic
    if ph is not None:
        if ph < OPTIMAL_PH_LOW:
            suggestions.append(f"Soil pH ({ph:.1f}) is low. Consider adding liming materials (e.g., agricultural lime, wood ash) to increase pH and improve nutrient availability.")
        elif ph > OPTIMAL_PH_HIGH:
            suggestions.append(f"Soil pH ({ph:.1f}) is high. Consider adding acidic organic matter (e.g., peat moss), elemental sulfur, or aluminum sulfate to lower pH.")
        else:
            suggestions.append(f"Soil pH ({ph:.1f}) is within the optimal range for most crops.")
    else:
        suggestions.append("pH value not provided. Cannot give pH-specific suggestions.")

    if N is not None:
        if N < OPTIMAL_N_LOW:
            suggestions.append(f"Nitrogen (N) ({N:.1f} kg/ha) is low. Apply nitrogen-rich fertilizers (e.g., urea, ammonium nitrate) or organic sources like compost, well-rotted manure, or cultivate nitrogen-fixing cover crops.")
        elif N > OPTIMAL_N_HIGH:
            suggestions.append(f"Nitrogen (N) ({N:.1f} kg/ha) is high. Excessive nitrogen can lead to lush vegetative growth at the expense of fruit/flower production, and can leach into groundwater. Consider planting nitrogen-loving cover crops or allowing rainfall to leach excess.")
        else:
            suggestions.append(f"Nitrogen (N) ({N:.1f} kg/ha) is within the optimal range. Good for vegetative growth.")
    else:
        suggestions.append("Nitrogen (N) value not provided. Cannot give N-specific suggestions.")

    if P is not None:
        if P < OPTIMAL_P_LOW:
            suggestions.append(f"Phosphorus (P) ({P:.1f} kg/ha) is low. Apply phosphorus-rich fertilizers (e.g., diammonium phosphate, single superphosphate) or natural sources like rock phosphate or bone meal for root development and flowering.")
        elif P > OPTIMAL_P_HIGH:
            suggestions.append(f"Phosphorus (P) ({P:.1f} kg/ha) is high. High phosphorus can tie up other essential micronutrients (like zinc and iron). Improve drainage or use crops that efficiently utilize high P.")
        else:
            suggestions.append(f"Phosphorus (P) ({P:.1f} kg/ha) is within the optimal range. Essential for root development and energy transfer.")
    else:
        suggestions.append("Phosphorus (P) value not provided. Cannot give P-specific suggestions.")

    if K is not None:
        if K < OPTIMAL_K_LOW:
            suggestions.append(f"Potassium (K) ({K:.1f} kg/ha) is low. Apply potassium-rich fertilizers (e.g., muriate of potash, sulfate of potash) or organic sources like wood ash, greensand, or compost for overall plant vigor and disease resistance.")
        elif K > OPTIMAL_K_HIGH:
            suggestions.append(f"Potassium (K) ({K:.1f} kg/ha) is high. High potassium can interfere with the uptake of other nutrients, particularly magnesium and calcium. Improve drainage and avoid excessive potassium fertilization.")
        else:
            suggestions.append(f"Potassium (K) ({K:.1f} kg/ha) is within the optimal range. Important for water regulation and stress tolerance.")
    else:
        suggestions.append("Potassium (K) value not provided. Cannot give K-specific suggestions.")

    return suggestions
def get_disease_suggestions(symptom):
    """
    Returns general management suggestions based on common crop disease symptoms.
    """
    if not symptom:
        return []

    suggestions_map = {
        "yellow_leaves": [
            "Yellowing leaves may indicate nitrogen deficiency or root rot. Test soil and ensure good drainage.",
            "Consider applying a balanced fertilizer containing nitrogen.",
        ],
        "wilting": [
            "Wilting may be due to under-watering, over-watering, or soil-borne fungi (like Fusarium).",
            "Avoid waterlogging and rotate crops to prevent soil disease buildup."
        ],
        "leaf_spots": [
            "Leaf spots are often caused by fungal or bacterial pathogens. Remove infected leaves.",
            "Use appropriate fungicides or bactericides if the problem persists."
        ],
        "stunted_growth": [
            "Stunted growth could result from nutrient deficiency or viral infections.",
            "Test for soil nutrients and avoid reusing seeds from stunted plants."
        ],
        "powdery_mildew": [
            "Powdery mildew appears as white powder on leaves. Common in humid conditions.",
            "Use neem oil or sulfur-based organic fungicides. Improve air circulation."
        ]
    }

    return suggestions_map.get(symptom, ["No specific suggestions available for this symptom."])


# Removed the @app.route('/') for serving HTML from App.py
# The frontend will be served by a separate server.

@app.route('/predict', methods=['POST'])
def predict_crop():
    data = request.get_json()
    print("🔁 Data received from frontend:", data)

    try:
        # Required inputs - ensure they are present
        area = float(data.get("area"))
        soil_type = data.get("soil_type")
        duration = data.get("duration")
        month = int(data.get("month"))

        if any(x is None for x in [area, soil_type, duration, month]):
            raise ValueError("Missing required input: area, soil_type, duration, or month.")

        # Optional inputs with fallback to None if not provided or empty string
        N = float(data.get("N")) if data.get("N") is not None and data.get("N") != '' else None
        P = float(data.get("P")) if data.get("P") is not None and data.get("P") != '' else None
        K = float(data.get("K")) if data.get("K") is not None and data.get("K") != '' else None
        pH = float(data.get("pH")) if data.get("pH") is not None and data.get("pH") != '' else None
        moisture = float(data.get("moisture")) if data.get("moisture") is not None and data.get("moisture") != '' else None
        symptom = data.get("symptoms") if data.get("symptoms") not in ["", None] else None

        # Encode categorical inputs
        encoded_soil = soil_encoder.transform([soil_type])[0]
        encoded_duration = duration_encoder.transform([duration])[0]

        # Construct input vector for the model
        features_array = np.array([[encoded_soil, encoded_duration, area, N, P, K, pH, moisture, month]])

        # Impute missing values
        features_imputed = imputer.transform(features_array)

        # Predict and decode output
        prediction = model.predict(features_imputed)
        predicted_crop = crop_encoder.inverse_transform(prediction)[0]
        
        # Generate soil suggestions
        suggestions = get_soil_suggestions(pH, N, P, K)
        disease_suggestions = get_disease_suggestions(symptom)




        return jsonify({
            "recommendation": predicted_crop,
            "suggestions": suggestions,  # soil suggestions
            "disease_suggestions": disease_suggestions
        })

        

    except ValueError as ve:
        print(f"❌ Input validation error: {ve}")
        return jsonify({"error": f"Invalid input: {ve}"}), 400
    except Exception as e:
        print(f"❌ Error during prediction: {e}")
        return jsonify({"error": f"An internal server error occurred: {e}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
