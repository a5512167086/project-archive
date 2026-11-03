# Development Environment Setup with Minikube and Traefik

This guide describes how to set up a local Kubernetes development environment using **Minikube** and **Traefik** as the Ingress Controller. This setup is compatible with tools like **Google OAuth** by enabling access to services via a custom domain `dev.local.com` **without a port number**.

---

## 1. Install Minikube

### Linux/macOS

```bash
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube
```

### Windows (using Chocolatey)

```powershell
choco install minikube
```

Ensure your system has a supported driver installed. For Fedora, we recommend using `--driver=kvm2`.

---

## 2. Start the Minikube Cluster

```bash
minikube start --driver=kvm2
```

Verify the cluster is running:

```bash
kubectl get nodes
```

---

## 3. Install Traefik (Ingress Controller)

### Add Helm repo and install

```bash
helm repo add traefik https://traefik.github.io/charts
helm repo update

kubectl create namespace traefik

helm install traefik traefik/traefik \
  --namespace traefik \
  --set service.type=ClusterIP \
  --set ingressClass.enabled=true \
  --set ingressClass.isDefaultClass=true \
  --set api.dashboard=true
```

Verify deployment:

```bash
kubectl get pods -n traefik
```

---

## 4. Port Forward Traefik to Port 80 (For OAuth Compatibility)

```bash
sudo KUBECONFIG=$HOME/.kube/config kubectl port-forward -n traefik svc/traefik 80:80
```

Keep this command running in a separate terminal. This makes Traefik accessible on `127.0.0.1:80`.

---

## 5. Update /etc/hosts

Edit your `/etc/hosts` file and add:

```
127.0.0.1 dev.local.com
```

> Windows: Edit `C:\Windows\System32\drivers\etc\hosts`

---

## 6. Define Traefik IngressRoute

Make sure you have a properly defined `IngressRoute` using `Host(`dev.local.com`)`. This is how Traefik knows where to route traffic.

Example:

```yaml
apiVersion: traefik.io/v1alpha1
kind: IngressRoute
metadata:
  name: easybot-ingress
  namespace: default
spec:
  entryPoints:
    - web
  routes:
    - match: Host(`dev.local.com`)
      kind: Rule
      services:
        - name: platform-web-service
          port: 80
```

Apply with:

```bash
kubectl apply -f ingressroute.yaml
```

---

## 7. Access the Application

Open your browser and visit:

```
http://dev.local.com/
```

To access the Traefik dashboard:

```
http://dev.local.com/dashboard/
```

---

## Notes

* You **do not need `minikube tunnel`** in this setup.
* Port 80 is exposed directly via `kubectl port-forward`.
* Works perfectly with OAuth flows since there is **no port number** in the URL.

---

## Optional: Create Alias for Port-Forward

You can add this to your shell config (`.bashrc` / `.zshrc`):

```bash
alias dev-forward='sudo KUBECONFIG=$HOME/.kube/config kubectl port-forward -n traefik svc/traefik 80:80'
```

Then just run:

```bash
dev-forward
```

---

You're now ready to develop locally with Kubernetes, Traefik, and a clean domain-based routing experience!
