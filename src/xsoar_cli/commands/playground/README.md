# playground

Execute commands and automations in the XSOAR playground or in a specific incident.

## Commands

### run

Execute an XSOAR command or automation. If no `--investigation-id` is provided the command runs in the XSOAR playground.

```
xsoar-cli playground run [OPTIONS] COMMAND
```

**Arguments**

| Argument  | Description                                          |
|-----------|------------------------------------------------------|
| `COMMAND` | XSOAR command to run. Must start with `!`.           |

**Options**

| Option                | Description                                                                     |
|-----------------------|---------------------------------------------------------------------------------|
| `--environment`       | Named environment from the config file. Defaults to `default_environment`.      |
| `--investigation-id`  | Incident or investigation ID. Defaults to the XSOAR playground.                 |

**Examples**

Run a simple print command in the playground:

```
xsoar-cli playground run '!Print value=hello'
```

Run a command in a specific incident:

```
xsoar-cli playground run --investigation-id 12345 '!MyAutomation arg=value'
```

Run a command against a named environment:

```
xsoar-cli playground run --environment prod '!Print value=hello'
```
