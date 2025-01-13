import os.path
import subprocess


def filter_log(log_path, z, t):
    print("Start")
    binary_arg = os.path.join("/home/fabian/Github/Bachelor_thesis_z_filter/z_filtering/target/release/z-anon-impl")

    try:
        res = subprocess.run(
            [binary_arg,
             log_path,
             str(z),
             str(t)],
            check=True,
            text=True,
            capture_output=True  # Um die Ausgabe zu erfassen
        )
        res.check_returncode()

    except subprocess.CalledProcessError as e:
        print(f"Raised error{e.stderr}")
        exit(1)

filter_log("/home/fabian/TU_DRESDEN/PrivateMine/SOURCED/data/Sepsis_Cases-Event_Log.xes", 1, "3600h")