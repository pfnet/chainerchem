set -eu

gpu=-1

for method in nfp ggnn schnet weavenet rsgcn
do
    echo ${method}
    python train_tox21.py --method ${method} --gpu ${gpu} 
done