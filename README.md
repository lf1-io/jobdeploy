# AI Job Deploy

Getting started.

```bash
pip install ai-jobdeploy
```

1. In a project `mkdir .js`
2. Create some deployment templates (see below)
3. Get experimenting!


## Base Template


Templates must implement 5 fields: `params`, `meta`, `config`, `values` and `builds`. 

`params` is a list of parameters specified on creation `up` of the resource.
`meta` is a list and subset of "subdir", "id", "project".
`config` is a dictionary of configured values (e.g. security group ids, etc..)
`values` are a dictionary of formatted values (on the basis of parameters) which are 
and may be referred to in the `builds`.

The `builds` section must implement `up` and `down`. There are 3 types of builds:

- `sequence`
- `script`
- `file`

`sequence`: sequence of `script`s or `file`s.

`script`: an executable script (usually bash).

`file`: a file saved to the path given by the build name.

**local.yaml**

```yaml
params:
  - name
  - run
  
meta:
  - id
  - subdir
  - project

config:
  python: /usr/bin/python3

builds:
  install:
    type: script
    content: |
      #!/bin/bash
      {{ params['python'] }} -m pip install -r requirements.txt

  deploy_script:
    type: file
    content: |
      #!/bin/bash
      mkdir -p checkpoints/{{ params.name }}
      {{ params['run'] }} | tee checkpoints/{{ params.name }}/log

  start:
    type: script
    content: |
      #!/bin/bash
      chmod +x .jd/{{ params['subdir'] }}/tasks/deploy_script
      tmux new-session -d -s {{ params['project'] }}-{{ params['id'] }} ".jd/{{ params['subdir'] }}/tasks/deploy_script"

  watch:
    type: script
    content: |
      #!/bin/bash
      tmux a -t {{ params['project'] }}-{{ params['id'] }}

  down:
    type: script
    whitelist: [256]
    content: |
      #!/bin/bash
      tmux kill-session -t {{ params['project'] }}-{{ params['id'] }}

  purge:
    type: script
    content: |
      #!/bin/bash
      rm -rf checkpoints/{{ params['name'] }}

  up:
    type: sequence
    content:
      - install
      - deploy_script
      - start
```

## Using templates to create and manage resources

List resources:
```bash
jd ls
```

Here is how to create the `my_model.yaml` resource:
```bash
jd build local up --params run='python3 -u test.py',name=test
```

Do something with the resource (anything apart from up). Get `id` from `jd ls`.

```bash
jd build watch --id <id>
```

Stop resource:
```bash
jd rm <id> [--purge/--no-purge]
```

