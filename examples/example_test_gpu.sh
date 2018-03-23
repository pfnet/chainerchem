#!/usr/bin/env bash

set -e

gpu=0

for method in nfp ggnn schnet weavenet rsgcn
do
    # Tox21
    cd tox21
    if [ ! -f "input" ]; then
        rm -rf input
    fi

    out_dir=nr_ar_${method}
    python train_tox21.py --method ${method} --label NR-AR --conv-layers 1 --gpu ${gpu} --epoch 1 --unit-num 10 --out ${out_dir}
    python inference_tox21.py --in-dir ${out_dir} --gpu ${gpu}
    snapshot=`ls ${out_dir}/snapshot_iter_* | head -1`
    python inference_tox21.py --in-dir ${out_dir} --gpu ${gpu} --trainer-snapshot ${snapshot}

    out_dir=all_${method}
    python train_tox21.py --method ${method} --conv-layers 1 --gpu ${gpu} --epoch 1 --unit-num 10 --out ${out_dir}
    python inference_tox21.py --in-dir ${out_dir}
    snapshot=`ls ${out_dir}/snapshot_iter_* | head -1`
    python inference_tox21.py --in-dir ${out_dir} --gpu ${gpu} --trainer-snapshot ${snapshot}
    cd ../

    # QM9
    cd qm9
    if [ ! -f "input" ]; then
        rm -rf input
    fi

    python train_qm9.py --method ${method} --label A --conv-layers 1 --gpu ${gpu} --epoch 1 --unit-num 10
    python train_qm9.py --method ${method} --conv-layers 1 --gpu ${gpu} --epoch 1 --unit-num 10
    cd ../
done

cd tox21
# BalancedSerialIterator test with Tox21
python train_tox21.py --method nfp --label NR-AR --conv-layers 1 --gpu ${gpu} --epoch 1 --unit-num 10 --out nr_ar_nfp_balanced --iterator-type balanced --eval-mode 0
python inference_tox21.py --in-dir nr_ar_nfp_balanced --gpu ${gpu}
# ROCAUCEvaluator test with Tox21
python train_tox21.py --method nfp --label NR-AR --conv-layers 1 --gpu ${gpu} --epoch 1 --unit-num 10 --out nr_ar_nfp_balanced --iterator-type serial --eval-mode 1
cd ..
