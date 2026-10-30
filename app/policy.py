import yaml

def load_policy(path="policies/policy.yaml"):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)