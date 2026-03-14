import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import pickle
import os

MODEL_PATH = 'instance/placement_model.pkl'

def train_model():
    if os.path.exists(MODEL_PATH):
        return
    
    # Dummy data: features [cgpa*10, aptitude, coding, technical], label: placed (1/0)
    np.random.seed(42)
    n_samples = 1000
    cgpa = np.random.uniform(4, 10, n_samples)
    apt = np.random.randint(0, 100, n_samples)
    code = np.random.randint(0, 100, n_samples)
    tech = np.random.randint(0, 100, n_samples)
    X = np.column_stack([cgpa*10, apt/10, code/10, tech/10])
    y = ((cgpa > 7.5) & (apt > 60) & (code > 70) & (tech > 65)).astype(int)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
    
    model = LogisticRegression()
    model.fit(X_train, y_train)
    
    os.makedirs('instance', exist_ok=True)
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
    
    print(f'Model trained. Accuracy: {accuracy_score(y_test, model.predict(X_test)):.2f}')

def predict_placement(cgpa, apt_score, code_score, tech_score):
    if not os.path.exists(MODEL_PATH):
        train_model()
    
    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)
    
    features = np.array([[cgpa*10, apt_score/10, code_score/10, tech_score/10]])
    prob = model.predict_proba(features)[0][1] * 100
    return f'{prob:.1f}%'

def get_recommendations(scores):
    recs = []
    if scores['aptitude_score'] < 60:
        recs.append('Practice aptitude questions')
    if scores['coding_score'] < 70:
        recs.append('Solve more coding problems')
    # etc.
    return recs or ['Great job! Keep it up.']

