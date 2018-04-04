#!/usr/bin/python3

import MySQLdb
import os
import csv
import bz2

arch = "x86"
version = "4.13.3"

default_values = {
    "UNKNOWN":"0",
    "INT":"0",
    "HEX":"0x0",
    "STRING":None,
    "TRISTATE":"n",
    "BOOL":"n",
    "FLOAT":"0.0"
}

def isWhitespace(c):
    return c==' ' or c=='\t' or c=='\n'

def scanConfig(configdata, bz2_enabled):
    if bz2_enabled:
        config = bz2.decompress(configdata).decode('ascii')
    else:
        config = configdata
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
                # remove quotes
                if value[0] == '"' and value[-1] == '"': value = value[1:-1]
                # set in dict and remove leading "CONFIG_" in name
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

def genCSV(credentials, output):
    try:
        print("Connecting to db...", end="", flush=True)
        conn = MySQLdb.connect(**credentials["creds"])
        cursor = conn.cursor()

        offset = 0
        step = 50
        get_prop = "SELECT name, type FROM Properties INNER JOIN Arch INNER JOIN Version where arch_name = %s AND version_name = %s"
        query = "SELECT cid, config_file, core_size, compilation_time FROM {} WHERE compilation_time > -1 ORDER BY cid LIMIT %s OFFSET %s".format(credentials["table"])
        count_rows = "SELECT COUNT(*) FROM {} WHERE compilation_time > -1".format(credentials["table"])
        end = False;

        # Header
        cursor.execute(get_prop, (arch, version))
        types_results = list(cursor.fetchall())
        types_results.append(("KERNEL_SIZE", "INT"))
        types_results.append(("COMPILE_TIME", "FLOAT"))
        names = [""]*len(types_results)
        defaults = [0]*len(types_results)
        order = {}
        index = 0
        for (name, typ) in types_results:
            order[name] = index
            names[index] = name
            defaults[index] = default_values[typ]
            index += 1
        order_kernel_size = order["KERNEL_SIZE"]
        order_compile_time = order["COMPILE_TIME"]
        # Row count
        cursor.execute(count_rows)
        row_count = cursor.fetchone()[0]
        # File
        csvfile = open(output, 'w')
        writer = csv.writer(csvfile)
        writer.writerow(names)

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
                    props = scanConfig(config_file, credentials["bz2"])
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
        print("CSV file generated at " + output)

    except MySQLdb.Error as err:
        print("\nError : Can't read from db : {}".format(err.args[1]))
        exit(-1)
    finally:
        conn.close()
