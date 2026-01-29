# type: ignore

import pandas as pd
import time
import warnings
warnings.filterwarnings("ignore", category=UserWarning)
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer
from sklearn.compose import ColumnTransformer
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
import lightgbm as lgb
import joblib
from extraction import (
    getLength, 
    specialChars, 
    countDigits, 
    ipAddress, 
    truncText
)
import seaborn as sns
from matplotlib import pyplot as plt


def preprocessing():
    preprocessor = ColumnTransformer(
        transformers=[
            ('sender_digits', FunctionTransformer(countDigits, validate=False, feature_names_out="one-to-one"), 'sender'),

            ('subj_len', FunctionTransformer(getLength, validate=False, feature_names_out="one-to-one"), 'subject'),
            ('subj_spec', FunctionTransformer(specialChars, validate=False, feature_names_out="one-to-one"), 'subject'),
            ('subj_tfidf', TfidfVectorizer(max_features=300, stop_words='english'), 'subject'),
            
            ('body_ip', FunctionTransformer(ipAddress, validate=False, feature_names_out="one-to-one"), 'body'),
            ('body_tfidf', TfidfVectorizer(
                preprocessor=truncText, 
                max_features=300, 
                stop_words='english', 
                min_df=0.02, 
                max_df=0.90
            ), 'body'),
            
            ('urls_passthrough', 'passthrough', ['urls'])
        ],
        remainder='drop',
        n_jobs=-1 
    )

    return preprocessor
    
def pipe(preprocessor):
    pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('classifier', lgb.LGBMClassifier(
            n_estimators=100,       
            learning_rate=0.1,      
            num_leaves=15,         
            objective='binary',
            n_jobs=-1,
            random_state=42,
            verbose=-1
        ))
    ])

    return pipeline

def train(pipeline, df):
    print("--- Training in corso... ---")
    X = df.drop(columns=['label'])
    y = df['label']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    start_train = time.time()
    pipeline.fit(X_train, y_train)
    end_train = time.time()
    print(f"Training completato in {end_train - start_train:.2f} secondi.")

    return pipeline, X_test, y_test


def evaluate(pipeline, X_test, y_test):
    y_pred = pipeline.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"Accuracy: {acc:.4f}")

    cm = confusion_matrix(y_test, y_pred)
    print(cm)
    print(classification_report(y_test, y_pred, target_names=['Legitimate (0)', 'Phishing (1)']))

def saveModel(pipeline):
    joblib.dump(pipeline, 'phishing_detector.pkl')
    print("\n--- Modello salvato ---")


if __name__ == '__main__':
    df = pd.read_csv("CEAS_08.csv")
    df['receiver'] = df['receiver'].fillna('unknown')
    df['subject'] = df['subject'].fillna('')
    df['body'] = df['body'].fillna('') 

    preprocessor = preprocessing()
    pipeline = pipe(preprocessor)
    model, X_test, y_test = train(pipeline, df)
    evaluate(model, X_test, y_test)
    saveModel(model)