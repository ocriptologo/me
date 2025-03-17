#!/usr/bin/env python3

import os
import subprocess
import argparse
import statistics
import csv
import time
import psutil

def parse_opt_tfhe_output(output_str):
    """
    Lê a saída do 'opt_tfhe' e extrai os campos relevantes.
    """
    enc_time = None
    hom_time = None
    dec_time = None
    score = None
    start_pos = None
    end_pos = None

    for line in output_str.splitlines():
        line = line.strip()
        if line.startswith("Encryption time:"):
            val = line.split(":")[1].strip().replace("s", "")
            enc_time = float(val)
        elif line.startswith("Homomorphic computation time:"):
            val = line.split(":")[1].strip().replace("s", "")
            hom_time = float(val)
        elif line.startswith("Decryption time:"):
            val = line.split(":")[1].strip().replace("s", "")
            dec_time = float(val)
        elif line.startswith("Score:"):
            val = line.split(":")[1].strip()
            score = int(val)
        elif line.startswith("Starting pos:"):
            positions = line.split(":")[1].strip().split()
            start_pos = (int(positions[0]), int(positions[1]))
        elif line.startswith("Ending pos:"):
            positions = line.split(":")[1].strip().split()
            end_pos = (int(positions[0]), int(positions[1]))

    return {
        "encryption_time": enc_time,
        "homomorphic_time": hom_time,
        "decryption_time": dec_time,
        "score": score,
        "start_pos": start_pos,
        "end_pos": end_pos
    }

def run_command_with_memory(cmd, interval=0.1):
    """
    Executa o comando 'cmd' com subprocess.Popen e monitora o uso de memória
    usando psutil enquanto o processo está em execução.
    
    Retorna uma tupla (stdout, mem_avg, mem_max).
    """
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    proc_psutil = psutil.Process(process.pid)
    mem_samples = []

    # Enquanto o processo estiver ativo, captura o uso de memória a cada 'interval' segundos.
    while process.poll() is None:
        try:
            mem_info = proc_psutil.memory_info()
            # Usaremos rss (Resident Set Size) em MB:
            mem_usage = mem_info.rss / (1024 * 1024)
            mem_samples.append(mem_usage)
        except psutil.NoSuchProcess:
            break
        time.sleep(interval)

    # Captura qualquer memória usada no fim, se possível
    try:
        mem_info = proc_psutil.memory_info()
        mem_usage = mem_info.rss / (1024 * 1024)
        mem_samples.append(mem_usage)
    except psutil.NoSuchProcess:
        pass

    stdout, stderr = process.communicate()
    mem_avg = statistics.mean(mem_samples) if mem_samples else None
    mem_max = max(mem_samples) if mem_samples else None

    return stdout, mem_avg, mem_max

