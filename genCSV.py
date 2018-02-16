#!/usr/bin/python3

import irmaDBCredentials
import MySQLdb
import os
import csv

arch = "x86"
version = "4.13.3"

default_values = {
    "UNKNOWN":"0",
    "INT":"0",
    "HEX":"0",
    "STRING":"\"\"",
    "TRISTATE":"n",
    "BOOL":"n",
}

def isWhitespace(c):
    return c==' ' or c=='\t' or c=='\n'

def scanConfig(config):
    props = {}
    cursor = 0
    s = len(config)
    while cursor < s:
        while isWhitespace(config[cursor]):
            cursor += 1
        name = ""
        while (config[cursor]!='='):
            name += config[cursor]
            cursor += 1
        cursor += 1
        value = ""
        while (config[cursor]!='\n' and cursor < s):
            value += config[cursor]
        props[name] = value
    return props

if __name__ == "__main__":
    try:
        conn = MySQLdb.connect(**irmaDBCredentials.info)
        cursor = conn.cursor()

        get_prop = "SELECT name, type FROM Types INNER JOIN Arch INNER JOIN Version where Arch.arch = %s AND Version.version = %s"
        query = "SELECT config_file, core_size, compilation_time FROM TuxML WHERE compilation_time > -1"

        cursor.execute(get_prop, (arch, version))
        types_results = cursor.fetchall()

        cursor.execute(query)
        results = cursor.fetchall()

        cursor.close()

        defaults = {}

        for (name, typ) in types_results:
            defaults[name] = default_values[typ]

        defaults["KERNEL_SIZE"] = 0
        defaults["COMPILE_TIME"] = 0

        for (k,v) in defaults:
            print(k + ",", end="")
        print("")
        for (config_file, core_size, compilation_time) in results:
            props = scanConfig(config_file)
            values = dict(defaults)
            values["KERNEL_SIZE"] = core_size
            values["COMPILE_TIME"] = compilation_time
            for (k,v) in props.items():
                values[k] = v
            for (k,v) in values.items():
                print(v + ",", end="")
        print("")

    except MySQLdb.Error as err:
        print("Error : Can't read from db : {}".format(err.args[1]))
        exit(-1)
    finally:
        conn.close()
