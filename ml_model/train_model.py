import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import joblib
import os

# Paths
data_path = os.path.join('data', 'usage_data.csv')
model_path = os.path.join('ml_model', 'model.pkl')

# Load real usage data
df = pd.read_csv(data_path)

# Drop rows with missing values
df.dropna(inplace=True)

# Encode email (if needed, optional)
if 'email' in df.columns:
    df = df.drop(columns=['email'])

# Extract features and define target
X = df.drop(columns=['date'])  # features = appliance usage hours
y = (X.sum(axis=1) > 15).astype(int)  # label: 1 if total usage > 15 hrs (custom logic)

# Split and train
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train, y_train)

# Save model
joblib.dump(clf, model_path)
print("✅ Model trained and saved to", model_path)