def main():
    parser = argparse.ArgumentParser(description="Automatiza execuções do opt_tfhe com monitoramento de memória.")
    parser.add_argument("--sizes", nargs="+", type=int, required=True,
                        help="Lista de tamanhos de sequência, ex: 4 8 16")
    parser.add_argument("--pairs", type=int, default=1,
                        help="Quantos pares de seq1/seq2 serão testados em cada tamanho")
    parser.add_argument("--reps", type=int, default=1,
                        help="Quantas repetições para cada par de arquivos")
    parser.add_argument("--fasta_dir", type=str, default="fasta_sequences",
                        help="Diretório base que contém as subpastas (4x4, 8x8, etc.)")
    parser.add_argument("--executable", type=str, default="./opt_tfhe",
                        help="Caminho para o executável opt_tfhe")
    parser.add_argument("--scores", type=str, default="5,-3,-9,-1",
                        help="String com parâmetros de score para o opt_tfhe (ex: 5,-3,-9,-1)")
    parser.add_argument("--output_dir", type=str, default="results",
                        help="Pasta onde serão gravados os arquivos de resultado (CSV).")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    # CSV com todas as execuções
    results_csv_path = os.path.join(args.output_dir, "all_runs.csv")
    # CSV com estatísticas para cada par
    summary_csv_path = os.path.join(args.output_dir, "summary.csv")

    summary_data = []

    with open(results_csv_path, "w", newline="") as rf:
        writer = csv.writer(rf)
        writer.writerow([
            "size", "pair_index", "repetition",
            "encryption_time", "homomorphic_time", "decryption_time",
            "score", "start_pos", "end_pos",
            "mem_avg_MB", "mem_max_MB"
        ])

        for size in args.sizes:
            folder_name = f"{size}x{size}"
            folder_path = os.path.join(args.fasta_dir, folder_name)

            if not os.path.isdir(folder_path):
                print(f"[AVISO] Diretório {folder_path} não existe. Pulando...")
                continue

            for pair_index in range(1, args.pairs + 1):
                seq1_name = f"seq1_{size}_{pair_index}.fasta"
                seq2_name = f"seq2_{size}_{pair_index}.fasta"

                seq1_path = os.path.join(folder_path, seq1_name)
                seq2_path = os.path.join(folder_path, seq2_name)

                if not os.path.isfile(seq1_path) or not os.path.isfile(seq2_path):
                    print(f"[AVISO] Faltam arquivos {seq1_path} ou {seq2_path}. Pulando par {pair_index} em {folder_name}.")
                    continue

                pair_results = []

                for rep in range(1, args.reps + 1):
                    # Divide os scores em argumentos individuais
                    score_args = args.scores.split(',')
                    cmd = [args.executable, seq1_path, seq2_path] + score_args

                    print(f"Executando: {' '.join(cmd)} (rep: {rep})")
                    # Executa o comando e monitora o uso de memória
                    output_str, mem_avg, mem_max = run_command_with_memory(cmd)
                    parsed = parse_opt_tfhe_output(output_str)

                    writer.writerow([
                        size,
                        pair_index,
                        rep,
                        parsed["encryption_time"],
                        parsed["homomorphic_time"],
                        parsed["decryption_time"],
                        parsed["score"],
                        parsed["start_pos"],
                        parsed["end_pos"],
                        mem_avg,
                        mem_max
                    ])

                    # Adiciona os dados de memória ao dicionário de resultados para estatísticas
                    parsed["mem_avg"] = mem_avg
                    parsed["mem_max"] = mem_max
                    pair_results.append(parsed)

                if pair_results:
                    def compute_stats(values):
                        values = [v for v in values if v is not None]
                        if not values:
                            return (None, None, None, None)
                        mean_val = statistics.mean(values)
                        stdev_val = statistics.pstdev(values) if len(values) > 1 else 0.0
                        return (mean_val, stdev_val, min(values), max(values))

                    enc_times = [r["encryption_time"] for r in pair_results]
                    hom_times = [r["homomorphic_time"] for r in pair_results]
                    dec_times = [r["decryption_time"] for r in pair_results]
                    scores    = [r["score"] for r in pair_results]
                    mem_avgs  = [r["mem_avg"] for r in pair_results]
                    mem_maxs  = [r["mem_max"] for r in pair_results]

                    enc_mean, enc_stdev, enc_min, enc_max = compute_stats(enc_times)
                    hom_mean, hom_stdev, hom_min, hom_max = compute_stats(hom_times)
                    dec_mean, dec_stdev, dec_min, dec_max = compute_stats(dec_times)
                    sco_mean, sco_stdev, sco_min, sco_max = compute_stats(scores)
                    mem_avg_mean, mem_avg_stdev, mem_avg_min, mem_avg_max = compute_stats(mem_avgs)
                    mem_max_mean, mem_max_stdev, mem_max_min, mem_max_max = compute_stats(mem_maxs)

                    summary_data.append({
                        "size": size,
                        "pair_index": pair_index,
                        "repetitions": len(pair_results),

                        "enc_mean": enc_mean,
                        "enc_stdev": enc_stdev,
                        "enc_min": enc_min,
                        "enc_max": enc_max,

                        "hom_mean": hom_mean,
                        "hom_stdev": hom_stdev,
                        "hom_min": hom_min,
                        "hom_max": hom_max,

                        "dec_mean": dec_mean,
                        "dec_stdev": dec_stdev,
                        "dec_min": dec_min,
                        "dec_max": dec_max,

                        "score_mean": sco_mean,
                        "score_stdev": sco_stdev,
                        "score_min": sco_min,
                        "score_max": sco_max,

                        "mem_avg_mean": mem_avg_mean,
                        "mem_avg_stdev": mem_avg_stdev,
                        "mem_avg_min": mem_avg_min,
                        "mem_avg_max": mem_avg_max,

                        "mem_max_mean": mem_max_mean,
                        "mem_max_stdev": mem_max_stdev,
                        "mem_max_min": mem_max_min,
                        "mem_max_max": mem_max_max,
                    })

    with open(summary_csv_path, "w", newline="") as sf:
        writer = csv.writer(sf)
        writer.writerow([
            "size", "pair_index", "repetitions",
            "enc_mean", "enc_stdev", "enc_min", "enc_max",
            "hom_mean", "hom_stdev", "hom_min", "hom_max",
            "dec_mean", "dec_stdev", "dec_min", "dec_max",
            "score_mean", "score_stdev", "score_min", "score_max",
            "mem_avg_mean", "mem_avg_stdev", "mem_avg_min", "mem_avg_max",
            "mem_max_mean", "mem_max_stdev", "mem_max_min", "mem_max_max"
        ])

        for row in summary_data:
            writer.writerow([
                row["size"],
                row["pair_index"],
                row["repetitions"],

                row["enc_mean"], row["enc_stdev"], row["enc_min"], row["enc_max"],
                row["hom_mean"], row["hom_stdev"], row["hom_min"], row["hom_max"],
                row["dec_mean"], row["dec_stdev"], row["dec_min"], row["dec_max"],
                row["score_mean"], row["score_stdev"], row["score_min"], row["score_max"],
                row["mem_avg_mean"], row["mem_avg_stdev"], row["mem_avg_min"], row["mem_avg_max"],
                row["mem_max_mean"], row["mem_max_stdev"], row["mem_max_min"], row["mem_max_max"]
            ])

if __name__ == "__main__":
    main()
