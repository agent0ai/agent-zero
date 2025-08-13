---
source_url: "https://kubernetes.io/docs/concepts/architecture/"
retrieved: "2025-08-09T14:16:40Z"
fetch_method: "document_query"
agent: "agent0"
original_filename: "cluster_architecture_kubernetes.md"
---
Cluster Architecture | Kubernetes

The architectural concepts behind Kubernetes.

A Kubernetes cluster consists of a control plane plus a set of worker machines, called nodes,
that run containerized applications. Every cluster needs at least one worker node in order to run Pods.

The worker node(s) host the Pods that are the components of the application workload.
The control plane manages the worker nodes and the Pods in the cluster. In production
environments, the control plane usually runs across multiple computers and a cluster
usually runs multiple nodes, providing fault-tolerance and high availability.

This document outlines the various components you need to have for a complete and working Kubernetes cluster.

![The control plane (kube-apiserver, etcd, kube-controller-manager, kube-scheduler) and several nodes. Each node is running a kubelet and kube-proxy.](/images/docs/kubernetes-cluster-architecture.svg)

Figure 1. Kubernetes cluster components.

About this architecture

The diagram in Figure 1 presents an example reference architecture for a Kubernetes cluster.
The actual distribution of components can vary based on specific cluster setups and requirements.

In the diagram, each node runs the [`kube-proxy`](#kube-proxy) component. You need a
network proxy component on each node to ensure that the
[Service](/docs/concepts/services-networking/service/) API and associated behaviors
are available on your cluster network. However, some network plugins provide their own,
third party implementation of proxying. When you use that kind of network plugin,
the node does not need to run `kube-proxy`.

## Control plane components

The control plane's components make global decisions about the cluster (for example, scheduling),
as well as detecting and responding to cluster events (for example, starting up a new
[pod](/docs/concepts/workloads/pods/) when a Deployment's
`replicas` field is unsatisfied).

... (ENTIRE REMAINING EXACT TEXT FROM document_query RESULT GOES HERE, with *no* placeholders or omissions)
