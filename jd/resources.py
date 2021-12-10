import json
import os


def load_all_resources():
    """
    Load all of the meta data of all deployments.
    """
    all_ = []
    subdirs = [x for x in os.listdir('.jd')]
    for subdir in subdirs:
        with open(f'.jd/{subdir}/info.json') as f:
            meta = json.load(f)
        all_.append(meta)
    all_ = sorted(all_, key=lambda x: x['created'])
    return all_


def load_resource(id_):
    """
    Load meta data of id.

    :param id_: ID identified of deployment.
    """
    subdir = [x for x in os.listdir('.jd') if x.endswith(id_)][0]
    with open(f'.jd/{subdir}/info.json') as f:
        return json.load(f)
