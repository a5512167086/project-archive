# Development Environment Dependencies

In the local development environment, we will use Kubernetes (Minikube) as the K8s cluster and Traefik as the Ingress Controller to manage traffic and enable reverse proxy functionality.

## 1. Setting Up the Kubernetes Cluster (Minikube)

Minikube is a lightweight Kubernetes cluster suitable for local development and testing. Refer to the official documentation for installation: [Minikube Official Documentation](https://minikube.sigs.k8s.io/docs/).

### Install and Start Minikube

1. Install Minikube:
   - Linux/macOS: `curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64 && sudo install minikube-linux-amd64 /usr/local/bin/minikube`
   - Windows (using Chocolatey): `choco install minikube`
2. Start the Minikube cluster:

   ```sh
   minikube start --driver=docker
   ```

## 2. Installing the Ingress Controller (Traefik)

Traefik is a lightweight, Kubernetes-supported Ingress Controller responsible for traffic management, load balancing, TLS termination, and more.

### Install Traefik

To install Traefik on Minikube, run:

```sh
kubectl apply -f https://raw.githubusercontent.com/traefik/traefik/v2.9.6/examples/k8s/traefik.yaml
```

Verify that Traefik is running:

```sh
kubectl get pods -n kube-system | grep traefik
```

## 3. Configure the Local Hosts File

To access the application via a user-friendly domain name, modify the `/etc/hosts` file and add the following entry:

```
127.0.0.1 dev.local
```

> Windows users can modify the `C:\Windows\System32\drivers\etc\hosts` file for the same configuration.

## 4. Accessing Traefik

Minikube does not provide an external LoadBalancer by default. Instead, use `minikube tunnel` to simulate a LoadBalancer, making services accessible via `127.0.0.1`.

### Start Minikube Tunnel

```sh
minikube tunnel
```

This command creates a local network tunnel, allowing LoadBalancer services to be accessible on `127.0.0.1`.

## 5. Accessing the EasyBot Application

Once Traefik is set up, the application should be accessible via `dev.local`.

Open in a browser:

```
http://dev.local/
```

At this point, the EasyBot application should be accessible, with traffic managed through Traefik.

---
By completing these steps, you can manage applications using Kubernetes and an Ingress Controller in the local environment while accessing services through the custom domain `dev.local`.
