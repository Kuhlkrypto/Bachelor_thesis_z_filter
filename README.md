# Bachelor Thesis Repository

## 📖 Overview
This repository contains the code and resources for my Bachelor's thesis titled **"Privacy and Utility in Process Discovery: Navigating the duality through Activity Filtering"**. 
The research focuses on as often activity filtering is suitable as a privacy-preserving technique in process discovery 
while also enhancing or at least maintaining the utility of process models, thereby challenging a perception of privacy and utility being inherently opposing.

This repository contains three applications: `data_parser`, `z_filtering`, and `evaluation`.

The `data_parser` converts event logs from the XES format into CSV format.
The `z_filtering` application filters event logs that have been processed by `data_parser`, based on specified relative and absolute z-values and a time parameter. These parameters can be set in the `evaluation/constants.py` file.

The evaluation algorithm is the core component of this thesis. It automatically applies the z_filtering process to event logs according to specified settings and subsequently evaluates the quality of process models discovered using the filtered event logs.

The following sections primarily describe how to run the evaluation algorithm using the executable versions of `data_parser` and `z_filtering`.
## 📌 Table of Contents
- [Overview](#-overview)
- [Project Structure](#-project-structure)
- [Installation](#-installation)
- [Usage](#-usage)
- [Technologies Used](#-technologies-used)

## 📂 Project Structure
```
├── data_parser/                # Dataset and preprocessing scripts
├── evaluation/                 # Source code of the project
├── z_filtering/                # application for the balanced and basic z filters
├── executables/                # Outputs, graphs, or evaluation results
├── Dockerfile                  # Dockerfile for setting up this project as docker image
├── results_measurements.zip    # results of measurements
├── requirements.txt            # requirements needed for the evaluation framework using python
└── README.md      
```

## ⚙️ Installation
To set up the project, follow these steps:
```bash
# Clone the repository
git clone https://github.com/Kuhlkrypto/Bachelor_thesis_z_filter.git
cd Bachelor_thesis_z_filter

# Install dependencies
pip install -r requirements.txt
```

If you do not trust the provided executables in the executables folder, you will need to install the necessary technologies manually, including the Logfile-parser and Sourced-simulator, as well as Rust's Tokio framework. 
To generate new executables you must modify the Cargo manifest to align with your local installation.

Alternatively, you can use the Dockerfile to run this project.
```bash
# build dokcer container 
docker build -t eval-pm4py .  

# make sure to have the directories data_xes, data_work, tmp and results in your current working directory
# Place xes files you want to be assessed in data_xes directory
# RUN
docker run --rm \                                                                            
 -v $(pwd)/tmp:/app/tmp \
 -v $(pwd)/data_xes_/app/data_xes \
 -v $(pwd)/data_work:/app/data_work \
 -v $(pwd)/evaluation:/app/evaluation \
 -v $(pwd)/results:/app/results -eval-pm4py
 
```

## 🚀 Usage
If you want to reproduce the experiments and trust the executables in the `executables` folder, you can place the event logs you want to investigate into a directory called `data_xes`.
The current parser implementation supports the following event logs:

1. [Sepsis Case Event Log](https://data.4tu.nl/articles/_/12707639/1)
2. [Real-life Hospital Log](https://data.4tu.nl/articles/_/12716513/1)
3. [BPI Challenge 2012](https://data.4tu.nl/articles/_/12689204/1)
4. [BPI Challenge 2017](https://data.4tu.nl/articles/_/12696884/1)
5. [BPI Challenge 2018](https://data.4tu.nl/articles/_/12688355/1)
6. [Road Traffic Fine Management](https://data.4tu.nl/articles/_/12683249/1)

After storing .xes files in the appropriate directory, parse them into the desired CSV format. The parser will create a directory called `data_work`:

```bash
./executables/data-parser
```
Now, navigate to `evaluation/constants.py` and specify the `z` values for filtering event logs, the time parameters, and other relevant settings. 
You may also define how many points should be considered for risk evaluation (relative and absolute) and whether to measure model quality, 
reference model quality, and risk evaluation, as well as enabling multiprocessing for the algorithm.

Once the configuration is complete, run the evaluation algorithm:
Run the evaluation algorithm:
```bash
python3 evaluation/main.py 
```
Ensure you start the algorithm from the working directory Bachelor_thesis_z_filter.

The algorithm will place results in the results directory.
This process may take some time, especially if alignment methods are enabled in constants.py.

## 🛠️ Technologies Used
- Python (e.g., NumPy, Pandas, Scikit-learn)
- Rust (Tokio)
- [Logfile-parser and Sourced-simulator](https://gitlab.mn.tu-dresden.de/sourced/logfile-parser)
