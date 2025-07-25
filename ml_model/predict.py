import pickle
import numpy as np
import os

# Load the model
model_path = os.path.join(os.path.dirname(__file__), 'model.pkl')
with open(model_path, 'rb') as f:
    model = pickle.load(f)

# Tips for specific appliances
tips_dict = {
    'AC': 'Use a fan along with AC to reduce AC usage.',
    'Heater': 'Switch off when not in use. Insulate your room properly.',
    'TV': 'Avoid idle time while TV is on.',
    'Fan': 'Turn off when leaving the room.',
    'Fridge': 'Don’t leave the door open for long.',
    'Washing Machine': 'Run full loads instead of small loads.',
    'Iron': 'Avoid frequent switching on and off.',
    'Computer': 'Shut down when not in use.',
    'Light': 'Switch to LED and turn off when not needed.',
    'Microwave': 'Use only when necessary.',
    'Others': 'Unplug devices when not in use.'
}

def predict_overuse(user_data):
    """
    Predicts energy overuse based on appliance usage hours.
    :param user_data: dict with appliance names as keys and hours as values
    :return: (is_overuse: bool, tips: list[str])
    """
    feature_order = ['TV', 'Fan', 'AC', 'Heater', 'Fridge',
                     'Washing Machine', 'Iron', 'Computer', 'Light',
                     'Microwave', 'Others']

    features = [user_data.get(appliance, 0) for appliance in feature_order]
    prediction = model.predict([features])[0]

    tips = []
    if prediction == 1:
        for appliance, hours in user_data.items():
            if hours > 4 and appliance in tips_dict:
                tips.append(tips_dict[appliance])

    return prediction == 1, tips
