import pandas as pd
import numpy as np
import os
import time
from sklearn.model_selection import cross_validate, StratifiedKFold, train_test_split
from sklearn.preprocessing import RobustScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from imblearn.pipeline import Pipeline
from imblearn.over_sampling import SMOTE
import warnings

warnings.filterwarnings('ignore')

DIR_BASE = os.path.dirname(os.path.abspath(__file__))
PATH_DATOS = os.path.abspath(os.path.join(DIR_BASE, "..", "data", "processed", "oferta_nacional_geo_final.csv"))
PATH_RESULTADOS = os.path.abspath(os.path.join(DIR_BASE, "..", "data", "resultados_modelos.csv"))

def ejecutar_benchmark_modelos():
    print("Iniciando benchmark de modelos supervisados...")
    
    df = pd.read_csv(PATH_DATOS).dropna(subset=['Superficie_m2', 'Precio_MXN', 'Recamaras', 'Banos', 'Latitud', 'Longitud'])
    
    bins = [0, 2000000, 6000000, float('inf')]
    labels = [0, 1, 2]
    df['Segmento'] = pd.cut(df['Precio_MXN'], bins=bins, labels=labels)
    
    X = df[['Superficie_m2', 'Recamaras', 'Banos', 'Latitud', 'Longitud']]
    y = df['Segmento']
    
    X_sample, _, y_sample, _ = train_test_split(X, y, train_size=50000, stratify=y, random_state=42)
    print(f"Dataset de entrenamiento: {len(X_sample)} registros.")

    modelos = {
        "Regresion Logistica": LogisticRegression(max_iter=1000, n_jobs=-1, random_state=42),
        "KNN (k=5)": KNeighborsClassifier(n_neighbors=5, n_jobs=-1),
        "Arbol de Decision": DecisionTreeClassifier(max_depth=15, random_state=42),
        "SVM (Kernel RBF)": SVC(kernel='rbf', max_iter=2000, probability=True, random_state=42),
        "Red Neuronal (MLP)": MLPClassifier(hidden_layer_sizes=(100, 50), max_iter=500, random_state=42),
        "Random Forest": RandomForestClassifier(n_estimators=100, n_jobs=-1, random_state=42)
    }

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    metricas = ['accuracy', 'precision_macro', 'recall_macro', 'f1_macro', 'roc_auc_ovo']
    
    resultados_lista = []

    print("\nEntrenando y evaluando modelos...")
    for nombre, clasificador in modelos.items():
        print(f"Procesando: {nombre}")
        inicio = time.time()
        
        pipeline = Pipeline([
            ('scaler', RobustScaler()),
            ('smote', SMOTE(random_state=42)),
            ('clf', clasificador)
        ])
        
        try:
            scores = cross_validate(pipeline, X_sample, y_sample, scoring=metricas, cv=cv, n_jobs=-1)
            tiempo_total = time.time() - inicio
            
            res = {
                'Modelo': nombre,
                'Accuracy': np.mean(scores['test_accuracy']),
                'Precision': np.mean(scores['test_precision_macro']),
                'Recall': np.mean(scores['test_recall_macro']),
                'F1-Score': np.mean(scores['test_f1_macro']),
                'ROC-AUC': np.mean(scores['test_roc_auc_ovo']),
                'Tiempo_Segundos': round(tiempo_total, 2)
            }
            resultados_lista.append(res)
            print(f"  -> Completado en {res['Tiempo_Segundos']}s | F1-Score: {res['F1-Score']:.4f}")
            
        except Exception as e:
            print(f"  -> Error en {nombre}: {e}")

    df_resultados = pd.DataFrame(resultados_lista)
    df_resultados = df_resultados.sort_values(by='F1-Score', ascending=False)
    df_resultados.to_csv(PATH_RESULTADOS, index=False)
    
    print("\nRanking Final de Algoritmos:")
    print("-" * 70)
    print(df_resultados[['Modelo', 'F1-Score', 'ROC-AUC', 'Tiempo_Segundos']].to_string(index=False))
    print(f"\nResultados completos guardados en: {PATH_RESULTADOS}")

if __name__ == "__main__":
    ejecutar_benchmark_modelos()