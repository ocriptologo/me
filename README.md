g++  par_circuit.cpp seq_circuit.cpp eval.cpp main.cpp -o opt_tfhe -ltfhe-spqlios-fma -fopenmp -DPOSITION
g++  par_circuit.cpp seq_circuit.cpp eval.cpp main.cpp -o opt_tfhe -ltfhe-spqlios-fma -fopenmp
python3 methodology.py --sizes 4 --pairs 1 --reps 2 --fasta_dir fasta_sequences --executable ./case1 --scores 1,-8,-5,-3 --output_dir results
python3 methodology.py --sizes 4 --pairs 1 --reps 2 --fasta_dir fasta_sequences --executable ./case2 --scores 1,-8,-5,-3 --output_dir results
