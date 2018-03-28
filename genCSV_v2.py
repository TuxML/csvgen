#!/usr/bin/python3

import irmaDBCredentials
import MySQLdb
import os
import csv
import sys
import bz2

arch = "x86"
version = "4.13.3"

default_values = {
    "UNKNOWN":"0",
    "INT":"0",
    "HEX":"0x0",
    "STRING":"\"\"",
    "TRISTATE":"n",
    "BOOL":"n",
    "FLOAT":"0.0"
}

def isWhitespace(c):
    return c==' ' or c=='\t' or c=='\n'

def scanConfig(bz2config):
    config = bz2.decompress(bz2config).decode('ascii')
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
        c = config[cursor]
        if state == 0:
            if c == '#':
                state = 1
            elif not isWhitespace(c):
                state = 2
                name = c
        elif state == 1:
            if c == '\n':
                state = 0
        elif state == 2:
            if c != '=':
                name += c
            else:
                state = 3
                value = ""
        elif state == 3:
            if c != '\n':
                value += c
            else:
                props[name[7:]] = value
                state = 0
        cursor += 1
    if state == 2: raise ValueError("Incomplete .config file : " + str(props))
    return props

def printProgress(p):
    if p > 100: p = 100
    if p < 0: p = 0
    progress = p/5
    print("\rProgression: [", end="", flush=True)
    for i in range(int(progress)):
        print("#", end="", flush=True)
    for i in range(int(progress), 20):
        print("-", end="", flush=True)
    print("] " + str(int(p)) + "%", end="", flush=True)


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("No output file specified")
        exit(-1)

    try:
        print("Connecting to db...", end="", flush=True)
        conn = MySQLdb.connect(**irmaDBCredentials.info_v2)
        cursor = conn.cursor()

        offset = 0
        step = 50
        get_prop = "SELECT name, type FROM Properties INNER JOIN Arch INNER JOIN Version where arch_name = %s AND version_name = %s"
        query = "SELECT cid, config_file, core_size, compilation_time FROM Compilations WHERE compilation_time > -1 ORDER BY cid LIMIT %s OFFSET %s"
        count_rows = "SELECT COUNT(*) FROM Compilations WHERE compilation_time > -1"
        end = False;

        # Header
        cursor.execute(get_prop, (arch, version))
        types_results = list(cursor.fetchall())
        types_results.append(("KERNEL_SIZE", "INT"))
        types_results.append(("COMPILE_TIME", "FLOAT"))
        names = [""]*len(types_results)
        defaults = [0]*len(types_results)
        types = [0]*len(types_results)
        order = {}
        index = 0
        for (name, typ) in types_results:
            order[name] = index
            names[index] = name
            defaults[index] = default_values[typ]
            types[index] = typ
            index += 1
        order_kernel_size = order["KERNEL_SIZE"]
        order_compile_time = order["COMPILE_TIME"]
        # Row count
        cursor.execute(count_rows)
        row_count = cursor.fetchone()[0]
        # File
        csvfile = open(sys.argv[1], 'w')
        writer = csv.writer(csvfile)
        writer.writerow(names)
        writer.writerow(types)

        print("Done\nFilling rows :")

        bad_files = []

        while not end:
            printProgress(100*offset/row_count)
            cursor.execute(query, (step, offset))
            results = cursor.fetchall()
            if len(results) == 0:
                end = True
                break

            for num, (cid, config_file, core_size, compilation_time) in enumerate(results):
                try:
                    props = scanConfig(config_file)
                    values = list(defaults)
                    values[order_kernel_size] = core_size
                    values[order_compile_time] = compilation_time
                    for (k,v) in props.items():
                        values[order[k]] = v
                    writer.writerow(values);
                except ValueError as e:
                    bad_files.append((cid, str(e)))

            offset += step

        cursor.close()
        printProgress(100)

        print("")
        if len(bad_files) > 0:
            print("Bad .configs : ")
            for file in bad_files:
                print("id = {}, error = {}".format(file[0], file[1]))
        print("CSV file generated at " + sys.argv[1])

    except MySQLdb.Error as err:
        print("\nError : Can't read from db : {}".format(err.args[1]))
        exit(-1)
    finally:
        conn.close()