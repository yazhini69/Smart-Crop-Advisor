import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import LabelEncoder
from pathlib import Path
import joblib

print("Starting model training...")

# Define paths
DATA_PATH = Path('D:/AgroNexus_CropAdvisor/data/crop_dataset_sample.csv') # Ensure this path is correct
ENCODER_DIR = Path("encoders")
MODEL_DIR = Path("model")

# Create directories if they don't exist
ENCODER_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)

try:
    # Load dataset
    df = pd.read_csv(DATA_PATH)
    print(f"Dataset loaded from: {DATA_PATH}")
    print(f"Dataset head:\n{df.head()}")

    # --- Ensure 'Month' column exists ---
    if 'Month' not in df.columns:
        raise ValueError("Error: 'Month' column not found in the dataset. Please add it to your CSV.")

    # Encode categorical variables
    soil_encoder = LabelEncoder()
    duration_encoder = LabelEncoder()
    crop_encoder = LabelEncoder()

    df['Soil_Type'] = soil_encoder.fit_transform(df['Soil_Type'])
    df['Duration'] = duration_encoder.fit_transform(df['Duration'])
    df['Crop'] = crop_encoder.fit_transform(df['Crop'])

    # Save encoders
    joblib.dump(soil_encoder, ENCODER_DIR / "soil_encoder.pkl")
    joblib.dump(duration_encoder, ENCODER_DIR / "duration_encoder.pkl")
    joblib.dump(crop_encoder, ENCODER_DIR / "crop_encoder.pkl")
    print("Encoders saved successfully.")

    # Define features (X) and target (y)
    # Ensure the order matches what your Flask app will send
    features = ['Soil_Type', 'Duration', 'Area', 'N', 'P', 'K', 'pH', 'Moisture', 'Month']
    X = df[features]
    y = df['Crop']
    print(f"Features for training: {features}")

    # Fill missing sensor values using SimpleImputer (mean strategy)
    imputer = SimpleImputer(strategy='mean')
    X_imputed = imputer.fit_transform(X)
    print("Missing values imputed.")

    # Train model
    model = RandomForestClassifier(n_estimators=100, random_state=42) # Added n_estimators and random_state
    model.fit(X_imputed, y)
    print("RandomForestClassifier model trained.")

    # Save model and imputer
    joblib.dump(model, MODEL_DIR / "crop_model.pkl")
    joblib.dump(imputer, MODEL_DIR / "imputer.pkl")
    print("Model and imputer saved successfully.")

    print("✅ Model and encoders trained and saved successfully.")

except FileNotFoundError:
    print(f"Error: Dataset not found at {DATA_PATH}. Please ensure the path is correct and the file exists.")
except ValueError as ve:
    print(f"Data processing error: {ve}")
except Exception as e:
    print(f"An unexpected error occurred during training: {e}")
