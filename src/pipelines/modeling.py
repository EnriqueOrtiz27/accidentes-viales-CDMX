"""
El objetivo es cargar el pickle generado en feature_engineering.py, tirar las columnas irrelevantes,
correr un magic loop e iniciar el resto de las actividades. Hoorray!
"""

import pandas as pd
import numpy as np
import pickle
import os
import random
import time
import joblib
from utils.utils import load_df
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from sklearn.linear_model import LogisticRegression

# from src.pipelines.model_evaluation import plot_roc_auc_curve


COLS_TO_KEEP = ['incidente_c4', 'latitud', 'longitud', 'bool_llamada', 'espacio_del_dia',
                'label']  # delegacion_inicio maybe no

NUM_VARS = ["latitud", "longitud", "bool_llamada", "sin_hr", "cos_hr", "sin_month", "cos_month",
            "sin_day", "cos_day"]

CAT_VARS = [ 'one_hot__x0_ALVARO OBREGON', 'one_hot__x0_AZCAPOTZALCO',
       'one_hot__x0_BENITO JUAREZ', 'one_hot__x0_COYOACAN',
       'one_hot__x0_CUAJIMALPA', 'one_hot__x0_CUAUHTEMOC',
       'one_hot__x0_GUSTAVO A. MADERO', 'one_hot__x0_IZTACALCO',
       'one_hot__x0_IZTAPALAPA', 'one_hot__x0_MAGDALENA CONTRERAS',
       'one_hot__x0_MIGUEL HIDALGO', 'one_hot__x0_MILPA ALTA',
       'one_hot__x0_No Disponible', 'one_hot__x0_TLAHUAC',
       'one_hot__x0_TLALPAN', 'one_hot__x0_VENUSTIANO CARRANZA',
       'one_hot__x0_XOCHIMILCO', 'one_hot__x2_APLICATIVOS',
       'one_hot__x2_BOTÓN DE AUXILIO', 'one_hot__x2_CÁMARA',
       'one_hot__x2_LLAMADA APP911', 'one_hot__x2_LLAMADA DEL 066',
       'one_hot__x2_LLAMADA DEL 911', 'one_hot__x2_RADIO', 'one_hot__x2_REDES',
       'one_hot__x2_ZELLO', 'one_hot__x1_accidente-choque con lesionados',
       'one_hot__x1_accidente-choque con prensados',
       'one_hot__x1_accidente-choque sin lesionados',
       'one_hot__x1_accidente-ciclista', 'one_hot__x1_accidente-ferroviario',
       'one_hot__x1_accidente-monopatín', 'one_hot__x1_accidente-motociclista',
       'one_hot__x1_accidente-otros',
       'one_hot__x1_accidente-persona atrapada / desbarrancada',
       'one_hot__x1_accidente-vehiculo atrapado',
       'one_hot__x1_accidente-vehiculo desbarrancado',
       'one_hot__x1_accidente-vehículo atrapado-varado',
       'one_hot__x1_accidente-volcadura',
       'one_hot__x1_cadáver-accidente automovilístico',
       'one_hot__x1_cadáver-atropellado',
       'one_hot__x1_detención ciudadana-accidente automovilístico',
       'one_hot__x1_detención ciudadana-atropellado',
       'one_hot__x1_lesionado-accidente automovilístico',
       'one_hot__x1_lesionado-atropellado',
       'one_hot__x1_mi ciudad-calle-incidente de tránsito',
       'one_hot__x1_mi ciudad-taxi-incidente de tránsito',
       'one_hot__x1_sismo-choque con lesionados',
       'one_hot__x1_sismo-choque con prensados',
       'one_hot__x1_sismo-choque sin lesionados',
       'one_hot__x1_sismo-persona atropellada','one_hot__x3_12-3 a.m.', 'one_hot__x3_12-3 p.m.',
       'one_hot__x3_3-6 a.m.', 'one_hot__x3_3-6 p.m.', 'one_hot__x3_6-9 a.m.',
       'one_hot__x3_6-9 p.m.', 'one_hot__x3_9-12 a.m.',
       'one_hot__x3_9-12 p.m.' ], #"incidente_c4", "espacio_del_dia","delegacion_inicio", "tipo_entrada"]  # delegacion_inicio

# ALGORITHMS = ['tree', 'random_forest'] #sinceramente no funcionaron muy bien; y ya no hay tiempo para entrenarlos
ALGORITHMS = ['logistic', 'tree']  # ya no hay tiempo pa'l Forrest Gump

# dejé delegación por si es más fácil hacer lo de Aequitas así; lo podemos quitar después

# lo primero es cargar el pickle

def load_features(path):
    """
    Cargar pickle que se generó durante la transformación
    :param path: Path donde se encuentra el pickle
    :return:
    """
    print("Opening feature engineering pickle from output path")
    output_path = os.path.join(path, "output", "fe_df.pkl")

    # Recuperar el pickle
    incidentes_pkl = load_df(output_path)
    print("Feature Engineering pickle successfully retrieved.")

    return incidentes_pkl


# lo segundo es quedarnos solo con las columnas que vamos a usar

def filter_drop(df):
    """
    Función para elegir variables relevantes y tirar los datos vacíos de latitud y longitud.
    :param df: dataframe a transformar
    :return df: dataframe con las columnas relevantes y sin datos nulos
    """
    print("Dropping columns and Nan's (don't worry, it'll be ok)")
    # solo por seguridad nos aseguramos que estén ordenadas (aunque ya están)
    df = df.sort_values(by=["año_creacion", "mes_creacion", "dia_creacion",
                            "hora_simple"])
    return df.drop(columns=["año_creacion", "mes_creacion", "dia_creacion"]).dropna()


