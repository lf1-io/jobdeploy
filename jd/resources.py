import glob
import json


def find_jd_files(depth=3):
    files = []
    for dep in range(depth):
        pattern = '*/' * dep + 'jd.json'
        files.extend(glob.glob(pattern))
    return files


def load_all_resources(root='', depth=3):
    """
    Load all of the meta data of all deployments.
    """
    all_files = find_jd_files(depth=depth)
    all_ = []
    for file_ in all_files:
        if not file_.startswith(root):
            continue
        with open(file_) as f:
            meta = json.load(f)
        all_.extend(meta)
    all_ = sorted(all_, key=lambda x: x['created'])
    return all_


def load_resource(id_):
    """
    Load meta data of id.

    :param id_: ID identified of deployment.
    """
    all_resources = load_all_resources()
    return next(x for x in all_resources if x['id'] == id_)
