# AI Job Deploy

Getting started.

```bash
pip install ai-jobdeploy
```

## Base Template


Templates must implement 2 fields: `params`, `values` and `builds`. 

`params` are a list of parameters specified on creation `up` of the resource.

`values` are a dictionary of formatted values (on the basis of parameters) which are created at `up` and may be referred to in the `builds`.

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
  - project
  - name
  - id
  - subdir
  - run
  - python

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

## Configured templates

Templates may be configured on the basis of a base template. For this, two additional fields must be specified `binds` and `parent`. For example, on the basis of the above template, we can configure a specific python version.

**my_model.yaml**

```yaml
parent: local.yaml

binds:
  python: /usr/bin/python3

watch:
  type: script
    content: |
    #!/bin/bash
    echo "watching the job..."
    tmux a -t {{ params['project'] }}-{{ params['id'] }}
```

## Using templates

Here is how to create the `local`.