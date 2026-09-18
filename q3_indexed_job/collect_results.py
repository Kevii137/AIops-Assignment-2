"""
collect_results.py -- AIOps Module 3 Assignment, Question 3.
Collects RESULT_JSON lines from every pod of the completed Indexed Job via the
Kubernetes API (pod logs), rather than a shared volume -- see write-up for why
(minikube's default storage provisioner is node-local, so a PV would not be reliably
reachable by pods scheduled onto a different node than the one it was provisioned on).
"""
import argparse
import json
import re
import sys

from kubernetes import client, config

RESULT_LINE_RE = re.compile(r"RESULT_JSON:(\{.*\})")


def load_kube_config(context=None):
    try:
        config.load_kube_config(context=context)
    except Exception:
        config.load_incluster_config()


def collect(job_name, namespace="default"):
    v1 = client.CoreV1Api()
    pods = v1.list_namespaced_pod(namespace=namespace, label_selector=f"job-name={job_name}")
    if not pods.items:
        print(f"No pods found for job '{job_name}'.", file=sys.stderr)
        return []

    rows = []
    for pod in pods.items:
        pod_name = pod.metadata.name
        try:
            logs = v1.read_namespaced_pod_log(name=pod_name, namespace=namespace)
        except client.exceptions.ApiException as e:
            print(f"  Could not read logs for {pod_name}: {e.reason}", file=sys.stderr)
            continue
        match = RESULT_LINE_RE.search(logs)
        if not match:
            print(f"  No RESULT_JSON line in {pod_name} yet.", file=sys.stderr)
            continue
        result = json.loads(match.group(1))
        result["k8s_pod_phase"] = pod.status.phase
        rows.append(result)

    rows.sort(key=lambda r: r["completion_index"])
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-name", default="shard-validate-job")
    parser.add_argument("--namespace", default="default")
    parser.add_argument("--context", default=None)
    args = parser.parse_args()

    load_kube_config(context=args.context)
    rows = collect(args.job_name, args.namespace)
    if not rows:
        print("No results collected.")
    else:
        header = f"{'idx':<4}{'shard_file':<16}{'total':<7}{'invalid':<9}{'pod_name':<32}{'node_name':<24}"
        print(header)
        print("-" * len(header))
        total_invalid = 0
        nodes = set()
        for r in rows:
            print(f"{r['completion_index']:<4}{r['shard_file']:<16}{r['total_rows']:<7}"
                  f"{r['invalid_rows']:<9}{r['pod_name']:<32}{r['node_name']:<24}")
            total_invalid += r["invalid_rows"]
            nodes.add(r["node_name"])
        print("-" * len(header))
        print(f"Total invalid rows across all shards: {total_invalid}")
        print(f"Distinct nodes used: {sorted(nodes)}")
