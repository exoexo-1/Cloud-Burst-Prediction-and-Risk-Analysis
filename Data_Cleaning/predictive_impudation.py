import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score

# Load dataset
df = pd.read_csv('cleaned_cloudburst_data_without_evaporation.csv')

# Features to predict evaporation (exclude Evaporation itself)
features_for_prediction = [
    'Temp9am', 'Temp3pm',
    'Humidity9am', 'Humidity3pm',
    'Pressure9am', 'Pressure3pm',
    'WindSpeed9am', 'WindSpeed3pm',
    'Cloud9am', 'Cloud3pm',
    'Rainfall', 'Sunshine'
]

# -----------------------
# 1️⃣ Predict missing Evaporation
# -----------------------
df_known = df[df['Evaporation'].notna()]
df_missing = df[df['Evaporation'].isna()]

# Training data
X_train = df_known[features_for_prediction]
y_train = df_known['Evaporation']

# Train model
model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
model.fit(X_train, y_train)

# Predict missing values
if not df_missing.empty:
    X_missing = df_missing[features_for_prediction]
    predicted_values = model.predict(X_missing)
    df.loc[df['Evaporation'].isna(), 'Evaporation'] = predicted_values

# Check missing values
print("Missing Evaporation after prediction:", df['Evaporation'].isna().sum())

# -----------------------
# 2️⃣ Validate model with train/test split on known data
# -----------------------
X = df_known[features_for_prediction]
y = df_known['Evaporation']

X_train_val, X_test_val, y_train_val, y_test_val = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model_val = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
model_val.fit(X_train_val, y_train_val)
y_pred_val = model_val.predict(X_test_val)

# Metrics
mse = mean_squared_error(y_test_val, y_pred_val)
rmse = np.sqrt(mse)
r2 = r2_score(y_test_val, y_pred_val)

print(f"RMSE: {rmse:.2f}")
print(f"R²: {r2:.2f}")

# -----------------------
# 3️⃣ Save cleaned dataset
# -----------------------
df.to_csv('clean_cloudburst_data.csv', index=False)
print("Cleaned dataset saved to 'clean_cloudburst_data.csv'.")