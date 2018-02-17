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
    state = 0
    # 0 -> seeking name, comment, or end of file
    # 1 -> skipping comment
    # 2 -> writing name
    # 3 -> writing value
    name = ""
    value = ""
    while cursor < s:
        if state == 0:
            if config[cursor] == '#':
                state = 1
            elif not isWhitespace(config[cursor]):
                state = 2
                name = ""
        elif state == 1:
            if config[cursor] == '\n':
                state = 0
        elif state == 2:
            if config[cursor] != '=':
                name += config[cursor]
            else:
                state = 3
                value = ""
        elif state == 3:
            if config[cursor] != '\n':
                value += config[cursor]
            else:
                props[name] = value
                state = 0
        cursor += 1
    if state == 2: raise ValueError("Incomplete .config file")
    return props

if __name__ == "__main__":
    tty = open("/dev/tty", mode='w')

    try:
        print("Connecting to db...", file=tty, end="", flush=True)
        conn = MySQLdb.connect(**irmaDBCredentials.info)
        cursor = conn.cursor()

        get_prop = "SELECT name, type FROM Properties INNER JOIN Arch INNER JOIN Version where arch_name = %s AND version_name = %s"
        query = "SELECT cid, config_file, core_size, compilation_time FROM TuxML WHERE compilation_time > -1"

        print("Done\nMaking request...", file=tty, end="", flush=True)
        cursor.execute(get_prop, (arch, version))
        types_results = cursor.fetchall()

        cursor.execute(query)
        results = cursor.fetchall()

        cursor.close()
        print("Done\nFilling default values...", file=tty, end="", flush=True)

        defaults = {}

        for (name, typ) in types_results:
            defaults[name] = default_values[typ]

        defaults["KERNEL_SIZE"] = 0
        defaults["COMPILE_TIME"] = 0

        print("Done\nPrinting header...", file=tty, end="", flush=True)

        for (k,v) in defaults.items():
            print(k + ",", end="")
        print("")

        bad_files = []

        print("Done\nPrinting rows", file=tty, end="", flush=True)
        for num, (cid, config_file, core_size, compilation_time) in enumerate(results):
            try:
                props = scanConfig(config_file)
                values = dict(defaults)
                values["KERNEL_SIZE"] = core_size
                values["COMPILE_TIME"] = compilation_time
                for (k,v) in props.items():
                    values[k] = v
                for (k,v) in values.items():
                    print(str(v) + ",", end="")
                print("\rPrinting rows ({}/{})".format(num+1, len(results)), file=tty, end="", flush=True)
            except ValueError as e:
                bad_files.append((cid, str(e)))
        print("")
        print("", file=tty)
        if len(bad_files) > 0:
            print("Bad .configs : ", file=tty)
            for file in bad_files:
                print("id = {}, error = {}".format(file[0], file[1]), file=tty)

    except MySQLdb.Error as err:
        print("\nError : Can't read from db : {}".format(err.args[1]), file=tty)
        exit(-1)
    finally:
        conn.close()
