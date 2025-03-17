#Author: Bryan Kano
#Example of usage: python3 generate_fasta.py --lengths 4 8 16 32 64 --num 100

import random
import os
import argparse

# Function to generate random nucleotide sequence
def random_sequence(length):
    return ''.join(random.choices('ACGT', k=length))

# Argument parser setup
parser = argparse.ArgumentParser(description='Generate random nucleotide sequences')
parser.add_argument('--lengths', nargs='+', type=int, required=True,
                    help='List of sequence lengths')
parser.add_argument('--num', type=int, required=True,
                    help='Number of sequences per length')
args = parser.parse_args()

# Base output directory
base_output_dir = 'fasta_sequences'
os.makedirs(base_output_dir, exist_ok=True)

# Generate and save sequences
for length in args.lengths:
    output_dir = os.path.join(base_output_dir, f"{length}x{length}")
    os.makedirs(output_dir, exist_ok=True)

    for i in range(1, args.num + 1):
        seq1 = random_sequence(length)
        seq2 = random_sequence(length)

        # Save seq1
        filename1 = f"seq1_{length}_{i}.fasta"
        with open(os.path.join(output_dir, filename1), 'w') as f:
            f.write(seq1 + "\n")

        # Save seq2
        filename2 = f"seq2_{length}_{i}.fasta"
        with open(os.path.join(output_dir, filename2), 'w') as f:
            f.write(seq2 + "\n")

print("Random sequences generated in folder:", base_output_dir)
