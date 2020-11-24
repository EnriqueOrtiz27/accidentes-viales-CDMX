"""
Ingestion module
"""

def ingest_file(file_name):
    """
    Function to retrieve and return the accidents dataset.
    Parameters:
    -----------
    file_name: str
               Path to the file.
    Returns:
    --------
    df: pandas dataframe
    """
    df = pd.read_csv(file_name)
    return df

def drop_cols(df):
    """
    Function to drop unnnecesary columns in the dataset.
    """
    df.drop(columns = ['folio', 'geopoint', 'mes', 'mes_cierre',
                       'hora_cierre', 'año_cierre'], inplace = True)
    return df


def generate_label(df):
    """
    Function to create a new column indicating whether there was
    a false alarm or not.
    Parameters:
    -----------
    df: pandas dataframe

    Returns:
    --------
    df: pandas dataframe
    """
    # transformamos la columna para solo quedarnos con la letra del código
    df["codigo_cierre"] = df["codigo_cierre"].apply(lambda x: x[1])
    df['label'] = np.where(
        (df.codigo_cierre == 'F') | (df.codigo_cierre == 'N'), 1, 0)
    return df

def save_ingestion(df, path):
    """
    Guarda en formato pickle (ver notebook feature_engineering.ipynb) el data frame
    que ya no tiene las columnas que ocuparemos y que incluye el label generado.
    :param df: Dataframe que se utilizará
    :param path:
    :return:
    """
    output_path = os.path.join(path, "output", "ingest_df.pkl")
    # Guardar en el pickle
    pickle.dump(df, open(output_path, "wb"))


def add_date_columns(df):
    """
    Esta función es muy importante puesto que nos ayudará a crear el mes, día y año de creación
    del registro. De esta manera podemos prescindir de las fechas de cierre, que no tendríamos en tiempo
    real en un modelo.
    Parameters:
    -----------
    df: pandas dataframe

    Returns:
    ---------
    df: pandas dataframe with 4 new columns
    """
    mapping_meses = {1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo",
                     6: "Junio", 7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre",
                     11: "Noviembre", 12: "Diciembre"}

    df["año_creacion"] = df.fecha_creacion.dt.year
    df["mes_creacion"] = df.fecha_creacion.dt.month
    df["dia_creacion"] = df.fecha_creacion.dt.day
    df["mes_creacion_str"] = df.mes_creacion.map(mapping_meses)
    df["año_creacion"] = df["año_creacion"].astype(str)
    return df


def create_time_blocks(df):
    """
    Function to group the hour of the day into 3-hour blocks.
    Parameters:
    -----------
    df: pandas dataframe

    Returns:
    ---------
    df: pandas dataframe with a new column indicating the time-block.
    """
    horas_int = set(df.hora_simple.astype(int).values)  # estaba como categórico
    f = lambda x: 12 if x == 0 else x
    mapping_hours = {}
    for hora in horas_int:
        grupo = (hora // 3) * 3
        if grupo < 12:
            nombre_grupo = str(f(grupo)) + "-" + str(grupo + 2) + " a.m."
        else:
            hora_tarde = grupo % 12
            nombre_grupo = str(f(hora_tarde)) + "-" + str(hora_tarde + 2) + " p.m."
        mapping_hours[hora] = nombre_grupo

    df["espacio_del_dia"] = df["hora_simple"].astype(int).map(mapping_hours)
    return df


def ingest(path):
    """
    Function to do all ingestion functions
    Parameters:
    -----------
    path: must be the root of the repo
    """

    df = ingest_file(path)
    df = generate_label(df)
    df = drop_cols(df)

    save_ingestion(df, path)


