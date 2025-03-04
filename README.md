# Bachelor Thesis Repository

## 📖 Overview
This repository contains the code and resources for my Bachelor's thesis titled **"Privacy and Utility in Process Discovery: Navigating the duality through Activity Filtering"**. 
The research focuses on as often activity filtering is suitable as a privacy-preserving technique in process discovery 
while also enhancing or at least maintaining the utility of process models, thereby challenging a perception of privacy and utility being inherently opposing.

## 📌 Table of Contents
- [Overview](#-overview)
- [Project Structure](#-project-structure)
- [Installation](#-installation)
- [Usage](#-usage)
- [Results](#-results)
- [Technologies Used](#-technologies-used)

## 📂 Project Structure
```
├── data_parser/          # Dataset and preprocessing scripts
├── evaluation/           # Source code of the project
├── z_filter/             # Jupyter Notebooks for experiments
├── executables/          # Outputs, graphs, or evaluation results
├── Dockerfile            
├── requirements.txt      # requirements needed for the evaluation framework using python
└── README.md      
```

## ⚙️ Installation
To set up the project, follow these steps:
```bash
# Clone the repository
git clone https://github.com/yourusername/your-repository.git
cd your-repository

# Install dependencies
pip install -r requirements.txt
```

## 🚀 Usage
If you just want to reproduce the experiments you can go ahead and place the event logs you want to investigate in a directory called `data_xes`. 
The current parser implementation supports following event logs:

    1. [Sepsis Case Event Log](https://data.4tu.nl/articles/_/12707639/1)
    2. Real-life Hospital Log
    3. BPI Challenge 2012
    4. BPI Challenge 2017
    5. BPI Challenge 2018
    6. Road Traffic Fine Management 



```bash
./executables/data-parser
```

Run the evaluation algorithm:
```bash
python3 evaluation/main.py 
```


## 📊 Results
Briefly summarize your key findings and include relevant charts or tables.

## 🛠️ Technologies Used
- Python (e.g., NumPy, Pandas, Scikit-learn)
- Rust (Tokio)
- [Other relevant technologies]
