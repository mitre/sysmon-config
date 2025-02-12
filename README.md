# Sysmon Configurations
This module is used by the Sysmon XML to ILF translator and the Sysmon to Logstash translator.

It allows for the configuration of:
* Allowed Sysmon events
* Allowed fields in a Sysmon event
* Sysmon field mappings to ECS
* Sysmon event names

## Directory Structure
```
sysmon_configurations
│   ├── allowed-field-configs
│   │   ├── allowed_fields.json (default config)
│   │   └── <custom allowed field configurations>
│   ├── field-mappings-configs
│   │   ├── field_mappings.json (default config)
│   │   └── <custom field mappings configurations>
│   ├── generation
│   │   ├── generate_config.py (config generation script)
│   │   ├── sysmon_ecs_event_mapping.csv (default mapping csv)
│   │   └── <custom mapping csvs>
│   └── name-mappings-configs
│       ├── name_mappings.json (default config)
│       └── <custom name mappings configurations>
```
## Configuration Files

There are 3 separate configuration files, all of these files are located in their own directories, see the [directory structure](./README.md#directory-structure) for more details. You can add custom configuration files by adding the new json file to the correct directory.

To aid in the construction of configuration files, a template csv, and [configuration generator script](#config-generation) are provided.

By default, the configuration will contain mappings for all Sysmon events/fields, and allow all fields for Sysmon v15.0.

### Allowed Fields Config

A json file that contains mappings from Sysmon-event ID to an array of allowed Sysmon fields.

Allowed fields configuration files should be placed in the `/allowed-field-configs` directory

See the [directory structure](./README.md#directory-structure) for more details.

Any fields that are not listed under an event will not be included in the output event.

*All events **must** contain an entry in the allowed fields config file. If one does not exist, the event will be **dropped** in the logstash pipeline.*

#### Allowed Fields Config Example

If we wanted to allow only the `UtcTime` and `ProcessId` Sysmon fields in event id `1`, `ProcessCreate`:

```json
{
  "1": [
    "UtcTime",
    "ProcessId"
  ],
  "2": [
    <Other field mappings here>
  ],
  <More event mappings here>
}
```

### Field Mappings Config

A json file that contains mappings from Sysmon-event ID to a json object containing key value pairs of Sysmon fields → ECS fields.

Field mappings configuration files should be placed in the `/field-mappings-configs` directory

See the [directory structure](./README.md#directory-structure) for more details.

*All events **must** contain at least one entry in the field mappings config file. If one does not exist, the translator using the configuration files will default to **dropping** the event.*

*Any fields that **do not** contain a mapping in the configuration file will be **dropped** from the event. If there are no valid ECS fields associated with the Sysmon field, map the field to `winlogbeat.event_data.[FIELD_NAME]`.*

#### Field Mapping Config Example

If we wanted to map only the `UtcTime` and `ProcessId` Sysmon fields in event id `1`, `ProcessCreate` to ECS fields:

```json
{
  "1": {
    "UtcTime": "@timestamp",
    "ProcessId": "process.pid"
  },
  "2": {
    <Other field mappings here>
  },
  <More event mappings here>
}
```

### Event Names Config

A json file that contains mappings from Sysmon-event ID to an event name. This name is used when generating the ILF associated with a Sysmon event.

Event name configuration files should be placed in the `/name-mappings-configs` directory

See the [directory structure](./README.md#directory-structure) for more details.

*Events that do **not** contain an entry in the event names config file, will be provided the default name of `NoMatchingEventName`. It is highly recommended to include a name mapping for all events*

#### Event Names Config Example

If we wanted to map the ILF event name of event id `1`, `ProcessCreate` to `CreateProcessEvent`:

```json
{
  "1": "CreateProcessEvent",
  "2": <Other ILF name>,
  <More event mappings here>
}
```

### Configuration Files Output Example

Here is an example output when using the configurations from the 3 configuration files listed above with the sysmon_to_ilf logstash translator.

#### Input

```json
{
    "winlog": {
        "process": {
            "pid": "45652"
        },
        "event_data": {
            "UtcTime": "2023-06-16 17:14:35.713",
            "ProcessGuid": "{d2a7e984-987b}",
            "ParentProcessGuid": "{d2a7e984-64b6}",
            "User": "MITRE\\CSCOPETSKI",
            "ProcessId": "8892"
        },
    },
    "event": {
        "code": "1",
        "action": "Process accessed (rule: ProcessAccess)"
    }
}
```

#### Output

```json
{
    "@timestamp":"2023-06-16T17:14:35.713Z",
    "process": {
      "pid": "8892"
    },
    "event": {
        "code": "1"
    },
    "ilf_string":"CreateProcessEvent[*,*,2023-06-16T17:14:35.713Z,(process__pid=8892,event__code=1)]"
}
```

Based on our example configs, only the `UtcTime` and `ProcessId` fields are allowed.

`UtcTime` is mapped to `@timestamp` and `ProcessId` is mapped to `process.pid`.

Every event will contain an `event.code` which is equal to the Sysmon event ID.

We can see that our ILF name "`CreateProcessEvent`" from the config was utilized in the `ilf_string`, which also contains the `@timestamp`, `process__pid`, and `event_code` fields.

### Config Generation

To help with customizing the [allowed fields](#allowed-fields-config) and [field mappings](#field-mappings-config) config files, a template CSV and generation script are provided.

#### CSV

The CSV consists of four columns

| Column Name       | Description                                                                                                                   | Valid Values        |
|-------------------|-------------------------------------------------------------------------------------------------------------------------------|---------------------|
| `EventId`         | The Sysmon event ID associated with the row                                                                                   | Any Sysmon Event ID |
| `SysmonFieldName` | The Sysmon field we are mapping from                                                                                          | Any Sysmon Field    |
| `ECSFieldName`    | The Elastic Common Schema field we are mapping to. In [special cases](#multivalue-mapping), we may map to multiple ECS fields | Any ECS Field       |
| `IsAllowed`       | Whether we want to allow this event field, or to filter it out in the logstash pipeline                                | TRUE or FALSE       |

The provided base csv `sysmon_ecs_event_mappings_config.csv` contains mappings for all events included in `Sysmon v15.0` (1-29 & 255).

For details on where it is located see the [directory structure](./README.md#directory-structure).

##### Multivalue Mapping

There are some Sysmon fields, that do not map properly to a single ECS field. These fields must be mapped to multiple ECS fields.

To map multiple values simply separate the ECS fields with commas, and surround them in quotes `""`

For example:

```csv
EventId,SysmonFieldName,ECSFieldName,IsAllowed
1,User,"user.domain,user.name",TRUE
1,Hashes,"process.hash.md5,process.hash.sha1,process.hash.sha256,process.pe.imphash",TRUE
```

The two currently supported multivalue mappings are for `User` and `Hashes`. Additional multivalue mappings will need to be programmed as special cases into all translators that use the configuration files.

#### Script

The config generator script is `generator.py`. For details on where it is located see the [directory structure](./README.md#directory-structure).

```text
usage: Sysmon-ILF Config Parser [-h] [-i INPUT] [-m MAPPING] [-a ALLOWED]

Converts sysmon-ecs mapping csv file into configuration files required for sysmon-ilf logstash module

options:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        name of the csv to be parsed (must be a csv file)
  -m MAPPING, --mappings MAPPING
                        name of the field mappings output file (must end in .json)
  -a ALLOWED, --allowed ALLOWED
                        name of the allowed fields output file (must end in .json)
```

The generator script looks for the default `sysmon_ecs_event_mappings_config.csv` in its directory as an input, and will by default output the two json configs `field_mappings.json` and `allowed_fields.json`.

Using the command line arguments you can change the names of the input/output files and the directories to look in

*The input file **must** be a CSV, and must follow the same [schema](#csv) as the default config csv*

## License

This software is licensed under the Apache 2.0 license.

## Public Release

> [!NOTE]
> Approved for Public Release; Distribution Unlimited. Public Release Case
> Number 24-3961.
