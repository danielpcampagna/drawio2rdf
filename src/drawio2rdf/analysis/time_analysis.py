from pathlib import Path
import os

import pandas as pd
import matplotlib.pyplot as plt



def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, sep=";", names=["function", "time_s"])
    df["time"] = df["time_s"].apply(lambda x: x[:-1]).astype(float, False)
    del df["time_s"]
    return df

def plot_bar_mean(df: pd.DataFrame, output_folder: str = "./") -> None:
    result = df.groupby("function").mean()
    result.plot.bar()
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, "time_analysis-mean.png"))
    plt.cla()

def plot_bar_count(df: pd.DataFrame, output_folder: str = "./") -> None:
    result = df.groupby("function").count()
    result.plot.bar()
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, "time_analysis-count.png"))
    plt.cla()

def plot_bar_relevance(df: pd.DataFrame, output_folder: str = "./") -> None:
    result1 = df.groupby("function").count()
    result2 = df.groupby("function").mean()
    result = result1 * result2
    result.plot.bar()
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, "time_analysis-relevance.png"))
    plt.cla()

def plot_box(df: pd.DataFrame, output_folder: str = "./") -> None:
    df2 = df.groupby('function')['time'].apply(lambda df: df.reset_index(drop=True)).unstack(0)
    df2.boxplot(rot=90)
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, "time_analysis-box.png"))
    plt.cla()

if __name__ == "__main__":
    input = Path("runtime.csv")
    output_folder = input.stem
    
    df = load_data(input)
    if not os.path.exists(output_folder):
        os.mkdir(output_folder)
    
    plot_bar_mean(df, output_folder=output_folder)
    plot_bar_count(df, output_folder=output_folder)
    plot_bar_relevance(df, output_folder=output_folder)
    plot_box(df, output_folder=output_folder)