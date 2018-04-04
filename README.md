# csvgen

## Synopsis

Part of the [TuxML](https://github.com/TuxML) Project to predict kernel properties from a wide range of already tested kernels.

Extracts data from the database filled by [ProjetIrma](https://github.com/TuxML/ProjetIrma) and writes a CSV file of features (config properties, kernel size, time of compilation, time of boot...) for machine learning use.

## Prerequisites

`python3` and some libs:

    pip3 install mysqlclient

## Usage

To get results from both IrmaDB databases :

    ./genCSV output.csv

To get results from one of the IrmaDB database :

    ./genCSV_v1.py output.csv
    ./genCSV_v2.py output.csv

To get your own results : add entries in DBCredentials.py to match your databases and create a new script following either genCSV_v1.py or genCSV_v2.py.