# el tercer paso sería el famoso magic loop, también conocido como 'Majin Boo' por los fans de Dragon Ball-Z
# (entre ellos Rhayid Ghani)


# train_test_split
def train_test_split(df, test_size=.70):
    """
    Función para separar en train y test el dataframe.
    Es un poco manual porque son datos temporales -- y no queremos problemas.
    :param df: dataframe a separar en train y test
    :param test_size: fracción entre 0 y 1 que nos permita separar el dataframe. El default es .70
    :return X_train, y_train, X_test, y_test: los 4 fantásticos.
    """
    if test_size <= 0 or test_size >= 1:
        raise ValueError("Test Size Error. Pick a test size between 0 and 1.")

    # separar features y labels
    print("Performing train test split")
    X = df.drop(columns=["label"]).copy()
    Y = df.label.copy()
    lim = round(df.shape[0] * test_size)  # 70% de train
    X_train, X_test = X[:lim], X[lim:]
    y_train, y_test = Y[:lim], Y[lim:]
    print("Train test split successfully performed")
    return X_train, y_train, X_test, y_test


# iniciar pipeline de transformación
def transformation_pipeline(X_train, X_test, numerical_attributes, categorical_attributes):
    """
    Crear un pipeline que permita estandarizar el proceso y también recuperar el nombre de las
    variables.
    :param X_train: features dataframe.
    :param numerical_attributes: variables numéricas
    :param categorical_attributes: variables categóricas
    :return X_prepared, Y: features (transformadas) y labels
    """
    # esto en realidad no hace nada porque no hay datos nulos, pero facilita lo que viene después
    num_pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy="mean"))
    ])

    full_pipeline = ColumnTransformer([
        ("numerical", num_pipeline, numerical_attributes),
        ("categorical", OneHotEncoder(handle_unknown='ignore'), categorical_attributes)
    ])

    print("Features are transformed and ready for magic loop. What about your computer?")
    X_train_reloaded = full_pipeline.fit_transform(X_train)
    X_test_reloaded = full_pipeline.transform(X_test)
    return X_train_reloaded, X_test_reloaded


# ahora sí, ya podemos implementar el Majin Boo
# en el pasado intentamos con el decision tree y el Random Forest, pero no funcionó muy bien
# había muy pocas variables, por lo que decidimos agregar más e intentarlo con Regresión Logística.
# ya no hay tiempo pa' entrenar un Random Forrest Gump.


def save_models(model, path):
    """
    Function to save model from magic loop.
    """
    output_path = os.path.join(path,'output','model_loop.joblib')
    joblib.dump(model, output_path)


def magic_loop(path, algorithms, X_train, y_train):
    """
    #Función para implementar al famosísimo Majin Boo
    #:param algorithms: list (of algorithms)
    #:X_train, y_train: features and labels of training set, respectively
    #:return:
    """

    estimators = {'tree': DecisionTreeClassifier(random_state=1789), \
                  'logistic': LogisticRegression()}
    estimators_params = {'tree': {'max_depth': [3, 5, 10],
                                  'min_samples_leaf': [1, 3, 5]},
                         'logistic': {'penalty': ['l2'],
                                      'solver': ['sag', 'saga']}
                         }

    nombres = {'tree': "decision_tree_VF.joblib",
               'logistic': 'logistic_regression_VF.joblib'}

    tscv = TimeSeriesSplit(n_splits=5)
    print("Beginning magic loop. This may take a while.")
    # best_estimators = []
    for algorithm in algorithms:
        print(f"Training model with: {estimators[algorithm]}")
        estimator = estimators[algorithm]
        grid_params = estimators_params[algorithm]

        gs = GridSearchCV(estimator, grid_params, scoring='precision', cv=tscv,
                          n_jobs=-1)

        start = time.time()
        gs.fit(X_train, y_train)
        print(gs)
        # best_estimators.append(gs)
        joblib.dump(gs, nombres[algorithm])
        print("successfully saved best estimator .")

        if algorithm == 'logistic':
            try:
                save_models(gs, path)
            except:
                pass

        print(f"Total number of seconds: {time.time() - start}")

    # return best_estimators

def save_train_test_datasets(path, X_train, y_train, X_test, y_test):
    """"
    Guardar los sets de prueba y entrenamiento
    :param path: Path del repo
    :param X_train: features-dataset de entrenamiento
    :param y_train: labels-dataset de entrenamiento
    :param X_test: features-dataset de prueba
    :param y_test: labels-dataset de prueba
    """
    path_X_train = os.path.join(path, "output", "X_train.pkl")
    path_X_test = os.path.join(path, "output", "X_test.pkl")
    path_Y_train = os.path.join(path, "output", "Y_train.pkl")
    path_Y_test = os.path.join(path, "output", "Y_test.pkl")
    pickle.dump(X_train, open(path_X_train, "wb"))
    pickle.dump(X_test, open(path_X_test, "wb"))
    pickle.dump(y_train, open(path_Y_train, "wb"))
    pickle.dump(y_test, open(path_Y_test, "wb"))

def modeling(path):
    # Cargamos fe_df.pkl
    df = load_features(path)

    # Eliminamos nans y features no deseados
    df = filter_drop(df)

    # Separación en train y test
    X_train, y_train, X_test, y_test = train_test_split(df)
    #X_train, X_test = transformation_pipeline(X_train, X_test, NUM_VARS, CAT_VARS)

    # Guardamos los pickles
    save_train_test_datasets(path, X_train, y_train, X_test, y_test)

    # Let's do the magic
    magic_loop(path, ALGORITHMS, X_train, y_train)
