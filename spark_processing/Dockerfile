# è la versione LTS
FROM apache/spark:3.5.0

# per installare i pacchetti
USER root

RUN pip install --no-cache-dir numpy pandas scikit-learn

# run sempre con il minimo privilegio
USER spark

WORKDIR /code/spark_processing/
