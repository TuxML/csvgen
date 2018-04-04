#!/usr/bin/python3

import genCSVlib
import sys
import DBCredentials

if __name__ == "__main__":  
    if len(sys.argv) < 2:
            print("No output file specified")
            exit(-1)

    genCSVlib.genCSV(DBCredentials.irmaDB_v2, sys.argv[1])