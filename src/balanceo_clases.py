import pandas as pd
import numpy as np
import os
from sklearn.model_selection import cross_validate, StratifiedKFold, train_test_split
from sklearn.preprocessing import RobustScaler
from sklearn.ensemble import RandomForestClassifier
from imblearn.pipeline import Pipeline
from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import RandomUnderSampler

DIR_BASE = os.path.dirname(os.path.abspath(__file__))
PATH_DATOS = os.path.abspath(os.path.join(DIR_BASE, "..", "data", "processed", "oferta_nacional_geo_final.csv"))

def evaluar_balanceo():
    print("Iniciando evaluación de técnicas de balanceo...")
    
    df = pd.read_csv(PATH_DATOS).dropna(subset=['Superficie_m2', 'Precio_MXN', 'Recamaras', 'Banos'])
    
    bins = [0, 2000000, 6000000, float('inf')]
    labels = [0, 1, 2]
    df['Segmento_Mercado'] = pd.cut(df['Precio_MXN'], bins=bins, labels=labels)
    
    X = df[['Superficie_m2', 'Recamaras', 'Banos']]
    y = df['Segmento_Mercado']
    
    X_sample, _, y_sample, _ = train_test_split(X, y, train_size=30000, stratify=y, random_state=42)
    
    dist = y_sample.value_counts(normalize=True) * 100
    print("\nDistribución de clases (Muestra 30k):")
    print(f"Clase 0 (Económico): {dist[0]:.2f}% (Minoritaria)")
    print(f"Clase 1 (Medio): {dist[1]:.2f}%")
    print(f"Clase 2 (Lujo): {dist[2]:.2f}%")

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    metricas = ['accuracy', 'precision_macro', 'recall_macro', 'f1_macro', 'roc_auc_ovo']
    
    clf = RandomForestClassifier(n_estimators=50, random_state=42, n_jobs=-1)
    
    pipelines = {
        "Baseline (Sin Balanceo)": Pipeline([
            ('scaler', RobustScaler()),
            ('clf', clf)
        ]),
        "Undersampling": Pipeline([
            ('scaler', RobustScaler()),
            ('sampler', RandomUnderSampler(random_state=42)),
            ('clf', clf)
        ]),
        "SMOTE": Pipeline([
            ('scaler', RobustScaler()),
            ('sampler', SMOTE(random_state=42)),
            ('clf', clf)
        ])
    }
    
    print("\nEjecutando validación cruzada estratificada (k=5)...")
    resultados = {}
    
    for nombre, pipeline in pipelines.items():
        print(f"Evaluando: {nombre}")
        scores = cross_validate(pipeline, X_sample, y_sample, scoring=metricas, cv=cv, n_jobs=-1)
        
        resultados[nombre] = {
            'Accuracy': np.mean(scores['test_accuracy']),
            'Precision': np.mean(scores['test_precision_macro']),
            'Recall': np.mean(scores['test_recall_macro']),
            'F1-Score': np.mean(scores['test_f1_macro']),
            'ROC-AUC': np.mean(scores['test_roc_auc_ovo'])
        }
        
    print("\nResultados del Experimento:")
    print(f"{'Técnica':<25} | {'Accuracy':<8} | {'Precision':<9} | {'Recall':<8} | {'F1-Score':<8} | {'ROC-AUC':<8}")
    print("-" * 75)
    for nombre, res in resultados.items():
        print(f"{nombre:<25} | {res['Accuracy']:.4f}   | {res['Precision']:.4f}    | {res['Recall']:.4f}   | {res['F1-Score']:.4f}   | {res['ROC-AUC']:.4f}")

if __name__ == "__main__":
    evaluar_balanceo()