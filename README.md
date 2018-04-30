# csvgen

## Synopsis

Part of the [TuxML](https://github.com/TuxML) Project to predict kernel properties from a wide range of tested kernels.

Extracts data from the database filled by [ProjetIrma](https://github.com/TuxML/ProjetIrma) and [Kanalyser](https://github.com/TuxML/Kanalyser) and writes a CSV file of features (config properties, kernel size, time of compilation, time of boot...) for machine learning use.

## Prerequisites

`python3` and some libs:

    pip3 install mysqlclient

## Usage

Fill out DBCredentials.py with your own databases (both TuxML databases are already there for examples) and run :
    
    ./genCSV.py output.csv
