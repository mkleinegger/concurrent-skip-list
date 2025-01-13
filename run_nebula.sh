# Author: Natalia Tylek (12332258), Marlene Riegel (01620782), Maximilian Kleinegger (12041500)
# Created: 2025-01-13

ZIP_FILE=$1
TARGET=$2
LOG_FILE=nebula.log
LOG_SMALL_BENCH=nebula_small_bench.log
DATA_DIR=data
USERNAME="amp24w28" # Explicitly set your username for nebula

function copy_to_nebula {
    scp $ZIP_FILE "$USERNAME@nebula:~/test/$ZIP_FILE"
}

function copy_from_nebula {
    mkdir -p $DATA_DIR
    scp -r "$USERNAME@nebula:~/test/uut/data/*" $DATA_DIR
}

function clean_test_dir {
    ssh "$USERNAME@nebula" "mkdir -p test"
    ssh "$USERNAME@nebula" "\
        cd test
        rm -rf *"
}

function run_on_nebula {
    ssh "$USERNAME@nebula" "\
        cd test
        unzip -u $ZIP_FILE -d uut &&
        cd uut &&
        make

        /usr/local/slurm/bin/srun -t 1 -p q_student make $TARGET &

        JOB_ID=\$(/usr/local/slurm/bin/squeue -u $USERNAME | awk 'NR==2 {print \$1}')
        while /usr/local/slurm/bin/squeue -u $USERNAME | grep -q \$JOB_ID; do
            /usr/local/slurm/bin/squeue -u $USERNAME
            sleep 10
        done

        echo 'done'" | tee $LOG_FILE
}

if [ ! $# = 2 ]; then
    echo "Error: first argument has to be a .zip archive"
    echo "Error: second argument has to be a valid make target, i.e., small-bench"
    exit 1
fi

clean_test_dir      &&
copy_to_nebula      &&
run_on_nebula       &&
copy_from_nebula
