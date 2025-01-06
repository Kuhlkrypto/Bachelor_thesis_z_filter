import os.path
import subprocess


def filter_log(log_path, z, t):
    binary_arg = os.path.join("/home/fabian/TU_DRESDEN/Bachelorarbeit/pm4py_test/z-anon-impl/target/release/z-anon-impl")

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
