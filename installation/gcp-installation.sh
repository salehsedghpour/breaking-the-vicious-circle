#!/bin/sh
echo "Creating 4 VM instances on GCP"
echo "It may take a while ...\n"

gcloud deployment-manager deployments create hydragen-experiments --config ./gcp/deployment.yaml
sleep 30

# Copying the installation scripts to the nodes
echo "\nCopying all required scripts to the nodes ..."
gcloud compute scp --recurse --zone "europe-north1-a" ./scripts hydragen-k8s-master:~ > /dev/null 2>&1
gcloud compute scp --recurse --zone "europe-north1-a" ./scripts hydragen-k8s-worker-1:~ > /dev/null 2>&1
gcloud compute scp --recurse --zone "europe-north1-a" ./scripts hydragen-k8s-worker-2:~ > /dev/null 2>&1
gcloud compute scp --recurse --zone "europe-north1-a" ./scripts hydragen-k8s-worker-3:~ > /dev/null 2>&1


echo "\nInstalling required setup on Master node"
echo "Installing Docker ..."
gcloud compute ssh --zone "europe-north1-a" "hydragen-k8s-master" --command "sudo bash ~/scripts/docker.sh"
gcloud compute ssh --zone "europe-north1-a" "hydragen-k8s-master" --command "sudo usermod -aG docker $USER"
echo "Installing Kubernetes ..."
gcloud compute ssh --zone "europe-north1-a" "hydragen-k8s-master" --command "sudo bash ~/scripts/k8s.sh"
echo "Initializing Kubernetes and installing Cilium CNI ..."
MASTER_PUBLIC_IP=$(gcloud compute instances list --filter='name=hydragen-k8s-master' --format 'get(networkInterfaces[0].accessConfigs[0].natIP)')
MASTER_PRIVATE_IP=$(gcloud compute instances list --filter='name=hydragen-k8s-master' --format 'get(networkInterfaces[0].networkIP)') 
gcloud compute ssh --zone "europe-north1-a" "hydragen-k8s-master" --command "sudo kubeadm init --pod-network-cidr 10.244.0.0/16 --apiserver-advertise-address=$MASTER_PRIVATE_IP --apiserver-cert-extra-sans=$MASTER_PRIVATE_IP,$MASTER_PUBLIC_IP  > /dev/null 2>&1"
gcloud compute ssh --zone "europe-north1-a" "hydragen-k8s-master" --command "bash ~/scripts/post-k8s.sh"
gcloud compute ssh --zone "europe-north1-a" "hydragen-k8s-master" --command "kubectl config set-cluster kubernetes --server=https://$MASTER_PUBLIC_IP:6443  > /dev/null 2>&1"
gcloud compute scp --recurse --zone "europe-north1-a" hydragen-k8s-master:~/.kube/config ~/.kube/config > /dev/null 2>&1

var=$(gcloud compute ssh --zone 'europe-north1-a' hydragen-k8s-master --command 'kubeadm token create --print-join-command')

echo "\nInstalling required setup on Worker-1"
gcloud compute ssh --zone "europe-north1-a" "hydragen-k8s-worker-1" --command "sudo bash ~/scripts/docker.sh"
gcloud compute ssh --zone "europe-north1-a" "hydragen-k8s-worker-1" --command "sudo bash ~/scripts/k8s.sh"
gcloud compute ssh --zone "europe-north1-a" "hydragen-k8s-worker-1" --command "sudo $var > /dev/null 2>&1"

echo "\nInstalling required setup on Worker-2"
gcloud compute ssh --zone "europe-north1-a" "hydragen-k8s-worker-2" --command "sudo bash ~/scripts/docker.sh"
gcloud compute ssh --zone "europe-north1-a" "hydragen-k8s-worker-2" --command "sudo bash ~/scripts/k8s.sh"
gcloud compute ssh --zone "europe-north1-a" "hydragen-k8s-worker-2" --command "sudo $var > /dev/null 2>&1"

echo "\nInstalling required setup on Worker-3"
gcloud compute ssh --zone "europe-north1-a" "hydragen-k8s-worker-3" --command "sudo bash ~/scripts/docker.sh"
gcloud compute ssh --zone "europe-north1-a" "hydragen-k8s-worker-3" --command "sudo bash ~/scripts/k8s.sh"
gcloud compute ssh --zone "europe-north1-a" "hydragen-k8s-worker-3" --command "sudo $var > /dev/null 2>&1"

echo "\nInstalling Istio ..."
gcloud compute ssh --zone "europe-north1-a" "hydragen-k8s-master"   --command "bash ~/scripts/mesh.sh"

echo "\nInstalling Prometheus ..."
kubectl apply -f addons/namespaces/monitoring.yaml > /dev/null 2>&1
kubectl apply -f addons/prometheus/ > /dev/null 2>&1

echo "\nInstalling Push Gateway ..."
kubectl apply -f addons/pushgateway/ > /dev/null 2>&1

# Creating namespace for the experiments that istio sidecar will be automatically injectel
kubectl apply -f addons/namespaces/experiments.yaml > /dev/null 2>&1