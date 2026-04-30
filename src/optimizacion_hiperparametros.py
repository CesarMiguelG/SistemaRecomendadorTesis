import pandas as pd
import numpy as np
import os
import time
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV, train_test_split
from sklearn.preprocessing import RobustScaler
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from imblearn.pipeline import Pipeline
from imblearn.over_sampling import SMOTE
import warnings

warnings.filterwarnings('ignore')

DIR_BASE = os.path.dirname(os.path.abspath(__file__))
PATH_DATOS = os.path.abspath(os.path.join(DIR_BASE, "..", "data", "processed", "oferta_nacional_geo_final.csv"))

def optimizar_modelos():
    print("Iniciando optimización de hiperparámetros...")
    
    # 1. Carga y preparación (Muestra de 20k para viabilidad computacional)
    df = pd.read_csv(PATH_DATOS).dropna()
    bins = [0, 2000000, 6000000, float('inf')]
    df['Segmento'] = pd.cut(df['Precio_MXN'], bins=bins, labels=[0, 1, 2])
    
    X = df[['Superficie_m2', 'Recamaras', 'Banos', 'Latitud', 'Longitud']]
    y = df['Segmento']
    X_train, X_test, y_train, y_test = train_test_split(X, y, train_size=20000, stratify=y, random_state=42)

    # --- EXPERIMENTO A: GRID SEARCH (Árbol de Decisión) ---
    print("\nEjecutando Grid Search (Decision Tree)...")
    pipe_dt = Pipeline([
        ('scaler', RobustScaler()),
        ('smote', SMOTE(random_state=42)),
        ('clf', DecisionTreeClassifier(random_state=42))
    ])
    
    param_grid_dt = {
        'clf__max_depth': [10, 20, 30],
        'clf__min_samples_split': [2, 10, 20],
        'clf__criterion': ['gini', 'entropy']
    }
    
    start = time.time()
    grid_search = GridSearchCV(pipe_dt, param_grid_dt, cv=3, scoring='f1_macro', n_jobs=-1)
    grid_search.fit(X_train, y_train)
    time_grid = time.time() - start
    
    # --- EXPERIMENTO B: RANDOM SEARCH (Random Forest) ---
    print("Ejecutando Random Search (Random Forest)...")
    pipe_rf = Pipeline([
        ('scaler', RobustScaler()),
        ('smote', SMOTE(random_state=42)),
        ('clf', RandomForestClassifier(random_state=42))
    ])
    
    param_dist_rf = {
        'clf__n_estimators': [50, 100, 200],
        'clf__max_depth': [None, 15, 30],
        'clf__min_samples_leaf': [1, 2, 4],
        'clf__bootstrap': [True, False]
    }
    
    start = time.time()
    random_search = RandomizedSearchCV(pipe_rf, param_dist_rf, n_iter=10, cv=3, scoring='f1_macro', n_jobs=-1, random_state=42)
    random_search.fit(X_train, y_train)
    time_random = time.time() - start

    # --- COMPARATIVA DE RESULTADOS ---
    print("\nResultados de Optimización:")
    print("-" * 50)
    
    print("GRID SEARCH (Decision Tree):")
    print(f"  Tiempo: {time_grid:.2f}s")
    print(f"  Mejores Parámetros: {grid_search.best_params_}")
    print(f"  F1-Score Optimizado: {grid_search.best_score_:.4f}")
    
    print("\nRANDOM SEARCH (Random Forest):")
    print(f"  Tiempo: {time_random:.2f}s")
    print(f"  Mejores Parámetros: {random_search.best_params_}")
    print(f"  F1-Score Optimizado: {random_search.best_score_:.4f}")

if __name__ == "__main__":
    optimizar_modelos()