#!/bin/sh
# Configuration de Vault pour monapi (mode dev).
# À exécuter DANS le pod Vault :
#   kubectl exec -n vault -i vault-0 -- sh < vault/configure-vault.sh
set -eu

# 1. Le secret, dans le moteur KV v2 monté sur secret/.
#    Nouvelle valeur aléatoire : l'ancienne a été commitée dans k8s/secret.yaml,
#    elle est donc considérée comme compromise (rotation).
vault kv put secret/monapi/config \
  storage_key="$(head -c 32 /dev/urandom | base64 | tr -d '\n')"

# 2. Authentification Kubernetes : Vault vérifiera l'identité des pods
#    (leur jeton de ServiceAccount) auprès de l'API Kubernetes.
vault auth list | grep -q '^kubernetes/' || vault auth enable kubernetes
vault write auth/kubernetes/config \
  kubernetes_host="https://$KUBERNETES_SERVICE_HOST:$KUBERNETES_SERVICE_PORT"

# 3. Politique Vault : lecture seule, sur ce seul chemin (moindre privilège).
vault policy write monapi - <<'HCL'
path "secret/data/monapi/config" {
  capabilities = ["read"]
}
HCL

# 4. Rôle : seul le ServiceAccount monapi du namespace default obtient
#    un jeton Vault, valable 10 minutes, avec la politique monapi.
vault write auth/kubernetes/role/monapi \
  bound_service_account_names=monapi \
  bound_service_account_namespaces=default \
  token_policies=monapi \
  token_ttl=10m \
  audience="https://kubernetes.default.svc.cluster.local"
