# Copyright (c) 2022-2023 The MITRE Corporation. ALL RIGHTS RESERVED.


import csv
import json
import argparse

FIELD_MAPPING_FILENAME = "field_mappings.json"
ALLOWED_FIELDS_FILENAME = "allowed_fields.json"

INPUT_FILE_NAME="sysmon_ecs_event_mappings_config.csv"

parser = argparse.ArgumentParser(prog="Sysmon-ILF Config Parser", description="Converts sysmon-ecs mapping csv file into configuration files required for sysmon-ilf logstash module")
parser.add_argument("-i", '--input', required=False, default=INPUT_FILE_NAME, help="name of the csv to be parsed (must be a csv file)", dest="input")
parser.add_argument("-m", '--mappings', required=False, default=FIELD_MAPPING_FILENAME, help="name of the field mappings output file (must end in .json)", dest="mapping")
parser.add_argument("-a", '--allowed', required=False, default=ALLOWED_FIELDS_FILENAME, help="name of the allowed fields output file (must end in .json)", dest="allowed")

args = parser.parse_args()
field_mappings = {}
allowed_fields = {}

with open(args.input, newline='') as file:
    reader = csv.DictReader(file, delimiter=',')

    for row in reader: 

        event_id = row['EventId']
        sysmon_name = row['SysmonFieldName'] 
        ecs_field = row['ECSFieldName']
        is_allowed = row['IsAllowed']

        if(',' in ecs_field):
            ecs_field = ecs_field.split(',')

        if(event_id in field_mappings):
            field_mappings[event_id][sysmon_name] = ecs_field
        else:
            field_mappings[event_id] = {sysmon_name: ecs_field}

        if(is_allowed == 'TRUE'):
            if(event_id in allowed_fields):
                allowed_fields[event_id].append(sysmon_name)
            else:
                allowed_fields[event_id] = [sysmon_name]

with open(args.mapping, "w") as outfile:
    json.dump(field_mappings, outfile)

with open(args.allowed, "w") as outfile:
    json.dump(allowed_fields, outfile)

print(f"\nFiles [{args.mapping}, {args.allowed}] successfully created from {args.input} mapping\n")
        
